"""Government of India & big-institution ownership / policy radar.

Curated, illustrative dataset (public, well-known facts) structured so it can be
wired to live sources later (disinvestment/DIPAM announcements, BSE/NSE
shareholding filings, LIC/EPFO/SUUTI disclosures, PLI notifications). It powers a
tab that answers: where is the Govt of India (and big institutions) BUYING vs
SELLING, which sectors are getting favourable POLICY, and which stocks can rise
on those decisions.

Not investment advice; holdings/percentages are indicative and change with each
filing/announcement.
"""
from __future__ import annotations

# --- 1. Government / govt-institution holdings & actions -----------------------
# holder: who holds it (GoI = President of India; or a state-owned institution)
# stance: accumulating | stable | divesting  (recent direction of the stake)
# action: the concrete recent move driving the stance
GOVT_HOLDINGS: list[dict] = [
    # PSUs the Govt of India directly controls (President of India as promoter)
    {"symbol": "LICI", "name": "Life Insurance Corp", "sector": "Financials",
     "holder": "Govt of India", "holding_pct": 96.5, "stance": "divesting",
     "action": "Minimum public shareholding glide-path → phased OFS likely"},
    {"symbol": "SBIN", "name": "State Bank of India", "sector": "Financials",
     "holder": "Govt of India", "holding_pct": 57.5, "stance": "stable",
     "action": "Held; strong credit growth, no divestment signalled"},
    {"symbol": "COALINDIA", "name": "Coal India", "sector": "Energy",
     "holder": "Govt of India", "holding_pct": 63.1, "stance": "divesting",
     "action": "Periodic OFS to meet MPSS; high dividend payout"},
    {"symbol": "ONGC", "name": "ONGC", "sector": "Energy",
     "holder": "Govt of India", "holding_pct": 58.9, "stance": "stable",
     "action": "Core energy security holding; capex on new fields"},
    {"symbol": "NTPC", "name": "NTPC", "sector": "Power",
     "holder": "Govt of India", "holding_pct": 51.1, "stance": "stable",
     "action": "Green-energy arm (NTPC Green) value unlock"},
    {"symbol": "POWERGRID", "name": "Power Grid", "sector": "Power",
     "holder": "Govt of India", "holding_pct": 51.3, "stance": "stable",
     "action": "Transmission capex; steady dividend"},
    {"symbol": "BEL", "name": "Bharat Electronics", "sector": "Defence",
     "holder": "Govt of India", "holding_pct": 51.1, "stance": "stable",
     "action": "Record defence-electronics order book; retained strategically"},
    {"symbol": "HAL", "name": "Hindustan Aeronautics", "sector": "Defence",
     "holder": "Govt of India", "holding_pct": 71.6, "stance": "stable",
     "action": "Large indigenisation orders; strategic hold"},
    {"symbol": "IRFC", "name": "Indian Railway Finance Corp", "sector": "Financials",
     "holder": "Govt of India", "holding_pct": 86.4, "stance": "divesting",
     "action": "MPSS-driven dilution over time; funds railway capex"},
    {"symbol": "RVNL", "name": "Rail Vikas Nigam", "sector": "Infrastructure",
     "holder": "Govt of India", "holding_pct": 72.8, "stance": "divesting",
     "action": "OFS tranches; strong railway order inflow"},
    {"symbol": "BHEL", "name": "BHEL", "sector": "Capital Goods",
     "holder": "Govt of India", "holding_pct": 63.2, "stance": "stable",
     "action": "Thermal + FGD order revival; turnaround watch"},
    {"symbol": "IRCTC", "name": "IRCTC", "sector": "Services",
     "holder": "Govt of India", "holding_pct": 62.4, "stance": "stable",
     "action": "Monopoly franchise; occasional OFS"},
    {"symbol": "GAIL", "name": "GAIL India", "sector": "Energy",
     "holder": "Govt of India", "holding_pct": 51.9, "stance": "stable",
     "action": "Gas infrastructure build-out"},
    {"symbol": "NHPC", "name": "NHPC", "sector": "Power",
     "holder": "Govt of India", "holding_pct": 67.4, "stance": "divesting",
     "action": "Periodic OFS; hydro + renewables pipeline"},
    {"symbol": "MAZDOCK", "name": "Mazagon Dock", "sector": "Defence",
     "holder": "Govt of India", "holding_pct": 84.8, "stance": "divesting",
     "action": "OFS to meet MPSS; naval order visibility"},
]

