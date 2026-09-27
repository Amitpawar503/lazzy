import { useEffect, useState } from "react";
import { api, type GovtRadar as GR } from "../api";
import { useStockDetail } from "./StockDetail";

type View = "picks" | "policy" | "holdings" | "institutions" | "superstars";
const VIEWS: { id: View; label: string }[] = [
  { id: "picks", label: "Can Rise (Policy + Ownership)" },
  { id: "policy", label: "Policy by Sector" },
  { id: "holdings", label: "Govt Buying / Selling" },
  { id: "institutions", label: "Institutions & FIIs" },
  { id: "superstars", label: "Superstar Investors" },
];

function fmtCr(cr: number) {
  return cr >= 100000 ? `₹${(cr / 100000).toFixed(1)}L cr`
    : cr >= 1000 ? `₹${(cr / 1000).toFixed(1)}k cr` : `₹${cr} cr`;
}

function stanceCls(s: string) {
  const v = s.toLowerCase();
  if (v.includes("tailwind") || v === "accumulating") return "st-pos";
  if (v.includes("headwind") || v === "divesting") return "st-neg";
  return "st-neu";
}
function actionCls(a: string) {
  return a === "add" ? "st-pos" : a === "reduce" ? "st-neg" : "st-neu";
}

export default function GovtRadar() {
  const [data, setData] = useState<GR | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [view, setView] = useState<View>("picks");
  const openStock = useStockDetail();

  useEffect(() => {
    api.govtRadar().then(setData).catch((e) => setErr(String(e)));
  }, []);

  return (
    <section>
      <div className="screen-head">
        <div>
          <h2>Govt &amp; Institutions Radar</h2>
          <p className="sub">
            Where the <b>Government of India</b> and big institutions (LIC, EPFO,
            SUUTI, SBI MF) are <b>buying vs selling</b>, which sectors get
            favourable <b>policy</b>, and which stocks can <b>rise on govt
            decisions</b>.
          </p>
        </div>
        <div className="seg">
          {VIEWS.map((v) => (
            <button key={v.id} className={`seg-btn ${v.id === view ? "on" : ""}`}
              onClick={() => setView(v.id)}>{v.label}</button>
          ))}
        </div>
      </div>

      {err && <div className="error">Failed to load: {err}</div>}
      {!data && !err && <div className="algo-loading">Loading radar…</div>}

      {data && view === "picks" && (
        <div className="gr-cards">
          {data.picks.map((p) => (
            <div className="gr-card" key={p.symbol}>
              <div className="gr-card-head">
                <span className="link" onClick={() => openStock(p.symbol)}>
                  <b>{p.symbol}</b> <span className="sig-name">{p.name}</span>
                </span>
                <span className={`gr-badge ${stanceCls(p.verdict)}`}>{p.verdict}</span>
              </div>
              <div className="gr-score">
                <div className="gr-score-bar">
                  <i style={{ width: `${Math.max(4, Math.min(100, p.score))}%` }} />
                </div>
                <span>{p.score >= 0 ? "+" : ""}{p.score}</span>
              </div>
              <div className="gr-sector">{p.sector}</div>
              <ul className="gr-reasons">
                {p.reasons.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          ))}
        </div>
      )}

      {data && view === "policy" && (
        <div className="gr-list">
          {data.policy_sectors.map((p) => (
            <div className="gr-policy" key={p.sector}>
              <div className="gr-policy-top">
                <b>{p.sector}</b>
                <span className={`gr-badge ${stanceCls(p.stance)}`}>{p.stance}</span>
                <span className="gr-meter"><i style={{ width: `${p.score}%` }} /></span>
                <span className="gr-score-n">{p.score}</span>
              </div>
              <div className="gr-policy-txt">{p.policy}</div>
              <div className="gr-benef">
                {p.beneficiaries.map((s) => (
                  <button key={s} className="chip link" onClick={() => openStock(s)}>{s}</button>
                ))}
              </div>
              <div className="gr-note">{p.note}</div>
            </div>
          ))}
        </div>
      )}

      {data && view === "holdings" && (
        <div className="gr-table">
          <div className="gr-th">
            <span>Company</span><span>Sector</span><span>Holder</span>
            <span>Stake %</span><span>Direction</span><span>Recent action</span>
          </div>
          {data.govt_holdings.map((h) => (
            <div className="gr-tr" key={h.symbol}>
              <span className="link" onClick={() => openStock(h.symbol)}>
                <b>{h.symbol}</b> <span className="sig-name">{h.name}</span>
              </span>
              <span>{h.sector}</span>
              <span>{h.holder}</span>
              <span className="num">{h.holding_pct}%</span>
              <span className={`gr-badge ${stanceCls(h.stance)}`}>{h.stance}</span>
              <span className="gr-action">{h.action}</span>
            </div>
          ))}
        </div>
      )}

      {data && view === "institutions" && (
        <div className="gr-inst-grid">
          {data.institutions.map((inst) => (
            <div className="gr-inst" key={inst.name}>
              <h3>
                {inst.name} <span className="sig-name">{inst.type}</span>
                {inst.category && <span className={`gr-cat cat-${inst.category.toLowerCase()}`}>{inst.category}</span>}
              </h3>
              <p className="gr-note">{inst.note}</p>
              {inst.holdings.map((h) => (
                <div className="gr-inst-row" key={h.symbol}>
                  <span className="link" onClick={() => openStock(h.symbol)}>
                    <b>{h.symbol}</b> <span className="sig-name">{h.name}</span>
                  </span>
                  <span className={`gr-badge ${actionCls(h.action)}`}>{h.action}</span>
                  <span className="gr-action">{h.detail}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {data && view === "superstars" && (
        <div className="gr-inst-grid">
          {data.superstars.map((s) => (
            <div className="gr-inst" key={s.name}>
              <h3>{s.name} <span className="gr-cat cat-star">{fmtCr(s.portfolio_cr)}</span></h3>
              <p className="gr-note">{s.style}</p>
              {s.holdings.map((h) => (
                <div className="gr-inst-row" key={h.symbol}>
                  <span className="link" onClick={() => openStock(h.symbol)}>
                    <b>{h.symbol}</b> <span className="sig-name">{h.name}</span>
                  </span>
                  <span className="gr-badge st-pos">holds</span>
                  <span className="gr-action">{h.detail}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      <p className="src-note">
        {data?.live ? "Live investor portfolios overlaid from Moneycontrol where reachable; " : ""}
        Holdings/policy are curated & indicative (public disclosures move with each
        filing/announcement) — not investment advice. Click any stock for its full thesis.
      </p>
    </section>
  );
}
