"""API response/request schemas (kept separate from DB models)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class JobOut(BaseModel):
    id: int
    source: str
    apply_url: str
    title: str
    company: str
    company_slug: str
    location_raw: str
    country: str
    category: str
    salary_raw: str
    salary_min: Optional[int]
    salary_max: Optional[int]
    is_remote: bool
    remote_scope: str
    is_wfh_ncr: bool
    posted_at: Optional[datetime]
    ingested_at: datetime
    description: str = ""
    # Populated only when a resume_id is supplied to the endpoint.
    match_score: Optional[float] = None
    match_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[JobOut]


class ResumeOut(BaseModel):
    id: int
    filename: str
    skills: str
    title_hint: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EnhanceRequest(BaseModel):
    resume_id: int
    job_id: int


class EnhanceResponse(BaseModel):
    job_id: int
    company: str
    title: str
    enhanced_summary: str
    tailored_bullets: list[str]
    keywords_to_add: list[str]
    cover_letter: str
    ai_used: bool


class SourceOut(BaseModel):
    id: int
    provider: str
    slug: str
    display_name: str
    enabled: bool
    last_polled_at: Optional[datetime]
    last_error: str

    model_config = ConfigDict(from_attributes=True)


class IngestResult(BaseModel):
    fetched: int
    inserted: int
    sources_ok: int
    sources_failed: int
    detail: list[str] = []
