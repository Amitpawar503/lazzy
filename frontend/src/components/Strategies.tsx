import { useEffect, useState } from "react";
import { api, type StrategyCard, type StrategyDetail } from "../api";
import { fmtPct } from "../color";
import { useStockDetail } from "./StockDetail";

function Spark({ a, b, w = 220, h = 54 }: { a: number[]; b: number[]; w?: number; h?: number }) {
  const all = [...a, ...b];
  if (all.length < 2) return <div style={{ height: h }} />;
  const min = Math.min(...all), max = Math.max(...all);
  const rng = max - min || 1;
  const path = (arr: number[]) =>
    arr.map((v, i) => `${(i / (arr.length - 1)) * w},${h - ((v - min) / rng) * h}`).join(" ");
  const up = a[a.length - 1] >= a[0];
  return (
    <svg width={w} height={h} className="spark">
      <polyline points={path(b)} fill="none" stroke="#4a5568" strokeWidth="1.2" strokeDasharray="3 3" />
      <polyline points={path(a)} fill="none" stroke={up ? "#4fb477" : "#d0645a"} strokeWidth="2" />
    </svg>
  );
}

function ret(v: number) {
  return <span className={v >= 0 ? "up" : "dn"}>{fmtPct(v)}</span>;
}

function Card({ s, onView }: { s: StrategyCard; onView: () => void }) {
  return (
    <div className="strat-card">
      <div className="strat-top">
        <span className={`cat cat-${s.category}`}>{s.category}</span>
        <span className="flag">{s.region === "IN" ? "🇮🇳" : "🌐"}</span>
        <button className="view-link" onClick={onView}>👁 View stocks</button>
      </div>
      <h3 className="strat-name">{s.name}</h3>
      <p className="strat-desc">{s.description}</p>
      {s.philosophy && <p className="strat-phil">🧠 {s.philosophy}</p>}
      <div className="strat-meta">
        <span>🕒 {s.period}</span><span>🔁 {s.rebalance}</span><span>{s.constituents_count} stocks</span>
      </div>
      <Spark a={s.spark} b={s.benchmark_spark} />
      <div className="strat-rets">
        <div className="strat-ret">
          <span className="k">Return (1Y)</span>
          <span className="v">{ret(s.ret_1y)}</span>
          <span className={`alpha ${s.beats_benchmark_1y ? "up" : "dn"}`}>
            {s.beats_benchmark_1y ? "beats" : "lags"} NIFTY {s.alpha_1y >= 0 ? "+" : ""}{s.alpha_1y}%
          </span>
        </div>
        <div className="strat-ret">
          <span className="k">Return (5Y)</span>
          <span className="v">{ret(s.ret_5y)}</span>
          <span className="alpha muted">vs {fmtPct(s.benchmark_ret_5y)}</span>
        </div>
      </div>
      <div className="strat-risk">
        <span title="Annualised volatility">Vol {s.volatility}%</span>
        <span title="Max drawdown">Max DD {s.max_drawdown}%</span>
        <span title="Sharpe ratio">Sharpe {s.sharpe}</span>
      </div>
    </div>
  );
}

