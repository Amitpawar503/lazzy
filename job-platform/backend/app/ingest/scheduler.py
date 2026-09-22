"""Background scheduler that polls all sources on an interval.

Uses APScheduler's AsyncIOScheduler so ingest runs on the app's event loop.
The interval is configurable (INGEST_INTERVAL_SECONDS). This is what makes the
feed "stream as soon as jobs are posted" — every new job found is broadcast to
connected SSE clients immediately after insert.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..config import get_settings
from .pipeline import run_ingest

log = logging.getLogger("ingest.scheduler")
settings = get_settings()

_scheduler: AsyncIOScheduler | None = None


async def _job() -> None:
    log.info("scheduled ingest starting")
    result = await run_ingest()
    log.info("scheduled ingest done: %s new / %s fetched", result["inserted"], result["fetched"])


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        _job,
        "interval",
        seconds=settings.ingest_interval_seconds,
        id="ingest",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    log.info("scheduler started; interval=%ss", settings.ingest_interval_seconds)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
