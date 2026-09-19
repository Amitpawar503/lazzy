from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.models.schemas import NewsFeed
from app.services.news import get_news

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("", response_model=NewsFeed, summary="Aggregated market news")
def news(
    category: str = Query("all", pattern="^(all|india|global)$"),
    ticker: Optional[str] = Query(None, description="Filter to news mentioning this symbol"),
    limit: int = Query(50, ge=1, le=200),
) -> NewsFeed:
    return get_news(category=category, ticker=ticker, limit=limit)
