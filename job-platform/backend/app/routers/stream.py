"""Server-Sent Events endpoint for the live job feed.

Clients open EventSource("/api/stream/jobs"). Every job the pipeline inserts is
pushed as a `job` event. When a resume has been uploaded, each pushed job also
carries a match_score so the UI can highlight relevant new postings instantly.
"""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ..events import subscribe, subscriber_count, unsubscribe

router = APIRouter(prefix="/api/stream", tags=["stream"])


@router.get("/jobs")
async def stream_jobs(request: Request):
    queue = subscribe()

    async def event_gen():
        # Greeting so the client knows the stream is live.
        yield f"event: hello\ndata: {json.dumps({'subscribers': subscriber_count()})}\n\n"
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=20.0)
                    yield f"event: job\ndata: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat keeps proxies from closing the idle connection.
                    yield ": keep-alive\n\n"
        finally:
            unsubscribe(queue)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
