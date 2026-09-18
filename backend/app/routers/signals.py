from __future__ import annotations

from fastapi import APIRouter, Query

from app.models.schemas import Scorecard, StockSignal
from app.services.signals import compute_signals, scorecard

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("/scorecard", response_model=Scorecard, summary="Multi-algo consensus per stock")
def get_scorecard(
    top_n: int = Query(20, ge=1, le=500, description="How many stocks to show"),
    view: str = Query("all", pattern="^(all|bullish|bearish)$"),
    sort: str = Query("score", pattern="^(score|bullish|bearish)$"),
) -> Scorecard:
    return scorecard(top_n=top_n, view=view, sort=sort)


@router.get("/{symbol}", response_model=StockSignal, summary="Per-algo breakdown for one stock")
def get_stock_signal(symbol: str) -> StockSignal:
    return compute_signals(symbol.upper())
