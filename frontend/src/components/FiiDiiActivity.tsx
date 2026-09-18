import { useEffect, useState } from "react";
import {
  api,
  type FlowSummary,
  type InstitutionalActivity,
  type HoldingChange,
} from "../api";
import { fmtPct } from "../color";
import Controls from "./Controls";

function crColor(v: number) {
  return v >= 0 ? "#4fb477" : "#d0645a";
}

function FlowBars({ flows }: { flows: FlowSummary }) {
  const all = flows.series.flatMap((p) => [p.fii_net, p.dii_net]);
  const max = Math.max(1, ...all.map(Math.abs));
  return (
    <div className="flows">
      <div className="flow-legend">
        <span><i style={{ background: "#5b8def" }} /> FII net</span>
        <span><i style={{ background: "#e0a458" }} /> DII net</span>
      </div>
      <div className="flow-chart">
        {flows.series.map((p) => (
          <div className="flow-day" key={p.date} title={p.date}>
            <div className="flow-pair">
              <div
                className="bar fii"
                style={{ height: `${(Math.abs(p.fii_net) / max) * 100}%`, opacity: p.fii_net >= 0 ? 1 : 0.55 }}
              />
              <div
                className="bar dii"
                style={{ height: `${(Math.abs(p.dii_net) / max) * 100}%`, opacity: p.dii_net >= 0 ? 1 : 0.55 }}
              />
            </div>
            <span className="flow-date">{p.date.slice(5)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ActivityTable({ title, rows, positive }: { title: string; rows: HoldingChange[]; positive: boolean }) {
  return (
    <div className="act-table">
      <h3 className={positive ? "added" : "removed"}>
        {positive ? "▲ Added by institutions" : "▼ Trimmed by institutions"}
        <span className="act-caption">{title}</span>
      </h3>
      <table>
        <thead>
          <tr><th>Stock</th><th>Sector</th><th>FII Δ</th><th>DII Δ</th><th>Net Δ</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.symbol}>
              <td><b>{r.symbol}</b><span className="rname">{r.name}</span></td>
              <td>{r.sector}</td>
              <td style={{ color: crColor(r.fii_delta_pct) }}>{fmtPct(r.fii_delta_pct)}</td>
              <td style={{ color: crColor(r.dii_delta_pct) }}>{fmtPct(r.dii_delta_pct)}</td>
              <td style={{ color: crColor(r.combined_delta_pct) }}><b>{fmtPct(r.combined_delta_pct)}</b></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function FiiDiiActivity() {
  const [topN, setTopN] = useState(10);
  const [flows, setFlows] = useState<FlowSummary | null>(null);
  const [act, setAct] = useState<InstitutionalActivity | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.flows().then(setFlows).catch((e) => setErr(String(e)));
  }, []);
  useEffect(() => {
    api.activity(topN).then(setAct).catch((e) => setErr(String(e)));
  }, [topN]);

  return (
    <section>
      <div className="screen-head">
        <div>
          <h2>FII / DII &amp; Investor Activity</h2>
          <p className="sub">Net institutional cash flows and stocks being added / removed</p>
        </div>
        <Controls topN={topN} onTopN={setTopN} topNOptions={[5, 10, 20, 50]} />
      </div>

      {err && <div className="error">Failed to load: {err}</div>}

      {flows && (
        <div className="flow-cards">
          <div className="stat">
            <span className="k">Latest FII net</span>
            <span className="v" style={{ color: crColor(flows.latest.fii_net) }}>
              ₹{flows.latest.fii_net.toLocaleString("en-IN")} cr
            </span>
            <span className="d">{flows.latest.date}</span>
          </div>
          <div className="stat">
            <span className="k">Latest DII net</span>
            <span className="v" style={{ color: crColor(flows.latest.dii_net) }}>
              ₹{flows.latest.dii_net.toLocaleString("en-IN")} cr
            </span>
            <span className="d">{flows.latest.date}</span>
          </div>
          <div className="stat">
            <span className="k">FII cumulative (10d)</span>
            <span className="v" style={{ color: crColor(flows.fii_cumulative) }}>
              ₹{flows.fii_cumulative.toLocaleString("en-IN")} cr
            </span>
          </div>
          <div className="stat">
            <span className="k">DII cumulative (10d)</span>
            <span className="v" style={{ color: crColor(flows.dii_cumulative) }}>
              ₹{flows.dii_cumulative.toLocaleString("en-IN")} cr
            </span>
          </div>
        </div>
      )}

      {flows && <FlowBars flows={flows} />}

      {act && (
        <div className="act-grid">
          <ActivityTable title={`top ${topN}`} rows={act.added} positive />
          <ActivityTable title={`top ${topN}`} rows={act.removed} positive={false} />
        </div>
      )}
    </section>
  );
}
