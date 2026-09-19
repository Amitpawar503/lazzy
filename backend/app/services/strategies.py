"""Curated strategy baskets (ProPicks-style).

Each strategy is a rule over the universe that selects a basket of stocks; we
then backtest the basket (return + risk vs a NIFTY-style benchmark) so the card
shows whether it beats the market and at what risk. Baskets cover sector-wise,
cap-wise, and thematic (value / quality / momentum / seasonal / dividend / high
conviction) angles.
"""
from __future__ import annotations

import datetime as _dt

from app.config import get_settings
from app.data.cache import cached
from app.data.fundamentals_data import fundamentals_for
from app.data.universe import get_universe, sectors
from app.services.backtest import backtest
from app.services.screener import _momentum_score, _row, _seasonal_score
from app.services.signals import universe_signals

REGION_IN = "IN"


def _enriched() -> list[dict]:
    uni = get_universe()
    sigs = universe_signals()
    out = []
    for r in uni:
        out.append({**r, "net_score": sigs[r["symbol"]]["net_score"],
                    "f": fundamentals_for(r)})
    return out


# Each spec: id, name, description, category, selector(enriched)->list[symbol], top_n
def _specs() -> list[dict]:
    specs: list[dict] = []

    # Sector-wise: top algo-consensus names per sector
    for sec in sectors():
        specs.append({
            "id": f"sector_{sec.lower().replace(' ', '_').replace('&','and')}",
            "name": f"{sec} Leaders",
            "description": f"Top {sec} stocks by multi-algo consensus, rebalanced monthly.",
            "category": "sector",
            "top_n": 6,
            "select": (lambda e, s=sec: [r["symbol"] for r in
                        sorted([x for x in e if x["sector"] == s],
                               key=lambda x: x["net_score"], reverse=True)]),
        })

    # Cap-wise
    cap_specs = [
        ("large", "Large Cap Leaders", "Blue-chip large caps with the strongest signals."),
        ("mid", "Mid Cap Movers", "High-momentum mid caps (₹5k–20k cr)."),
        ("small", "Small Cap Gems", "Under-the-radar small caps with strong consensus."),
        ("micro", "Micro Cap Explorers", "Speculative micro caps — higher risk, higher variance."),
    ]
    for cap, name, desc in cap_specs:
        specs.append({
            "id": f"cap_{cap}", "name": name, "description": desc, "category": "cap",
            "top_n": 8,
            "select": (lambda e, c=cap: [r["symbol"] for r in
                        sorted([x for x in e if x["cap_class"] == c],
                               key=lambda x: x["net_score"], reverse=True)]),
        })

    # Thematic
    specs += [
        {"id": "high_conviction", "name": "High Conviction", "category": "theme", "top_n": 10,
         "description": "The strongest multi-algo net scores across the whole market.",
         "select": lambda e: [r["symbol"] for r in sorted(e, key=lambda x: x["net_score"], reverse=True)]},
        {"id": "value_bargains", "name": "Bharat Bargains", "category": "theme", "top_n": 10,
         "description": "Undervalued names: cheaper than peers with healthy returns.",
         "select": lambda e: [r["symbol"] for r in sorted(
             [x for x in e if x["f"]["cheap_vs_industry"] and x["f"]["roe"] >= 12],
             key=lambda x: (x["f"]["roe"] - x["f"]["pe"] / max(x["f"]["industry_pe"], 1) * 10),
             reverse=True)]},
        {"id": "quality", "name": "Quality Compounders", "category": "theme", "top_n": 10,
         "description": "High ROE/ROCE, low debt — durable compounders.",
         "select": lambda e: [r["symbol"] for r in sorted(
             [x for x in e if x["f"]["roe"] >= 18 and x["f"]["roce"] >= 15 and x["f"]["debt_to_equity"] < 0.6],
             key=lambda x: x["f"]["roe"], reverse=True)]},
        {"id": "momentum", "name": "Momentum Masters", "category": "theme", "top_n": 10,
         "description": "Strongest 3-month price momentum.",
         "select": lambda e: [s for s, _ in sorted(
             [(x["symbol"], _momentum_score(x["symbol"], x.get("ret_1m", 0.0))) for x in e],
             key=lambda t: t[1], reverse=True)]},
        {"id": "seasonal", "name": "Seasonal Stars", "category": "theme", "top_n": 10,
         "description": f"Historically strong in {_dt.date.today():%B}.",
         "select": lambda e: [s for s, _ in sorted(
             [(x["symbol"], _seasonal_score(x["symbol"], x.get("ret_1m", 0.0))) for x in e],
             key=lambda t: t[1], reverse=True)]},
        {"id": "dividend", "name": "Dividend Aristocrats", "category": "theme", "top_n": 10,
         "description": "Highest dividend yields with positive cash flow.",
         "select": lambda e: [r["symbol"] for r in sorted(
             [x for x in e if x["f"]["ocf_positive"]],
             key=lambda x: x["f"]["dividend_yield"], reverse=True)]},
    ]

    specs += _fundamental_specs()
    specs += _investor_specs()
    return specs


