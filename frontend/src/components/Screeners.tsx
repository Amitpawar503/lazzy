import { useEffect, useMemo, useState } from "react";
import {
  api,
  type Dimension,
  type ScreenerResult,
  type ScreenerRow,
} from "../api";
import Controls from "./Controls";
import AlgoBreakdown from "./AlgoBreakdown";

const DIMS: { id: Dimension; label: string; blurb: string }[] = [
  { id: "sector", label: "Sector-wise", blurb: "Best stocks within a sector by algo consensus" },
  { id: "cap", label: "Cap-wise", blurb: "Leaders by market-cap class" },
  { id: "momentum", label: "Momentum", blurb: "Ranked by 3-month price momentum" },
  { id: "seasonal", label: "Seasonal", blurb: "Strongest in the current calendar month" },
];
const CAPS = ["large", "mid", "small", "micro"];

function verdictClass(v: string) {
  if (v.includes("Strong Buy")) return "v-strong-buy";
  if (v === "Buy") return "v-buy";
  if (v.includes("Strong Sell")) return "v-strong-sell";
  if (v === "Sell") return "v-sell";
  return "v-neutral";
}

// Compact "which algos up / which down and how much" cell.
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

export default function Screeners() {
  const [dim, setDim] = useState<Dimension>("momentum");
  const [key, setKey] = useState<string | null>(null);
  const [topN, setTopN] = useState(20);
  const [sectors, setSectors] = useState<string[]>([]);
  const [data, setData] = useState<ScreenerResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    api.meta().then((m) => setSectors(m.sectors)).catch(() => setSectors([]));
  }, []);

  useEffect(() => {
    setErr(null);
    setData(null);
    api.screener(dim, topN, key).then(setData).catch((e) => setErr(String(e)));
  }, [dim, topN, key]);

  // reset key filter when switching to a dimension that doesn't use it
  useEffect(() => {
    setKey(null);
  }, [dim]);

  const keyOptions = useMemo(() => {
    if (dim === "sector") return sectors;
    if (dim === "cap") return CAPS;
    return [];
  }, [dim, sectors]);

  return (
    <section>
      <div className="screen-head">
        <div>
          <h2>Best Stocks — Screeners</h2>
          <p className="sub">
            {DIMS.find((d) => d.id === dim)?.blurb}. Each row shows which
            algorithms push it up vs down (and by how much). Click a row for the
            full breakdown.
          </p>
        </div>
        <Controls topN={topN} onTopN={setTopN} topNOptions={[10, 20, 50, 100, 200]} />
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
        {keyOptions.length > 0 && (
          <div className="control">
            <label>{dim === "sector" ? "Sector" : "Cap class"}</label>
            <select value={key ?? ""} onChange={(e) => setKey(e.target.value || null)}>
              <option value="">All</option>
              {keyOptions.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {err && <div className="error">Failed to load: {err}</div>}
      {!data && !err && <div className="algo-loading">Running algorithms…</div>}

      {data && (
        <div className="sig-table">
          <div className="scr-head">
            <span>Stock</span>
            <span>{data.metric_label}</span>
            <span>Algos up ▲ / down ▼ (how much)</span>
            <span>Verdict</span>
          </div>
          {data.rows.map((r) => (
            <div key={r.symbol} className="sig-rowwrap">
              <div className="scr-row" onClick={() => setOpen(open === r.symbol ? null : r.symbol)}>
                <span className="sig-stock">
                  <b>{r.symbol}</b>
                  <span className="sig-name">{r.name} · {r.sector} · {r.cap_class}</span>
                </span>
                <span className="metric">
                  {r.metric_value >= 0 && data.dimension !== "sector" && data.dimension !== "cap" ? "+" : ""}
                  {r.metric_value}
                  {data.metric_label.includes("%") ? "%" : ""}
                </span>
                <span><AlgoPills r={r} /></span>
                <span>
                  <em className={`verdict ${verdictClass(r.verdict)}`}>{r.verdict}</em>
                  <span className="expand">{open === r.symbol ? "▾" : "▸"}</span>
                </span>
              </div>
              {open === r.symbol && <AlgoBreakdown symbol={r.symbol} />}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
