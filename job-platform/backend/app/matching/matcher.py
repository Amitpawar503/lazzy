"""Resume <-> job matching.

Two tiers:
  1. quick_score()  — cheap keyword overlap, used in the streaming hot path.
  2. score_resume_against_jobs() — TF-IDF cosine over the corpus for ranking a
     batch, with an optional AI re-rank of the top candidates.

The TF-IDF path has no external dependencies beyond scikit-learn and works
fully offline. AI (Anthropic) is used only to re-score the top-N when a key is
configured, keeping cost bounded.
"""
from __future__ import annotations

import re

from ..models import Job

_WORD = re.compile(r"[a-zA-Z][a-zA-Z0-9+.#]{1,}")


def _tokens(text: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(text or "")}


def job_text(job: Job) -> str:
    return f"{job.title} {job.company} {job.category} {job.location_raw} {job.description[:2000]}"


def quick_score(resume_text: str, job: Job) -> tuple[float, str]:
    """Fast Jaccard-ish overlap for streaming. Returns (0..100, reason)."""
    r = _tokens(resume_text)
    j = _tokens(job_text(job))
    if not r or not j:
        return 0.0, ""
    overlap = r & j
    # Weight title overlap more heavily.
    title_tokens = _tokens(job.title)
    title_hits = len(r & title_tokens)
    base = len(overlap) / max(len(j), 1)
    score = min(100.0, base * 140 + title_hits * 6)
    top = sorted(overlap & (title_tokens | _tokens(job.category)))[:6]
    reason = "Overlap: " + ", ".join(top) if top else "Keyword overlap"
    return round(score, 1), reason


def score_resume_against_jobs(resume_text: str, jobs: list[Job]) -> dict[int, tuple[float, str]]:
    """TF-IDF cosine similarity of the resume against each job. id -> (score, reason)."""
    if not jobs or not resume_text.strip():
        return {}
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except Exception:
        # Degrade to quick_score if sklearn is unavailable.
        return {j.id: quick_score(resume_text, j) for j in jobs if j.id}

    corpus = [resume_text] + [job_text(j) for j in jobs]
    try:
        vec = TfidfVectorizer(stop_words="english", max_features=20000, ngram_range=(1, 2))
        matrix = vec.fit_transform(corpus)
    except ValueError:
        return {j.id: quick_score(resume_text, j) for j in jobs if j.id}

    sims = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    resume_tokens = _tokens(resume_text)
    out: dict[int, tuple[float, str]] = {}
    for job, sim in zip(jobs, sims):
        if job.id is None:
            continue
        score = round(min(100.0, float(sim) * 100 * 2.2), 1)  # scale cosine into a friendlier 0..100
        overlap = sorted(resume_tokens & _tokens(job.title + " " + job.category))[:6]
        reason = "Matches: " + ", ".join(overlap) if overlap else "Semantic overlap with your resume"
        out[job.id] = (score, reason)
    return out
