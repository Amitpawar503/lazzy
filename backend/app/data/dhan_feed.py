"""DhanHQ v2 realtime layer — Live Market Feed + 20-level Full Market Depth.

Docs: https://docs.dhanhq.co/api/v2/data-apis (Live Market Feed, Full Market Depth)

Dhan pushes realtime data over a **websocket** (LTP / quote / full packets, and a
separate 20-level depth feed). We keep two shared, thread-safe caches that the
rest of the app reads instantly:

    TICKS[symbol]  -> {price, prev_close, change_pct, ts}
    DEPTH[symbol]  -> {"buy": [{price, quantity, orders} * ≤20],
                       "sell": [...], "ts": ...}

Two ways they get filled, tried in order:
  1. **Websocket** (true push, tick-by-tick + full depth) via the official
     ``dhanhq`` SDK when it's installed and creds are present. Runs in a daemon
     thread; reconnects on drop.
  2. **REST poller** fallback — a daemon thread that refreshes the batch market
     quote every few seconds (still "live", seconds-fresh, and always available
     with just an access token). No 20-level depth in this mode.

Both degrade to nothing (empty caches) offline, so callers fall back to the
cached EOD quote. Creds live ONLY in .env.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from app.config import get_settings
from app.data import dhan_provider as dh

log = logging.getLogger("lazzy.dhan.feed")

# --- shared caches ------------------------------------------------------------
_LOCK = threading.Lock()
TICKS: dict[str, dict] = {}
DEPTH: dict[str, dict] = {}

_SUBSCRIBED: set[str] = set()
_STARTED = False
_WS_OK = False


def _now() -> int:
    return int(time.time())


def get_tick(symbol: str) -> Optional[dict]:
    with _LOCK:
        t = TICKS.get(symbol.upper())
        return dict(t) if t else None


def get_depth(symbol: str) -> Optional[dict]:
    with _LOCK:
        d = DEPTH.get(symbol.upper())
        return dict(d) if d else None


def _set_tick(symbol: str, price: float, prev_close: float) -> None:
    change_pct = round((price / prev_close - 1) * 100, 2) if prev_close else 0.0
    with _LOCK:
        TICKS[symbol.upper()] = {
            "price": round(float(price), 2),
            "prev_close": round(float(prev_close), 2),
            "change_pct": change_pct,
            "ts": _now(),
        }


def _set_depth(symbol: str, buy: list[dict], sell: list[dict]) -> None:
    with _LOCK:
        DEPTH[symbol.upper()] = {"buy": buy[:20], "sell": sell[:20], "ts": _now()}


# --- REST poller (always-available fallback) ----------------------------------
def _rest_poll_loop(interval: float = 3.0) -> None:
    log.info("[dhan.feed] REST quote poller started (interval=%.1fs)", interval)
    while True:
        with _LOCK:
            syms = list(_SUBSCRIBED)
        if syms:
            try:
                quotes = dh.dhan_quotes_batch(syms)
                for sym, q in quotes.items():
                    _set_tick(sym, q["price"], q["prev_close"])
                if quotes:
                    log.info("[dhan.feed] REST poll refreshed %d live ticks", len(quotes))
            except Exception as e:
                log.warning("[dhan.feed] REST poll failed: %s", e)
        time.sleep(interval)


# --- Websocket (true push + 20-level depth) -----------------------------------
def _instruments(symbols: list[str]) -> list[tuple]:
    """Build (exchange_segment, security_id) tuples for subscription."""
    out = []
    for sym in symbols:
        sid = dh.security_id(sym)
        if sid:
            out.append((dh._EXCH_SEGMENT, str(sid)))
    return out


def _ws_loop(symbols: list[str]) -> None:
    """Best-effort websocket ingest via the dhanhq SDK. Reconnects on failure;
    if the SDK/protocol isn't available it returns and the REST poller carries on.
    """
    global _WS_OK
    s = get_settings()
    try:
        from dhanhq import marketfeed  # type: ignore
    except Exception:
        log.info("[dhan.feed] dhanhq SDK not installed → websocket disabled, "
                 "using REST poller only (pip install dhanhq for tick push + 20-level depth)")
        return  # SDK missing → REST poller only

    instruments = []
    for sym in symbols:
        sid = dh.security_id(sym)
        if sid:
            # (exchange_segment, security_id, subscription_type) — Full = quote+depth
            instruments.append((getattr(marketfeed, "NSE", dh._EXCH_SEGMENT), str(sid),
                                getattr(marketfeed, "Full", 21)))
    if not instruments:
        return

    while True:
        try:
            log.info("[dhan.feed] connecting Live Market Feed websocket (%d instruments, "
                     "Full packet = quote + 20-level depth)", len(instruments))
            feed = marketfeed.DhanFeed(s.dhan_client_id, s.dhan_access_token, instruments)
            _WS_OK = True
            log.info("[dhan.feed] websocket CONNECTED — streaming live ticks + depth")
            while True:
                feed.run_forever()
                msg = feed.get_data()
                if isinstance(msg, dict):
                    _handle_ws_message(msg)
        except Exception as e:
            _WS_OK = False
            log.warning("[dhan.feed] websocket dropped (%s) → reconnecting in 5s", e)
            time.sleep(5)  # backoff then reconnect


def _handle_ws_message(msg: dict) -> None:
    """Normalise a decoded SDK packet into our tick/depth caches. Defensive: the
    SDK's field names vary by version, so probe several spellings."""
    sid = msg.get("security_id") or msg.get("securityId") or msg.get("SecurityId")
    sym = dh.symbol_for_id(sid) if sid is not None else None
    if not sym:
        return

    price = msg.get("LTP") or msg.get("ltp") or msg.get("last_price")
    prev = (msg.get("close") or msg.get("prev_close") or msg.get("previous_close")
            or (msg.get("ohlc") or {}).get("close"))
    if price is not None:
        try:
            _set_tick(sym, float(price), float(prev) if prev else float(price))
        except Exception:
            pass

    # 20-level full depth (buy/bid + sell/ask ladders)
    depth = msg.get("depth") or msg.get("market_depth")
    if isinstance(depth, dict):
        buy = _norm_ladder(depth.get("buy") or depth.get("bid") or [])
        sell = _norm_ladder(depth.get("sell") or depth.get("ask") or [])
        if buy or sell:
            _set_depth(sym, buy, sell)
            log.debug("[dhan.feed] DEPTH %s: %d bid / %d ask levels", sym, len(buy), len(sell))


