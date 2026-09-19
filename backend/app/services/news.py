"""News aggregation.

v1 serves bundled sample headlines (already entity-linked + sentiment-tagged).
The live path (RSS_FEEDS in data/news_data.py) plugs in here behind cache().
Filtering by category and by ticker is supported.
"""
from __future__ import annotations

from app.config import get_settings
from app.data.cache import cached
from app.data.news_data import RSS_FEEDS, sample_news


def _load() -> list[dict]:
    # TODO(phase3): fetch + parse RSS_FEEDS with httpx, dedup, then fall back.
    items = sample_news()
    items.sort(key=lambda n: n["published"], reverse=True)
    return items


def get_news(category: str = "all", ticker: str | None = None, limit: int = 50) -> dict:
    ttl = get_settings().cache_ttl_seconds
    items = cached("news:v1", ttl, _load)
    if category in ("india", "global"):
        items = [n for n in items if n["category"] == category]
    if ticker:
        t = ticker.upper()
        items = [n for n in items if t in n["tickers"]]
    return {
        "count": min(len(items), max(1, limit)),
        "sources": list(RSS_FEEDS.keys()),
        "items": items[: max(1, limit)],
    }
