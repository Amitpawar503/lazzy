"""Structured, data-backed factors for a stock — SWOT + corporate actions +
order wins + management, in the spirit of Moneycontrol's #KnowBeforeYouInvest
and MC Insights. Each factor cites the concrete figure behind it.
"""
from __future__ import annotations

from app.data.corporate_events import events_for


def _f(label, detail, sentiment, category):
    return {"label": label, "detail": detail, "sentiment": sentiment, "category": category}


def build_factors(row: dict, fund: dict, pct_from_high: float = 0.0,
                  pct_from_low: float = 100.0) -> dict:
    strengths, weaknesses, opportunities, threats = [], [], [], []

    # --- Strengths ---
    if fund["debt_to_equity"] < 0.4:
        strengths.append(_f("Low debt", f"Debt/Equity {fund['debt_to_equity']}", "positive", "balance_sheet"))
    if fund["sales_growth_yoy"] >= 10:
        strengths.append(_f("Rising revenue", f"Sales +{fund['sales_growth_yoy']}% YoY", "positive", "growth"))
    if fund["profit_growth_yoy"] >= 12:
        strengths.append(_f("Profit growth", f"PAT +{fund['profit_growth_yoy']}% YoY, margin {fund['net_profit_margin']}%", "positive", "growth"))
    if fund["roe"] >= 18 and fund["roce"] >= 15:
        strengths.append(_f("High returns", f"ROE {fund['roe']}%, ROCE {fund['roce']}%", "positive", "returns"))
    if fund["ocf_positive"] and fund["free_cash_flow_cr"] > 0:
        strengths.append(_f("Cash generative", f"Positive OCF, FCF ₹{fund['free_cash_flow_cr']:.0f} cr", "positive", "cash_flow"))
    if fund["promoter_pledge"] < 1:
        strengths.append(_f("Zero pledge", "No promoter pledge", "positive", "ownership"))

    # --- Weaknesses ---
    if fund["roe"] < 10:
        weaknesses.append(_f("Weak ROE", f"ROE {fund['roe']}% — inefficient use of capital", "negative", "returns"))
    if fund["profit_growth_yoy"] < 0:
        weaknesses.append(_f("Profit contraction", f"PAT {fund['profit_growth_yoy']}% YoY", "negative", "growth"))
    if fund["debt_to_equity"] > 1.0:
        weaknesses.append(_f("High leverage", f"Debt/Equity {fund['debt_to_equity']}", "negative", "balance_sheet"))
    if fund["operating_margin"] < 12:
        weaknesses.append(_f("Thin margins", f"Operating margin {fund['operating_margin']}%", "negative", "growth"))

    # --- Opportunities ---
    if fund["cheap_vs_industry"]:
        opportunities.append(_f("Re-rating potential", f"PE {fund['pe']} vs industry {fund['industry_pe']}", "positive", "valuation"))
    if fund["fii_holding"] >= 18:
        opportunities.append(_f("FII interest", f"FII holding {fund['fii_holding']}%", "positive", "ownership"))
    if fund["dii_holding"] >= 15:
        opportunities.append(_f("DII accumulation", f"DII holding {fund['dii_holding']}%", "positive", "ownership"))

    # --- Threats ---
    if fund["expensive_vs_industry"]:
        threats.append(_f("Rich valuation", f"PE {fund['pe']} vs industry {fund['industry_pe']}", "negative", "valuation"))
    if fund["high_pledge"]:
        threats.append(_f("Promoter pledge", f"{fund['promoter_pledge']}% pledged", "negative", "ownership"))
    if pct_from_low <= 8:
        threats.append(_f("Near 52w low", f"{pct_from_low}% above 52-week low", "negative", "technical"))

    ev = events_for(row, fund)

    def _tag(items, category):
        return [{**it, "category": it.get("category", category)} for it in items]

    return {
        "strengths": strengths[:5],
        "weaknesses": weaknesses[:4],
        "opportunities": opportunities[:4],
        "threats": threats[:4],
        "corporate_actions": _tag(ev["corporate_actions"][:4], "corporate_action"),
        "orders": _tag(ev["orders"][:3], "order"),
        "management": _tag(ev["management"][:3], "management"),
    }
