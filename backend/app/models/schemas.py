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


class ScreenerSection(BaseModel):
    key: str
    label: str
    count: int
    rows: list[ScreenerRow]


class GroupedScreener(BaseModel):
    dimension: str        # sector | cap
    metric_label: str
    sections: list[ScreenerSection]


# --- Style Picks (6 sections + style consensus) --- #

class StyleConsensus(BaseModel):
    favour: int
    neutral: int
    against: int
    total: int


class StyleRow(ScreenerRow):
    consensus: StyleConsensus
    volatility: float


class StyleSection(BaseModel):
    key: str
    label: str
    metric_label: str
    count: int
    ret_1y: float
    ret_5y: float
    alpha_1y: float
    beats_benchmark_1y: bool
    volatility: float
    max_drawdown: float
    sharpe: float
    spark: list[float]
    benchmark_spark: list[float]
    rows: list[StyleRow]


class StyleSections(BaseModel):
    section_count: int
    sections: list[StyleSection]


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


# --- Stock detail (bull/bear thesis) --- #

class Quote(BaseModel):
    last_price: float
    change_pct_1d: float
    ret_1w: float
    ret_1m: float
    high_52w: float
    low_52w: float
    pct_from_52w_high: float
    pct_from_52w_low: float
    live: bool


class Fundamentals(BaseModel):
    symbol: str
    pe: float
    industry_pe: float
    pb: float
    dividend_yield: float
    eps: float
    book_value: float
    roe: float
    roce: float
    sales_growth_yoy: float
    profit_growth_yoy: float
    operating_margin: float
    net_profit_margin: float
    debt_to_equity: float
    current_ratio: float
    ocf_positive: bool
    free_cash_flow_cr: float
    promoter_holding: float
    promoter_pledge: float
    fii_holding: float
    dii_holding: float
    public_holding: float
    high_pledge: bool
    falling_sales: bool
    expensive_vs_industry: bool
    cheap_vs_industry: bool


class ThesisPoint(BaseModel):
    kind: str
    point: str
    detail: str


class Factor(BaseModel):
    label: str
    detail: str
    sentiment: str        # positive | negative | neutral
    category: str


class Factors(BaseModel):
    strengths: list[Factor]
    weaknesses: list[Factor]
    opportunities: list[Factor]
    threats: list[Factor]
    corporate_actions: list[Factor]
    orders: list[Factor]
    management: list[Factor]


class StockDetail(BaseModel):
    symbol: str
    name: str
    sector: str
    cap_class: str
    market_cap_cr: float
    quote: Quote
    verdict: str
    net_score: float
    bullish: int
    bearish: int
    neutral: int
    algos: list[AlgoVote]
    fundamentals: Fundamentals
    bull_points: list[ThesisPoint]
    bear_points: list[ThesisPoint]
    factors: Factors


# --- Reasoning (row hover) --- #

class NewsImpactNote(BaseModel):
    title: str
    short_term: float
    long_term: float
    direction: str


class Reasoning(BaseModel):
    symbol: str
    verdict: str
    net_score: float
    bull: list[ThesisPoint]
    bear: list[ThesisPoint]
    factors: Factors
    news: list[str]                 # headlines mentioning the stock
    impact: list[NewsImpactNote]    # event-graph impact on the stock


# --- Strategies (ProPicks-style baskets) --- #

class StrategyCard(BaseModel):
    id: str
    name: str
    description: str
    philosophy: str = ""     # how this style/guru picks stocks
    category: str        # sector | cap | theme | style
    region: str
    period: str
    rebalance: str
    constituents_count: int
    ret_1y: float
    ret_5y: float
    benchmark_ret_1y: float
    benchmark_ret_5y: float
    alpha_1y: float
    alpha_5y: float
    beats_benchmark_1y: bool
    beats_benchmark_5y: bool
    volatility: float
    max_drawdown: float
    sharpe: float
    spark: list[float]
    benchmark_spark: list[float]


class StrategyList(BaseModel):
    count: int
    strategies: list[StrategyCard]


class StrategyDetail(StrategyCard):
    constituents: list[ScreenerRow]
