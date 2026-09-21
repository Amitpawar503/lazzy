"""Stock detail: the 'why it can go up / why it can go down' thesis.

Combines quote + multi-algo technicals + fundamentals into two evidence-backed
lists (bull points / bear points), each with the concrete fact behind it — so
clicking a stock explains the recommendation with figures.
"""
from __future__ import annotations

from app.config import get_settings
from app.data.fundamentals_data import fundamentals_for
from app.data.ohlcv import get_ohlcv
from app.data.universe import get_universe
from app.services.factors import build_factors
from app.services.signals import compute_signals_cached


def _row_for(symbol: str) -> dict | None:
    for r in get_universe():
        if r["symbol"] == symbol:
            return r
    return None


def _quote(symbol: str, row: dict) -> dict:
    df = get_ohlcv(symbol, days=260, drift_hint=row.get("ret_1m", 0.0))
    close = df["close"].astype(float).dropna()
    last = float(close.iloc[-1]) if len(close) else float(row.get("last_price") or 0.0)
    high_52w = float(df["high"].astype(float).max())
    low_52w = float(df["low"].astype(float).min())
    # guard against thin/NaN live history
    if not (high_52w == high_52w):  # NaN check
        high_52w = last
    if not (low_52w == low_52w):
        low_52w = last
    return {
        "last_price": round(last, 2),
        "change_pct_1d": row.get("ret_1d", 0.0),
        "ret_1w": row.get("ret_1w", 0.0),
        "ret_1m": row.get("ret_1m", 0.0),
        "high_52w": round(high_52w, 2),
        "low_52w": round(low_52w, 2),
        "pct_from_52w_high": round((last / high_52w - 1) * 100, 1) if high_52w else 0.0,
        "pct_from_52w_low": round((last / low_52w - 1) * 100, 1) if low_52w else 0.0,
        "live": get_settings().provider() != "sample",
    }


def _bull_bear(algos: list[dict], f: dict, q: dict) -> tuple[list, list]:
    bull, bear = [], []

    # Technicals from the algo panel
    for a in algos:
        if a["signal"] > 0:
            bull.append({"kind": "technical", "point": f"{a['algo']} bullish",
                         "detail": a["detail"]})
        elif a["signal"] < 0:
            bear.append({"kind": "technical", "point": f"{a['algo']} bearish",
                         "detail": a["detail"]})

    # Fundamentals — bull
    if f["roe"] >= 15:
        bull.append({"kind": "fundamental", "point": "Strong return on equity",
                     "detail": f"ROE {f['roe']}% (ROCE {f['roce']}%)"})
    if f["sales_growth_yoy"] >= 12:
        bull.append({"kind": "fundamental", "point": "Healthy sales growth",
                     "detail": f"{f['sales_growth_yoy']}% YoY"})
    if f["profit_growth_yoy"] >= 15:
        bull.append({"kind": "fundamental", "point": "Strong profit growth",
                     "detail": f"{f['profit_growth_yoy']}% YoY, margin {f['net_profit_margin']}%"})
    if f["debt_to_equity"] < 0.4:
        bull.append({"kind": "balance_sheet", "point": "Low leverage",
                     "detail": f"Debt/Equity {f['debt_to_equity']}"})
    if f["cheap_vs_industry"]:
        bull.append({"kind": "valuation", "point": "Cheaper than peers",
                     "detail": f"PE {f['pe']} vs industry {f['industry_pe']}"})
    if f["dividend_yield"] >= 1.5:
        bull.append({"kind": "valuation", "point": "Attractive dividend",
                     "detail": f"Yield {f['dividend_yield']}%"})
    if f["promoter_holding"] >= 55 and f["promoter_pledge"] < 1:
        bull.append({"kind": "ownership", "point": "High promoter skin-in-the-game",
                     "detail": f"Promoter {f['promoter_holding']}%, no pledge"})
    if f["ocf_positive"] and f["free_cash_flow_cr"] > 0:
        bull.append({"kind": "cash_flow", "point": "Cash generative",
                     "detail": f"Positive OCF, FCF ₹{f['free_cash_flow_cr']:.0f} cr"})
    if q["pct_from_52w_high"] >= -5:
        bull.append({"kind": "technical", "point": "Near 52-week high",
                     "detail": f"{q['pct_from_52w_high']}% from high"})

    # Fundamentals — bear
    if f["high_pledge"]:
        bear.append({"kind": "red_flag", "point": "Promoter pledge elevated",
                     "detail": f"{f['promoter_pledge']}% of holding pledged"})
    if f["falling_sales"]:
        bear.append({"kind": "red_flag", "point": "Sales declining",
                     "detail": f"{f['sales_growth_yoy']}% YoY"})
    if f["profit_growth_yoy"] < 0:
        bear.append({"kind": "P&L", "point": "Profit contraction",
                     "detail": f"{f['profit_growth_yoy']}% YoY"})
    if f["debt_to_equity"] > 1.0:
        bear.append({"kind": "balance_sheet", "point": "High leverage",
                     "detail": f"Debt/Equity {f['debt_to_equity']}"})
    if f["expensive_vs_industry"]:
        bear.append({"kind": "valuation", "point": "Rich valuation",
                     "detail": f"PE {f['pe']} vs industry {f['industry_pe']}"})
    if f["roe"] < 10:
        bear.append({"kind": "fundamental", "point": "Weak return on equity",
                     "detail": f"ROE {f['roe']}%"})
    if not f["ocf_positive"]:
        bear.append({"kind": "cash_flow", "point": "Weak operating cash flow",
                     "detail": "Operating cash flow under pressure"})
    if q["pct_from_52w_low"] <= 8:
        bear.append({"kind": "technical", "point": "Near 52-week low",
                     "detail": f"{q['pct_from_52w_low']}% above low"})

    return bull, bear


