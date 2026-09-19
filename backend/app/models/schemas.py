"""Pydantic response models (API contract)."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class HeatmapTile(BaseModel):
    symbol: str
    name: str
    sector: str
    market_cap_cr: float
    cap_class: str
    weight: float          # market-cap share (0..1) → treemap box size
    return_pct: float
    last_price: Optional[float] = None


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
    top_gainer: Optional[str] = None
    top_loser: Optional[str] = None


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


# --- Multi-algo signal consensus --- #

class AlgoVote(BaseModel):
    algo: str
    signal: int          # +1 bullish / 0 neutral / -1 bearish
    strength: float      # 0..1
    detail: str


class StockSignal(BaseModel):
    symbol: str
    total_algos: int
    bullish: int
    bearish: int
    neutral: int
    net_score: float     # -100..+100
    verdict: str
    algos: list[AlgoVote]


class ScorecardRow(BaseModel):
    symbol: str
    name: str
    sector: str
    cap_class: str
    bullish: int
    bearish: int
    neutral: int
    total_algos: int
    net_score: float
    verdict: str


class Scorecard(BaseModel):
    algos: list[str]
    count: int
    rows: list[ScorecardRow]
