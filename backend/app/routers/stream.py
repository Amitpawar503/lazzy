"""Quotes: REST batch + Server-Sent Events stream (near-live).

The SSE stream polls the quote provider on an interval and pushes updates to the
browser (EventSource), buffering between ticks. When LIVE_DATA is off it applies
a tiny random walk so movement is visible for demos; when on, each tick reflects
the latest polled price. Zero-delay ticks → broker websocket (Phase 6).
"""
from __future__ import annotations

import asyncio
import json
import random

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.data.live_quotes import get_quote

router = APIRouter(prefix="/api", tags=["quotes"])


def _parse(symbols: str) -> list[str]:
    return [s.strip().upper() for s in symbols.split(",") if s.strip()][:50]


@router.get("/quotes", summary="Batch near-live quotes")
def quotes(symbols: str = Query(..., description="Comma-separated symbols")) -> dict:
    syms = _parse(symbols)
    return {"quotes": [get_quote(s) for s in syms]}


@router.get("/depth/{symbol}", summary="20-level Full Market Depth (Dhan live feed)")
def depth(symbol: str) -> dict:
    """Live 20-level order book from Dhan's Full Market Depth websocket feed.

    Returns empty ladders unless DATA_PROVIDER=dhan with valid creds and the
    websocket feed is connected (20-level depth is websocket-only)."""
    symbol = symbol.upper()
    if get_settings().provider() != "dhan":
        return {"symbol": symbol, "buy": [], "sell": [], "live": False,
                "note": "Set DATA_PROVIDER=dhan (with a demat account) for live depth."}
    try:
        from app.data import dhan_feed

        dhan_feed.ensure_started([symbol])
        book = dhan_feed.get_depth(symbol)
        if book:
            return {"symbol": symbol, **book, "live": True}
        return {"symbol": symbol, "buy": [], "sell": [], "live": False,
                "note": "Depth feed warming up or symbol not subscribed."}
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/stream/quotes", summary="SSE near-live quote stream")
async def stream_quotes(
    symbols: str = Query(..., description="Comma-separated symbols"),
    interval: float = Query(2.0, ge=0.5, le=10.0),
) -> StreamingResponse:
    syms = _parse(symbols)

    # Start the Dhan realtime feed (websocket push + poller) for these symbols so
    # each SSE tick reflects the latest live price (no-op unless provider=dhan).
    if get_settings().provider() == "dhan":
        try:
            from app.data import dhan_feed

            dhan_feed.ensure_started(syms)
        except Exception:
            pass

    async def gen():
        # seed prices
        state = {s: get_quote(s) for s in syms}
        while True:
            batch = []
            for s in syms:
                q = get_quote(s)
                # demo jitter when not live so the stream visibly moves
                if not q["live"]:
                    drift = random.uniform(-0.004, 0.004)
                    base = state[s]["price"]
                    price = round(base * (1 + drift), 2)
                    q = {**q, "price": price,
                         "change_pct": round((price / q["prev_close"] - 1) * 100, 2)}
                    state[s] = q
                batch.append(q)
            yield f"data: {json.dumps(batch)}\n\n"
            await asyncio.sleep(interval)

    return StreamingResponse(gen(), media_type="text/event-stream")
