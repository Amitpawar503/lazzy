// Typed API client for the Lazzy Markets backend.

export type Timeframe = "1d" | "1w" | "1m";

export interface HeatmapTile {
  symbol: string;
  name: string;
  sector: string;
  market_cap_cr: number;
  cap_class: string;
  weight: number;
  return_pct: number;
  last_price: number | null;
}
export interface Heatmap360 {
  timeframe: string;
  count: number;
  min_return: number;
  max_return: number;
  tiles: HeatmapTile[];
}
export interface SectorTile {
  sector: string;
  market_cap_cr: number;
  weight: number;
  return_pct: number;
  constituents: number;
  top_gainer: string | null;
  top_loser: string | null;
}
export interface SectorHeatmap {
  timeframe: string;
  min_return: number;
  max_return: number;
  sectors: SectorTile[];
}
export interface FlowPoint {
  date: string;
  fii_net: number;
  dii_net: number;
}
export interface FlowSummary {
  latest: FlowPoint;
  fii_cumulative: number;
  dii_cumulative: number;
  series: FlowPoint[];
}
export interface HoldingChange {
  symbol: string;
  name: string;
  sector: string;
  fii_delta_pct: number;
  dii_delta_pct: number;
  combined_delta_pct: number;
}
export interface InstitutionalActivity {
  added: HoldingChange[];
  removed: HoldingChange[];
}

export interface AlgoVote {
  algo: string;
  signal: number; // +1 / 0 / -1
  strength: number;
  detail: string;
}
export interface StockSignal {
  symbol: string;
  total_algos: number;
  bullish: number;
  bearish: number;
  neutral: number;
  net_score: number;
  verdict: string;
  algos: AlgoVote[];
}
export interface ScorecardRow {
  symbol: string;
  name: string;
  sector: string;
  cap_class: string;
  bullish: number;
  bearish: number;
  neutral: number;
  total_algos: number;
  net_score: number;
  verdict: string;
}
export interface Scorecard {
  algos: string[];
  count: number;
  rows: ScorecardRow[];
}
export type SignalView = "all" | "bullish" | "bearish";
export type SignalSort = "score" | "bullish" | "bearish";

// --- Screeners ---
export type Dimension = "sector" | "cap" | "momentum" | "seasonal";
export interface AlgoStrength {
  algo: string;
  strength_pct: number;
}
export interface ScreenerRow {
  symbol: string;
  name: string;
  sector: string;
  cap_class: string;
  market_cap_cr: number;
  metric_label: string;
  metric_value: number;
  bullish: number;
  bearish: number;
  neutral: number;
  net_score: number;
  verdict: string;
  up_algos: AlgoStrength[];
  down_algos: AlgoStrength[];
}
export interface ScreenerResult {
  dimension: string;
  key: string | null;
  metric_label: string;
  count: number;
  rows: ScreenerRow[];
}

export interface ScreenerSection {
  key: string;
  label: string;
  count: number;
  rows: ScreenerRow[];
}
export interface GroupedScreener {
  dimension: string;
  metric_label: string;
  sections: ScreenerSection[];
}

// --- Stock detail ---
export interface Quote {
  last_price: number;
  change_pct_1d: number;
  ret_1w: number;
  ret_1m: number;
  high_52w: number;
  low_52w: number;
  pct_from_52w_high: number;
  pct_from_52w_low: number;
  live: boolean;
}
export interface Fundamentals {
  symbol: string;
  pe: number; industry_pe: number; pb: number;
  dividend_yield: number; eps: number; book_value: number;
  roe: number; roce: number;
  sales_growth_yoy: number; profit_growth_yoy: number;
  operating_margin: number; net_profit_margin: number;
  debt_to_equity: number; current_ratio: number;
  ocf_positive: boolean; free_cash_flow_cr: number;
  promoter_holding: number; promoter_pledge: number;
  fii_holding: number; dii_holding: number; public_holding: number;
  high_pledge: boolean; falling_sales: boolean;
  expensive_vs_industry: boolean; cheap_vs_industry: boolean;
}
export interface ThesisPoint { kind: string; point: string; detail: string; }
export interface StockDetail {
  symbol: string; name: string; sector: string; cap_class: string;
  market_cap_cr: number;
  quote: Quote;
  verdict: string; net_score: number;
  bullish: number; bearish: number; neutral: number;
  algos: AlgoVote[];
  fundamentals: Fundamentals;
  bull_points: ThesisPoint[];
  bear_points: ThesisPoint[];
}

// --- News ---
export interface NewsItem {
  id: string;
  source: string;
  title: string;
  url: string;
  published: string;
  summary: string;
  tickers: string[];
  sentiment: string;
  sentiment_score: number;
  category: string;
}
export interface NewsFeed {
  count: number;
  sources: string[];
  items: NewsItem[];
}

// --- News impact ---
export interface ImpactedStock {
  symbol: string;
  name: string;
  relation: string;
  relation_detail: string;
  short_term: number;
  long_term: number;
  direction: string;
  rationale: string;
}
export interface MarketEvent {
  id: string;
  title: string;
  entity: string;
  kind: string;
  date: string;
  summary: string;
  impacted: ImpactedStock[];
}
export interface EventList {
  count: number;
  events: MarketEvent[];
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  market360: (tf: Timeframe, topN: number) =>
    get<Heatmap360>(`/api/heatmap/360?timeframe=${tf}&top_n=${topN}`),
  sectorHeatmap: (tf: Timeframe) =>
    get<SectorHeatmap>(`/api/heatmap/sectors?timeframe=${tf}`),
  flows: () => get<FlowSummary>(`/api/fiidii/flows`),
  activity: (topN: number) =>
    get<InstitutionalActivity>(`/api/fiidii/activity?top_n=${topN}`),
  scorecard: (topN: number, view: SignalView, sort: SignalSort) =>
    get<Scorecard>(
      `/api/signals/scorecard?top_n=${topN}&view=${view}&sort=${sort}`
    ),
  stockSignal: (symbol: string) =>
    get<StockSignal>(`/api/signals/${encodeURIComponent(symbol)}`),
  screener: (dimension: Dimension, topN: number, key?: string | null) =>
    get<ScreenerResult>(
      `/api/screener?dimension=${dimension}&top_n=${topN}` +
        (key ? `&key=${encodeURIComponent(key)}` : "")
    ),
  screenerGrouped: (dimension: "sector" | "cap", perGroup: number) =>
    get<GroupedScreener>(
      `/api/screener/grouped?dimension=${dimension}&per_group=${perGroup}`
    ),
  stock: (symbol: string) =>
    get<StockDetail>(`/api/stock/${encodeURIComponent(symbol)}`),
  news: (category: "all" | "india" | "global", limit: number) =>
    get<NewsFeed>(`/api/news?category=${category}&limit=${limit}`),
  events: () => get<EventList>(`/api/impact/events`),
  meta: () =>
    get<{ universe_size: number; sectors: string[]; timeframes: string[] }>(
      `/meta`
    ),
};
