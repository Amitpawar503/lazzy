"""Best-stock screeners: sector / cap / momentum / seasonal.

Every screened row carries the multi-algo consensus (which algorithms vote the
stock up, which down, and by how much) so the "in front of each stock" panel
works on every screener screen — reusing the same engine as the Algo Signals
screen.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from app.data.ohlcv import get_ohlcv
from app.data.universe import get_universe
from app.services.signals import compute_signals

CAP_CLASSES = {"large", "mid", "small", "micro"}


def _split_algos(res: dict):
    up = [
        {"algo": a["algo"], "strength_pct": round(a["strength"] * 100, 1)}
        for a in res["algos"]
        if a["signal"] > 0
    ]
    down = [
        {"algo": a["algo"], "strength_pct": round(a["strength"] * 100, 1)}
        for a in res["algos"]
        if a["signal"] < 0
    ]
    up.sort(key=lambda x: x["strength_pct"], reverse=True)
    down.sort(key=lambda x: x["strength_pct"], reverse=True)
    return up, down


def _momentum_score(symbol: str, drift_hint: float) -> float:
    """63-day rate of change (%) — classic 3-month momentum."""
    df = get_ohlcv(symbol, days=260, drift_hint=drift_hint)
    c = df["close"].astype(float)
    if len(c) < 64:
        return 0.0
    return round((c.iloc[-1] / c.iloc[-64] - 1) * 100, 2)


def _seasonal_score(symbol: str, drift_hint: float) -> float:
    """Average historical return in the current calendar month (%)."""
    df = get_ohlcv(symbol, days=780, drift_hint=drift_hint)  # ~3y
    c = df["close"].astype(float).copy()
    c.index = pd.to_datetime(df.index)
    monthly = c.resample("ME").last().pct_change() * 100
    cur = _dt.date.today().month
    same_month = monthly[monthly.index.month == cur].dropna()
    if len(same_month) == 0:
        return 0.0
    return round(float(same_month.mean()), 2)


def _row(r: dict, metric_label: str, metric_value: float) -> dict:
    res = compute_signals(r["symbol"], drift_hint=r.get("ret_1m", 0.0))
    up, down = _split_algos(res)
    return {
        "symbol": r["symbol"],
        "name": r["name"],
        "sector": r["sector"],
        "cap_class": r["cap_class"],
        "market_cap_cr": r["market_cap_cr"],
        "metric_label": metric_label,
        "metric_value": metric_value,
        "bullish": res["bullish"],
        "bearish": res["bearish"],
        "neutral": res["neutral"],
        "net_score": res["net_score"],
        "verdict": res["verdict"],
        "up_algos": up,
        "down_algos": down,
    }


def screen(dimension: str, key: str | None = None, top_n: int = 20) -> dict:
    uni = get_universe()
    dimension = dimension.lower()

    if dimension == "sector":
        label = "Algo net score"
        cands = [r for r in uni if not key or r["sector"] == key]
        rows = [_row(r, label, 0.0) for r in cands]
        for row in rows:
            row["metric_value"] = row["net_score"]
        rows.sort(key=lambda x: x["net_score"], reverse=True)

    elif dimension == "cap":
        label = "Algo net score"
        k = key if key in CAP_CLASSES else None
        cands = [r for r in uni if not k or r["cap_class"] == k]
        rows = [_row(r, label, 0.0) for r in cands]
        for row in rows:
            row["metric_value"] = row["net_score"]
        rows.sort(key=lambda x: (x["net_score"]), reverse=True)

    elif dimension == "momentum":
        label = "3M momentum %"
        rows = []
        for r in uni:
            m = _momentum_score(r["symbol"], r.get("ret_1m", 0.0))
            rows.append(_row(r, label, m))
        rows.sort(key=lambda x: x["metric_value"], reverse=True)

    elif dimension == "seasonal":
        label = f"Avg {_dt.date.today():%b} return %"
        rows = []
        for r in uni:
            s = _seasonal_score(r["symbol"], r.get("ret_1m", 0.0))
            rows.append(_row(r, label, s))
        rows.sort(key=lambda x: x["metric_value"], reverse=True)

    else:
        raise ValueError(f"unknown dimension: {dimension}")

    return {
        "dimension": dimension,
        "key": key,
        "metric_label": label,
        "count": min(len(rows), max(1, top_n)),
        "rows": rows[: max(1, top_n)],
    }
