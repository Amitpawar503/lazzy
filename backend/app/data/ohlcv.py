"""OHLCV history per symbol.

Fast by default: a deterministic synthetic series (seeded per symbol, no network)
so every screen loads instantly. Turn on `LIVE_DATA=true` to fetch real history
(yfinance ~1y). One long series is fetched/generated per symbol and cached; all
callers slice what they need (momentum 260, seasonal ~780) from that single copy
— no duplicate fetches. With `DATA_STORE_DIR` set, live history is persisted to
JSON on disk and refreshed at most once per day.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import logging
import os
import threading
import time

import numpy as np
import pandas as pd

from app.config import get_settings
from app.data.cache import cached

log = logging.getLogger("lazzy.ohlcv")

# Keep enough history for the longest consumer (5-year backtests ≈ 1250 sessions).
_KEEP = 1300


def _seed(symbol: str) -> int:
    return int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)


def _synthetic(symbol: str, days: int, drift_hint: float) -> pd.DataFrame:
    rng = np.random.default_rng(_seed(symbol))
    base = 100 + (_seed(symbol) % 3000)
    daily_drift = (drift_hint / 100.0) / 21.0 * 0.6 + (rng.normal(0, 1) * 0.0002)
    vol = 0.012 + (rng.random() * 0.012)
    shocks = rng.normal(daily_drift, vol, days)
    close = base * np.cumprod(1 + shocks)
    intraday = np.abs(rng.normal(0, vol, days))
    high = close * (1 + intraday)
    low = close * (1 - intraday)
    open_ = np.concatenate([[close[0]], close[:-1]])
    volume = rng.integers(2_00_000, 50_00_000, days)
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=idx,
    )


def _live_yf(symbol: str) -> pd.DataFrame | None:
    try:
        import yfinance as yf  # type: ignore

        from app.data.yf_symbols import quiet_yfinance_logging, yf_ticker

        quiet_yfinance_logging()
        yf_sym = yf_ticker(symbol)
        if not yf_sym:                       # known-delisted → skip (use synthetic)
            return None
        df = yf.download(
            yf_sym, period="2y", interval="1d", auto_adjust=True, progress=False
        )
        if df is None or len(df) < 60:
            return None
        df = df.rename(
            columns={"Open": "open", "High": "high", "Low": "low",
                     "Close": "close", "Volume": "volume"}
        )[["open", "high", "low", "close", "volume"]].tail(_KEEP)
        return df
    except Exception:
        return None


def _records_from_df(df: pd.DataFrame) -> list[dict]:
    out = df.reset_index()
    out.columns = ["date", "open", "high", "low", "close", "volume"]
    out["date"] = out["date"].astype(str)
    return out.to_dict("records")


def _disk_path(symbol: str) -> str | None:
    d = get_settings().data_store_dir
    if not d:
        return None
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{symbol.replace('/', '_')}.json")


def _read_disk_fresh(path: str) -> list[dict] | None:
    try:
        mtime = _dt.date.fromtimestamp(os.path.getmtime(path))
        if mtime < _dt.date.today():
            return None  # stale — refresh once per day
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def _history_from(prov: str, symbol: str) -> list[dict] | None:
    """EOD history for one symbol from a named provider, or None."""
    try:
        if prov == "fmp":
            from app.data.live_providers import fmp_history
            return fmp_history(symbol, _KEEP)
        if prov == "dhan":
            from app.data.dhan_provider import dhan_history
            return dhan_history(symbol, _KEEP)
        if prov == "yfinance":
            df = _live_yf(symbol)
            return _records_from_df(df) if df is not None else None
    except Exception:
        return None
    return None


def _full_history(symbol: str, drift_hint: float) -> list[dict]:
    settings = get_settings()
    prov = settings.provider()
    path = _disk_path(symbol)

    if prov != "sample":
        if path:
            disk = _read_disk_fresh(path)
            if disk:
                return disk
        # Try the effective provider, then the free fallback (e.g. Dhan not
        # subscribed → yfinance), before synthetic.
        recs = None
        tried: list[str] = []
        for p in (prov, settings.data_provider_fallback):
            p = (p or "").lower()
            if not p or p == "sample" or p in tried:
                continue
            tried.append(p)
            recs = _history_from(p, symbol)
            if recs:
                break
        if recs:
            if path:
                try:
                    with open(path, "w") as f:
                        json.dump(recs, f)
                except Exception:
                    pass
            return recs
        # live requested but unavailable → synthetic fallback (still fast)

    return _records_from_df(_synthetic(symbol, _KEEP, drift_hint))


# In-process cache of the *constructed* DataFrame per symbol (rebuilding a
# DataFrame from records on every call was the hot path when backtesting 100+
# baskets). Keyed by symbol; slice to `days` per caller.
_DF_CACHE: dict[str, tuple[float, pd.DataFrame]] = {}


# One-shot bulk warm: fetch the WHOLE universe's history in a single yfinance
# call and fill the in-memory cache, instead of N sequential per-symbol
# downloads. Turns the first universe-wide screen from ~minutes to ~seconds.
_BULK_DONE = False
_BULK_LOCK = threading.Lock()


def _maybe_bulk_warm() -> None:
    global _BULK_DONE
    if _BULK_DONE:
        return
    s = get_settings()
    provs = [(s.provider() or "").lower(), (s.data_provider_fallback or "").lower()]
    if "yfinance" not in provs:
        return  # only yfinance benefits from a single grouped download
    with _BULK_LOCK:
        if _BULK_DONE:
            return
        _BULK_DONE = True
        try:
            import yfinance as yf  # type: ignore

            from app.data.universe import get_universe
            from app.data.yf_symbols import quiet_yfinance_logging, yf_ticker

            quiet_yfinance_logging()
            rows = get_universe()
            mp = {r["symbol"]: yf_ticker(r["symbol"]) for r in rows}
            tickers = [t for t in mp.values() if t]
            if not tickers:
                return
            log.info("[ohlcv] bulk-warming %d symbols' history from yfinance (one call)…",
                     len(tickers))
            data = yf.download(tickers, period="2y", interval="1d", group_by="ticker",
                               auto_adjust=True, progress=False, threads=True)
            if data is None or len(data) == 0:
                log.warning("[ohlcv] bulk warm returned no data")
                return
            now = time.time()
            ttl = s.cache_ttl_seconds
            filled = 0
            for sym, tk in mp.items():
                if not tk:
                    continue
                try:
                    sub = data[tk][["Open", "High", "Low", "Close", "Volume"]].dropna()
                    if len(sub) < 20:
                        continue
                    sub = sub.rename(columns={"Open": "open", "High": "high", "Low": "low",
                                              "Close": "close", "Volume": "volume"}).tail(_KEEP)
                    recs = _records_from_df(sub)
                    df = pd.DataFrame(recs).set_index("date")
                    _DF_CACHE[sym] = (now + ttl, df)
                    path = _disk_path(sym)
                    if path:
                        try:
                            with open(path, "w") as f:
                                json.dump(recs, f)
                        except Exception:
                            pass
                    filled += 1
                except Exception:
                    continue
            log.info("[ohlcv] bulk warm filled history for %d/%d symbols", filled, len(tickers))
        except Exception as e:
            log.warning("[ohlcv] bulk warm failed (%s) → per-symbol fetch", e)


def get_ohlcv(symbol: str, days: int = 260, drift_hint: float = 0.0) -> pd.DataFrame:
    """Return the last `days` sessions for `symbol` (from one cached long series)."""
    _maybe_bulk_warm()
    ttl = get_settings().cache_ttl_seconds
    now = time.time()
    ent = _DF_CACHE.get(symbol)
    if ent is None or ent[0] <= now:
        records = cached(f"ohlcv:{symbol}:v2", ttl, lambda: _full_history(symbol, drift_hint))
        df = pd.DataFrame(records).set_index("date")
        _DF_CACHE[symbol] = (now + ttl, df)
    else:
        df = ent[1]
    return df.tail(max(1, days))
