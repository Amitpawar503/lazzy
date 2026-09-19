"""Lightweight equal-weight basket backtest.

Given a list of symbols, build an equal-weight daily-return series from their
cached OHLCV history and compute: total return (since inception of the window),
1-year and (up to) 5-year returns, annualised volatility, max drawdown, Sharpe,
plus the same for a NIFTY-style benchmark (equal-weight universe) so we can show
alpha and whether a strategy actually beats the market. A downsampled equity
curve is returned for the card sparkline.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.config import get_settings
from app.data.cache import cached
from app.data.ohlcv import get_ohlcv
from app.data.universe import get_universe

_YEAR = 252


def _daily(symbol: str, drift: float, days: int) -> pd.Series:
    df = get_ohlcv(symbol, days=days, drift_hint=drift)
    return df["close"].astype(float).reset_index(drop=True).pct_change()


def _basket(symbols: list[str], meta: dict, days: int) -> pd.Series:
    cols = []
    for s in symbols:
        drift = meta.get(s, {}).get("ret_1m", 0.0)
        cols.append(_daily(s, drift, days))
    if not cols:
        return pd.Series(dtype=float)
    df = pd.concat(cols, axis=1)
    return df.mean(axis=1).dropna()


def _sparkline(cum: pd.Series, points: int = 48) -> list[float]:
    if len(cum) == 0:
        return []
    step = max(1, len(cum) // points)
    vals = (cum.iloc[::step] * 100).round(2).tolist()
    return vals[-points:]


def _window_return(daily: pd.Series, n: int) -> float:
    tail = daily.tail(n)
    if len(tail) == 0:
        return 0.0
    return round((float((1 + tail).prod()) - 1) * 100, 1)


def _stats(daily: pd.Series) -> dict:
    daily = daily.dropna()
    if len(daily) < 5:
        return {"total_return": 0.0, "ret_1y": 0.0, "ret_5y": 0.0,
                "volatility": 0.0, "max_drawdown": 0.0, "sharpe": 0.0, "spark": []}
    cum = (1 + daily).cumprod()
    total = round((float(cum.iloc[-1]) - 1) * 100, 1)
    vol = round(float(daily.std()) * np.sqrt(_YEAR) * 100, 1)
    sharpe = round(float(daily.mean()) * _YEAR / (float(daily.std()) * np.sqrt(_YEAR)), 2) \
        if float(daily.std()) > 0 else 0.0
    peak = cum.cummax()
    max_dd = round(float((cum / peak - 1).min()) * 100, 1)
    return {
        "total_return": total,
        "ret_1y": _window_return(daily, _YEAR),
        "ret_5y": _window_return(daily, _YEAR * 5),
        "volatility": vol,
        "max_drawdown": max_dd,
        "sharpe": sharpe,
        "spark": _sparkline(cum),
    }


def _benchmark(meta: dict, days: int) -> dict:
    # Same for every strategy in a cycle → cache it once.
    ttl = get_settings().cache_ttl_seconds
    return cached(f"backtest:benchmark:{days}:v1",
                  ttl, lambda: _stats(_basket(list(meta.keys()), meta, days)))


def backtest(symbols: list[str], days: int = _YEAR * 5) -> dict:
    uni = get_universe()
    meta = {r["symbol"]: r for r in uni}
    strat = _stats(_basket(symbols, meta, days))
    bench = _benchmark(meta, days)
    return {
        **strat,
        "benchmark_ret_1y": bench["ret_1y"],
        "benchmark_ret_5y": bench["ret_5y"],
        "alpha_1y": round(strat["ret_1y"] - bench["ret_1y"], 1),
        "alpha_5y": round(strat["ret_5y"] - bench["ret_5y"], 1),
        "beats_benchmark_1y": strat["ret_1y"] > bench["ret_1y"],
        "beats_benchmark_5y": strat["ret_5y"] > bench["ret_5y"],
        "benchmark_spark": bench["spark"],
    }
