"""FII/DII flow summary and institutional activity (added / removed)."""
from __future__ import annotations

from app.data.providers.fiidii_provider import get_flows, get_holding_changes
from app.data.universe import get_universe


def flow_summary() -> dict:
    series = get_flows()
    if not series:
        return {
            "latest": {"date": "", "fii_net": 0, "dii_net": 0},
            "fii_cumulative": 0,
            "dii_cumulative": 0,
            "series": [],
        }
    return {
        "latest": series[-1],
        "fii_cumulative": round(sum(p["fii_net"] for p in series), 2),
        "dii_cumulative": round(sum(p["dii_net"] for p in series), 2),
        "series": series,
    }


def institutional_activity(top_n: int = 10) -> dict:
    changes = get_holding_changes()
    meta = {r["symbol"]: r for r in get_universe()}

    enriched = []
    for c in changes:
        m = meta.get(c["symbol"], {})
        combined = round(c["fii_delta_pct"] + c["dii_delta_pct"], 2)
        enriched.append(
            {
                "symbol": c["symbol"],
                "name": m.get("name", c["symbol"]),
                "sector": m.get("sector", "—"),
                "fii_delta_pct": c["fii_delta_pct"],
                "dii_delta_pct": c["dii_delta_pct"],
                "combined_delta_pct": combined,
            }
        )

    added = sorted(
        [e for e in enriched if e["combined_delta_pct"] > 0],
        key=lambda e: e["combined_delta_pct"],
        reverse=True,
    )[: max(1, top_n)]
    removed = sorted(
        [e for e in enriched if e["combined_delta_pct"] < 0],
        key=lambda e: e["combined_delta_pct"],
    )[: max(1, top_n)]
    return {"added": added, "removed": removed}
