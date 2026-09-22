"""Location + remote classification.

Job feeds are wildly inconsistent about how they express location and
remoteness. This module turns a raw location string (plus any remote flag the
source already gave us) into the fields the UI tabs need:

  - is_remote:     the job can be done remotely
  - remote_scope:  "india" | "outside_india" | "global" | ""
  - is_wfh_ncr:    remote/hybrid/flexible AND tied to Delhi-NCR
  - country:       best-effort country name for the Country filter

It is deliberately heuristic and dependency-free. AI extraction (app/ai) can
override these when enabled, but this keeps the base pipeline fast and offline.
"""
import re

# Delhi-NCR cities/areas the user specifically called out.
NCR_TERMS = [
    "delhi ncr", "ncr", "new delhi", "delhi", "noida", "greater noida",
    "gurgaon", "gurugram", "ghaziabad", "faridabad",
]

REMOTE_TERMS = [
    "remote", "work from home", "wfh", "anywhere", "distributed",
    "fully remote", "home based", "home-based",
]

HYBRID_TERMS = ["hybrid", "flexible", "flex "]

INDIA_TERMS = [
    "india", "bharat", "bengaluru", "bangalore", "hyderabad", "pune",
    "mumbai", "chennai", "kolkata", "delhi", "noida", "gurgaon", "gurugram",
    "ahmedabad", "jaipur", "indore", "kochi", "chandigarh",
] + NCR_TERMS

# Minimal country hinting; extend as needed.
COUNTRY_HINTS = {
    "united states": ["united states", "usa", "u.s.", " us ", "new york", "san francisco",
                       "california", "texas", "seattle", "austin", "boston", "remote us"],
    "united kingdom": ["united kingdom", "uk", "london", "england", "manchester", "scotland"],
    "canada": ["canada", "toronto", "vancouver", "ontario", "montreal"],
    "germany": ["germany", "berlin", "munich", "hamburg"],
    "india": INDIA_TERMS,
    "singapore": ["singapore"],
    "australia": ["australia", "sydney", "melbourne"],
    "netherlands": ["netherlands", "amsterdam"],
    "ireland": ["ireland", "dublin"],
}


def _norm(s: str) -> str:
    return f" {re.sub(r'[^a-z0-9 ]+', ' ', (s or '').lower())} "


def _contains_any(hay: str, terms: list[str]) -> bool:
    return any(t in hay for t in terms)


def guess_country(location_raw: str, description: str = "") -> str:
    hay = _norm(location_raw) + _norm(description[:400])
    for country, hints in COUNTRY_HINTS.items():
        if _contains_any(hay, [h.strip() for h in hints]):
            return country.title()
    return ""


def classify(location_raw: str, description: str = "", source_remote: bool | None = None) -> dict:
    """Return {is_remote, remote_scope, is_wfh_ncr, country}."""
    loc = _norm(location_raw)
    desc = _norm(description[:600])
    blob = loc + desc

    is_remote = bool(source_remote) or _contains_any(loc, REMOTE_TERMS) or _contains_any(desc, REMOTE_TERMS)
    is_hybrid = _contains_any(blob, HYBRID_TERMS)

    country = guess_country(location_raw, description)
    mentions_india = _contains_any(blob, INDIA_TERMS)
    mentions_ncr = _contains_any(blob, NCR_TERMS)

    remote_scope = ""
    if is_remote:
        if mentions_india and not _contains_any(loc, ["remote us", "remote usa", "remote uk", "remote eu"]):
            remote_scope = "india"
        elif country and country.lower() != "india":
            remote_scope = "outside_india"
        elif _contains_any(blob, ["anywhere", "global", "worldwide", "fully remote"]):
            remote_scope = "global"
        else:
            remote_scope = "outside_india" if country else "global"

    # WFH / flexible tab for Delhi-NCR: remote or hybrid/flexible AND NCR-tied.
    is_wfh_ncr = mentions_ncr and (is_remote or is_hybrid)

    if not country and mentions_ncr:
        country = "India"

    return {
        "is_remote": is_remote,
        "remote_scope": remote_scope,
        "is_wfh_ncr": is_wfh_ncr,
        "country": country,
    }


_SALARY_RE = re.compile(
    r"(?:(?P<cur>[$₹€£])\s?)?(?P<a>\d{2,3}(?:[,.]\d{3})+|\d{2,7})\s*(?:k)?\s*(?:-|to|–|—)\s*(?:[$₹€£]\s?)?(?P<b>\d{2,3}(?:[,.]\d{3})+|\d{2,7})\s*(?:k)?",
    re.IGNORECASE,
)


def parse_salary(text: str) -> tuple[int | None, int | None]:
    """Very rough salary-range extraction. Returns (min, max) ints or (None, None)."""
    if not text:
        return None, None
    m = _SALARY_RE.search(text)
    if not m:
        return None, None
    def to_int(raw: str, had_k: bool) -> int | None:
        n = raw.replace(",", "").replace(".", "")
        try:
            v = int(n)
        except ValueError:
            return None
        if had_k or v < 1000:
            v *= 1000
        return v
    had_k = "k" in m.group(0).lower()
    lo = to_int(m.group("a"), had_k)
    hi = to_int(m.group("b"), had_k)
    if lo and hi and lo > hi:
        lo, hi = hi, lo
    return lo, hi
