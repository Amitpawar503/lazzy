from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.data.universe import get_universe
from app.models.schemas import Reasoning, StockDetail
from app.services.news import stock_news as stock_news_svc
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


@router.get("/{symbol}/news", summary="Per-stock news (Moneycontrol logged-in + live feed)")
def stock_news(symbol: str, limit: int = Query(20, ge=1, le=50)) -> dict:
    symbol = symbol.upper()
    name = next((r.get("name", "") for r in get_universe() if r["symbol"] == symbol), "")
    return stock_news_svc(symbol, name, limit)
