from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import Reasoning, StockDetail
from app.services.stock import reasoning, stock_detail

router = APIRouter(prefix="/api/stock", tags=["stock"])


@router.get("/{symbol}", response_model=StockDetail, summary="Full stock thesis (why up / why down)")
def detail(symbol: str) -> StockDetail:
    d = stock_detail(symbol)
    if d is None:
        raise HTTPException(status_code=404, detail="unknown symbol")
    return d


@router.get("/{symbol}/reasoning", response_model=Reasoning, summary="Compact bull/bear + news reasoning (row hover)")
def stock_reasoning(symbol: str) -> Reasoning:
    r = reasoning(symbol)
    if r is None:
        raise HTTPException(status_code=404, detail="unknown symbol")
    return r
