"""Resume upload, listing, matches, and per-job enhancement."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session, select

from ..database import get_session
from ..models import Job, Resume
from ..schemas import EnhanceRequest, EnhanceResponse, JobOut, ResumeOut

router = APIRouter(prefix="/api/resumes", tags=["resumes"])

MAX_BYTES = 8 * 1024 * 1024  # 8 MB


@router.post("", response_model=ResumeOut)
async def upload_resume(file: UploadFile = File(...), session: Session = Depends(get_session)):
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "Resume too large (max 8MB)")
    from ..matching.resume_parser import parse_resume

    parsed = parse_resume(file.filename or "resume", content)
    if not parsed["text"]:
        raise HTTPException(422, "Could not extract text from resume. Use PDF, DOCX, or TXT.")
    resume = Resume(
        filename=file.filename or "resume",
        text=parsed["text"][:60000],
        skills=parsed["skills"],
        title_hint=parsed["title_hint"],
    )
    session.add(resume)
    session.commit()
    session.refresh(resume)
    return ResumeOut.model_validate(resume)


@router.get("", response_model=list[ResumeOut])
def list_resumes(session: Session = Depends(get_session)):
    rows = session.exec(select(Resume).order_by(Resume.created_at.desc())).all()
    return [ResumeOut.model_validate(r) for r in rows]


@router.get("/{resume_id}/matches", response_model=list[JobOut])
def resume_matches(
    resume_id: int,
    limit: int = 30,
    use_ai: bool = False,
    session: Session = Depends(get_session),
):
    resume = session.get(Resume, resume_id)
    if not resume:
        raise HTTPException(404, "Resume not found")

    # Score a recent candidate window; rank; optionally AI re-rank the top.
    candidates = list(session.exec(select(Job).order_by(Job.ingested_at.desc()).limit(400)))
    from ..matching.matcher import score_resume_against_jobs

    rtext = f"{resume.title_hint} {resume.skills} {resume.text}"
    scored = score_resume_against_jobs(rtext, candidates)
    candidates.sort(key=lambda j: scored.get(j.id, (0.0, ""))[0], reverse=True)

    top = candidates[: max(limit, 20)]
    if use_ai:
        from ..ai.enhancer import ai_rerank
        ai_scores = ai_rerank(rtext, top[:20])
        for jid, val in ai_scores.items():
            scored[jid] = val
        top.sort(key=lambda j: scored.get(j.id, (0.0, ""))[0], reverse=True)

    out = []
    for j in top[:limit]:
        item = JobOut.model_validate(j)
        item.description = (j.description or "")[:400]
        sc = scored.get(j.id)
        if sc:
            item.match_score, item.match_reason = sc
        out.append(item)
    return out


@router.post("/enhance", response_model=EnhanceResponse)
def enhance(req: EnhanceRequest, session: Session = Depends(get_session)):
    resume = session.get(Resume, req.resume_id)
    job = session.get(Job, req.job_id)
    if not resume:
        raise HTTPException(404, "Resume not found")
    if not job:
        raise HTTPException(404, "Job not found")
    from ..ai.enhancer import enhance_resume_for_job

    result = enhance_resume_for_job(resume, job)
    return EnhanceResponse(**result)
