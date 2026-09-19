"""Bundled sample dataset — a curated slice of the NSE universe.

Used as a fallback so every screen renders without network/keys. Market caps are
approximate (₹ crore) and returns are illustrative. Real values come from the
live providers when available.

`cap_class` thresholds (SEBI-style, approximate):
  large  >= 20,000 cr | mid 5,000–20,000 cr | small 500–5,000 cr | micro < 500 cr
"""
from __future__ import annotations

# symbol, name, sector, market_cap_cr, ret_1d_pct, ret_1w_pct, ret_1m_pct
_ROWS: list[tuple[str, str, str, float, float, float, float]] = [
    # IT
    ("TCS", "Tata Consultancy Services", "IT", 1420000, 0.8, 2.1, -1.4),
    ("INFY", "Infosys", "IT", 780000, 1.2, 3.0, 4.5),
    ("WIPRO", "Wipro", "IT", 285000, -0.5, 1.1, 2.2),
    ("HCLTECH", "HCL Technologies", "IT", 480000, 0.9, 2.6, 5.1),
    ("TECHM", "Tech Mahindra", "IT", 155000, -1.1, -0.4, 1.0),
    # Banks / Financials
    ("HDFCBANK", "HDFC Bank", "Financials", 1250000, 0.4, 1.5, 3.2),
    ("ICICIBANK", "ICICI Bank", "Financials", 870000, 1.1, 2.8, 6.0),
    ("SBIN", "State Bank of India", "Financials", 720000, 2.0, 4.2, 8.1),
    ("KOTAKBANK", "Kotak Mahindra Bank", "Financials", 360000, -0.3, 0.6, -2.1),
    ("AXISBANK", "Axis Bank", "Financials", 350000, 0.7, 1.9, 3.8),
    ("BAJFINANCE", "Bajaj Finance", "Financials", 460000, 1.5, 3.4, 7.2),
    # Energy / Oil & Gas
    ("RELIANCE", "Reliance Industries", "Energy", 1980000, 1.0, 2.4, 5.5),
    ("ONGC", "Oil & Natural Gas Corp", "Energy", 320000, -0.8, -1.5, 2.0),
    ("NTPC", "NTPC", "Power", 350000, 0.6, 2.0, 4.4),
    ("POWERGRID", "Power Grid Corp", "Power", 300000, 0.3, 1.2, 1.8),
    ("ADANIGREEN", "Adani Green Energy", "Power", 290000, 3.2, 6.1, -4.0),
    # Auto
    ("MARUTI", "Maruti Suzuki", "Auto", 400000, 0.5, 1.4, 2.9),
    ("TATAMOTORS", "Tata Motors", "Auto", 360000, 2.4, 5.0, 9.5),
    ("M&M", "Mahindra & Mahindra", "Auto", 340000, 1.8, 3.6, 6.8),
    ("BAJAJ-AUTO", "Bajaj Auto", "Auto", 260000, -0.4, 0.8, 1.5),
    ("EICHERMOT", "Eicher Motors", "Auto", 130000, 0.9, 2.2, 3.1),
    # FMCG
    ("HINDUNILVR", "Hindustan Unilever", "FMCG", 590000, -0.6, -1.2, -3.0),
    ("ITC", "ITC", "FMCG", 560000, 0.2, 0.9, 1.1),
    ("NESTLEIND", "Nestle India", "FMCG", 230000, -0.3, 0.4, -1.5),
    ("BRITANNIA", "Britannia Industries", "FMCG", 120000, 0.5, 1.0, 2.0),
    # Pharma / Healthcare
    ("SUNPHARMA", "Sun Pharmaceutical", "Pharma", 400000, 1.3, 2.9, 5.6),
    ("DRREDDY", "Dr. Reddy's Labs", "Pharma", 110000, -0.7, -0.2, 0.9),
    ("CIPLA", "Cipla", "Pharma", 130000, 0.8, 1.6, 3.3),
    ("APOLLOHOSP", "Apollo Hospitals", "Healthcare", 100000, 1.1, 2.3, 4.0),
    # Metals
    ("TATASTEEL", "Tata Steel", "Metals", 200000, 2.6, 4.8, -1.0),
    ("JSWSTEEL", "JSW Steel", "Metals", 230000, 1.9, 3.5, 2.4),
    ("HINDALCO", "Hindalco Industries", "Metals", 160000, 1.4, 2.7, 6.1),
    ("COALINDIA", "Coal India", "Metals", 270000, -0.5, 0.3, -2.8),
    # Cement / Infra
    ("ULTRACEMCO", "UltraTech Cement", "Cement", 320000, 0.6, 1.3, 2.5),
    ("GRASIM", "Grasim Industries", "Cement", 170000, 0.4, 1.0, 1.9),
    ("LT", "Larsen & Toubro", "Infrastructure", 500000, 1.0, 2.5, 4.7),
    # Telecom
    ("BHARTIARTL", "Bharti Airtel", "Telecom", 900000, 0.9, 2.2, 5.9),
    # Consumer / Retail
    ("TITAN", "Titan Company", "Consumer", 300000, 0.7, 1.8, 3.4),
    ("ASIANPAINT", "Asian Paints", "Consumer", 260000, -0.9, -1.8, -4.2),
    ("DMART", "Avenue Supermarts", "Retail", 250000, -0.2, 0.5, -1.0),
    # Tata entities referenced by the news-impact graph
    ("TATACONSUM", "Tata Consumer Products", "FMCG", 110000, 0.5, 1.2, 2.8),
    ("TRENT", "Trent", "Retail", 200000, 1.4, 3.2, 7.0),
    ("TATAPOWER", "Tata Power", "Power", 130000, 0.9, 2.1, 4.2),
    ("INDHOTEL", "Indian Hotels", "Consumer", 100000, 0.6, 1.5, 3.9),
    ("TATAINVEST", "Tata Investment Corp", "Financials", 35000, 1.1, 2.6, 5.5),
    ("TATACHEM", "Tata Chemicals", "Metals", 26000, 0.4, 1.0, -1.2),
    # Mid caps (₹5k–20k cr)
    ("BSE", "BSE Ltd", "Financials", 12000, 0.8, 2.0, 5.0),
    ("IEX", "Indian Energy Exchange", "Power", 15000, -0.4, 0.5, 1.2),
    ("CAMS", "Computer Age Management", "Financials", 18000, 0.6, 1.5, 3.0),
    ("RADICO", "Radico Khaitan", "FMCG", 8000, 0.3, 1.0, 2.5),
    ("KPITTECH", "KPIT Technologies", "IT", 14000, 1.0, 2.4, 4.8),
    # Small caps (₹500–5k cr)
    ("RAILTEL", "RailTel Corp", "Telecom", 4000, 1.2, 2.5, 4.0),
    ("HFCL", "HFCL", "Telecom", 3000, -0.8, -1.5, 2.0),
    ("NELCO", "Nelco", "Telecom", 2500, 1.5, 3.0, -2.0),
    ("GRAVITA", "Gravita India", "Metals", 4500, 0.9, 2.2, 6.0),
    # Micro caps (< ₹500 cr)
    ("TI", "Tilaknagar Industries", "FMCG", 420, 1.0, 2.0, 3.0),
    ("EXCELINDUS", "Excel Industries", "Metals", 300, 0.5, 1.0, 2.0),
]

