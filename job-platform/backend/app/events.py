"""In-process pub/sub for streaming newly ingested jobs to SSE clients.

Each connected SSE client gets an asyncio.Queue. When the pipeline inserts a
new job it calls `broadcast()`, which fans the payload out to every queue.
This is intentionally simple (single-process). For multi-worker deployments,
swap this for Redis pub/sub behind the same interface.
"""
from __future__ import annotations

import asyncio
from typing import Any

_subscribers: set[asyncio.Queue] = set()


def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=1000)
    _subscribers.add(q)
    return q


def unsubscribe(q: asyncio.Queue) -> None:
    _subscribers.discard(q)


def broadcast(event: dict[str, Any]) -> None:
    for q in list(_subscribers):
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            # Slow client: drop the event rather than block ingestion.
            pass


def subscriber_count() -> int:
    return len(_subscribers)
