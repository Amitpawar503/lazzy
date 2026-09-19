"""DhanHQ v2 Data-API provider (live NSE/BSE data with a demat account).

Docs: https://docs.dhanhq.co/api/v2/data-apis

What this gives us, from the DhanHQ v2 REST endpoints:
  - **Scrip master** (a free public CSV) → maps a bare trading symbol (RELIANCE)
    to Dhan's numeric ``security_id`` (needed by every other Dhan call).
  - **Get Daily Historical Data** (``POST /v2/charts/historical``) → EOD OHLCV
    used to build the per-symbol history series.
  - **Market Quote (batch)** (``POST /v2/marketfeed/quote``) → near-live LTP +
    previous close for up to 1000 instruments in a single call, used to enrich
    the universe (1-day change) and to answer per-symbol quotes cheaply.

The realtime **Live Market Feed** and **20-level Full Market Depth** are
websocket-only; those live in ``dhan_feed.py`` and push into a shared tick cache.

Auth (kept ONLY in .env, never committed):
    DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN

Everything is best-effort and returns ``None`` on any failure so callers fall
back to bundled sample data — the app never breaks. NOTE: this sandbox blocks
outbound finance hosts, so live fetching runs on the user's machine; the code
paths degrade cleanly (and are shape-verified) here.

Internal symbols are bare (e.g. RELIANCE); Dhan uses numeric security ids on the
``NSE_EQ`` exchange segment.
"""
from __future__ import annotations

import csv
import datetime as _dt
import io
import logging
import threading
import time
from collections import deque
from typing import Optional

import httpx

from app.config import get_settings
from app.data.sample_data import cap_class, sample_universe

log = logging.getLogger("lazzy.dhan")

_TIMEOUT = 30.0


class _RateLimiter:
    """Thread-safe rolling-window throttle: at most ``rate`` calls per ``per``
    seconds across ALL threads (REST poller, universe, history, quotes). Blocks
    the caller just long enough to stay under Dhan's data-API limit (5 req/sec)."""

    def __init__(self, rate: int, per: float = 1.0) -> None:
        self.rate = max(1, rate)
        self.per = per
        self._calls: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                # drop timestamps outside the rolling window
                while self._calls and now - self._calls[0] >= self.per:
                    self._calls.popleft()
                if len(self._calls) < self.rate:
                    self._calls.append(now)
                    return
                wait = self.per - (now - self._calls[0])
            if wait > 0:
                log.debug("[dhan] rate limit reached (%d/%.0fs) — waiting %.3fs",
                          self.rate, self.per, wait)
                time.sleep(wait)


# Built lazily so it picks up DHAN_RATE_LIMIT from settings.
_LIMITER: Optional[_RateLimiter] = None
_LIMITER_LOCK = threading.Lock()


def _limiter() -> _RateLimiter:
    global _LIMITER
    if _LIMITER is None:
        with _LIMITER_LOCK:
            if _LIMITER is None:
                _LIMITER = _RateLimiter(get_settings().dhan_rate_limit)
    return _LIMITER
_EXCH_SEGMENT = "NSE_EQ"      # NSE cash-equity segment
_INSTRUMENT = "EQUITY"

# --- Scrip master (symbol <-> security_id), loaded once and memoised ----------
_SCRIP_LOCK = threading.Lock()
_SYM_TO_ID: dict[str, str] = {}
_ID_TO_SYM: dict[str, str] = {}
_SCRIP_LOADED = False


def _headers() -> Optional[dict]:
    s = get_settings()
    if not s.dhan_access_token:
        return None
    h = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "access-token": s.dhan_access_token,
    }
    if s.dhan_client_id:
        h["client-id"] = s.dhan_client_id
    return h


