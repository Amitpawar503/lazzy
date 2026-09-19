import { useEffect, useState } from "react";
import { api, type StyleRow, type StyleSection, type StyleSections } from "../api";
import { fmtPct } from "../color";
import { useStockDetail } from "./StockDetail";
import WhyCell from "./WhyCell";

function verdictClass(v: string) {
  if (v.includes("Strong Buy")) return "v-strong-buy";
  if (v === "Buy") return "v-buy";
  if (v.includes("Strong Sell")) return "v-strong-sell";
  if (v === "Sell") return "v-sell";
  return "v-neutral";
}

function Spark({ a, b, w = 150, h = 34 }: { a: number[]; b: number[]; w?: number; h?: number }) {
  const all = [...a, ...b];
  if (all.length < 2) return null;
  const min = Math.min(...all), max = Math.max(...all), rng = max - min || 1;
  const path = (arr: number[]) => arr.map((v, i) => `${(i / (arr.length - 1)) * w},${h - ((v - min) / rng) * h}`).join(" ");
  const up = a[a.length - 1] >= a[0];
  return (
    <svg width={w} height={h} className="spark">
      <polyline points={path(b)} fill="none" stroke="#4a5568" strokeWidth="1" strokeDasharray="3 3" />
      <polyline points={path(a)} fill="none" stroke={up ? "#4fb477" : "#d0645a"} strokeWidth="1.8" />
    </svg>
  );
}

// stacked favour/neutral/against bar + counts
function Consensus({ r }: { r: StyleRow }) {
  const c = r.consensus;
  const t = c.total || 1;
  return (
    <div className="cons">
      <div className="cons-bar" title={`${c.favour} favour · ${c.neutral} neutral · ${c.against} against (of ${t} styles)`}>
        <span style={{ width: `${(c.favour / t) * 100}%` }} className="cb fav" />
        <span style={{ width: `${(c.neutral / t) * 100}%` }} className="cb neu" />
        <span style={{ width: `${(c.against / t) * 100}%` }} className="cb agn" />
      </div>
      <div className="cons-nums">
        <span className="fav">{c.favour}👍</span>
        <span className="neu">{c.neutral}•</span>
        <span className="agn">{c.against}👎</span>
      </div>
    </div>
  );
}

function Pills({ r }: { r: StyleRow }) {
  return (
    <div className="pills">
      <div className="pill-row up">
        {r.up_algos.slice(0, 5).map((a) => <span key={a.algo} className="pill up">▲ {a.algo.split(" ")[0]} {a.strength_pct}%</span>)}
        {r.up_algos.length === 0 && <span className="pill-none">—</span>}
      </div>
      <div className="pill-row dn">
        {r.down_algos.slice(0, 5).map((a) => <span key={a.algo} className="pill dn">▼ {a.algo.split(" ")[0]} {a.strength_pct}%</span>)}
        {r.down_algos.length === 0 && <span className="pill-none">—</span>}
      </div>
    </div>
  );
}

function Section({ s }: { s: StyleSection }) {
  const openStock = useStockDetail();
  const [open, setOpen] = useState(true);
  return (
    <div className="stp-section">
      <div className="stp-head" onClick={() => setOpen(!open)}>
        <div>
          <h3>{s.label} <span className="grp-count">{s.count} stocks</span></h3>
          <div className="stp-metrics">
            <span>1Y <b className={s.ret_1y >= 0 ? "up" : "dn"}>{fmtPct(s.ret_1y)}</b></span>
            <span>5Y <b className={s.ret_5y >= 0 ? "up" : "dn"}>{fmtPct(s.ret_5y)}</b></span>
            <span className={`alpha ${s.beats_benchmark_1y ? "up" : "dn"}`}>{s.beats_benchmark_1y ? "beats" : "lags"} NIFTY {s.alpha_1y >= 0 ? "+" : ""}{s.alpha_1y}%</span>
            <span className="muted">Vol {s.volatility}% · DD {s.max_drawdown}% · Sharpe {s.sharpe}</span>
          </div>
        </div>
        <Spark a={s.spark} b={s.benchmark_spark} />
      </div>
      {open && (
        <div className="sig-table">
          <div className="stp-row stp-head-row">
            <span>Stock</span><span>{s.metric_label}</span><span>Algos ▲ / ▼</span>
            <span>Verdict</span><span>Styles 👍 / • / 👎</span><span>Why</span>
          </div>
          {s.rows.map((r) => (
            <div className="stp-row" key={r.symbol}>
              <span className="sig-stock link" onClick={() => openStock(r.symbol)}>
                <b>{r.symbol}</b><span className="sig-name">{r.name} · {r.sector} · {r.cap_class}</span>
              </span>
              <span className="metric">{r.metric_value}</span>
              <span><Pills r={r} /></span>
              <span><em className={`verdict ${verdictClass(r.verdict)}`}>{r.verdict}</em></span>
              <span><Consensus r={r} /></span>
              <span><WhyCell symbol={r.symbol} /></span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function StylePicks() {
  const [data, setData] = useState<StyleSections | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [active, setActive] = useState<string>("large");

  useEffect(() => {
    api.styleSections().then(setData).catch((e) => setErr(String(e)));
  }, []);

  const sec = data?.sections.find((s) => s.key === active);

  return (
    <section>
      <div className="screen-head">
        <div>
          <h2>Style Picks — 6 Sections</h2>
          <p className="sub">
            Best ~30 stocks per bucket by investor-style consensus. The last column shows how many
            of the investor styles are <span className="up">in favour</span> / neutral /{" "}
            <span className="dn">against</span> each stock.
          </p>
        </div>
      </div>

      {err && <div className="error">Failed to load: {err}</div>}
      {!data && !err && <div className="algo-loading">Scoring styles across the universe…</div>}

      {data && (
        <>
          <div className="sig-filters">
            <div className="control">
              <label>Section</label>
              <div className="segmented">
                {data.sections.map((s) => (
                  <button key={s.key} className={s.key === active ? "on" : ""} onClick={() => setActive(s.key)}>
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
          {sec && <Section s={sec} />}
        </>
      )}
    </section>
  );
}
