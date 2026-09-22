"""Ingestion pipeline: fetch -> normalize -> classify -> dedupe -> persist.

Called by both the scheduler (periodic) and the manual /ingest endpoint.
New jobs are broadcast to SSE subscribers, optionally scored against the most
recent resume so the live feed can highlight matches immediately.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import httpx
from sqlmodel import Session, select

from ..config import get_settings
from ..database import engine
from ..events import broadcast
from ..models import CompanySource, Job, Resume
from ..utils.location import classify, parse_salary
from .adapters import PROVIDERS
from .base import RawJob, SourceError

log = logging.getLogger("ingest")
settings = get_settings()


def _to_job(raw: RawJob) -> Job:
    cls = classify(raw.location_raw, raw.description, raw.source_remote)
    smin, smax = parse_salary(raw.salary_raw or raw.description[:400])
    return Job(
        fingerprint=raw.fingerprint(),
        source=raw.source,
        external_id=raw.external_id,
        apply_url=raw.apply_url,
        title=raw.title,
        company=raw.company,
        company_slug=raw.company_slug,
        location_raw=raw.location_raw,
        country=cls["country"],
        category=raw.category,
        description=raw.description,
        salary_raw=raw.salary_raw,
        salary_min=smin,
        salary_max=smax,
        is_remote=cls["is_remote"],
        remote_scope=cls["remote_scope"],
        is_wfh_ncr=cls["is_wfh_ncr"],
        posted_at=raw.posted_at,
    )


async def _fetch_source(client: httpx.AsyncClient, src: CompanySource) -> list[RawJob]:
    fn, wants_slug = PROVIDERS[src.provider]
    if wants_slug:
        return await fn(client, src.slug, limit=settings.ingest_max_per_source)
    return await fn(client, limit=settings.ingest_max_per_source)


def _persist(raws: list[RawJob]) -> list[Job]:
    """Insert only new fingerprints; return the newly inserted Job rows.

    expire_on_commit=False keeps the returned instances' attributes populated
    after the session closes, so the SSE broadcast can read them detached.
    """
    inserted: list[Job] = []
    with Session(engine, expire_on_commit=False) as session:
        for raw in raws:
            if not raw.apply_url or not raw.title:
                continue
            fp = raw.fingerprint()
            exists = session.exec(select(Job.id).where(Job.fingerprint == fp)).first()
            if exists:
                continue
            job = _to_job(raw)
            session.add(job)
            try:
                session.commit()
            except Exception:  # unique race across concurrent polls
                session.rollback()
                continue
            session.refresh(job)
            inserted.append(job)
    return inserted


def _latest_resume_text() -> tuple[int, str] | None:
    with Session(engine) as session:
        r = session.exec(select(Resume).order_by(Resume.created_at.desc())).first()
        if r and r.text:
            return r.id, f"{r.title_hint} {r.skills} {r.text}"
    return None


def _broadcast_new(jobs: list[Job]) -> None:
    from ..matching.matcher import quick_score  # local import avoids cycle

    resume = _latest_resume_text()
    for job in jobs:
        payload = {
            "type": "job",
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "apply_url": job.apply_url,
            "location_raw": job.location_raw,
            "country": job.country,
            "is_remote": job.is_remote,
            "remote_scope": job.remote_scope,
            "is_wfh_ncr": job.is_wfh_ncr,
            "source": job.source,
        }
        if resume:
            _, rtext = resume
            score, reason = quick_score(rtext, job)
            payload["match_score"] = score
            payload["match_reason"] = reason
        broadcast(payload)


async def run_ingest(sources: list[CompanySource] | None = None) -> dict:
    """Run a full ingest pass over the given (or all enabled) sources."""
    with Session(engine) as session:
        if sources is None:
            sources = list(session.exec(select(CompanySource).where(CompanySource.enabled == True)))  # noqa: E712

    fetched = 0
    inserted_total = 0
    ok = 0
    failed = 0
    detail: list[str] = []

    timeout = httpx.Timeout(30.0, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for src in sources:
            try:
                raws = await _fetch_source(client, src)
                fetched += len(raws)
                inserted = _persist(raws)
                inserted_total += len(inserted)
                if inserted:
                    _broadcast_new(inserted)
                ok += 1
                _mark_source(src.id, error="")
                detail.append(f"{src.provider}:{src.slug} -> {len(raws)} fetched, {len(inserted)} new")
            except SourceError as e:
                failed += 1
                _mark_source(src.id, error=str(e)[:400])
                detail.append(f"{src.provider}:{src.slug} FAILED: {e}")
                log.warning("source failed %s:%s %s", src.provider, src.slug, e)
            except Exception as e:  # never let one bad source kill the pass
                failed += 1
                _mark_source(src.id, error=repr(e)[:400])
                detail.append(f"{src.provider}:{src.slug} ERROR: {e!r}")
                log.exception("unexpected source error")
            await asyncio.sleep(settings.ingest_request_delay)

    return {
        "fetched": fetched,
        "inserted": inserted_total,
        "sources_ok": ok,
        "sources_failed": failed,
        "detail": detail,
    }


def _mark_source(source_id: int | None, error: str) -> None:
    if source_id is None:
        return
    with Session(engine) as session:
        src = session.get(CompanySource, source_id)
        if src:
            src.last_polled_at = datetime.now(timezone.utc)
            src.last_error = error
            session.add(src)
            session.commit()