def _load_scrip_master() -> None:
    """Download and parse Dhan's scrip-master CSV → NSE equity symbol maps.

    The CSV is public (no auth). We keep only NSE cash-equity rows in the ``EQ``
    series so option/future/index rows don't pollute the symbol map.
    """
    global _SCRIP_LOADED
    if _SCRIP_LOADED:
        return
    with _SCRIP_LOCK:
        if _SCRIP_LOADED:  # re-check inside the lock
            return
        s = get_settings()
        log.info("[dhan] loading scrip master: %s", s.dhan_scrip_master_url)
        try:
            r = httpx.get(s.dhan_scrip_master_url, timeout=_TIMEOUT, follow_redirects=True)
            r.raise_for_status()
            reader = csv.DictReader(io.StringIO(r.text))
            for row in reader:
                # Column names differ between the compact and detailed CSVs; probe both.
                exch = (row.get("SEM_EXM_EXCH_ID") or row.get("EXCH_ID") or "").strip().upper()
                seg = (row.get("SEM_SEGMENT") or row.get("SEGMENT") or "").strip().upper()
                series = (row.get("SEM_SERIES") or row.get("SERIES") or "").strip().upper()
                instr = (row.get("SEM_INSTRUMENT_NAME") or row.get("INSTRUMENT") or "").strip().upper()
                sym = (row.get("SEM_TRADING_SYMBOL") or row.get("SYMBOL_NAME")
                       or row.get("SM_SYMBOL_NAME") or "").strip().upper()
                sid = (row.get("SEM_SMST_SECURITY_ID") or row.get("SECURITY_ID") or "").strip()
                if not sym or not sid:
                    continue
                is_nse = exch in ("NSE", "NSE_EQ", "NSE ")
                is_equity = (seg in ("E", "EQUITY", "NSE_EQ")) or (instr in ("EQUITY", "ES"))
                is_eq_series = series in ("", "EQ", "BE")
                if is_nse and is_equity and is_eq_series:
                    _SYM_TO_ID.setdefault(sym, sid)
                    _ID_TO_SYM.setdefault(sid, sym)
            log.info("[dhan] scrip master loaded: %d NSE equity symbols mapped", len(_SYM_TO_ID))
        except Exception as e:
            # leave maps empty → callers fall back to sample
            log.warning("[dhan] scrip master load FAILED (%s) → will fall back to sample", e)
        finally:
            _SCRIP_LOADED = True


def security_id(symbol: str) -> Optional[str]:
    _load_scrip_master()
    return _SYM_TO_ID.get(symbol.upper())


def symbol_for_id(sid: str | int) -> Optional[str]:
    _load_scrip_master()
    return _ID_TO_SYM.get(str(sid))


def _post(path: str, body: dict) -> Optional[dict]:
    h = _headers()
    if h is None:
        log.warning("[dhan] %s skipped: DHAN_ACCESS_TOKEN not set", path)
        return None
    s = get_settings()
    url = f"{s.dhan_base_url}{path}"
    try:
        _limiter().acquire()          # stay within Dhan's 5 req/sec data-API limit
        log.info("[dhan] POST %s", url)
        r = httpx.post(url, json=body, headers=h, timeout=_TIMEOUT)
        r.raise_for_status()
        log.info("[dhan] POST %s → %s OK", path, r.status_code)
        return r.json()
    except httpx.HTTPStatusError as e:
        log.warning("[dhan] POST %s → HTTP %s: %s", path, e.response.status_code,
                    e.response.text[:300])
        return None
    except Exception as e:
        log.warning("[dhan] POST %s FAILED: %s", path, e)
        return None


# --- Batch market quote -------------------------------------------------------
def dhan_quotes_batch(symbols: list[str]) -> dict[str, dict]:
    """Near-live quote for many symbols in one call (chunked to 1000/instr).

    Returns ``{symbol: {price, prev_close, change_pct}}`` for whatever resolved.
    """
    _load_scrip_master()
    ids: list[str] = []
    id_to_sym: dict[str, str] = {}
    for sym in symbols:
        sid = _SYM_TO_ID.get(sym.upper())
        if sid:
            ids.append(sid)
            id_to_sym[sid] = sym.upper()
    if not ids:
        return {}

    out: dict[str, dict] = {}
    for i in range(0, len(ids), 1000):                      # Dhan: ≤1000 instruments/call
        chunk = ids[i : i + 1000]
        resp = _post("/marketfeed/quote", {_EXCH_SEGMENT: [int(x) for x in chunk]})
        if not isinstance(resp, dict):
            continue
        seg = (resp.get("data") or {}).get(_EXCH_SEGMENT) or {}
        for sid, q in seg.items():
            sym = id_to_sym.get(str(sid))
            if not sym or not isinstance(q, dict):
                continue
            price = q.get("last_price")
            ohlc = q.get("ohlc") or {}
            prev = ohlc.get("close") or q.get("prev_close") or price
            if price is None:
                continue
            change_pct = round((float(price) / float(prev) - 1) * 100, 2) if prev else 0.0
            out[sym] = {
                "price": float(price),
                "prev_close": float(prev) if prev else float(price),
                "change_pct": change_pct,
            }
    log.info("[dhan] LIVE quotes: requested %d, resolved %d symbols", len(ids), len(out))
    return out


