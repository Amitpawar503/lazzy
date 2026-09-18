"""Pydantic response models (API contract)."""
from __future__ import annotations

from pydantic import BaseModel


class HeatmapTile(BaseModel):
    symbol: str
    name: str
    sector: str
    market_cap_cr: float
    cap_class: str
    weight: float          # market-cap share (0..1) → treemap box size
    return_pct: float
    last_price: float | None = None


class Heatmap360(BaseModel):
    timeframe: str
    count: int
    min_return: float
    max_return: float
    tiles: list[HeatmapTile]


class SectorTile(BaseModel):
    sector: str
    market_cap_cr: float
    weight: float
    return_pct: float       # market-cap-weighted sector return
    constituents: int
    top_gainer: str | None = None
    top_loser: str | None = None


class SectorHeatmap(BaseModel):
    timeframe: str
    min_return: float
    max_return: float
    sectors: list[SectorTile]


class FlowPoint(BaseModel):
    date: str
    fii_net: float
    dii_net: float


class FlowSummary(BaseModel):
    latest: FlowPoint
    fii_cumulative: float
    dii_cumulative: float
    series: list[FlowPoint]


class HoldingChange(BaseModel):
    symbol: str
    name: str
    sector: str
    fii_delta_pct: float
    dii_delta_pct: float
    combined_delta_pct: float


class InstitutionalActivity(BaseModel):
    added: list[HoldingChange]     # institutions increased stake
    removed: list[HoldingChange]   # institutions trimmed stake
