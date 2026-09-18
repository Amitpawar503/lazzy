import { useEffect, useState } from "react";
import { api, type SectorHeatmap as SH, type Timeframe } from "../api";
import { returnColor, fmtPct, fmtCr } from "../color";
import Controls from "./Controls";

export default function SectorHeatmap() {
  const [tf, setTf] = useState<Timeframe>("1d");
  const [data, setData] = useState<SH | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setErr(null);
    api.sectorHeatmap(tf).then(setData).catch((e) => setErr(String(e)));
  }, [tf]);

  const maxAbs = data
    ? Math.max(Math.abs(data.min_return), Math.abs(data.max_return))
    : 1;

  return (
    <section>
      <div className="screen-head">
        <div>
          <h2>Sector Heatmap</h2>
          <p className="sub">Market-cap-weighted {tf} return per sector</p>
        </div>
        <Controls timeframe={tf} onTimeframe={setTf} />
      </div>

      {err && <div className="error">Failed to load: {err}</div>}

      <div className="sector-grid">
        {data?.sectors.map((s) => (
          <div
            key={s.sector}
            className="sector-card"
            style={{ background: returnColor(s.return_pct, maxAbs) }}
          >
            <div className="sector-top">
              <span className="sname">{s.sector}</span>
              <span className="sret">{fmtPct(s.return_pct)}</span>
            </div>
            <div className="sector-meta">
              <span>{s.constituents} stocks · {fmtCr(s.market_cap_cr)}</span>
            </div>
            <div className="sector-movers">
              <span className="up">▲ {s.top_gainer}</span>
              <span className="down">▼ {s.top_loser}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
