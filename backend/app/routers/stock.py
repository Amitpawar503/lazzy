from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import StockDetail
from app.services.stock import stock_detail

router = APIRouter(prefix="/api/stock", tags=["stock"])


@router.get("/{symbol}", response_model=StockDetail, summary="Full stock thesis (why up / why down)")
def detail(symbol: str) -> StockDetail:
    d = stock_detail(symbol)
    if d is None:
        raise HTTPException(status_code=404, detail="unknown symbol")
    return d
