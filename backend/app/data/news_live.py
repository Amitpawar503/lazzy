"""Live news fetcher — free, no-login sources.

Pulls real headlines from public RSS feeds (Moneycontrol, Economic Times,
Livemint, Business Standard, Google News, Reuters, CNBC, MarketWatch) and,
when a key is present, Finnhub's market-news API. Everything is best-effort and
returns ``[]`` on failure so the caller falls back to bundled sample news.

RSS and these APIs are **free and need no login** — that's deliberately the path
we wire, rather than scraping login-walled portals (Moneycontrol/Screener/
TradingView accounts), which is fragile and ToS-sensitive. Site-login creds in
.env remain available for an optional Playwright scraper, but live headlines
don't require them.

Each item is normalised to the app's news shape and:
  - **entity-linked** — tickers whose symbol or company name appears in the
    headline/summary are attached (so News-Impact and per-stock filters work);
  - **sentiment-tagged** — a lightweight positive/negative lexicon.

Every fetch logs which source was hit and how many items it returned.
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

import httpx

from app.config import get_settings
from app.data.news_data import RSS_FEEDS
from app.data.universe import get_universe

log = logging.getLogger("lazzy.news")

_TIMEOUT = 12.0
_UA = {"User-Agent": "Mozilla/5.0 (LazzyMarkets news reader)"}

_POS = {"gain", "gains", "rise", "rises", "surge", "jump", "rally", "record",
        "high", "beat", "beats", "profit", "growth", "upgrade", "buy", "bullish",
        "wins", "win", "order", "strong", "positive", "outperform", "soar"}
_NEG = {"fall", "falls", "drop", "drops", "slip", "slips", "plunge", "loss",
        "losses", "miss", "misses", "cut", "cuts", "downgrade", "sell", "bearish",
        "weak", "slump", "decline", "fraud", "probe", "ban", "concern", "worry",
        "worries", "crash", "selloff", "negative"}


def _sentiment(text: str) -> tuple[str, float]:
    words = re.findall(r"[a-z]+", text.lower())
    pos = sum(w in _POS for w in words)
    neg = sum(w in _NEG for w in words)
    if pos == neg:
        return "neutral", 0.0
    score = round((pos - neg) / max(1, pos + neg), 2)
    return ("positive" if score > 0 else "negative"), score


def _ticker_index() -> list[tuple[str, re.Pattern]]:
    """Build (symbol, regex) matchers from the universe: match the bare symbol or
    the distinctive first word of the company name as a whole word."""
    idx = []
    for r in get_universe():
        sym = r["symbol"]
        terms = {sym}
        name = (r.get("name") or "").upper()
        first = re.sub(r"[^A-Z]", "", name.split(" ")[0]) if name else ""
        if len(first) >= 4 and first not in {"THE", "INDIA", "LTD"}:
            terms.add(first)
        pat = re.compile(r"\b(" + "|".join(re.escape(t) for t in terms) + r")\b", re.I)
        idx.append((sym, pat))
    return idx


def _link_tickers(text: str, idx: list[tuple[str, re.Pattern]]) -> list[str]:
    up = text.upper()
    return [sym for sym, pat in idx if pat.search(up)][:8]


def _parse_dt(raw: str | None) -> str:
    if not raw:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    try:
        return parsedate_to_datetime(raw).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return raw[:16]


def _fetch_rss(name: str, url: str, category: str,
               idx: list[tuple[str, re.Pattern]]) -> list[dict]:
    try:
        r = httpx.get(url, timeout=_TIMEOUT, headers=_UA, follow_redirects=True)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception as e:
        log.warning("[news] RSS %s FAILED: %s", name, e)
        return []
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        if not title:
            continue
        link = (it.findtext("link") or "").strip()
        desc = re.sub(r"<[^>]+>", "", it.findtext("description") or "").strip()
        pub = _parse_dt(it.findtext("pubDate"))
        blob = f"{title}. {desc}"
        sent, score = _sentiment(blob)
        items.append({
            "id": "rss_" + hashlib.md5((name + title).encode()).hexdigest()[:10],
            "source": name, "title": title, "url": link, "published": pub,
            "summary": desc[:300], "tickers": _link_tickers(blob, idx),
            "sentiment": sent, "sentiment_score": score, "category": category,
        })
    log.info("[news] RSS %s → %d items", name, len(items))
    return items


def _fetch_finnhub(idx: list[tuple[str, re.Pattern]]) -> list[dict]:
    s = get_settings()
    if not s.finnhub_api_key:
        return []
    try:
        r = httpx.get("https://finnhub.io/api/v1/news",
                      params={"category": "general", "token": s.finnhub_api_key},
                      timeout=_TIMEOUT, headers=_UA)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.warning("[news] Finnhub FAILED: %s", e)
        return []
    items = []
    for n in data if isinstance(data, list) else []:
        title = (n.get("headline") or "").strip()
        if not title:
            continue
        summary = (n.get("summary") or "").strip()
        blob = f"{title}. {summary}"
        sent, score = _sentiment(blob)
        ts = n.get("datetime")
        pub = (datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M")
               if ts else _parse_dt(None))
        items.append({
            "id": "fh_" + str(n.get("id") or hashlib.md5(title.encode()).hexdigest()[:10]),
            "source": f"Finnhub · {n.get('source', '')}".strip(" ·"),
            "title": title, "url": n.get("url") or "", "published": pub,
            "summary": summary[:300], "tickers": _link_tickers(blob, idx),
            "sentiment": sent, "sentiment_score": score, "category": "global",
        })
    log.info("[news] Finnhub → %d items", len(items))
    return items


def fetch_live_news() -> list[dict]:
    """Fetch + normalise live headlines from all free sources. Empty on total
    failure (offline) so the caller falls back to sample."""
    idx = _ticker_index()
    india = {"Moneycontrol", "Economic Times", "Livemint", "Business Standard",
             "Google News (India markets)"}
    out: list[dict] = []
    for name, url in RSS_FEEDS.items():
        cat = "india" if name in india else "global"
        out.extend(_fetch_rss(name, url, cat, idx))
    out.extend(_fetch_finnhub(idx))
    # de-dup by title, newest first
    seen, dedup = set(), []
    for n in sorted(out, key=lambda x: x["published"], reverse=True):
        key = n["title"].lower()[:80]
        if key in seen:
            continue
        seen.add(key)
        dedup.append(n)
    log.info("[news] LIVE fetch total: %d unique items from %d sources",
             len(dedup), len(RSS_FEEDS) + (1 if get_settings().finnhub_api_key else 0))
    return dedup
