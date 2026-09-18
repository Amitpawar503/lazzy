from __future__ import annotations

from fastapi import APIRouter, Query

from app.models.schemas import FlowSummary, InstitutionalActivity
from app.services.fiidii import flow_summary, institutional_activity

router = APIRouter(prefix="/api/fiidii", tags=["fii-dii"])


@router.get("/flows", response_model=FlowSummary, summary="FII/DII net cash flows")
def flows() -> FlowSummary:
    return flow_summary()


@router.get(
    "/activity",
    response_model=InstitutionalActivity,
    summary="Stocks institutions added / removed",
)
def activity(
    top_n: int = Query(10, ge=1, le=100, description="How many stocks per side"),
) -> InstitutionalActivity:
    return institutional_activity(top_n=top_n)
