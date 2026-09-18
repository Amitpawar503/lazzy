import { useEffect, useMemo, useRef, useState } from "react";
import { api, type Heatmap360 as H360, type Timeframe } from "../api";
import { returnColor, fmtPct, fmtCr } from "../color";
import { squarify } from "../treemap";
import Controls from "./Controls";

const HEIGHT = 560;

export default function Heatmap360() {
  const [tf, setTf] = useState<Timeframe>("1d");
  const [topN, setTopN] = useState(50);
  const [data, setData] = useState<H360 | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const wrap = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(900);

  useEffect(() => {
    setErr(null);
    api.market360(tf, topN).then(setData).catch((e) => setErr(String(e)));
  }, [tf, topN]);

  useEffect(() => {
    if (!wrap.current) return;
    const ro = new ResizeObserver((entries) => {
      for (const e of entries) setWidth(e.contentRect.width);
    });
    ro.observe(wrap.current);
    return () => ro.disconnect();
  }, []);

  const placed = useMemo(() => {
    if (!data) return [];
    const items = data.tiles.map((t) => ({ item: t, value: t.market_cap_cr }));
    return squarify(items, width, HEIGHT);
  }, [data, width]);

  const maxAbs = data
    ? Math.max(Math.abs(data.min_return), Math.abs(data.max_return))
    : 1;

  return (
    <section>
      <div className="screen-head">
        <div>
          <h2>360° Market View</h2>
          <p className="sub">
            Box size = market cap · colour = {tf} return
            {data ? ` · ${data.count} stocks` : ""}
          </p>
        </div>
        <Controls
          timeframe={tf}
          onTimeframe={setTf}
          topN={topN}
          onTopN={setTopN}
        />
      </div>

      {err && <div className="error">Failed to load: {err}</div>}

      <div className="treemap" ref={wrap} style={{ height: HEIGHT }}>
        {placed.map((p) => {
          const t = p.item;
          const big = p.w > 64 && p.h > 34;
          return (
            <div
              key={t.symbol}
              className="tile"
              title={`${t.name} · ${fmtCr(t.market_cap_cr)} · ${fmtPct(
                t.return_pct
              )}`}
              style={{
                left: p.x,
                top: p.y,
                width: Math.max(p.w - 2, 0),
                height: Math.max(p.h - 2, 0),
                background: returnColor(t.return_pct, maxAbs),
              }}
            >
              {big && (
                <>
                  <span className="tsym">{t.symbol}</span>
                  <span className="tret">{fmtPct(t.return_pct)}</span>
                </>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
