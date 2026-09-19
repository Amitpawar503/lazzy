"""News-impact engine: turn an event into per-company short/long-term impact.

For each connected company we derive:
  short_term = lean * st * 100     (immediate price/sentiment reaction)
  long_term  = lean * lt * 100     (fundamental / value-unlock horizon)
and a direction label. Impacted lists are sorted by absolute long-term impact so
the most-affected names surface first; near-zero rows are the "not materially
impacted" tail the user asked to see.
"""
from __future__ import annotations

from app.config import get_settings
from app.data.cache import cached
from app.data.entity_graph import EVENTS, EXTRA_NAMES
from app.data.universe import get_universe


def _name_map() -> dict[str, str]:
    m = {r["symbol"]: r["name"] for r in get_universe()}
    m.update(EXTRA_NAMES)
    return m


def _direction(st: float, lt: float) -> str:
    if abs(st) < 5 and abs(lt) < 5:
        return "neutral"
    if st >= 0 and lt >= 0:
        return "positive"
    if st <= 0 and lt <= 0:
        return "negative"
    return "mixed"


def _build_event(ev: dict, names: dict[str, str]) -> dict:
    impacted = []
    for c in ev["impacted"]:
        # direction always comes from `lean`; st/lt are magnitudes.
        st = round(c["lean"] * abs(c["st"]) * 100, 1)
        lt = round(c["lean"] * abs(c["lt"]) * 100, 1)
        impacted.append(
            {
                "symbol": c["symbol"],
                "name": names.get(c["symbol"], c["symbol"]),
                "relation": c["relation"],
                "relation_detail": c["relation_detail"],
                "short_term": st,
                "long_term": lt,
                "direction": _direction(st, lt),
                "rationale": c["rationale"],
            }
        )
    impacted.sort(key=lambda x: abs(x["long_term"]), reverse=True)
    return {
        "id": ev["id"],
        "title": ev["title"],
        "entity": ev["entity"],
        "kind": ev["kind"],
        "date": ev["date"],
        "summary": ev["summary"],
        "impacted": impacted,
    }


def list_events() -> dict:
    def _load():
        names = _name_map()
        return [_build_event(ev, names) for ev in EVENTS]

    ttl = get_settings().cache_ttl_seconds
    events = cached("impact:events:v1", ttl, _load)
    return {"count": len(events), "events": events}


def get_event(event_id: str) -> dict | None:
    names = _name_map()
    for ev in EVENTS:
        if ev["id"] == event_id:
            return _build_event(ev, names)
    return None