# --- Investor-style / guru personas: mimic HOW famous investors pick --- #

def _magic_formula_rank(e: list[dict]) -> list[str]:
    # Greenblatt: rank by ROCE and earnings yield (1/PE), sum ranks (lower=better)
    by_roce = sorted(e, key=lambda x: x["f"]["roce"], reverse=True)
    by_ey = sorted(e, key=lambda x: (1.0 / max(x["f"]["pe"], 1)), reverse=True)
    rank = {}
    for i, x in enumerate(by_roce):
        rank[x["symbol"]] = rank.get(x["symbol"], 0) + i
    for i, x in enumerate(by_ey):
        rank[x["symbol"]] = rank.get(x["symbol"], 0) + i
    return [s for s, _ in sorted(rank.items(), key=lambda t: t[1])]


# --- Archetype selectors: return symbols best-first (unclamped) --- #

def _sorted_syms(items, key, rev=True):
    return [x["symbol"] for x in sorted(items, key=key, reverse=rev)]


def _mom(e):
    return [s for s, _ in sorted(
        [(x["symbol"], _momentum_score(x["symbol"], x.get("ret_1m", 0.0))) for x in e],
        key=lambda t: t[1], reverse=True)]


ARCHETYPES = {
    "activist": lambda e: _sorted_syms(
        [x for x in e if x["f"]["cheap_vs_industry"] and x["f"]["debt_to_equity"] < 0.9 and 5 <= x["f"]["roe"] <= 20],
        key=lambda x: (x["f"]["industry_pe"] - x["f"]["pe"])),
    "growth": lambda e: [s for s, _ in sorted(
        [(x["symbol"], _momentum_score(x["symbol"], x.get("ret_1m", 0.0))) for x in e if x["f"]["sales_growth_yoy"] >= 12],
        key=lambda t: t[1], reverse=True)],
    "quality": lambda e: _sorted_syms(
        [x for x in e if x["f"]["roe"] >= 16 and x["f"]["debt_to_equity"] < 0.6 and x["f"]["ocf_positive"]],
        key=lambda x: x["f"]["roe"]),
    "deep_value": lambda e: _sorted_syms(
        [x for x in e if x["f"]["pb"] < 4 and x["f"]["cheap_vs_industry"]],
        key=lambda x: (x["f"]["pb"] + x["f"]["pe"] / max(x["f"]["industry_pe"], 1)), rev=False),
    "value": lambda e: _sorted_syms(
        [x for x in e if x["f"]["cheap_vs_industry"] and x["f"]["roe"] >= 10],
        key=lambda x: (x["f"]["industry_pe"] - x["f"]["pe"])),
    "garp": lambda e: _sorted_syms(
        [x for x in e if x["f"]["profit_growth_yoy"] >= 10 and x["f"]["pe"] <= x["f"]["industry_pe"] * 1.15],
        key=lambda x: x["f"]["profit_growth_yoy"] / max(x["f"]["pe"], 1)),
    "magic": lambda e: _magic_formula_rank(e),
    "contrarian": lambda e: _sorted_syms(
        [x for x in e if x["net_score"] < 5 and x["f"]["roe"] >= 12 and x["f"]["debt_to_equity"] < 1.0],
        key=lambda x: x["f"]["roe"]),
    "momentum": lambda e: [s for s, _ in sorted(
        [(x["symbol"], _momentum_score(x["symbol"], x.get("ret_1m", 0.0))) for x in e if x["f"]["profit_growth_yoy"] >= 8],
        key=lambda t: t[1], reverse=True)],
    "dividend": lambda e: _sorted_syms(
        [x for x in e if x["f"]["ocf_positive"]], key=lambda x: x["f"]["dividend_yield"]),
    "low_debt": lambda e: _sorted_syms(e, key=lambda x: x["f"]["debt_to_equity"], rev=False),
    "high_roe": lambda e: _sorted_syms(e, key=lambda x: x["f"]["roe"]),
    "high_fii": lambda e: _sorted_syms(e, key=lambda x: x["f"]["fii_holding"] + x["f"]["dii_holding"]),
    "cashflow": lambda e: _sorted_syms(
        [x for x in e if x["f"]["ocf_positive"]], key=lambda x: x["f"]["free_cash_flow_cr"]),
    "small_cap": lambda e: _sorted_syms(
        [x for x in e if x["cap_class"] in ("small", "micro", "mid")], key=lambda x: x["net_score"]),
    "large_quality": lambda e: _sorted_syms(
        [x for x in e if x["cap_class"] == "large"], key=lambda x: x["net_score"]),
    "turnaround": lambda e: _sorted_syms(
        [x for x in e if x["net_score"] < 0 and x["f"]["roe"] >= 8], key=lambda x: x["f"]["roe"]),
    "blend": lambda e: _sorted_syms(e, key=lambda x: x["net_score"]),
}


