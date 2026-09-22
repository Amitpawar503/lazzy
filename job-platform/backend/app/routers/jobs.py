"""Job listing + filtering endpoints.

Supports the UI tabs and filters directly:
  - tab=remote_india / remote_outside / wfh_ncr / all
  - q (title search), company, category, country, remote, min_salary, date_from
  - resume_id -> attaches match_score/match_reason and sorts by best match
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, func, or_, select

from ..database import get_session
from ..models import Job, Resume
from ..schemas import JobOut, JobPage

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _apply_tab(stmt, tab: str):
    if tab == "remote_india":
        return stmt.where(Job.is_remote == True, Job.remote_scope == "india")  # noqa: E712
    if tab == "remote_outside":
        return stmt.where(Job.is_remote == True, Job.remote_scope.in_(["outside_india", "global"]))  # noqa: E712
    if tab == "wfh_ncr":
        return stmt.where(Job.is_wfh_ncr == True)  # noqa: E712
    return stmt


@router.get("", response_model=JobPage)
def list_jobs(
    session: Session = Depends(get_session),
    tab: str = Query("all"),
    q: Optional[str] = None,
    company: Optional[str] = None,
    category: Optional[str] = None,
    country: Optional[str] = None,
    remote: Optional[bool] = None,
    min_salary: Optional[int] = None,
    date_from: Optional[str] = None,
    resume_id: Optional[int] = None,
    sort: str = Query("recent", pattern="^(recent|match)$"),
    limit: int = Query(30, le=100),
    offset: int = 0,
):
    stmt = select(Job)
    stmt = _apply_tab(stmt, tab)

    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(Job.title).like(like), func.lower(Job.company).like(like)))
    if company:
        stmt = stmt.where(func.lower(Job.company).like(f"%{company.lower()}%"))
    if category:
        stmt = stmt.where(func.lower(Job.category).like(f"%{category.lower()}%"))
    if country:
        stmt = stmt.where(func.lower(Job.country) == country.lower())
    if remote is not None:
        stmt = stmt.where(Job.is_remote == remote)
    if min_salary is not None:
        stmt = stmt.where(Job.salary_max >= min_salary)
    if date_from:
        try:
            dt = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
            stmt = stmt.where(Job.posted_at >= dt)
        except ValueError:
            pass

    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()

    resume = session.get(Resume, resume_id) if resume_id else None

    if resume and sort == "match":
        # Score a bounded candidate window, then rank by match.
        candidates = list(session.exec(stmt.order_by(Job.ingested_at.desc()).limit(400)))
        scored = _score(resume, candidates)
        candidates.sort(key=lambda j: scored.get(j.id, (0.0, ""))[0], reverse=True)
        window = candidates[offset:offset + limit]
        items = [_to_out(j, scored.get(j.id)) for j in window]
        return JobPage(total=total, limit=limit, offset=offset, items=items)

    stmt = stmt.order_by(Job.ingested_at.desc()).offset(offset).limit(limit)
    jobs = list(session.exec(stmt))
    scored = _score(resume, jobs) if resume else {}
    items = [_to_out(j, scored.get(j.id)) for j in jobs]
    return JobPage(total=total, limit=limit, offset=offset, items=items)


def _score(resume: Optional[Resume], jobs: list[Job]) -> dict:
    if not resume or not jobs:
        return {}
    from ..matching.matcher import score_resume_against_jobs
    rtext = f"{resume.title_hint} {resume.skills} {resume.text}"
    return score_resume_against_jobs(rtext, jobs)


def _to_out(job: Job, score: Optional[tuple[float, str]]) -> JobOut:
    out = JobOut.model_validate(job)
    # Trim description in list view for payload size.
    out.description = (job.description or "")[:400]
    if score:
        out.match_score, out.match_reason = score
    return out


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        from fastapi import HTTPException
        raise HTTPException(404, "Job not found")
    return JobOut.model_validate(job)


@router.get("/meta/facets")
def facets(session: Session = Depends(get_session)):
    """Distinct categories/countries for building filter dropdowns."""
    cats = session.exec(select(Job.category).distinct().where(Job.category != "")).all()
    countries = session.exec(select(Job.country).distinct().where(Job.country != "")).all()
    total = session.exec(select(func.count()).select_from(Job)).one()
    return {
        "categories": sorted({c for c in cats if c})[:60],
        "countries": sorted({c for c in countries if c}),
        "total_jobs": total,
    }
