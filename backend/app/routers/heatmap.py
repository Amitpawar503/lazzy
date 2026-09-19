from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.models.schemas import Heatmap360, SectorHeatmap
from app.services.heatmap import build_360, build_sector_heatmap

router = APIRouter(prefix="/api/heatmap", tags=["heatmap"])

Timeframe = Query("1d", pattern="^(1d|1w|1m)$", description="Return window")


@router.get("/360", response_model=Heatmap360, summary="360° market treemap")
def market_360(
    timeframe: str = Timeframe,
    top_n: int = Query(50, ge=1, le=500, description="How many stocks to show"),
    sector: Optional[str] = Query(None, description="Optional sector filter"),
) -> Heatmap360:
    return build_360(timeframe=timeframe, top_n=top_n, sector=sector)


@router.get("/sectors", response_model=SectorHeatmap, summary="Sector heatmap")
def sector_heatmap(timeframe: str = Timeframe) -> SectorHeatmap:
    return build_sector_heatmap(timeframe=timeframe)
