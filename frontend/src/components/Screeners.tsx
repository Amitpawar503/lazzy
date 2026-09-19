import { useEffect, useState } from "react";
import {
  api,
  type Dimension,
  type GroupedScreener,
  type ScreenerResult,
  type ScreenerRow,
} from "../api";
import Controls from "./Controls";
import AlgoBreakdown from "./AlgoBreakdown";
import { useStockDetail } from "./StockDetail";

const DIMS: { id: Dimension; label: string; blurb: string }[] = [
  { id: "sector", label: "Sector-wise", blurb: "Best stocks grouped into a subsection per sector" },
  { id: "cap", label: "Cap-wise", blurb: "Best stocks grouped by market-cap class (large / mid / small / micro)" },
  { id: "momentum", label: "Momentum", blurb: "Ranked by 3-month price momentum" },
  { id: "seasonal", label: "Seasonal", blurb: "Strongest in the current calendar month" },
];

function verdictClass(v: string) {
  if (v.includes("Strong Buy")) return "v-strong-buy";
  if (v === "Buy") return "v-buy";
  if (v.includes("Strong Sell")) return "v-strong-sell";
  if (v === "Sell") return "v-sell";
  return "v-neutral";
}

function AlgoPills({ r }: { r: ScreenerRow }) {
  return (
    <div className="pills">
      <div className="pill-row up">
        {r.up_algos.length === 0 && <span className="pill-none">—</span>}
        {r.up_algos.map((a) => (
          <span key={a.algo} className="pill up" title={`${a.algo}: ${a.strength_pct}%`}>
            ▲ {a.algo.split(" ")[0]} {a.strength_pct > 0 ? `${a.strength_pct}%` : ""}
          </span>
        ))}
      </div>
      <div className="pill-row dn">
        {r.down_algos.length === 0 && <span className="pill-none">—</span>}
        {r.down_algos.map((a) => (
          <span key={a.algo} className="pill dn" title={`${a.algo}: ${a.strength_pct}%`}>
            ▼ {a.algo.split(" ")[0]} {a.strength_pct > 0 ? `${a.strength_pct}%` : ""}
          </span>
        ))}
      </div>
    </div>
  );
}

function RowTable({ rows, metricLabel, showMetric }: { rows: ScreenerRow[]; metricLabel: string; showMetric: boolean }) {
  const [open, setOpen] = useState<string | null>(null);
  const openStock = useStockDetail();
  const pct = metricLabel.includes("%");
  return (
    <div className="sig-table">
      <div className="scr-head">
        <span>Stock</span>
        <span>{showMetric ? metricLabel : "Net score"}</span>
        <span>Algos up ▲ / down ▼ (how much)</span>
        <span>Verdict</span>
      </div>
      {rows.map((r) => (
        <div key={r.symbol} className="sig-rowwrap">
          <div className="scr-row">
            <span className="sig-stock link" onClick={() => openStock(r.symbol)} title="Open full thesis">
              <b>{r.symbol}</b>
              <span className="sig-name">{r.name} · {r.sector} · {r.cap_class}</span>
            </span>
            <span className="metric" onClick={() => setOpen(open === r.symbol ? null : r.symbol)}>
              {showMetric
                ? `${r.metric_value >= 0 ? "+" : ""}${r.metric_value}${pct ? "%" : ""}`
                : `${r.net_score >= 0 ? "+" : ""}${r.net_score}`}
            </span>
            <span onClick={() => setOpen(open === r.symbol ? null : r.symbol)}><AlgoPills r={r} /></span>
            <span onClick={() => setOpen(open === r.symbol ? null : r.symbol)}>
              <em className={`verdict ${verdictClass(r.verdict)}`}>{r.verdict}</em>
              <span className="expand">{open === r.symbol ? "▾" : "▸"}</span>
            </span>
          </div>
          {open === r.symbol && <AlgoBreakdown symbol={r.symbol} />}
        </div>
      ))}
    </div>
  );
}

export default function Screeners() {
  const [dim, setDim] = useState<Dimension>("sector");
  const [topN, setTopN] = useState(10);
  const [flat, setFlat] = useState<ScreenerResult | null>(null);
  const [grouped, setGrouped] = useState<GroupedScreener | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const isGrouped = dim === "sector" || dim === "cap";

  useEffect(() => {
    setErr(null);
    setFlat(null);
    setGrouped(null);
    if (dim === "sector" || dim === "cap") {
      api.screenerGrouped(dim, topN).then(setGrouped).catch((e) => setErr(String(e)));
    } else {
      api.screener(dim, topN).then(setFlat).catch((e) => setErr(String(e)));
    }
  }, [dim, topN]);

  return (
    <section>
      <div className="screen-head">
        <div>
          <h2>Best Stocks — Screeners</h2>
          <p className="sub">
            {DIMS.find((d) => d.id === dim)?.blurb}. Each row shows which algos push it up ▲ / down ▼
            (and by how much). Click a stock name for its full thesis.
          </p>
        </div>
        <Controls
          topN={topN}
          onTopN={setTopN}
          topNOptions={isGrouped ? [3, 5, 10, 20] : [10, 20, 50, 100, 200]}
        />
      </div>

      <div className="sig-filters">
        <div className="control">
          <label>Dimension</label>
          <div className="segmented">
            {DIMS.map((d) => (
              <button key={d.id} className={d.id === dim ? "on" : ""} onClick={() => setDim(d.id)}>
                {d.label}
              </button>
            ))}
          </div>
        </div>
        {isGrouped && <div className="control"><label>&nbsp;</label><span className="hint">showing top {topN} per {dim === "sector" ? "sector" : "cap class"}</span></div>}
      </div>

      {err && <div className="error">Failed to load: {err}</div>}
      {!flat && !grouped && !err && <div className="algo-loading">Running algorithms…</div>}

      {/* Grouped: subsection per sector / cap class */}
      {grouped &&
        grouped.sections.map((s) => (
          <div className="grp" key={s.key}>
            <h3 className="grp-title">
              {s.label} <span className="grp-count">{s.count} stocks</span>
            </h3>
            <RowTable rows={s.rows} metricLabel={grouped.metric_label} showMetric={false} />
          </div>
        ))}

      {/* Flat: momentum / seasonal */}
      {flat && <RowTable rows={flat.rows} metricLabel={flat.metric_label} showMetric={true} />}
    </section>
  );
}
