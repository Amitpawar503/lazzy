"""Base types shared by all ingest adapters.

Every adapter yields `RawJob` objects. The pipeline (pipeline.py) is
responsible for classification, dedupe, and persistence, so adapters stay thin
and only know how to talk to their source.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


def strip_html(html: str) -> str:
    if not html:
        return ""
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


@dataclass
class RawJob:
    source: str
    external_id: str
    title: str
    company: str
    apply_url: str
    location_raw: str = ""
    description: str = ""
    category: str = ""
    salary_raw: str = ""
    company_slug: str = ""
    posted_at: Optional[datetime] = None
    source_remote: Optional[bool] = None  # source explicitly said remote
    extra: dict = field(default_factory=dict)

    def fingerprint(self) -> str:
        key = f"{self.source}:{self.external_id}".lower()
        return hashlib.sha1(key.encode("utf-8")).hexdigest()


class SourceError(Exception):
    """Raised by an adapter when a source can't be fetched/parsed."""
