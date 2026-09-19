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
import os
import time

import numpy as np
import pandas as pd

from app.config import get_settings
from app.data.cache import cached

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

        yf_sym = f"{symbol.replace('&', '')}.NS"
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


def _full_history(symbol: str, drift_hint: float) -> list[dict]:
    settings = get_settings()
    path = _disk_path(symbol)

    if settings.live_data:
        if path:
            disk = _read_disk_fresh(path)
            if disk:
                return disk
        df = _live_yf(symbol)
        if df is not None:
            recs = _records_from_df(df)
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


def get_ohlcv(symbol: str, days: int = 260, drift_hint: float = 0.0) -> pd.DataFrame:
    """Return the last `days` sessions for `symbol` (from one cached long series)."""
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
