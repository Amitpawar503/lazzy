from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.models.schemas import ScreenerResult
from app.services.screener import screen

router = APIRouter(prefix="/api/screener", tags=["screener"])


@router.get("", response_model=ScreenerResult, summary="Best stocks by dimension")
def get_screener(
    dimension: str = Query("momentum", pattern="^(sector|cap|momentum|seasonal)$"),
    key: Optional[str] = Query(None, description="Filter, e.g. sector name or cap class (large/mid/small/micro)"),
    top_n: int = Query(20, ge=1, le=500, description="How many stocks to show"),
) -> ScreenerResult:
    return screen(dimension=dimension, key=key, top_n=top_n)
