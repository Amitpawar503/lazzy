"""Fundamentals per stock.

Sample/illustrative data, generated deterministically per symbol so every stock
has a consistent, plausible fundamental profile covering the Moneycontrol scanner
categories: valuation/ratios, P&L, balance sheet, cash flow, returns, red flags,
and shareholding. Real values would come from screener.in / Tapetide / FMP in a
later phase — this keeps the stock-detail thesis populated offline.
"""
from __future__ import annotations

import hashlib


def _rng_floats(symbol: str, n: int) -> list[float]:
    """Deterministic pseudo-random floats in [0,1) from the symbol."""
    out = []
    h = hashlib.sha256(symbol.encode()).digest()
    for i in range(n):
        out.append(h[i % len(h)] / 255.0)
        if (i + 1) % len(h) == 0:
            h = hashlib.sha256(h).digest()
    return out


# Sector-typical valuation anchors (illustrative industry P/E).
_SECTOR_PE = {
    "IT": 26, "Financials": 18, "Energy": 14, "Power": 16, "Auto": 22,
    "FMCG": 45, "Pharma": 30, "Healthcare": 55, "Metals": 12, "Cement": 28,
    "Infrastructure": 24, "Telecom": 40, "Consumer": 60, "Retail": 90,
}


def fundamentals_for(row: dict) -> dict:
    """row is a universe instrument dict."""
    sym = row["symbol"]
    sector = row.get("sector", "—")
    ret_1m = row.get("ret_1m", 0.0)
    r = _rng_floats(sym, 20)

    industry_pe = _SECTOR_PE.get(sector, 25)
    pe = round(industry_pe * (0.6 + r[0] * 0.9), 1)               # 0.6x–1.5x industry
    pb = round(1 + r[1] * 8, 1)
    roe = round(6 + r[2] * 24, 1)                                  # 6%–30%
    roce = round(roe * (0.8 + r[3] * 0.5), 1)
    debt_to_equity = round(r[4] * 1.6, 2)                          # 0–1.6
    sales_growth = round(-6 + r[5] * 32, 1)                        # -6%..+26%
    profit_growth = round(-12 + r[6] * 44, 1)
    opm = round(8 + r[7] * 32, 1)
    npm = round(opm * (0.4 + r[8] * 0.4), 1)
    div_yield = round(r[9] * 3.5, 2)
    promoter = round(35 + r[10] * 40, 1)                           # 35%–75%
    pledge = round((r[11] ** 3) * 30, 1)                           # mostly low, some high
    fii = round(5 + r[12] * 30, 1)
    dii = round(5 + r[13] * 25, 1)
    public = round(max(0.0, 100 - promoter - fii - dii), 1)
    current_ratio = round(0.8 + r[14] * 2.2, 2)
    ocf_positive = r[15] > 0.25
    fcf_cr = round((r[16] - 0.4) * row.get("market_cap_cr", 10000) * 0.03, 0)
    eps = round(max(1.0, row.get("market_cap_cr", 10000) / max(pe, 5) / 100), 1)
    book_value = round(eps * pb * (0.8 + r[17]), 1)

    return {
        "symbol": sym,
        # valuation / ratios
        "pe": pe, "industry_pe": industry_pe, "pb": pb,
        "dividend_yield": div_yield, "eps": eps, "book_value": book_value,
        # returns
        "roe": roe, "roce": roce,
        # P&L
        "sales_growth_yoy": sales_growth, "profit_growth_yoy": profit_growth,
        "operating_margin": opm, "net_profit_margin": npm,
        # balance sheet
        "debt_to_equity": debt_to_equity, "current_ratio": current_ratio,
        # cash flow
        "ocf_positive": ocf_positive, "free_cash_flow_cr": fcf_cr,
        # shareholding
        "promoter_holding": promoter, "promoter_pledge": pledge,
        "fii_holding": fii, "dii_holding": dii, "public_holding": public,
        # derived flags
        "high_pledge": pledge > 15,
        "falling_sales": sales_growth < 0,
        "expensive_vs_industry": pe > industry_pe * 1.15,
        "cheap_vs_industry": pe < industry_pe * 0.85,
    }