_SECTOR_INDEX = {  # illustrative sector index period returns (%)
    "IT": {"ret_1d": 0.6, "ret_1w": 2.1, "ret_1m": 2.8},
    "Financials": {"ret_1d": 0.9, "ret_1w": 2.4, "ret_1m": 4.4},
    "Energy": {"ret_1d": 0.4, "ret_1w": 1.2, "ret_1m": 4.6},
    "Power": {"ret_1d": 1.0, "ret_1w": 2.8, "ret_1m": 1.1},
    "Auto": {"ret_1d": 1.2, "ret_1w": 2.9, "ret_1m": 5.4},
    "FMCG": {"ret_1d": -0.1, "ret_1w": 0.2, "ret_1m": -0.9},
    "Pharma": {"ret_1d": 0.6, "ret_1w": 1.8, "ret_1m": 3.4},
    "Healthcare": {"ret_1d": 1.1, "ret_1w": 2.3, "ret_1m": 4.0},
    "Metals": {"ret_1d": 1.5, "ret_1w": 3.1, "ret_1m": 1.2},
    "Cement": {"ret_1d": 0.5, "ret_1w": 1.2, "ret_1m": 2.2},
    "Infrastructure": {"ret_1d": 1.0, "ret_1w": 2.5, "ret_1m": 4.7},
    "Telecom": {"ret_1d": 0.9, "ret_1w": 2.2, "ret_1m": 5.9},
    "Consumer": {"ret_1d": -0.1, "ret_1w": 0.0, "ret_1m": -0.4},
    "Retail": {"ret_1d": -0.2, "ret_1w": 0.5, "ret_1m": -1.0},
}