def _investor_specs() -> list[dict]:
    from app.data.investors import investor_catalog

    specs = []
    for inv in investor_catalog():
        arch = inv["archetype"]
        sel = ARCHETYPES.get(arch, ARCHETYPES["blend"])
        slug = "inv_" + "".join(c.lower() if c.isalnum() else "_" for c in inv["name"])[:48]
        specs.append({
            "id": slug, "name": inv["name"], "category": "style", "top_n": inv["top_n"],
            "description": f"Style: {arch.replace('_', ' ')}.",
            "philosophy": inv["philosophy"],
            "select": (lambda e, fn=sel: fn(e)),
        })
    return specs


def _fundamental_specs() -> list[dict]:
    defs = [
        ("fund_high_roe", "High ROE / ROCE", "Best returns on equity & capital.", "high_roe"),
        ("fund_low_debt", "Low Debt / Strong Balance Sheet", "Least leveraged, financially safest.", "low_debt"),
        ("fund_dividend", "High Dividend Yield", "Top income payers with positive cash flow.", "dividend"),
        ("fund_value", "Undervalued (Low PE vs peers)", "Trading cheap to their industry.", "value"),
        ("fund_deep_value", "Deep Value (Low P/B)", "Statistically cheap on book value.", "deep_value"),
        ("fund_growth", "High Sales Growth", "Fastest top-line growers.", "growth"),
        ("fund_cashflow", "Free Cash Flow Machines", "Strongest free-cash-flow generators.", "cashflow"),
        ("fund_quality", "Quality (High ROE + Low Debt)", "Durable, well-run compounders.", "quality"),
        ("fund_institutional", "Institutional Favourites", "Highest FII+DII ownership.", "high_fii"),
        ("fund_garp", "Growth at Reasonable Price", "Earnings growth vs a sensible P/E.", "garp"),
    ]
    out = []
    for sid, name, desc, arch in defs:
        sel = ARCHETYPES[arch]
        out.append({"id": sid, "name": name, "category": "fundamentals", "top_n": 15,
                    "description": desc, "philosophy": "",
                    "select": (lambda e, fn=sel: fn(e))})
    return out


def _period_label() -> str:
    y = _dt.date.today().year
    return f"{y - 5} – {y}"


MIN_HOLDINGS = 5
MAX_HOLDINGS = 25


def _clamp_holdings(symbols: list[str], top_n: int, enriched: list[dict]) -> list[str]:
    top_n = max(MIN_HOLDINGS, min(MAX_HOLDINGS, top_n))
    picked = symbols[:top_n]
    if len(picked) < MIN_HOLDINGS:  # backfill from strongest net-score names
        seen = set(picked)
        pool = [x["symbol"] for x in sorted(enriched, key=lambda r: r["net_score"], reverse=True)]
        for s in pool:
            if s not in seen:
                picked.append(s)
                seen.add(s)
            if len(picked) >= MIN_HOLDINGS:
                break
    return picked


def _build(spec: dict, enriched: list[dict], detail: bool) -> dict:
    symbols = _clamp_holdings(spec["select"](enriched), spec.get("top_n", 15), enriched)
    bt = backtest(symbols)
    card = {
        "id": spec["id"],
        "name": spec["name"],
        "description": spec["description"],
        "philosophy": spec.get("philosophy", ""),
        "category": spec["category"],
        "region": REGION_IN,
        "period": _period_label(),
        "rebalance": "Monthly",
        "constituents_count": len(symbols),
        "ret_1y": bt["ret_1y"],
        "ret_5y": bt["ret_5y"],
        "benchmark_ret_1y": bt["benchmark_ret_1y"],
        "benchmark_ret_5y": bt["benchmark_ret_5y"],
        "alpha_1y": bt["alpha_1y"],
        "alpha_5y": bt["alpha_5y"],
        "beats_benchmark_1y": bt["beats_benchmark_1y"],
        "beats_benchmark_5y": bt["beats_benchmark_5y"],
        "volatility": bt["volatility"],
        "max_drawdown": bt["max_drawdown"],
        "sharpe": bt["sharpe"],
        "spark": bt["spark"],
        "benchmark_spark": bt["benchmark_spark"],
    }
    if detail:
        meta = {r["symbol"]: r for r in enriched}
        rows = [_row(meta[s], "Algo net score", meta[s]["net_score"]) for s in symbols if s in meta]
        card["constituents"] = rows
    return card


def list_strategies() -> dict:
    def _load():
        from concurrent.futures import ThreadPoolExecutor
        enriched = _enriched()
        specs = _specs()
        workers = max(4, get_settings().compute_workers)
        with ThreadPoolExecutor(max_workers=workers) as ex:
            cards = list(ex.map(lambda s: _build(s, enriched, detail=False), specs))
        return {"count": len(cards), "strategies": cards}

    ttl = get_settings().cache_ttl_seconds
    return cached("strategies:list:v1", ttl, _load)


def get_strategy(strategy_id: str) -> dict | None:
    enriched = _enriched()
    for s in _specs():
        if s["id"] == strategy_id:
            return _build(s, enriched, detail=True)
    return None
