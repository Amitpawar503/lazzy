"""Near-live quotes.

- LIVE_DATA off  → last close from the cached OHLCV series (fast, deterministic).
- LIVE_DATA on   → best-effort live price via yfinance fast_info (falls back to
                   last close). Cached with a short TTL to respect rate limits.

Zero-delay tick streaming requires a broker websocket (Zerodha Kite / Fyers /
Upstox / Dhan) — that's Phase 6. The SSE endpoint here polls this provider on an
interval and buffers updates, which is near-live (seconds), not tick-by-tick.
"""
from __future__ import annotations

import time

from app.config import get_settings
from app.data.cache import cached
from app.data.ohlcv import get_ohlcv
from app.data.universe import get_universe


def _base(symbol: str) -> tuple[float, float]:
    row = next((r for r in get_universe() if r["symbol"] == symbol), None)
    drift = row.get("ret_1m", 0.0) if row else 0.0
    df = get_ohlcv(symbol, days=5, drift_hint=drift)
    close = df["close"].astype(float)
    last = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close) > 1 else last
    return last, prev


def _live_price(symbol: str) -> float | None:
    try:
        import yfinance as yf  # type: ignore

        t = yf.Ticker(f"{symbol.replace('&', '')}.NS")
        fi = getattr(t, "fast_info", None)
        if fi:
            p = fi.get("last_price") or fi.get("lastPrice")
            if p:
                return float(p)
    except Exception:
        return None
    return None


def get_quote(symbol: str) -> dict:
    symbol = symbol.upper()
    settings = get_settings()

    def _load() -> dict:
        last, prev = _base(symbol)
        price = last
        prov = settings.provider()
        if prov == "fmp":
            try:
                from app.data.live_providers import fmp_quote

                q = fmp_quote(symbol)
                if q and q.get("price"):
                    price = float(q["price"])
                    if q.get("prev_close"):
                        prev = float(q["prev_close"])
            except Exception:
                pass
        elif prov == "dhan":
            try:
                from app.data import dhan_feed
                from app.data.dhan_provider import dhan_quote

                dhan_feed.ensure_started([symbol])
                tick = dhan_feed.get_tick(symbol)   # websocket / poller push cache
                if tick and tick.get("price"):
                    price = float(tick["price"])
                    if tick.get("prev_close"):
                        prev = float(tick["prev_close"])
                else:                               # cold cache → one REST quote
                    q = dhan_quote(symbol)
                    if q and q.get("price"):
                        price = float(q["price"])
                        if q.get("prev_close"):
                            prev = float(q["prev_close"])
            except Exception:
                pass
        elif prov == "yfinance":
            live = _live_price(symbol)
            if live:
                price = live
        change_pct = round((price / prev - 1) * 100, 2) if prev else 0.0
        return {
            "symbol": symbol,
            "price": round(price, 2),
            "prev_close": round(prev, 2),
            "change_pct": change_pct,
            "ts": int(time.time()),
            "live": prov != "sample",
        }

    # short TTL so live polling stays cheap; 2s
    return cached(f"quote:{symbol}", 2, _load)
