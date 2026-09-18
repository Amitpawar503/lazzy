"""OHLCV history per symbol — live (yfinance) with a deterministic synthetic
fallback so indicators compute offline.

The synthetic series is seeded from the symbol (stable across runs) and nudged
by the sample 1-month return so the latest trend roughly matches the heatmaps.
Returns a pandas DataFrame indexed by date with open/high/low/close/volume.
"""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from app.config import get_settings
from app.data.cache import cached


def _seed(symbol: str) -> int:
    return int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)


def _synthetic(symbol: str, days: int, drift_hint: float) -> pd.DataFrame:
    rng = np.random.default_rng(_seed(symbol))
    base = 100 + (_seed(symbol) % 3000)          # stable per-symbol base price
    # daily drift: blend a small symbol-specific bias with the 1m return hint
    daily_drift = (drift_hint / 100.0) / 21.0 * 0.6 + (rng.normal(0, 1) * 0.0002)
    vol = 0.012 + (rng.random() * 0.012)          # 1.2%–2.4% daily vol
    shocks = rng.normal(daily_drift, vol, days)
    close = base * np.cumprod(1 + shocks)
    # build OHLC around close
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


def _live(symbol: str, days: int) -> pd.DataFrame | None:
    try:
        import yfinance as yf  # type: ignore

        yf_sym = f"{symbol.replace('&', '')}.NS"
        df = yf.download(
            yf_sym, period="1y", interval="1d",
            auto_adjust=True, progress=False,
        )
        if df is None or len(df) < 60:
            return None
        df = df.rename(
            columns={"Open": "open", "High": "high", "Low": "low",
                     "Close": "close", "Volume": "volume"}
        )[["open", "high", "low", "close", "volume"]].tail(days)
        return df
    except Exception:
        return None


def get_ohlcv(symbol: str, days: int = 260, drift_hint: float = 0.0) -> pd.DataFrame:
    def _load() -> list[dict]:
        df = _live(symbol, days)
        if df is None:
            df = _synthetic(symbol, days, drift_hint)
        out = df.reset_index()
        out.columns = ["date", "open", "high", "low", "close", "volume"]
        out["date"] = out["date"].astype(str)
        return out.to_dict("records")

    ttl = get_settings().cache_ttl_seconds
    records = cached(f"ohlcv:{symbol}:{days}:v1", ttl, _load)
    df = pd.DataFrame(records).set_index("date")
    return df