function DetailModal({ id, onClose }: { id: string; onClose: () => void }) {
  const [d, setD] = useState<StrategyDetail | null>(null);
  const openStock = useStockDetail();
  useEffect(() => { api.strategy(id).then(setD).catch(() => setD(null)); }, [id]);
  return (
    <div className="modal-back" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-x" onClick={onClose}>✕</button>
        {!d && <div className="algo-loading">Loading…</div>}
        {d && (
          <>
            <h2>{d.name} <span className="sd-name">{d.constituents_count} stocks · {d.rebalance}</span></h2>
            <p className="strat-desc">{d.description}</p>
            {d.philosophy && <p className="strat-phil">🧠 How it picks: {d.philosophy}</p>}
            <div className="strat-rets" style={{ maxWidth: 520 }}>
              <div className="strat-ret"><span className="k">Return (1Y)</span><span className="v">{ret(d.ret_1y)}</span>
                <span className={`alpha ${d.beats_benchmark_1y ? "up" : "dn"}`}>α {d.alpha_1y >= 0 ? "+" : ""}{d.alpha_1y}%</span></div>
              <div className="strat-ret"><span className="k">Return (5Y)</span><span className="v">{ret(d.ret_5y)}</span>
                <span className="alpha muted">vs NIFTY {fmtPct(d.benchmark_ret_5y)}</span></div>
              <div className="strat-ret"><span className="k">Risk</span>
                <span className="v" style={{ fontSize: 14 }}>Vol {d.volatility}% · DD {d.max_drawdown}% · Sharpe {d.sharpe}</span></div>
            </div>
            <div className="sd-section">
              <h3>Constituents</h3>
              <div className="sig-table">
                <div className="scr-head" style={{ gridTemplateColumns: "2fr 1fr 3fr 1.2fr" }}>
                  <span>Stock</span><span>Net score</span><span>Algos up ▲ / down ▼</span><span>Verdict</span>
                </div>
                {d.constituents.map((r) => (
                  <div className="scr-row" key={r.symbol} style={{ gridTemplateColumns: "2fr 1fr 3fr 1.2fr" }}>
                    <span className="sig-stock link" onClick={() => openStock(r.symbol)}>
                      <b>{r.symbol}</b><span className="sig-name">{r.name} · {r.sector} · {r.cap_class}</span>
                    </span>
                    <span className="metric">{r.net_score >= 0 ? "+" : ""}{r.net_score}</span>
                    <span className="pills">
                      <div className="pill-row up">{r.up_algos.slice(0, 5).map((a) => <span key={a.algo} className="pill up">▲ {a.algo.split(" ")[0]} {a.strength_pct}%</span>)}</div>
                      <div className="pill-row dn">{r.down_algos.slice(0, 5).map((a) => <span key={a.algo} className="pill dn">▼ {a.algo.split(" ")[0]} {a.strength_pct}%</span>)}</div>
                    </span>
                    <span><em className={`verdict ${d ? "" : ""}`}>{r.verdict}</em></span>
                  </div>
                ))}
              </div>
            </div>
            <p className="src-note">Backtest on cached history · illustrative · not investment advice.</p>
          </>
        )}
      </div>
    </div>
  );
}

const CATS = ["all", "style", "sector", "cap", "theme"] as const;
type Cat = (typeof CATS)[number];

export default function Strategies() {
  const [cards, setCards] = useState<StrategyCard[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [cat, setCat] = useState<Cat>("all");
  const [sel, setSel] = useState<string | null>(null);

  useEffect(() => {
    api.strategies().then((d) => setCards(d.strategies)).catch((e) => setErr(String(e)));
  }, []);

  const shown = (cards || []).filter((c) => cat === "all" || c.category === cat);

  return (
    <section>
      <div className="screen-head">
        <div>
          <h2>Ideas — AI Strategy Baskets</h2>
          <p className="sub">
            Curated baskets (sector / cap / theme), each backtested vs a NIFTY-style benchmark
            with risk. Only adopt one if it <b>beats the benchmark</b> at acceptable risk.
          </p>
        </div>
        <div className="control">
          <label>Category</label>
          <div className="segmented">
            {CATS.map((c) => (
              <button key={c} className={c === cat ? "on" : ""} onClick={() => setCat(c)}>{c}</button>
            ))}
          </div>
        </div>
      </div>

      {err && <div className="error">Failed to load: {err}</div>}
      {!cards && !err && <div className="algo-loading">Backtesting strategies…</div>}

      <div className="strat-grid">
        {shown.map((s) => <Card key={s.id} s={s} onView={() => setSel(s.id)} />)}
      </div>

      {sel && <DetailModal id={sel} onClose={() => setSel(null)} />}
    </section>
  );
}
