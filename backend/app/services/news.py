"""News aggregation.

Live by default (``NEWS_LIVE=true``): pulls real headlines from free RSS feeds +
Finnhub via ``data/news_live.py``, entity-linked + sentiment-tagged. Falls back
to bundled sample headlines when live fetch returns nothing (offline). Filtering
by category and by ticker is supported.
"""
from __future__ import annotations

import logging

from app.config import get_settings
from app.data.cache import cached
from app.data.news_data import RSS_FEEDS, sample_news

log = logging.getLogger("lazzy.news")


def _load() -> list[dict]:
    if get_settings().news_live:
        try:
            from app.data.news_live import fetch_live_news

            live = fetch_live_news()
            if live:
                return live
            log.warning("[news] live fetch returned 0 items → serving SAMPLE news")
        except Exception as e:
            log.warning("[news] live fetch error (%s) → serving SAMPLE news", e)
    items = sample_news()
    items.sort(key=lambda n: n["published"], reverse=True)
    return items


def get_news(category: str = "all", ticker: str | None = None, limit: int = 50) -> dict:
    ttl = get_settings().cache_ttl_seconds
    items = cached("news:v2", ttl, _load)
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
