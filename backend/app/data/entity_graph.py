"""Event → affected-companies graph.

Each market event names a subject entity and the listed companies connected to
it (holders, parent/subsidiary, peers, index members, suppliers). Every
connection carries a directional lean plus short- and long-term conviction, from
which services/impact.py derives short/long impact scores.

The headline example is a Tata Sons listing: the companies that HOLD Tata Sons
stock (value-unlock upside), the crown-jewel TCS (stake-overhang risk), and Tata
names with little direct exposure ("what's NOT materially impacted").

lean: -1..+1  ·  st / lt: 0..1 conviction multipliers  ·  scores = lean*mult*100
"""
from __future__ import annotations

# Names for symbols that may not be in the sample universe.
EXTRA_NAMES = {
    "TATAINVEST": "Tata Investment Corporation",
    "TATACHEM": "Tata Chemicals",
    "TATAPOWER": "Tata Power",
    "INDHOTEL": "Indian Hotels",
    "TATACONSUM": "Tata Consumer Products",
    "TRENT": "Trent",
    "VOLTAS": "Voltas",
    "TITAN": "Titan Company",
    "TATAELXSI": "Tata Elxsi",
}

EXTRA_NAMES.update({
    "HDFCBANK": "HDFC Bank", "ICICIBANK": "ICICI Bank", "AXISBANK": "Axis Bank",
    "MARUTI": "Maruti Suzuki", "M&M": "Mahindra & Mahindra", "BEL": "Bharat Electronics",
    "HAL": "Hindustan Aeronautics", "BHEL": "BHEL", "MAZDOCK": "Mazagon Dock",
    "SOLARINDS": "Solar Industries", "IRFC": "Indian Railway Finance Corp",
    "RVNL": "Rail Vikas Nigam", "TITAGARH": "Titagarh Rail", "NTPC": "NTPC",
    "POWERGRID": "Power Grid", "COALINDIA": "Coal India", "ONGC": "ONGC",
    "SUZLON": "Suzlon Energy", "INOXWIND": "Inox Wind",
})

