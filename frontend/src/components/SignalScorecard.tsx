import { useEffect, useState } from "react";
import {
  api,
  type Scorecard,
  type ScorecardRow,
  type SignalSort,
  type SignalView,
} from "../api";
import Controls from "./Controls";
import AlgoBreakdown from "./AlgoBreakdown";
import { useStockDetail } from "./StockDetail";

function verdictClass(v: string) {
  if (v.includes("Strong Buy")) return "v-strong-buy";
  if (v === "Buy") return "v-buy";
  if (v.includes("Strong Sell")) return "v-strong-sell";
  if (v === "Sell") return "v-sell";
  return "v-neutral";
}

// Diverging bar for net score in -100..+100.
function ScoreBar({ score }: { score: number }) {
  const pct = Math.min(100, Math.abs(score));
  const pos = score >= 0;
  return (
    <div className="scorebar" title={`${score >= 0 ? "+" : ""}${score}`}>
      <div className="sb-track">
        <div className="sb-zero" />
        <div
          className={`sb-fill ${pos ? "pos" : "neg"}`}
          style={{ width: `${pct / 2}%`, [pos ? "left" : "right"]: "50%" } as any}
        />
      </div>
      <span className={`sb-num ${pos ? "pos" : "neg"}`}>
        {score >= 0 ? "+" : ""}
        {score}
      </span>
    </div>
  );
}

function Counts({ r }: { r: ScorecardRow }) {
  return (
    <div className="counts">
      <span className="c-up">{r.bullish}▲</span>
      <span className="c-dn">{r.bearish}▼</span>
      <span className="c-nu">{r.neutral}•</span>
      <span className="c-total">/ {r.total_algos}</span>
    </div>
  );
}

export default function SignalScorecard() {
  const [topN, setTopN] = useState(20);
  const [view, setView] = useState<SignalView>("all");
  const [sort, setSort] = useState<SignalSort>("score");
  const [data, setData] = useState<Scorecard | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const openStock = useStockDetail();

  useEffect(() => {
    setErr(null);
    api.scorecard(topN, view, sort).then(setData).catch((e) => setErr(String(e)));
  }, [topN, view, sort]);

  return (
    <section>
      <div className="screen-head">
        <div>
          <h2>Algo Signal Consensus</h2>
          <p className="sub">
            {data ? data.algos.length : 10} algorithms vote per stock — how many
            turn positive vs negative, and the net conviction. Click a row for the
            per-algorithm breakdown.
          </p>
        </div>
        <Controls topN={topN} onTopN={setTopN} topNOptions={[10, 20, 50, 100, 200]} />
      </div>

      <div className="sig-filters">
        <div className="control">
          <label>Show</label>
          <div className="segmented">
            {(["all", "bullish", "bearish"] as SignalView[]).map((v) => (
              <button key={v} className={v === view ? "on" : ""} onClick={() => setView(v)}>
                {v}
              </button>
            ))}
          </div>
        </div>
        <div className="control">
          <label>Sort by</label>
          <div className="segmented">
            {(["score", "bullish", "bearish"] as SignalSort[]).map((s) => (
              <button key={s} className={s === sort ? "on" : ""} onClick={() => setSort(s)}>
                {s === "score" ? "net score" : `# ${s}`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {err && <div className="error">Failed to load: {err}</div>}

      <div className="sig-table">
        <div className="sig-head">
          <span>Stock</span>
          <span>Algos +ve / −ve / •</span>
          <span>Net conviction</span>
          <span>Verdict</span>
        </div>
        {data?.rows.map((r) => (
          <div key={r.symbol} className="sig-rowwrap">
            <div className="sig-row">
              <span className="sig-stock link" onClick={() => openStock(r.symbol)} title="Open full thesis">
                <b>{r.symbol}</b>
                <span className="sig-name">
                  {r.name} · {r.sector} · {r.cap_class}
                </span>
              </span>
              <span onClick={() => setOpen(open === r.symbol ? null : r.symbol)}><Counts r={r} /></span>
              <span onClick={() => setOpen(open === r.symbol ? null : r.symbol)}><ScoreBar score={r.net_score} /></span>
              <span onClick={() => setOpen(open === r.symbol ? null : r.symbol)}>
                <em className={`verdict ${verdictClass(r.verdict)}`}>{r.verdict}</em>
                <span className="expand">{open === r.symbol ? "▾" : "▸"}</span>
              </span>
            </div>
            {open === r.symbol && <AlgoBreakdown symbol={r.symbol} />}
          </div>
        ))}
      </div>
    </section>
  );
}