# --- 2. Policy stance by sector -----------------------------------------------
# stance: tailwind | neutral | headwind ; score 0..100 (policy support strength)
POLICY_SECTORS: list[dict] = [
    {"sector": "Defence", "stance": "tailwind", "score": 92,
     "policy": "Higher defence capex, positive-indigenisation lists, export targets",
     "beneficiaries": ["HAL", "BEL", "MAZDOCK", "SOLARINDS", "BDL", "COCHINSHIP"],
     "note": "Multi-year order visibility; import substitution."},
    {"sector": "Railways", "stance": "tailwind", "score": 88,
     "policy": "Record railway capex, Vande Bharat, dedicated freight corridors",
     "beneficiaries": ["IRFC", "RVNL", "TITAGARH", "IRCON", "RAILTEL", "JWL"],
     "note": "Rolling stock, electrification, station redevelopment."},
    {"sector": "Renewables / Power", "stance": "tailwind", "score": 86,
     "policy": "500 GW non-fossil target, PLI solar modules, green hydrogen mission",
     "beneficiaries": ["NTPC", "POWERGRID", "SUZLON", "INOXWIND", "TATAPOWER", "JSWENERGY"],
     "note": "Capex super-cycle in generation + transmission."},
    {"sector": "Electronics / Semis", "stance": "tailwind", "score": 84,
     "policy": "PLI for electronics & IT hardware, semiconductor mission (ISM)",
     "beneficiaries": ["DIXON", "KAYNES", "SYRMA", "AMBER", "CGPOWER"],
     "note": "Import substitution + global supply-chain shift."},
    {"sector": "Capital Goods / Infra", "stance": "tailwind", "score": 80,
     "policy": "Gati Shakti, roads/ports capex, PLI for manufacturing",
     "beneficiaries": ["LT", "BHEL", "SIEMENS", "ABB", "BEL"],
     "note": "Public capex crowds in private investment."},
    {"sector": "Financials (PSU banks)", "stance": "tailwind", "score": 74,
     "policy": "Recapitalised, clean balance sheets, credit-growth push",
     "beneficiaries": ["SBIN", "BANKBARODA", "CANBK", "PNB", "UNIONBANK"],
     "note": "Re-rating on improving RoA/asset quality."},
    {"sector": "Pharma / API", "stance": "tailwind", "score": 70,
     "policy": "PLI for bulk drugs / APIs to cut China dependence",
     "beneficiaries": ["SUNPHARMA", "DIVISLAB", "AUROPHARMA", "LAURUSLABS"],
     "note": "API localisation + export incentives."},
    {"sector": "IT Services", "stance": "neutral", "score": 50,
     "policy": "No direct fiscal support; global-demand dependent",
     "beneficiaries": ["TCS", "INFY", "HCLTECH"],
     "note": "Policy-neutral; driven by global discretionary spend."},
    {"sector": "Tobacco", "stance": "headwind", "score": 30,
     "policy": "High GST / sin-tax stance, periodic duty hikes",
     "beneficiaries": ["ITC"],
     "note": "Regulatory/tax overhang on cigarettes."},
]

# --- 3. Big-institution portfolios (how they're positioning) ------------------
# action per holding: add | hold | reduce
INSTITUTIONS: list[dict] = [
    {"name": "LIC", "type": "Life insurer (state-owned)",
     "note": "India's largest domestic institutional investor.",
     "holdings": [
         {"symbol": "SBIN", "action": "add", "detail": "Raised stake in Q2 filings"},
         {"symbol": "LT", "action": "hold", "detail": "Core infra holding"},
         {"symbol": "ITC", "action": "add", "detail": "Dividend + value accumulation"},
         {"symbol": "NTPC", "action": "add", "detail": "Green-energy re-rating bet"},
         {"symbol": "TCS", "action": "reduce", "detail": "Trimmed after run-up"},
     ]},
    {"name": "EPFO (ETF)", "type": "Retirement fund (index ETFs)",
     "note": "Invests in Nifty/Sensex + CPSE/Bharat-22 ETFs — steady index bid.",
     "holdings": [
         {"symbol": "RELIANCE", "action": "add", "detail": "Index-weight SIP flows"},
         {"symbol": "HDFCBANK", "action": "add", "detail": "Index-weight SIP flows"},
         {"symbol": "COALINDIA", "action": "hold", "detail": "Via CPSE ETF"},
         {"symbol": "NTPC", "action": "hold", "detail": "Via Bharat-22 / CPSE ETF"},
     ]},
    {"name": "SUUTI", "type": "Govt special-purpose holding",
     "note": "Legacy govt holdings the Treasury monetises opportunistically.",
     "holdings": [
         {"symbol": "AXISBANK", "action": "reduce", "detail": "Periodic stake sale"},
         {"symbol": "ITC", "action": "reduce", "detail": "Monetised in tranches"},
     ]},
    {"name": "SBI Mutual Fund", "type": "Largest domestic AMC",
     "note": "Biggest active + passive equity manager.",
     "holdings": [
         {"symbol": "HDFCBANK", "action": "add", "detail": "Top overweight"},
         {"symbol": "BEL", "action": "add", "detail": "Defence theme addition"},
         {"symbol": "M&M", "action": "add", "detail": "Auto/SUV conviction"},
         {"symbol": "WIPRO", "action": "reduce", "detail": "Trimmed IT underweight"},
     ]},
]