def _norm_ladder(levels: list) -> list[dict]:
    out = []
    for lv in levels or []:
        if not isinstance(lv, dict):
            continue
        out.append({
            "price": lv.get("price") or lv.get("Price") or 0,
            "quantity": lv.get("quantity") or lv.get("qty") or lv.get("Quantity") or 0,
            "orders": lv.get("orders") or lv.get("no_of_orders") or lv.get("Orders") or 0,
        })
    return out


# --- lifecycle ----------------------------------------------------------------
def subscribe(symbols: list[str]) -> None:
    with _LOCK:
        for s in symbols:
            _SUBSCRIBED.add(s.upper())


def ensure_started(symbols: Optional[list[str]] = None) -> None:
    """Idempotently start the realtime layer for the given symbols. Safe to call
    on every request; only spins threads once."""
    global _STARTED
    if get_settings().provider() != "dhan":
        return
    if symbols:
        subscribe(symbols)
    if _STARTED:
        return
    with _LOCK:
        if _STARTED:
            return
        _STARTED = True
        syms = list(_SUBSCRIBED)

    log.info("[dhan.feed] starting realtime layer for %d symbols", len(syms))
    # REST poller: always on (guarantees live-ish ticks even without the SDK).
    threading.Thread(target=_rest_poll_loop, daemon=True, name="dhan-rest").start()
    # Websocket: best-effort push + 20-level depth.
    threading.Thread(target=_ws_loop, args=(syms,), daemon=True, name="dhan-ws").start()


def status() -> dict:
    with _LOCK:
        return {
            "started": _STARTED,
            "websocket": _WS_OK,
            "subscribed": len(_SUBSCRIBED),
            "ticks": len(TICKS),
            "depth_symbols": len(DEPTH),
        }