# session: which "news session" this event belongs to —
#   daily   = breaking / today's tape reaction
#   weekly  = this week's theme (earnings, sector moves)
#   monthly = structural / policy / corporate-action horizon
EVENTS: list[dict] = [
    {
        "id": "e_tatasons_listing",
        "title": "Tata Sons weighs a stock-market listing",
        "entity": "Tata Sons",
        "kind": "listing",
        "session": "monthly",
        "date": "2026-09-18",
        "summary": (
            "Tata Sons — the unlisted holding company of the Tata group — is "
            "reported to be weighing a listing. Value flows to listed companies "
            "that HOLD Tata Sons shares, while the group's crown jewels face a "
            "possible stake-sale overhang. Many Tata operating companies have "
            "little direct exposure."
        ),
        "impacted": [
            # Holders of Tata Sons — value unlock (positive, stronger long-term)
            {"symbol": "TATAINVEST", "relation": "holder",
             "relation_detail": "Holds Tata Sons equity on its books",
             "lean": 0.9, "st": 0.8, "lt": 0.95,
             "rationale": "Direct Tata Sons stake gets a market price → NAV re-rating."},
            {"symbol": "TATACHEM", "relation": "holder",
             "relation_detail": "Holds a small Tata Sons stake",
             "lean": 0.5, "st": 0.5, "lt": 0.7,
             "rationale": "Balance-sheet stake is marked up on listing."},
            {"symbol": "TATAMOTORS", "relation": "holder",
             "relation_detail": "Holds a minor Tata Sons stake",
             "lean": 0.3, "st": 0.35, "lt": 0.5,
             "rationale": "Modest holding value unlock; core auto story dominates."},
            {"symbol": "TATASTEEL", "relation": "holder",
             "relation_detail": "Holds a minor Tata Sons stake",
             "lean": 0.25, "st": 0.3, "lt": 0.45,
             "rationale": "Small stake mark-up; metals cycle still the driver."},
            {"symbol": "TATAPOWER", "relation": "holder",
             "relation_detail": "Holds a minor Tata Sons stake",
             "lean": 0.2, "st": 0.25, "lt": 0.4,
             "rationale": "Marginal NAV benefit."},
            {"symbol": "INDHOTEL", "relation": "holder",
             "relation_detail": "Holds a minor Tata Sons stake",
             "lean": 0.2, "st": 0.25, "lt": 0.4,
             "rationale": "Marginal NAV benefit; hospitality cycle leads."},
            # Crown jewel — overhang risk (negative short-term, mixed long)
            {"symbol": "TCS", "relation": "subsidiary",
             "relation_detail": "Tata Sons owns ~72% of TCS",
             "lean": -0.4, "st": 0.6, "lt": 0.15,
             "rationale": "A listing could pressure a TCS stake sale → supply overhang; "
                          "fundamentals intact long-term."},
            # Peers / little direct exposure — "what's NOT impacted"
            {"symbol": "TITAN", "relation": "peer",
             "relation_detail": "Tata group operating company, negligible cross-holding",
             "lean": 0.05, "st": 0.05, "lt": 0.05,
             "rationale": "Sentiment halo only; no material direct exposure."},
            {"symbol": "TATACONSUM", "relation": "peer",
             "relation_detail": "Tata group operating company, negligible cross-holding",
             "lean": 0.05, "st": 0.05, "lt": 0.05,
             "rationale": "No material direct exposure to a Tata Sons listing."},
            {"symbol": "TRENT", "relation": "peer",
             "relation_detail": "Tata group operating company, negligible cross-holding",
             "lean": 0.0, "st": 0.0, "lt": 0.0,
             "rationale": "Not materially impacted; retail growth is its own story."},
        ],
    },
    {
        "id": "e_it_guidance",
        "title": "IT majors cautious on FY27 guidance",
        "entity": "Indian IT sector",
        "kind": "earnings",
        "session": "weekly",
        "date": "2026-09-18",
        "summary": "Soft discretionary spend weighs on near-term IT services demand.",
        "impacted": [
            {"symbol": "TCS", "relation": "peer", "relation_detail": "Large-cap IT",
             "lean": -0.5, "st": -0.6, "lt": -0.3,
             "rationale": "Guidance caution pressures multiples."},
            {"symbol": "INFY", "relation": "peer", "relation_detail": "Large-cap IT",
             "lean": -0.5, "st": -0.6, "lt": -0.3, "rationale": "Same demand backdrop."},
            {"symbol": "WIPRO", "relation": "peer", "relation_detail": "Large-cap IT",
             "lean": -0.45, "st": -0.55, "lt": -0.3, "rationale": "Same demand backdrop."},
            {"symbol": "HCLTECH", "relation": "peer", "relation_detail": "Large-cap IT",
             "lean": -0.35, "st": -0.4, "lt": -0.2,
             "rationale": "More resilient mix cushions the hit."},
        ],
    },
    {
        "id": "e_metals_selloff",
        "title": "Metal stocks slip on China demand worries",
        "entity": "Metals sector",
        "kind": "policy",
        "session": "daily",
        "date": "2026-09-19",
        "summary": "Weaker global cues pressure steel and aluminium names.",
        "impacted": [
            {"symbol": "TATASTEEL", "relation": "peer", "relation_detail": "Steel",
             "lean": -0.6, "st": -0.7, "lt": -0.3, "rationale": "China demand sensitivity."},
            {"symbol": "JSWSTEEL", "relation": "peer", "relation_detail": "Steel",
             "lean": -0.55, "st": -0.65, "lt": -0.3, "rationale": "China demand sensitivity."},
            {"symbol": "HINDALCO", "relation": "peer", "relation_detail": "Aluminium",
             "lean": -0.4, "st": -0.5, "lt": -0.2,
             "rationale": "Novelis mix partially offsets."},
        ],
    },
    # --- daily ---
    {
        "id": "e_fii_banks",
        "title": "FII inflows lift private banks intraday",
        "entity": "Banking sector",
        "kind": "flow",
        "session": "daily",
        "date": "2026-09-19",
        "summary": "Foreign buying pushes large private banks higher through the session.",
        "impacted": [
            {"symbol": "HDFCBANK", "relation": "peer", "relation_detail": "Large private bank",
             "lean": 0.6, "st": 0.7, "lt": 0.3, "rationale": "Heaviest FII index weight benefits first."},
            {"symbol": "ICICIBANK", "relation": "peer", "relation_detail": "Large private bank",
             "lean": 0.55, "st": 0.65, "lt": 0.3, "rationale": "Strong FII ownership + earnings momentum."},
            {"symbol": "AXISBANK", "relation": "peer", "relation_detail": "Large private bank",
             "lean": 0.45, "st": 0.55, "lt": 0.25, "rationale": "Rides the flow, cheaper valuation."},
        ],
    },
    # --- weekly ---
    {
        "id": "e_auto_festive",
        "title": "Auto sales momentum builds into the festive week",
        "entity": "Auto sector",
        "kind": "earnings",
        "session": "weekly",
        "date": "2026-09-16",
        "summary": "Festive bookings and new launches lift passenger-vehicle makers this week.",
        "impacted": [
            {"symbol": "MARUTI", "relation": "peer", "relation_detail": "Market leader PV",
             "lean": 0.55, "st": 0.5, "lt": 0.45, "rationale": "Volume leverage to festive demand."},
            {"symbol": "M&M", "relation": "peer", "relation_detail": "SUV + tractors",
             "lean": 0.5, "st": 0.45, "lt": 0.5, "rationale": "SUV mix + rural recovery."},
            {"symbol": "TATAMOTORS", "relation": "peer", "relation_detail": "PV + EV + JLR",
             "lean": 0.4, "st": 0.4, "lt": 0.4, "rationale": "EV share gains; JLR swing factor."},
        ],
    },
    # --- monthly (policy / structural) ---
    {
        "id": "e_defence_capex",
        "title": "Govt pushes defence indigenisation + capex order pipeline",
        "entity": "Government of India",
        "kind": "policy",
        "session": "monthly",
        "date": "2026-09-05",
        "summary": (
            "Higher defence capex, an expanded positive-indigenisation list and export "
            "targets favour domestic defence manufacturers over a multi-quarter horizon."
        ),
        "impacted": [
            {"symbol": "HAL", "relation": "beneficiary", "relation_detail": "Aircraft/engines PSU",
             "lean": 0.8, "st": 0.5, "lt": 0.9, "rationale": "Large order book from indigenisation."},
            {"symbol": "BEL", "relation": "beneficiary", "relation_detail": "Defence electronics PSU",
             "lean": 0.8, "st": 0.5, "lt": 0.9, "rationale": "Radar/EW orders + healthy margins."},
            {"symbol": "MAZDOCK", "relation": "beneficiary", "relation_detail": "Warship/submarine PSU",
             "lean": 0.7, "st": 0.45, "lt": 0.85, "rationale": "Naval order pipeline visibility."},
            {"symbol": "SOLARINDS", "relation": "beneficiary", "relation_detail": "Explosives/defence",
             "lean": 0.6, "st": 0.4, "lt": 0.75, "rationale": "Defence + export ramp."},
        ],
    },
    {
        "id": "e_railway_capex",
        "title": "Record railway capex + Vande Bharat / freight corridor orders",
        "entity": "Government of India",
        "kind": "policy",
        "session": "monthly",
        "date": "2026-09-02",
        "summary": (
            "Sustained railway capex, rolling-stock tenders and electrification favour "
            "railway PSUs and rolling-stock makers structurally."
        ),
        "impacted": [
            {"symbol": "IRFC", "relation": "beneficiary", "relation_detail": "Railway financing PSU",
             "lean": 0.6, "st": 0.4, "lt": 0.75, "rationale": "Balance-sheet growth funds capex."},
            {"symbol": "RVNL", "relation": "beneficiary", "relation_detail": "Rail infra execution PSU",
             "lean": 0.7, "st": 0.45, "lt": 0.8, "rationale": "Order inflow from network expansion."},
            {"symbol": "TITAGARH", "relation": "beneficiary", "relation_detail": "Rolling stock",
             "lean": 0.65, "st": 0.45, "lt": 0.8, "rationale": "Vande Bharat + wagon orders."},
        ],
    },
]
