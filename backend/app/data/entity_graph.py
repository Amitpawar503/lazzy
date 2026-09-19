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

EVENTS: list[dict] = [
    {
        "id": "e_tatasons_listing",
        "title": "Tata Sons weighs a stock-market listing",
        "entity": "Tata Sons",
        "kind": "listing",
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
        "date": "2026-09-17",
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
]
