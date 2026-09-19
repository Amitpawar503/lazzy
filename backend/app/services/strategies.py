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

    specs += _style_specs()
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


def _style_specs() -> list[dict]:
    return [
        {"id": "style_activist", "name": "Activist Value (Icahn-style)", "category": "style", "top_n": 10,
         "description": "Undervalued, under-managed businesses ripe for a turnaround / value unlock.",
         "philosophy": "Buy cheap, sound-balance-sheet companies the market has given up on, "
                       "where a catalyst (restructuring, capital return, activism) can unlock value.",
         "select": lambda e: [r["symbol"] for r in sorted(
             [x for x in e if x["f"]["cheap_vs_industry"] and x["f"]["debt_to_equity"] < 0.8
              and 5 <= x["f"]["roe"] <= 18],
             key=lambda x: (x["f"]["industry_pe"] - x["f"]["pe"]), reverse=True)]},
        {"id": "style_growth", "name": "Disruptive Growth (ARK-style)", "category": "style", "top_n": 10,
         "description": "Fast-growing disruptors; pay up for growth and momentum.",
         "philosophy": "Prioritise high revenue growth and price momentum over valuation, "
                       "betting on innovation-led compounding — higher risk, higher variance.",
         "select": lambda e: [s for s, _ in sorted(
             [(x["symbol"], _momentum_score(x["symbol"], x.get("ret_1m", 0.0)))
              for x in e if x["f"]["sales_growth_yoy"] >= 15],
             key=lambda t: t[1], reverse=True)]},
        {"id": "style_quality", "name": "Quality Compounder (Buffett-style)", "category": "style", "top_n": 10,
         "description": "Durable, cash-rich franchises with high returns and low debt.",
         "philosophy": "Own wonderful businesses — high, consistent ROE/ROCE, low leverage, "
                       "positive cash flow — and hold them; let compounding do the work.",
         "select": lambda e: [r["symbol"] for r in sorted(
             [x for x in e if x["f"]["roe"] >= 18 and x["f"]["debt_to_equity"] < 0.5
              and x["f"]["profit_growth_yoy"] > 0 and x["f"]["ocf_positive"]],
             key=lambda x: x["f"]["roe"], reverse=True)]},
        {"id": "style_deep_value", "name": "Deep Value (Graham)", "category": "style", "top_n": 10,
         "description": "Statistically cheap: low P/B, low P/E, strong liquidity — margin of safety.",
         "philosophy": "Ben Graham's net-cheap screen: buy well below intrinsic value with a "
                       "margin of safety (low P/B & P/E, healthy current ratio).",
         "select": lambda e: [r["symbol"] for r in sorted(
             [x for x in e if x["f"]["pb"] < 3 and x["f"]["cheap_vs_industry"] and x["f"]["current_ratio"] > 1.3],
             key=lambda x: (x["f"]["pb"] + x["f"]["pe"] / max(x["f"]["industry_pe"], 1)))]},
        {"id": "style_garp", "name": "GARP (Peter Lynch)", "category": "style", "top_n": 10,
         "description": "Growth at a reasonable price — earnings growth vs a sensible P/E.",
         "philosophy": "Lynch's GARP: favour solid earnings growth that isn't overpriced "
                       "(low PEG-style trade-off of growth against valuation).",
         "select": lambda e: [r["symbol"] for r in sorted(
             [x for x in e if x["f"]["profit_growth_yoy"] >= 12 and x["f"]["pe"] <= x["f"]["industry_pe"] * 1.1],
             key=lambda x: x["f"]["profit_growth_yoy"] / max(x["f"]["pe"], 1), reverse=True)]},
        {"id": "style_magic", "name": "Magic Formula (Greenblatt)", "category": "style", "top_n": 10,
         "description": "Good + cheap: rank by return on capital and earnings yield.",
         "philosophy": "Joel Greenblatt's Magic Formula: combine high ROCE (good business) with "
                       "high earnings yield (cheap price) and buy the top-ranked names.",
         "select": lambda e: _magic_formula_rank(e)},
        {"id": "style_contrarian", "name": "Contrarian / Distressed", "category": "style", "top_n": 10,
         "description": "Beaten-down names with improving fundamentals — buying pessimism.",
         "philosophy": "Go against the crowd: weak recent price/signal but sound underlying "
                       "returns, betting on mean reversion as sentiment turns.",
         "select": lambda e: [r["symbol"] for r in sorted(
             [x for x in e if x["net_score"] < 5 and x["f"]["roe"] >= 12 and x["f"]["debt_to_equity"] < 1.0],
             key=lambda x: x["f"]["roe"], reverse=True)]},
        {"id": "style_momentum", "name": "Trend Momentum (CANSLIM-style)", "category": "style", "top_n": 10,
         "description": "Winners keep winning — strong momentum backed by earnings growth.",
         "philosophy": "Ride established uptrends in companies with strong earnings growth; "
                       "cut laggards. Trend-following with a fundamental filter.",
         "select": lambda e: [s for s, _ in sorted(
             [(x["symbol"], _momentum_score(x["symbol"], x.get("ret_1m", 0.0)))
              for x in e if x["f"]["profit_growth_yoy"] >= 10],
             key=lambda t: t[1], reverse=True)]},
    ]


def _period_label() -> str:
    y = _dt.date.today().year
    return f"{y - 5} – {y}"


def _build(spec: dict, enriched: list[dict], detail: bool) -> dict:
    symbols = spec["select"](enriched)[: spec["top_n"]]
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
        enriched = _enriched()
        cards = [_build(s, enriched, detail=False) for s in _specs()]
        return {"count": len(cards), "strategies": cards}

    ttl = get_settings().cache_ttl_seconds
    return cached("strategies:list:v1", ttl, _load)


def get_strategy(strategy_id: str) -> dict | None:
    enriched = _enriched()
    for s in _specs():
        if s["id"] == strategy_id:
            return _build(s, enriched, detail=True)
    return None
