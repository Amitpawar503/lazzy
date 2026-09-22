"""Seed and manage the set of career-page sources to poll."""
from __future__ import annotations

import json
from pathlib import Path

from sqlmodel import Session, select

from ..database import engine
from ..models import CompanySource
from .adapters import PROVIDERS

SEED_FILE = Path(__file__).parent / "seed_sources.json"


def seed_sources_if_empty() -> int:
    """Load seed_sources.json into the DB the first time the app runs."""
    with Session(engine) as session:
        existing = session.exec(select(CompanySource)).first()
        if existing:
            return 0
        try:
            seeds = json.loads(SEED_FILE.read_text())
        except (OSError, json.JSONDecodeError):
            return 0
        count = 0
        for s in seeds:
            if s.get("provider") not in PROVIDERS:
                continue
            session.add(CompanySource(
                provider=s["provider"],
                slug=s["slug"],
                display_name=s.get("display_name", ""),
                enabled=True,
            ))
            count += 1
        session.commit()
        return count


def add_source(provider: str, slug: str, display_name: str = "") -> CompanySource | None:
    if provider not in PROVIDERS:
        return None
    with Session(engine) as session:
        found = session.exec(
            select(CompanySource).where(
                CompanySource.provider == provider, CompanySource.slug == slug
            )
        ).first()
        if found:
            return found
        src = CompanySource(provider=provider, slug=slug, display_name=display_name or slug)
        session.add(src)
        session.commit()
        session.refresh(src)
        return src
