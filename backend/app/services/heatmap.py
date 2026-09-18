"""Heatmap builders — 360° market view and sector heatmap.

360°: treemap where box size ∝ market cap and color ∝ return over `timeframe`.
Sector: market-cap-weighted return per sector + top gainer/loser drilldown.
"""
from __future__ import annotations

from app.data.providers.base import return_field
from app.data.universe import get_universe


def build_360(timeframe: str = "1d", top_n: int = 50, sector: str | None = None) -> dict:
    field = return_field(timeframe)
    rows = get_universe()
    if sector:
        rows = [r for r in rows if r["sector"] == sector]
    rows = sorted(rows, key=lambda r: r["market_cap_cr"], reverse=True)[: max(1, top_n)]

    total_mcap = sum(r["market_cap_cr"] for r in rows) or 1.0
    tiles = [
        {
            "symbol": r["symbol"],
            "name": r["name"],
            "sector": r["sector"],
            "market_cap_cr": r["market_cap_cr"],
            "cap_class": r["cap_class"],
            "weight": round(r["market_cap_cr"] / total_mcap, 6),
            "return_pct": r[field],
            "last_price": r.get("last_price"),
        }
        for r in rows
    ]
    returns = [t["return_pct"] for t in tiles] or [0.0]
    return {
        "timeframe": timeframe,
        "count": len(tiles),
        "min_return": min(returns),
        "max_return": max(returns),
        "tiles": tiles,
    }


def build_sector_heatmap(timeframe: str = "1d") -> dict:
    field = return_field(timeframe)
    rows = get_universe()
    total_mcap = sum(r["market_cap_cr"] for r in rows) or 1.0

    by_sector: dict[str, list[dict]] = {}
    for r in rows:
        by_sector.setdefault(r["sector"], []).append(r)

    sectors = []
    for name, members in by_sector.items():
        smcap = sum(m["market_cap_cr"] for m in members) or 1.0
        weighted_ret = sum(m[field] * m["market_cap_cr"] for m in members) / smcap
        top_gainer = max(members, key=lambda m: m[field])
        top_loser = min(members, key=lambda m: m[field])
        sectors.append(
            {
                "sector": name,
                "market_cap_cr": smcap,
                "weight": round(smcap / total_mcap, 6),
                "return_pct": round(weighted_ret, 2),
                "constituents": len(members),
                "top_gainer": top_gainer["symbol"],
                "top_loser": top_loser["symbol"],
            }
        )
    sectors.sort(key=lambda s: s["return_pct"], reverse=True)
    rets = [s["return_pct"] for s in sectors] or [0.0]
    return {
        "timeframe": timeframe,
        "min_return": min(rets),
        "max_return": max(rets),
        "sectors": sectors,
    }
