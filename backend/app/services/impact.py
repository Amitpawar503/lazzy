"""News-impact engine: turn an event into per-company short/long-term impact.

For each connected company we derive:
  short_term = lean * st * 100     (immediate price/sentiment reaction)
  long_term  = lean * lt * 100     (fundamental / value-unlock horizon)
and a direction label. Impacted lists are sorted by absolute long-term impact so
the most-affected names surface first; near-zero rows are the "not materially
impacted" tail the user asked to see.
"""
from __future__ import annotations

import logging

from app.config import get_settings
from app.data.cache import cached
from app.data.entity_graph import EVENTS, EXTRA_NAMES
from app.data.universe import get_universe

log = logging.getLogger("lazzy.impact")


def _name_map() -> dict[str, str]:
    m = {r["symbol"]: r["name"] for r in get_universe()}
    m.update(EXTRA_NAMES)
    return m


def _sector_map() -> dict[str, str]:
    return {r["symbol"]: r.get("sector", "—") for r in get_universe()}


def _session_for(published: str) -> str:
    """daily = last ~2 days, weekly = last ~8 days, else monthly."""
    import datetime as _dt

    if not published:
        return "daily"
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            d = _dt.datetime.strptime(published[:16], fmt).date()
            age = (_dt.date.today() - d).days
            return "daily" if age <= 2 else "weekly" if age <= 8 else "monthly"
        except Exception:
            continue
    return "daily"


def _live_events(limit: int = 40) -> list[dict]:
    """Turn live headlines (Moneycontrol / Yahoo / ET / Finnhub / NewsAPI) into
    impact events: each mentioned stock is a primary impact (sentiment-driven),
    with a few sector peers as a secondary 'halo'. Empty if live news is off/dry."""
    if not get_settings().news_live:
        return []
    try:
        from app.services.news import get_news

        items = get_news(category="all", limit=120)["items"]
    except Exception as e:
        log.warning("[impact] live news fetch failed: %s", e)
        return []

    names = _name_map()
    sectors = _sector_map()
    by_sector: dict[str, list[str]] = {}
    for sym, sec in sectors.items():
        by_sector.setdefault(sec, []).append(sym)

    out: list[dict] = []
    seen: set[str] = set()
    for n in items:
        tickers = [t for t in n.get("tickers", []) if t]
        if not tickers:
            continue                      # need at least one linked company
        key = n["title"].lower()[:80]
        if key in seen:
            continue
        seen.add(key)
        score = float(n.get("sentiment_score") or 0.0)
        lean = score if abs(score) > 0.01 else 0.15   # faint positive if flat
        impacted = []
        primary = set()
        for sym in tickers[:6]:
            primary.add(sym)
            st = round(lean * 70, 1)
            lt = round(lean * 35, 1)
            impacted.append({
                "symbol": sym, "name": names.get(sym, sym),
                "relation": "mentioned",
                "relation_detail": f"Named in {n.get('source', 'news')}",
                "short_term": st, "long_term": lt,
                "direction": _direction(st, lt),
                "rationale": (n.get("summary") or n["title"])[:160],
            })
        # sector-peer halo (not already mentioned)
        peer_secs = {sectors.get(s) for s in primary if sectors.get(s)}
        for sec in peer_secs:
            for sym in by_sector.get(sec, [])[:4]:
                if sym in primary or any(i["symbol"] == sym for i in impacted):
                    continue
                st = round(lean * 20, 1)
                lt = round(lean * 10, 1)
                impacted.append({
                    "symbol": sym, "name": names.get(sym, sym),
                    "relation": "peer",
                    "relation_detail": f"{sec} sector peer",
                    "short_term": st, "long_term": lt,
                    "direction": _direction(st, lt),
                    "rationale": f"Sentiment halo from {sec} news; no direct mention.",
                })
                if len(impacted) >= 10:
                    break
        impacted.sort(key=lambda x: abs(x["long_term"]), reverse=True)
        out.append({
            "id": "live_" + n["id"],
            "title": n["title"],
            "entity": n.get("source", "Market news"),
            "kind": "news",
            "session": _session_for(n.get("published", "")),
            "date": (n.get("published") or "")[:10],
            "summary": n.get("summary") or n["title"],
            "impacted": impacted,
            "url": n.get("url", ""),
            "source": "live",
        })
        if len(out) >= limit:
            break
    log.info("[impact] built %d live impact events from headlines", len(out))
    return out


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
        "session": ev.get("session", "daily"),
        "date": ev["date"],
        "summary": ev["summary"],
        "impacted": impacted,
    }


def _all_events() -> list[dict]:
    """Live headline-driven events first (Moneycontrol/Yahoo/ET/…), then the
    curated deep-dive events (Tata Sons, defence/railway policy, …)."""
    names = _name_map()
    curated = [_build_event(ev, names) for ev in EVENTS]
    live = _live_events()
    return live + curated


def list_events(session: str = "all") -> dict:
    ttl = get_settings().cache_ttl_seconds
    events = cached("impact:events:v3", ttl, _all_events)
    if session and session != "all":
        events = [e for e in events if e.get("session") == session]
    return {"count": len(events), "events": events}


def get_event(event_id: str) -> dict | None:
    for ev in _all_events():
        if ev["id"] == event_id:
            return ev
    return None