def cap_class(market_cap_cr: float) -> str:
    if market_cap_cr >= 20000:
        return "large"
    if market_cap_cr >= 5000:
        return "mid"
    if market_cap_cr >= 500:
        return "small"
    return "micro"


def sample_universe() -> list[dict]:
    out = []
    for sym, name, sector, mcap, r1d, r1w, r1m in _ROWS:
        out.append(
            {
                "symbol": sym,
                "name": name,
                "sector": sector,
                "market_cap_cr": mcap,
                "cap_class": cap_class(mcap),
                "ret_1d": r1d,
                "ret_1w": r1w,
                "ret_1m": r1m,
            }
        )
    return out


def sample_sector_returns() -> dict[str, dict]:
    return _SECTOR_INDEX


def sample_fii_dii() -> list[dict]:
    """Last 10 sessions of net FII/DII cash-market flows (₹ crore)."""
    # date, fii_net, dii_net
    rows = [
        ("2026-09-05", -1240.5, 2010.3),
        ("2026-09-08", 880.2, -540.1),
        ("2026-09-09", 1560.7, 320.9),
        ("2026-09-10", -2100.4, 2450.8),
        ("2026-09-11", -640.0, 1180.2),
        ("2026-09-12", 2210.6, -210.5),
        ("2026-09-15", 1740.9, 640.3),
        ("2026-09-16", -980.1, 1520.7),
        ("2026-09-17", 430.5, 890.4),
        ("2026-09-18", 1990.2, -120.6),
    ]
    return [{"date": d, "fii_net": f, "dii_net": i} for d, f, i in rows]


def sample_holding_changes() -> list[dict]:
    """Illustrative institutional holding deltas over the latest quarter (%)."""
    # symbol, fii_delta_pct, dii_delta_pct
    rows = [
        ("TATAMOTORS", 1.8, 0.6), ("SBIN", 1.2, 0.9), ("ICICIBANK", 0.9, 1.1),
        ("BHARTIARTL", 0.7, 0.4), ("LT", 0.6, 0.8), ("SUNPHARMA", 0.5, 0.3),
        ("RELIANCE", 0.4, -0.2), ("TCS", -0.3, 0.5), ("BAJFINANCE", 0.8, -0.1),
        ("HINDUNILVR", -1.1, 0.2), ("ASIANPAINT", -1.4, -0.6), ("KOTAKBANK", -0.9, -0.4),
        ("NESTLEIND", -0.6, 0.1), ("WIPRO", -0.7, -0.3), ("COALINDIA", -0.5, -0.8),
        ("ADANIGREEN", -1.9, 0.4), ("TATASTEEL", 1.0, -0.5), ("MARUTI", 0.3, 0.7),
    ]
    return [
        {"symbol": s, "fii_delta_pct": f, "dii_delta_pct": d} for s, f, d in rows
    ]
