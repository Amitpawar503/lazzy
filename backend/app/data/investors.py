"""Catalog of ~100 investors/funds for the Ideas → Style bucket.

Each investor maps to a selection ARCHETYPE (value, growth, quality, activist,
…). We EMULATE the manager's style on the Indian universe — these are NOT their
real 13F holdings (no such feed exists for NSE); they are style-emulated baskets,
clearly labelled as such. Names/philosophies are drawn from well-known managers
and the investing.com-style guru list.

Entry: (name, archetype, top_n, philosophy)
"""
from __future__ import annotations

# Default one-liners per archetype (used for generic fund names).
ARCHETYPE_BLURB = {
    "activist": "Buys undervalued, sound-balance-sheet companies where a catalyst can unlock value.",
    "growth": "Pays up for fast revenue growth and momentum; innovation-led compounding.",
    "quality": "Owns durable, cash-rich franchises with high, consistent returns and low debt.",
    "deep_value": "Statistically cheap: low P/B & P/E with a margin of safety.",
    "garp": "Growth at a reasonable price — earnings growth weighed against valuation.",
    "magic": "Good + cheap: ranks by return on capital and earnings yield (Greenblatt).",
    "contrarian": "Goes against the crowd — beaten-down names with sound fundamentals.",
    "momentum": "Rides established uptrends backed by earnings growth; cuts laggards.",
    "dividend": "Income focus — durable, high-yield payers with positive cash flow.",
    "low_debt": "Balance-sheet safety first — low leverage, strong liquidity.",
    "high_roe": "Concentrates on the highest returns on equity and capital.",
    "high_fii": "Follows institutional (FII/DII) accumulation.",
    "cashflow": "Free-cash-flow compounders that self-fund growth.",
    "small_cap": "Hunts under-researched small caps with growth prospects.",
    "large_quality": "Large-cap blue chips with the strongest signals.",
    "turnaround": "Distressed / turnaround situations with improving fundamentals.",
    "blend": "Diversified core — strongest multi-factor names across the market.",
}

# Marquee managers with an explicit style.
_FAMOUS = [
    ("Carl Icahn (Activist)", "activist", 18, "Corporate raider: undervalued businesses ripe for restructuring/value unlock."),
    ("ARK / Cathie Wood (Disruptive Growth)", "growth", 20, "High-growth disruptors; valuation secondary to innovation & momentum."),
    ("Warren Buffett (Quality Value)", "quality", 20, "Wonderful businesses at fair prices; high ROE, low debt, hold forever."),
    ("Benjamin Graham (Deep Value)", "deep_value", 20, "Net-cheap, margin-of-safety bargains — low P/B & P/E."),
    ("Peter Lynch (GARP)", "garp", 20, "Growth at a reasonable price; low PEG-style trade-off."),
    ("Joel Greenblatt (Magic Formula)", "magic", 20, "High ROCE + high earnings yield, buy top-ranked."),
    ("Elliott / Paul Singer (Activist)", "activist", 15, "Activist pressure to surface value in mispriced companies."),
    ("Oaktree / Howard Marks (Contrarian)", "contrarian", 18, "Distressed & contrarian value when sentiment is washed out."),
    ("Stanley Druckenmiller (Growth Macro)", "growth", 15, "Concentrated growth with macro-aware conviction."),
    ("Viking / Andreas Halvorsen (Quality Growth)", "quality", 18, "High-quality compounders with durable growth."),
    ("Starboard / Jeffrey Smith (Activist)", "activist", 15, "Operational activism to improve margins and capital allocation."),
    ("GQG Partners (Quality Growth)", "quality", 22, "Forward-looking quality with adaptable positioning."),
    ("Mark Rachesky / MHR (Activist)", "activist", 12, "Deep-value activist, turnaround catalysts."),
    ("Duquesne Family Office (Growth)", "growth", 15, "Flexible growth with strong risk management."),
    ("Sculptor Capital (Multi-Strategy)", "blend", 20, "Multi-factor, opportunistic core."),
    ("Jennison Associates (Growth)", "growth", 22, "Large-cap secular growth leaders."),
    ("Light Street (Tech Growth)", "growth", 12, "Technology-led disruptive growth."),
    ("Weiss Asset Management (Value)", "deep_value", 20, "Global value & special situations."),
    ("Tang Capital (Contrarian)", "contrarian", 10, "Deep contrarian bets on beaten-down names."),
    ("Ithaka Group (Quality Growth)", "quality", 15, "Concentrated high-quality growth."),
]

