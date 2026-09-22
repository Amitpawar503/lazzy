"""Resume enhancement + AI match re-ranking.

`enhance_resume_for_job` tailors a resume to a specific job/company. With AI
enabled it produces a genuinely tailored summary, bullets, keywords and cover
letter. Without AI it returns a useful deterministic draft built from the
resume<->job keyword gap, so the feature works with zero keys.
"""
from __future__ import annotations

from ..matching.matcher import _tokens, job_text
from ..models import Job, Resume
from . import client


def enhance_resume_for_job(resume: Resume, job: Job) -> dict:
    if client.is_enabled():
        ai = _ai_enhance(resume, job)
        if ai:
            ai["ai_used"] = True
            return ai
    result = _fallback_enhance(resume, job)
    result["ai_used"] = False
    return result


def _ai_enhance(resume: Resume, job: Job) -> dict | None:
    system = (
        "You are an expert technical resume writer and career coach. "
        "Tailor the candidate's resume to the target job. Be truthful — never "
        "invent experience the resume does not support. Return ONLY JSON."
    )
    prompt = f"""Target company: {job.company}
Target role: {job.title}
Job location: {job.location_raw}
Job description (truncated):
{job.description[:3500]}

Candidate resume (truncated):
{resume.text[:4000]}

Return JSON with exactly these keys:
{{
  "enhanced_summary": "2-3 sentence professional summary tailored to this role",
  "tailored_bullets": ["4-6 resume bullet points rewritten to match this job, using the candidate's real experience"],
  "keywords_to_add": ["ATS keywords from the JD the candidate should surface if truthful"],
  "cover_letter": "a concise 150-200 word cover letter for this company and role"
}}"""
    data = client.complete_json(system, prompt, max_tokens=1800)
    if not data:
        return None
    return {
        "job_id": job.id,
        "company": job.company,
        "title": job.title,
        "enhanced_summary": str(data.get("enhanced_summary", "")),
        "tailored_bullets": [str(b) for b in data.get("tailored_bullets", [])][:8],
        "keywords_to_add": [str(k) for k in data.get("keywords_to_add", [])][:20],
        "cover_letter": str(data.get("cover_letter", "")),
    }


def _fallback_enhance(resume: Resume, job: Job) -> dict:
    r = _tokens(resume.text)
    j = _tokens(job_text(job))
    missing = sorted(j - r)
    # Keep it meaningful: only alphabetic-ish, longer tokens.
    missing = [m for m in missing if len(m) > 3 and not m.isdigit()][:20]
    have = sorted(r & j)[:12]

    summary = (
        f"{resume.title_hint or 'Experienced professional'} targeting the "
        f"{job.title} role at {job.company}. Strengths aligned to this role include "
        f"{', '.join(have[:6]) or 'relevant technical experience'}."
    )
    bullets = [
        f"Aligned experience in {kw} to the requirements of {job.title}."
        for kw in have[:5]
    ] or [f"Relevant experience for the {job.title} role at {job.company}."]
    cover = (
        f"Dear {job.company} Hiring Team,\n\n"
        f"I'm excited to apply for the {job.title} position. My background as a "
        f"{resume.title_hint or 'professional'} maps closely to what you're looking for, "
        f"particularly around {', '.join(have[:4]) or 'the core requirements'}. "
        f"I'd welcome the chance to bring this experience to {job.company}.\n\n"
        f"Best regards"
    )
    return {
        "job_id": job.id,
        "company": job.company,
        "title": job.title,
        "enhanced_summary": summary,
        "tailored_bullets": bullets,
        "keywords_to_add": missing,
        "cover_letter": cover,
    }


def ai_rerank(resume_text: str, jobs: list[Job]) -> dict[int, tuple[float, str]]:
    """Optionally re-score a small batch of jobs with the LLM. id -> (score, reason)."""
    if not client.is_enabled() or not jobs:
        return {}
    listing = "\n".join(
        f"[{j.id}] {j.title} @ {j.company} ({j.location_raw})" for j in jobs
    )
    system = (
        "You are a precise job-matching engine. Score how well the resume fits each "
        "job from 0-100 and give a 6-word reason. Return ONLY JSON."
    )
    prompt = f"""Resume (truncated):
{resume_text[:3500]}

Jobs:
{listing}

Return JSON: {{"scores": [{{"id": <job id>, "score": <0-100>, "reason": "<short>"}}]}}"""
    data = client.complete_json(system, prompt, max_tokens=1500)
    if not data:
        return {}
    out: dict[int, tuple[float, str]] = {}
    for row in data.get("scores", []):
        try:
            jid = int(row["id"])
            score = float(row["score"])
            out[jid] = (round(min(100.0, max(0.0, score)), 1), str(row.get("reason", "")))
        except (KeyError, ValueError, TypeError):
            continue
    return out
