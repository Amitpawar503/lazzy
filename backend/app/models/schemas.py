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


# --- Best-stock screeners (sector / cap / momentum / seasonal) --- #

class AlgoStrength(BaseModel):
    algo: str
    strength_pct: float   # 0..100 — "how much" this algo leans


class ScreenerRow(BaseModel):
    symbol: str
    name: str
    sector: str
    cap_class: str
    market_cap_cr: float
    metric_label: str     # what the dimension ranked on
    metric_value: float
    # multi-algo consensus attached to every row
    bullish: int
    bearish: int
    neutral: int
    net_score: float
    verdict: str
    up_algos: list[AlgoStrength]     # algos voting the stock UP (+ how much)
    down_algos: list[AlgoStrength]   # algos voting the stock DOWN (+ how much)


class ScreenerResult(BaseModel):
    dimension: str        # sector | cap | momentum | seasonal
    key: Optional[str]    # e.g. sector name or cap class, when filtered
    metric_label: str
    count: int
    rows: list[ScreenerRow]


# --- News feed --- #

class NewsItem(BaseModel):
    id: str
    source: str
    title: str
    url: str
    published: str
    summary: str
    tickers: list[str]
    sentiment: str        # positive | negative | neutral
    sentiment_score: float  # -1..+1
    category: str         # india | global


class NewsFeed(BaseModel):
    count: int
    sources: list[str]
    items: list[NewsItem]


# --- News impact (event → affected companies) --- #

class ImpactedStock(BaseModel):
    symbol: str
    name: str
    relation: str         # holder | parent | subsidiary | peer | index | supplier
    relation_detail: str
    short_term: float     # -100..+100
    long_term: float      # -100..+100
    direction: str        # positive | negative | mixed | neutral
    rationale: str


class MarketEvent(BaseModel):
    id: str
    title: str
    entity: str           # the subject entity (e.g. "Tata Sons")
    kind: str             # listing | earnings | policy | mna | rating | management
    date: str
    summary: str
    impacted: list[ImpactedStock]


class EventList(BaseModel):
    count: int
    events: list[MarketEvent]