# Broader guru / fund list (style-emulated). Assigned archetypes for variety.
_FUND_NAMES = [
    "WorldQuant", "Wesbanco Bank", "Richard C. Young & Co", "Fayez Sarofim & Co",
    "Capital International", "Bluespruce Investments", "State of Michigan Retirement",
    "Truxt Investimentos", "TT International", "Arbiter Partners", "Alamar Capital",
    "West Family Investments", "Verus Capital Partners", "Highland Capital",
    "Geosphere Capital", "Kepos Capital", "Marathon Trading", "Sculptor Capital LP",
    "Whalerock Point", "Longitude Cayman", "Kercheville Advisors", "Ironbridge Private",
    "Interchange Capital", "Hudson Value Partners", "Empirical Finance", "Ellsworth Advisors",
    "Cypress Point Wealth", "Cornerstone Advisors", "Bluefin Capital", "Blue Water Life Science",
    "Alpha Family Trust", "Affinity Investment", "Dock Street Asset", "Convergence Investment",
    "Nikko Asset Management", "Todd Asset Management", "Jacobs Levy Equity", "Capital Fund Management",
    "Robeco Institutional", "Nordea Investment", "Candriam Luxembourg", "National Asset Mgmt",
    "Slow Capital", "Intellectus Partners", "Aristotle Atlantic", "Kovitz Investment Group",
    "Marietta Investment", "Nut Tree Capital", "Miura Global", "Shah Capital",
    "First Light Asset", "Wexford Capital", "Glynn Capital", "Ark Investment",
    "Whetstone Capital", "Edenbrook Capital", "Pathway Capital", "DCF Advisers",
    "Schwab Charitable", "Ossiam", "Qtron Investments", "Voleon Capital", "Maplelane Capital",
    "12 West Capital", "LSV Asset Management", "Forest Hill Capital", "Solus Alternative",
    "Weiss Global", "Timber Creek Capital", "Kamunting Street", "Alphadyne Asset",
    "Coastal Investment", "Gateway Investment", "Securian Asset", "Jag Capital",
    "Twin Capital", "Ativo Capital", "Convergence Partners", "Hoey Investments",
    "Cfm Wealth Partners", "Aurora Investment Managers", "Princeton Capital", "Intellectus Capital",
    "Sterneck Capital", "Foster & Motley", "Meridian Investment", "Convex Capital",
    "Stoneridge Investment", "Cheviot Value", "BTC Capital", "Affluent Capital",
]

_ARCH_CYCLE = [
    "blend", "quality", "growth", "deep_value", "value", "garp", "momentum",
    "dividend", "high_roe", "low_debt", "contrarian", "high_fii", "cashflow",
    "magic", "large_quality", "small_cap", "turnaround", "activist",
]


def investor_catalog() -> list[dict]:
    out = []
    for name, arch, top_n, phil in _FAMOUS:
        out.append({"name": name, "archetype": arch, "top_n": top_n, "philosophy": phil})
    for i, name in enumerate(_FUND_NAMES):
        arch = _ARCH_CYCLE[i % len(_ARCH_CYCLE)]
        top_n = 12 + (i * 7) % 14  # 12..25
        blurb = ARCHETYPE_BLURB.get(arch, ARCHETYPE_BLURB["blend"])
        out.append({"name": name, "archetype": arch, "top_n": top_n,
                    "philosophy": f"{blurb} (style-emulated)"})
    return out
