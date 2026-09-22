"""Manage career-page sources and trigger manual ingestion."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from ..database import get_session
from ..ingest.adapters import PROVIDERS
from ..ingest.pipeline import run_ingest
from ..ingest.registry import add_source
from ..models import CompanySource
from ..schemas import IngestResult, SourceOut

router = APIRouter(prefix="/api/sources", tags=["sources"])


class AddSourceReq(BaseModel):
    provider: str
    slug: str
    display_name: str = ""


@router.get("", response_model=list[SourceOut])
def list_sources(session: Session = Depends(get_session)):
    rows = session.exec(select(CompanySource).order_by(CompanySource.provider)).all()
    return [SourceOut.model_validate(r) for r in rows]


@router.get("/providers")
def providers():
    return {"providers": sorted(PROVIDERS.keys())}


@router.post("", response_model=SourceOut)
def create_source(req: AddSourceReq):
    if req.provider not in PROVIDERS:
        raise HTTPException(400, f"Unknown provider. Use one of: {sorted(PROVIDERS)}")
    src = add_source(req.provider, req.slug.strip(), req.display_name.strip())
    if not src:
        raise HTTPException(400, "Could not add source")
    return SourceOut.model_validate(src)


@router.post("/ingest", response_model=IngestResult)
async def trigger_ingest():
    """Run an ingest pass now (blocks until done — handy for demos/testing)."""
    result = await run_ingest()
    return IngestResult(**result)


@router.post("/ingest/async")
def trigger_ingest_async(background: BackgroundTasks):
    """Kick off ingestion in the background and return immediately."""
    async def _run():
        await run_ingest()
    background.add_task(_run)
    return {"status": "started"}


@router.post("/load-sample")
def load_sample():
    """Load offline sample jobs so the stack is usable without network egress."""
    from ..ingest.sample import load_sample_jobs

    inserted = load_sample_jobs()
    return {"inserted": inserted}
