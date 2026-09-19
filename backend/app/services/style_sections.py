"""Style Picks — 6 sections with a per-stock style-consensus column.

Sections: Large / Mid / Small / Micro cap, plus Multibagger and Most Volatile
(for weekly/monthly SIP). Each holds ~25–30 stocks ranked to maximise
style-driven return, and every row shows how many investor STYLES (archetypes)
are in favour / neutral / against that stock.
"""
from __future__ import annotations

import numpy as np

from app.config import get_settings
from app.data.cache import cached
from app.data.ohlcv import get_ohlcv
from app.services.backtest import backtest
from app.services.screener import _row
from app.services.strategies import _enriched, investor_selectors

SECTION_SIZE = 25
CAP_LABELS = {"large": "Large Cap", "mid": "Mid Cap", "small": "Small Cap", "micro": "Micro Cap"}


def _volatility(symbol: str, drift: float) -> float:
    df = get_ohlcv(symbol, days=260, drift_hint=drift)
    r = df["close"].astype(float).pct_change().dropna()
    if len(r) < 5:
        return 0.0
    return round(float(r.std()) * np.sqrt(252) * 100, 1)


def style_consensus(enriched: list[dict]) -> dict[str, dict]:
    """Check every stock against ALL ~110 investor styles (each with its own
    archetype + cap focus) and count how many are in favour / neutral / against
    it. Favour = the style would pick it (top of its ranking); against = it drops
    out of that style's list entirely (filtered out or bottom); neutral = held
    but not a top pick."""
    selectors = investor_selectors()
    total = len(selectors)
    syms = [x["symbol"] for x in enriched]
    consensus = {s: {"favour": 0, "neutral": 0, "against": 0} for s in syms}
    for _, sel in selectors:
        lst = sel(enriched)
        n = len(lst)
        pos = {s: i for i, s in enumerate(lst)}
        fav_cut = max(1, min(20, n // 2))   # top picks the style would actually buy
        for s in syms:
            if s not in pos:
                consensus[s]["against"] += 1
            elif pos[s] < fav_cut:
                consensus[s]["favour"] += 1
            else:
                consensus[s]["neutral"] += 1
    for s in consensus:
        consensus[s]["total"] = total
    return consensus


def _multibagger_score(x: dict) -> float:
    f = x["f"]
    cap_bonus = {"micro": 12, "small": 10, "mid": 6, "large": 0}.get(x["cap_class"], 0)
    return round(
        0.5 * f["sales_growth_yoy"] + 0.5 * f["profit_growth_yoy"]
        + 0.4 * f["roe"] + 0.2 * x["net_score"] + cap_bonus, 1)


def _build_section(key: str, label: str, metric_label: str, ranked: list[tuple[dict, float]],
                   consensus: dict, meta: dict) -> dict:
    ranked = ranked[:SECTION_SIZE]
    symbols = [x["symbol"] for x, _ in ranked]
    rows = []
    for x, metric in ranked:
        r = _row(meta[x["symbol"]], metric_label, round(metric, 1))
        c = consensus.get(x["symbol"], {"favour": 0, "neutral": 0, "against": 0, "total": 0})
        r["consensus"] = c
        r["volatility"] = _volatility(x["symbol"], x.get("ret_1m", 0.0))
        rows.append(r)
    bt = backtest(symbols)
    return {
        "key": key, "label": label, "metric_label": metric_label,
        "count": len(rows),
        "ret_1y": bt["ret_1y"], "ret_5y": bt["ret_5y"], "alpha_1y": bt["alpha_1y"],
        "beats_benchmark_1y": bt["beats_benchmark_1y"],
        "volatility": bt["volatility"], "max_drawdown": bt["max_drawdown"], "sharpe": bt["sharpe"],
        "spark": bt["spark"], "benchmark_spark": bt["benchmark_spark"],
        "rows": rows,
    }


def _load_sections() -> dict:
    enriched = _enriched()
    meta = {x["symbol"]: x for x in enriched}
    consensus = style_consensus(enriched)

    def cap_ranked(cap):
        items = [(x, consensus[x["symbol"]]["favour"] + x["net_score"] / 100.0)
                 for x in enriched if x["cap_class"] == cap]
        return sorted(items, key=lambda t: t[1], reverse=True)

    sections = []
    for cap in ("large", "mid", "small", "micro"):
        sections.append(_build_section(
            cap, CAP_LABELS[cap], "Styles in favour",
            [(x, consensus[x["symbol"]]["favour"]) for x, _ in cap_ranked(cap)],
            consensus, meta))

    multi = sorted([(x, _multibagger_score(x)) for x in enriched],
                   key=lambda t: t[1], reverse=True)
    sections.append(_build_section("multibagger", "Multibagger Candidates",
                                   "Multibagger score", multi, consensus, meta))

    vol = sorted([(x, _volatility(x["symbol"], x.get("ret_1m", 0.0))) for x in enriched],
                 key=lambda t: t[1], reverse=True)
    sections.append(_build_section("volatile", "Most Volatile (SIP)",
                                   "Volatility %", vol, consensus, meta))

    return {"section_count": len(sections), "sections": sections}


def style_sections() -> dict:
    ttl = get_settings().cache_ttl_seconds
    return cached("style:sections:v1", ttl, _load_sections)
