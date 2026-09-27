"""Per-stock news from Moneycontrol (optionally logged-in).

Flow:
  1. Resolve an internal symbol → Moneycontrol stock (sc_id + news URL) via MC's
     public autosuggest JSON (no login needed).
  2. Fetch that stock's news list page and parse the headlines.
  3. If MONEYCONTROL_LOGIN=true (+ creds), obtain a logged-in cookie jar once with
     Playwright (persisted to disk) and send it with the news request so Pro /
     members-only items are included too.

Everything is best-effort: on any failure it returns [] and the caller falls back
to the Google-News Moneycontrol feed. Requires, for the login step only:
    pip install playwright && playwright install chromium
Respect Moneycontrol's Terms of Service and rate limits; creds live in .env only.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from typing import Optional

import httpx

from app.config import get_settings

log = logging.getLogger("lazzy.moneycontrol")

_TIMEOUT = 15.0
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_AUTOSUGGEST = "https://www.moneycontrol.com/mccode/common/autosuggestion_solr.php"

# --- caches -------------------------------------------------------------------
_RESOLVE_CACHE: dict[str, Optional[dict]] = {}
_NEWS_CACHE: dict[str, tuple[float, list[dict]]] = {}
_COOKIES: Optional[dict] = None
_COOKIE_LOADED = False
_LOGIN_LOCK = threading.Lock()


def _headers() -> dict:
    return {"User-Agent": _UA, "Accept": "text/html,application/json,*/*",
            "Referer": "https://www.moneycontrol.com/"}


# --- 1. resolve symbol → MC stock --------------------------------------------
def resolve(symbol: str, name: str = "") -> Optional[dict]:
    """Return {sc_id, name, url} for a symbol via MC autosuggest, or None."""
    key = symbol.upper()
    if key in _RESOLVE_CACHE:
        return _RESOLVE_CACHE[key]
    result = None
    for query in (symbol, name):
        if not query:
            continue
        try:
            r = httpx.get(_AUTOSUGGEST,
                          params={"classic": "true", "query": query, "type": "1",
                                  "format": "json"},
                          headers=_headers(), timeout=_TIMEOUT, follow_redirects=True)
            r.raise_for_status()
            rows = r.json()
        except Exception as e:
            log.warning("[mc] autosuggest '%s' failed: %s", query, e)
            continue
        if isinstance(rows, list) and rows:
            top = rows[0]
            result = {
                "sc_id": top.get("sc_id") or top.get("link_id") or "",
                "name": top.get("stock_name") or top.get("name") or query,
                "url": top.get("link_src") or top.get("link") or "",
            }
            log.info("[mc] resolved %s → %s (sc_id=%s)", symbol, result["name"], result["sc_id"])
            break
    _RESOLVE_CACHE[key] = result
    return result


# --- 3. logged-in cookies (optional, Playwright) ------------------------------
def _load_cookies() -> Optional[dict]:
    """Return a cookie dict for authenticated requests, logging in once if needed."""
    global _COOKIES, _COOKIE_LOADED
    s = get_settings()
    if not s.moneycontrol_login:
        return None
    if _COOKIE_LOADED:
        return _COOKIES
    with _LOGIN_LOCK:
        if _COOKIE_LOADED:
            return _COOKIES
        _COOKIE_LOADED = True
        # reuse a persisted session if present
        try:
            if os.path.exists(s.moneycontrol_state_path):
                with open(s.moneycontrol_state_path) as f:
                    state = json.load(f)
                _COOKIES = {c["name"]: c["value"] for c in state.get("cookies", [])}
                if _COOKIES:
                    log.info("[mc] reusing persisted login session (%d cookies)", len(_COOKIES))
                    return _COOKIES
        except Exception:
            pass
        if not (s.moneycontrol_username and s.moneycontrol_password):
            log.warning("[mc] MONEYCONTROL_LOGIN set but username/password missing")
            return None
        _COOKIES = _playwright_login(s.moneycontrol_username, s.moneycontrol_password,
                                     s.moneycontrol_state_path)
        return _COOKIES


def _playwright_login(user: str, pw: str, state_path: str) -> Optional[dict]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        log.warning("[mc] Playwright not installed → login skipped (public news only). "
                    "pip install playwright && playwright install chromium")
        return None
    log.info("[mc] logging in to Moneycontrol via Playwright…")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent=_UA)
            page = ctx.new_page()
            # MC login page (email/password tab)
            page.goto("https://accounts.moneycontrol.com/mclogin/?d=2",
                      wait_until="domcontentloaded", timeout=45000)
            # try to switch to the "Log-in with Password" tab if present
            for sel in ("text=Log-in with Password", "text=Login with Password",
                        "text=Use Password"):
                try:
                    page.click(sel, timeout=2500)
                    break
                except Exception:
                    continue
            # fill email + password across a few possible selector spellings
            for sel in ("input[name='email']", "input#email", "input[type='email']"):
                try:
                    page.fill(sel, user, timeout=3000); break
                except Exception:
                    continue
            for sel in ("input[name='pwd']", "input[name='password']",
                        "input#pwd", "input[type='password']"):
                try:
                    page.fill(sel, pw, timeout=3000); break
                except Exception:
                    continue
            for sel in ("button:has-text('Login')", "button:has-text('Log In')",
                        "input[type='submit']", "button[type='submit']"):
                try:
                    page.click(sel, timeout=3000); break
                except Exception:
                    continue
            page.wait_for_timeout(5000)  # let the auth round-trip settle
            ctx.storage_state(path=state_path)
            cookies = {c["name"]: c["value"] for c in ctx.cookies()}
            browser.close()
            if cookies:
                log.info("[mc] login OK — %d cookies stored to %s", len(cookies), state_path)
                return cookies
            log.warning("[mc] login produced no cookies (selectors/flow may have changed)")
            return None
    except Exception as e:
        log.warning("[mc] Playwright login failed: %s", e)
        return None


# --- 2. fetch + parse the stock's news ---------------------------------------
def _news_urls(mc: dict) -> list[str]:
    """Candidate Moneycontrol news-list URLs for a resolved stock."""
    urls = []
    sc = mc.get("sc_id") or ""
    if sc:
        urls.append(f"https://www.moneycontrol.com/stocks/company_info/stock_news.php?sc_did={sc}")
    url = mc.get("url") or ""
    if url:
        if url.startswith("/"):
            url = "https://www.moneycontrol.com" + url
        urls.append(url)
    return urls


_A_TAG = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
_TAG = re.compile(r"<[^>]+>")


def stock_news(symbol: str, name: str = "", limit: int = 20) -> list[dict]:
    """Return recent Moneycontrol news items for a stock, or [] on failure."""
    key = symbol.upper()
    now = time.time()
    ttl = get_settings().cache_ttl_seconds
    ent = _NEWS_CACHE.get(key)
    if ent and ent[0] > now:
        return ent[1]

    mc = resolve(symbol, name)
    if not mc:
        return []
    cookies = _load_cookies()
    items: list[dict] = []
    seen = set()
    for url in _news_urls(mc):
        try:
            r = httpx.get(url, headers=_headers(), cookies=cookies, timeout=_TIMEOUT,
                          follow_redirects=True)
            r.raise_for_status()
            html = r.text
        except Exception as e:
            log.warning("[mc] news fetch failed (%s): %s", url, e)
            continue
        for href, inner in _A_TAG.findall(html):
            if "/news/" not in href.lower() and "/business/" not in href.lower():
                continue
            title = _TAG.sub("", inner).strip()
            if len(title) < 25 or title.lower() in seen:
                continue
            if href.startswith("/"):
                href = "https://www.moneycontrol.com" + href
            seen.add(title.lower())
            items.append({
                "id": "mc_" + str(abs(hash(title)) % (10 ** 10)),
                "source": "Moneycontrol" + (" Pro" if cookies else ""),
                "title": title, "url": href, "published": "",
                "summary": "", "tickers": [key], "sentiment": "neutral",
                "sentiment_score": 0.0, "category": "india",
            })
            if len(items) >= limit:
                break
        if items:
            break
    log.info("[mc] %s → %d news items%s", symbol, len(items),
             " (logged-in)" if cookies else "")
    _NEWS_CACHE[key] = (now + ttl, items)
    return items
