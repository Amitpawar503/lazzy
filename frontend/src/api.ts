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
};
