"""Corporate actions, order wins, and management notes per stock.

Curated overrides for marquee names + a deterministic generator so every stock
has plausible entries. Sample/illustrative data — real feeds (BSE/NSE corporate
announcements, exchange filings, news) plug in later with the same shape.

Each entry: {label, detail, sentiment: positive|negative|neutral}.
"""
from __future__ import annotations

import hashlib

# Curated, realistic-flavoured entries for well-known names.
_CURATED: dict[str, dict] = {
    "RELIANCE": {
        "corporate_actions": [
            {"label": "Dividend", "detail": "₹10/share final dividend declared", "sentiment": "positive"},
        ],
        "orders": [
            {"label": "New energy capex", "detail": "₹75,000 cr green-energy giga-complex plan", "sentiment": "positive"},
        ],
        "management": [
            {"label": "Management", "detail": "Jio + Retail demerger value-unlock in focus; market rewards execution", "sentiment": "positive"},
        ],
    },
    "LT": {
        "orders": [
            {"label": "Order win", "detail": "₹15,000 cr infra + defence orders this quarter", "sentiment": "positive"},
            {"label": "Order book", "detail": "Record order book, strong govt capex pipeline", "sentiment": "positive"},
        ],
        "management": [
            {"label": "Management", "detail": "Consistent execution; guidance maintained", "sentiment": "positive"},
        ],
    },
    "TATAMOTORS": {
        "orders": [
            {"label": "Demand", "detail": "JLR order backlog healthy; EV portfolio scaling", "sentiment": "positive"},
        ],
        "corporate_actions": [
            {"label": "Deleveraging", "detail": "Net auto debt reduction on track", "sentiment": "positive"},
        ],
    },
    "BHARTIARTL": {
        "orders": [
            {"label": "5G rollout", "detail": "Rapid 5G capex; ARPU uptrend", "sentiment": "positive"},
        ],
    },
    "TATASTEEL": {
        "management": [
            {"label": "Cost", "detail": "UK restructuring drag; India volumes strong", "sentiment": "neutral"},
        ],
    },
    "SBIN": {
        "management": [
            {"label": "Asset quality", "detail": "GNPA at multi-year lows; credit growth healthy", "sentiment": "positive"},
        ],
    },
    "ADANIGREEN": {
        "management": [
            {"label": "Governance", "detail": "Leverage + promoter-pledge scrutiny", "sentiment": "negative"},
        ],
    },
}

_SECTOR_ORDER = {
    "Infrastructure": "large EPC order win",
    "Power": "PPA / transmission order",
    "Metals": "long-term supply contract",
    "Auto": "export / fleet order",
    "Telecom": "network expansion deal",
    "IT": "large multi-year deal win",
    "Healthcare": "hospital expansion",
    "Pharma": "USFDA approval / supply deal",
}


def _seed(symbol: str) -> list[int]:
    h = hashlib.sha256(symbol.encode()).digest()
    return list(h)


def _generated(row: dict, fund: dict) -> dict:
    sym, sector = row["symbol"], row.get("sector", "—")
    s = _seed(sym)
    ca, orders, mgmt = [], [], []

    if fund["dividend_yield"] >= 1.0:
        ca.append({"label": "Dividend", "detail": f"Dividend yield {fund['dividend_yield']}%", "sentiment": "positive"})
    if s[0] % 7 == 0:
        ca.append({"label": "Bonus/Split", "detail": "Recent bonus/split improved liquidity", "sentiment": "positive"})
    if s[1] % 6 == 0:
        ca.append({"label": "Buyback", "detail": "Share buyback announced", "sentiment": "positive"})
    if fund["high_pledge"]:
        ca.append({"label": "Pledge", "detail": f"Promoter pledge {fund['promoter_pledge']}% — monitor", "sentiment": "negative"})

    if sector in _SECTOR_ORDER and s[2] % 3 != 0:
        val = 500 + (s[3] * 40)
        orders.append({"label": "Order win", "detail": f"₹{val:,} cr {_SECTOR_ORDER[sector]}", "sentiment": "positive"})

    if fund["promoter_holding"] >= 55 and not fund["high_pledge"]:
        mgmt.append({"label": "Management", "detail": f"Stable promoter holding {fund['promoter_holding']}%, no pledge", "sentiment": "positive"})
    elif fund["promoter_holding"] < 40:
        mgmt.append({"label": "Ownership", "detail": f"Low promoter holding {fund['promoter_holding']}%", "sentiment": "negative"})
    if fund["profit_growth_yoy"] < 0:
        mgmt.append({"label": "Execution", "detail": "Recent profit miss — watch commentary", "sentiment": "negative"})

    return {"corporate_actions": ca, "orders": orders, "management": mgmt}


def events_for(row: dict, fund: dict) -> dict:
    gen = _generated(row, fund)
    cur = _CURATED.get(row["symbol"], {})
    # merge curated (first) + generated
    return {
        "corporate_actions": cur.get("corporate_actions", []) + gen["corporate_actions"],
        "orders": cur.get("orders", []) + gen["orders"],
        "management": cur.get("management", []) + gen["management"],
    }
