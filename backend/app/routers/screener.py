from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.models.schemas import GroupedScreener, ScreenerResult
from app.services.screener import screen, screen_grouped

router = APIRouter(prefix="/api/screener", tags=["screener"])


@router.get("", response_model=ScreenerResult, summary="Best stocks by dimension")
def get_screener(
    dimension: str = Query("momentum", pattern="^(sector|cap|momentum|seasonal)$"),
    key: Optional[str] = Query(None, description="Filter, e.g. sector name or cap class (large/mid/small/micro)"),
    top_n: int = Query(20, ge=1, le=500, description="How many stocks to show"),
) -> ScreenerResult:
    return screen(dimension=dimension, key=key, top_n=top_n)


@router.get("/grouped", response_model=GroupedScreener, summary="Subsections per sector / cap class")
def get_grouped(
    dimension: str = Query("sector", pattern="^(sector|cap)$"),
    per_group: int = Query(10, ge=1, le=100, description="How many stocks per subsection"),
) -> GroupedScreener:
    return screen_grouped(dimension=dimension, per_group=per_group)