def _news_for(symbol: str) -> list[str]:
    from app.data.news_data import sample_news
    return [n["title"] for n in sample_news() if symbol in n["tickers"]][:3]


def _impact_for(symbol: str) -> list[dict]:
    from app.services.impact import list_events
    notes = []
    for ev in list_events()["events"]:
        for im in ev["impacted"]:
            if im["symbol"] == symbol and (abs(im["short_term"]) >= 5 or abs(im["long_term"]) >= 5):
                notes.append({
                    "title": ev["title"],
                    "short_term": im["short_term"],
                    "long_term": im["long_term"],
                    "direction": im["direction"],
                })
    return notes[:3]


def reasoning(symbol: str) -> dict | None:
    """Compact reasoning for the row-hover tooltip."""
    symbol = symbol.upper()
    d = stock_detail(symbol)
    if d is None:
        return None
    return {
        "symbol": symbol,
        "verdict": d["verdict"],
        "net_score": d["net_score"],
        "bull": d["bull_points"][:4],
        "bear": d["bear_points"][:4],
        "factors": d["factors"],
        "news": _news_for(symbol),
        "impact": _impact_for(symbol),
    }


def stock_detail(symbol: str) -> dict | None:
    symbol = symbol.upper()
    row = _row_for(symbol)
    if row is None:
        return None
    sig = compute_signals_cached(symbol, drift_hint=row.get("ret_1m", 0.0))
    fund = fundamentals_for(row)
    q = _quote(symbol, row)
    bull, bear = _bull_bear(sig["algos"], fund, q)
    factors = build_factors(row, fund, q["pct_from_52w_high"], q["pct_from_52w_low"])
    return {
        "symbol": symbol,
        "name": row["name"],
        "sector": row["sector"],
        "cap_class": row["cap_class"],
        "market_cap_cr": row["market_cap_cr"],
        "quote": q,
        "verdict": sig["verdict"],
        "net_score": sig["net_score"],
        "bullish": sig["bullish"],
        "bearish": sig["bearish"],
        "neutral": sig["neutral"],
        "algos": sig["algos"],
        "fundamentals": fund,
        "bull_points": bull,
        "bear_points": bear,
        "factors": factors,
    }
