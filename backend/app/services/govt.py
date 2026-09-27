"""Govt & institutions radar service.

Combines three curated signals into one view and a synthesized pick list:
  - Government of India holdings & their direction (accumulate / divest / stable)
  - Sector policy stance (tailwind / neutral / headwind + strength score)
  - Big-institution positioning (LIC / EPFO / SUUTI / SBI MF adds & reduces)

The pick list answers "which stocks can rise on government decisions": a stock
scores higher when it sits in a policy-tailwind sector AND the govt / big
institutions are accumulating (or holding) rather than dumping it.
"""
from __future__ import annotations

from app.config import get_settings
from app.data.cache import cached
from app.data.govt_data import GOVT_HOLDINGS, INSTITUTIONS, POLICY_SECTORS, SUPERSTARS
from app.data.universe import get_universe

_NAMES: dict[str, str] = {}


def _name(symbol: str) -> str:
    if not _NAMES:
        for r in get_universe():
            _NAMES[r["symbol"]] = r["name"]
        for h in GOVT_HOLDINGS:
            _NAMES.setdefault(h["symbol"], h["name"])
    return _NAMES.get(symbol, symbol)


def _picks() -> list[dict]:
    """Rank stocks by policy tailwind + govt/institution accumulation."""
    score: dict[str, float] = {}
    reasons: dict[str, list[str]] = {}
    sector_of: dict[str, str] = {}

    def bump(sym: str, pts: float, why: str, sector: str = "") -> None:
        score[sym] = score.get(sym, 0.0) + pts
        reasons.setdefault(sym, []).append(why)
        if sector:
            sector_of.setdefault(sym, sector)

    # policy tailwind → beneficiaries
    for p in POLICY_SECTORS:
        if p["stance"] == "tailwind":
            for sym in p["beneficiaries"]:
                bump(sym, p["score"] * 0.5, f"Policy tailwind: {p['policy']}", p["sector"])
        elif p["stance"] == "headwind":
            for sym in p["beneficiaries"]:
                bump(sym, -30, f"Policy headwind: {p['policy']}", p["sector"])

    # govt ownership direction
    for h in GOVT_HOLDINGS:
        if h["stance"] == "accumulating":
            bump(h["symbol"], 25, f"Govt accumulating ({h['action']})", h["sector"])
        elif h["stance"] == "stable":
            bump(h["symbol"], 12, f"Govt holds strategically ({h['action']})", h["sector"])
        else:  # divesting → mild supply overhang, but govt-backed
            bump(h["symbol"], -6, f"Govt divesting/OFS overhang ({h['action']})", h["sector"])

    # institutions add / reduce (FIIs weighted a touch higher for flow impact)
    for inst in INSTITUTIONS:
        w = 1.3 if inst.get("category") == "FII" else 1.0
        for hld in inst["holdings"]:
            if hld["action"] == "add":
                bump(hld["symbol"], 18 * w, f"{inst['name']} buying: {hld['detail']}")
            elif hld["action"] == "reduce":
                bump(hld["symbol"], -12 * w, f"{inst['name']} trimming: {hld['detail']}")
            else:
                bump(hld["symbol"], 5 * w, f"{inst['name']} holding: {hld['detail']}")

    # superstar / marquee investor ownership (signal, not flow)
    for star in SUPERSTARS:
        for hld in star["holdings"]:
            bump(hld["symbol"], 10, f"{star['name']} holds: {hld['detail']}")

    rows = []
    for sym, sc in score.items():
        rows.append({
            "symbol": sym,
            "name": _name(sym),
            "sector": sector_of.get(sym, "—"),
            "score": round(sc, 1),
            "verdict": ("Strong tailwind" if sc >= 55 else "Tailwind" if sc >= 30
                        else "Watch" if sc >= 0 else "Headwind"),
            "reasons": reasons[sym][:4],
        })
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows


def radar() -> dict:
    def _load() -> dict:
        holdings = [{**h, "name": _name(h["symbol"])} for h in GOVT_HOLDINGS]
        institutions = [
            {**inst, "holdings": [{**hld, "name": _name(hld["symbol"])}
                                  for hld in inst["holdings"]]}
            for inst in INSTITUTIONS
        ]
        superstars = [
            {**s, "holdings": [{**h, "name": _name(h["symbol"])} for h in s["holdings"]]}
            for s in SUPERSTARS
        ]
        institutions += _live_portfolios()
        return {
            "policy_sectors": POLICY_SECTORS,
            "govt_holdings": holdings,
            "institutions": institutions,
            "superstars": superstars,
            "picks": _picks(),
            "live": get_settings().govt_live,
        }

    ttl = get_settings().cache_ttl_seconds
    return cached("govt:radar:v2", ttl, _load)


# Moneycontrol india-investors-portfolio slugs → labels (the pages the user gave).
_MC_PORTFOLIOS = [
    ("president-of-india", "President of India (live)", "Govt", "Govt of India direct equity holdings"),
    ("government-pension-fund-global", "Government Pension Fund Global (live)", "FII",
     "Norway sovereign fund — live Moneycontrol portfolio"),
]


def _live_portfolios() -> list[dict]:
    """When GOVT_LIVE=true, overlay live Moneycontrol investor portfolios."""
    if not get_settings().govt_live:
        return []
    out = []
    try:
        from app.data.moneycontrol import investor_portfolio
    except Exception:
        return []
    for slug, label, cat, note in _MC_PORTFOLIOS:
        rows = investor_portfolio(slug)
        if not rows:
            continue
        out.append({
            "name": label, "type": note, "category": cat,
            "note": "Live from moneycontrol.com/india-investors-portfolio",
            "holdings": [{"symbol": r["name"], "name": r["name"],
                          "action": "hold", "detail": r.get("detail", "")}
                         for r in rows],
        })
    return out
