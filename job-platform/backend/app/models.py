"""Database models.

The central entity is `Job`. Jobs are normalized from many sources into a
single shape, deduplicated by `fingerprint`, and classified for the remote /
WFH tabs at ingest time so filtering is cheap at query time.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Stable hash of (source, external_id) used to dedupe across polls.
    fingerprint: str = Field(index=True, unique=True)

    source: str = Field(index=True)          # e.g. "greenhouse", "remotive"
    external_id: str                         # id within the source
    apply_url: str                           # the real link to apply
    title: str = Field(index=True)
    company: str = Field(index=True)
    company_slug: str = Field(default="", index=True)

    location_raw: str = Field(default="")
    country: str = Field(default="", index=True)   # best-effort ISO-ish name
    category: str = Field(default="", index=True)  # e.g. "Software"
    description: str = Field(default="")           # plain-ish text/html
    salary_raw: str = Field(default="")
    salary_min: Optional[int] = Field(default=None, index=True)
    salary_max: Optional[int] = Field(default=None)

    # Classification for the UI tabs (computed at ingest).
    is_remote: bool = Field(default=False, index=True)
    remote_scope: str = Field(default="", index=True)   # "india" | "outside_india" | "global" | ""
    is_wfh_ncr: bool = Field(default=False, index=True)  # WFH/flexible in Delhi-NCR

    posted_at: Optional[datetime] = Field(default=None, index=True)
    ingested_at: datetime = Field(default_factory=utcnow, index=True)


class CompanySource(SQLModel, table=True):
    """A configured career-page source to poll.

    `provider` is the ATS/board type; `slug` is that provider's board token,
    e.g. provider="greenhouse", slug="stripe".
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str = Field(index=True)
    slug: str = Field(index=True)
    display_name: str = Field(default="")
    enabled: bool = Field(default=True)
    last_polled_at: Optional[datetime] = Field(default=None)
    last_error: str = Field(default="")


class Resume(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(default="")
    text: str = Field(default="")            # extracted plain text
    skills: str = Field(default="")         # comma-separated, extracted
    title_hint: str = Field(default="")     # inferred target role
    created_at: datetime = Field(default_factory=utcnow)


class Match(SQLModel, table=True):
    """Cached resume<->job match score so the feed can rank without recompute."""
    id: Optional[int] = Field(default=None, primary_key=True)
    resume_id: int = Field(index=True)
    job_id: int = Field(index=True)
    score: float = Field(default=0.0, index=True)   # 0..100
    reason: str = Field(default="")                 # short explanation
    method: str = Field(default="tfidf")            # "tfidf" | "ai"
    created_at: datetime = Field(default_factory=utcnow)