def dhan_quote(symbol: str) -> Optional[dict]:
    q = dhan_quotes_batch([symbol]).get(symbol.upper())
    if not q:
        return None
    return {"price": q["price"], "change_pct": q["change_pct"], "prev_close": q["prev_close"]}


# --- Daily historical ---------------------------------------------------------
def dhan_history(symbol: str, days: int) -> Optional[list[dict]]:
    """Daily OHLCV as chronological records via ``POST /v2/charts/historical``.

    Response arrays are column-oriented (open/high/low/close/volume/timestamp);
    we zip them into row records. ``timestamp`` is epoch seconds.
    """
    sid = security_id(symbol)
    if not sid:
        log.warning("[dhan] HISTORY %s: no security_id (scrip master empty/miss)", symbol)
        return None
    log.info("[dhan] HISTORY %s (security_id=%s, days=%d)", symbol, sid, days)
    today = _dt.date.today()
    # pad calendar days generously — ~250 trading days per ~365 calendar days
    from_date = today - _dt.timedelta(days=int(days * 1.6) + 10)
    body = {
        "securityId": sid,
        "exchangeSegment": _EXCH_SEGMENT,
        "instrument": _INSTRUMENT,
        "expiryCode": 0,
        "fromDate": from_date.isoformat(),
        "toDate": today.isoformat(),
    }
    data = _post("/charts/historical", body)
    if not isinstance(data, dict):
        return None
    closes = data.get("close") or []
    if not closes:
        return None
    opens = data.get("open") or []
    highs = data.get("high") or []
    lows = data.get("low") or []
    vols = data.get("volume") or []
    ts = data.get("timestamp") or data.get("start_Time") or []
    n = len(closes)

    def _at(arr, i, default=None):
        return arr[i] if i < len(arr) else default

    recs: list[dict] = []
    for i in range(n):
        c = _at(closes, i)
        if c is None:
            continue
        t = _at(ts, i)
        try:
            date = (_dt.datetime.utcfromtimestamp(int(t)).date().isoformat()
                    if t is not None else str(i))
        except Exception:
            date = str(t)
        recs.append({
            "date": date,
            "open": _at(opens, i, c),
            "high": _at(highs, i, c),
            "low": _at(lows, i, c),
            "close": c,
            "volume": _at(vols, i, 0) or 0,
        })
    log.info("[dhan] HISTORY %s → %d daily bars", symbol, len(recs))
    # already chronological (oldest → newest); keep the last `days`
    return recs[-days:] if len(recs) > days else recs or None


# --- Universe -----------------------------------------------------------------
def dhan_universe() -> Optional[list[dict]]:
    """Universe rows enriched with live Dhan quotes.

    Dhan's data APIs don't carry sector / market-cap, so we keep the curated
    bundled metadata (sector + market cap → cap class) as the instrument list and
    overlay **live last price + 1-day change** from Dhan's batch market quote.
    This gives real, live prices for the whole curated NSE universe. History and
    per-symbol quotes then also come from Dhan (see ``ohlcv.py`` / ``live_quotes``).
    """
    _load_scrip_master()
    if not _SYM_TO_ID:
        log.warning("[dhan] universe: scrip master empty → falling back to sample")
        return None
    base = sample_universe()
    quotes = dhan_quotes_batch([r["symbol"] for r in base])
    if not quotes:
        log.warning("[dhan] universe: no live quotes returned → falling back to sample")
        return None
    log.info("[dhan] universe: overlaying live prices on %d curated symbols", len(base))
    rows = []
    for r in base:
        q = quotes.get(r["symbol"].upper())
        row = dict(r)
        if q:
            row["last_price"] = q["price"]
            row["ret_1d"] = q["change_pct"]
        rows.append(row)
    # keep the same shape/keys the rest of the app expects
    for row in rows:
        row["cap_class"] = cap_class(row.get("market_cap_cr", 0))
    return rows
