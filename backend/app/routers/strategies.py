from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import StrategyDetail, StrategyList
from app.services.strategies import get_strategy, list_strategies

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


@router.get("", response_model=StrategyList, summary="Curated strategy baskets (ProPicks-style)")
def strategies() -> StrategyList:
    return list_strategies()


@router.get("/{strategy_id}", response_model=StrategyDetail, summary="Strategy detail + constituents")
def strategy(strategy_id: str) -> StrategyDetail:
    s = get_strategy(strategy_id)
    if s is None:
        raise HTTPException(status_code=404, detail="unknown strategy")
    return s
