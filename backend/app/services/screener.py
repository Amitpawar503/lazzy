"""Best-stock screeners: sector / cap / momentum / seasonal.

Every screened row carries the multi-algo consensus (which algorithms vote the
stock up, which down, and by how much) so the "in front of each stock" panel
works on every screener screen — reusing the same engine as the Algo Signals
screen.
"""
from __future__ import annotations

import datetime as _dt
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from app.config import get_settings
from app.data.ohlcv import get_ohlcv
from app.data.universe import get_universe
from app.services.signals import compute_signals_cached

CAP_CLASSES = {"large", "mid", "small", "micro"}
CAP_LABELS = {"large": "Large cap", "mid": "Mid cap", "small": "Small cap", "micro": "Micro cap"}


def _parallel(fn, items):
    workers = max(1, get_settings().compute_workers)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, items))


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
    res = compute_signals_cached(r["symbol"], drift_hint=r.get("ret_1m", 0.0))
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


def _all_rows(dimension: str) -> tuple[str, list[dict]]:
    """Compute every universe row for a dimension (parallel), unsorted."""
    uni = get_universe()
    if dimension == "sector" or dimension == "cap":
        label = "Algo net score"
        rows = _parallel(lambda r: _row(r, label, 0.0), uni)
        for row in rows:
            row["metric_value"] = row["net_score"]
    elif dimension == "momentum":
        label = "3M momentum %"
        rows = _parallel(
            lambda r: _row(r, label, _momentum_score(r["symbol"], r.get("ret_1m", 0.0))),
            uni,
        )
    elif dimension == "seasonal":
        label = f"Avg {_dt.date.today():%b} return %"
        rows = _parallel(
            lambda r: _row(r, label, _seasonal_score(r["symbol"], r.get("ret_1m", 0.0))),
            uni,
        )
    else:
        raise ValueError(f"unknown dimension: {dimension}")
    return label, rows


def screen(dimension: str, key: str | None = None, top_n: int = 20) -> dict:
    dimension = dimension.lower()
    label, rows = _all_rows(dimension)

    if dimension == "sector" and key:
        rows = [r for r in rows if r["sector"] == key]
    elif dimension == "cap" and key in CAP_CLASSES:
        rows = [r for r in rows if r["cap_class"] == key]

    rows.sort(key=lambda x: x["metric_value"], reverse=True)
    return {
        "dimension": dimension,
        "key": key,
        "metric_label": label,
        "count": min(len(rows), max(1, top_n)),
        "rows": rows[: max(1, top_n)],
    }


def screen_grouped(dimension: str, per_group: int = 10) -> dict:
    """Sector → a subsection per sector; cap → subsections large/mid/small/micro.
    Each subsection holds its top `per_group` stocks by algo net score."""
    dimension = dimension.lower()
    if dimension not in ("sector", "cap"):
        raise ValueError("grouped view supports only 'sector' or 'cap'")
    label, rows = _all_rows(dimension)

    groups: dict[str, list[dict]] = {}
    for r in rows:
        gkey = r["sector"] if dimension == "sector" else r["cap_class"]
        groups.setdefault(gkey, []).append(r)

    sections = []
    for gkey, grows in groups.items():
        grows.sort(key=lambda x: x["net_score"], reverse=True)
        sections.append(
            {
                "key": gkey,
                "label": CAP_LABELS.get(gkey, gkey) if dimension == "cap" else gkey,
                "count": min(len(grows), per_group),
                "rows": grows[:per_group],
            }
        )
    if dimension == "cap":
        order = {"large": 0, "mid": 1, "small": 2, "micro": 3}
        sections.sort(key=lambda s: order.get(s["key"], 9))
    else:
        sections.sort(key=lambda s: s["label"])
    return {"dimension": dimension, "metric_label": label, "sections": sections}
