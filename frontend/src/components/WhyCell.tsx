import { useRef, useState } from "react";
import { api, type Reasoning } from "../api";

// Hover cell: shows bull / bear reasoning + news impact for a stock.
export default function WhyCell({ symbol }: { symbol: string }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<Reasoning | null>(null);
  const [pos, setPos] = useState<{ top: number; left: number }>({ top: 0, left: 0 });
  const cache = useRef<Reasoning | null>(null);

  const enter = (e: React.MouseEvent) => {
    const r = (e.currentTarget as HTMLElement).getBoundingClientRect();
    // place popover to the left of the trigger, escaping table overflow via fixed
    setPos({ top: Math.min(r.top, window.innerHeight - 320), left: Math.max(12, r.left - 340) });
    setOpen(true);
    if (cache.current) return;
    api.reasoning(symbol).then((d) => { cache.current = d; setData(d); }).catch(() => {});
  };

  const d = data || cache.current;
  return (
    <span className="why" onMouseEnter={enter} onMouseLeave={() => setOpen(false)}
          onClick={(e) => e.stopPropagation()}>
      <span className="why-trigger">ⓘ why</span>
      {open && (
        <div className="why-pop" style={{ top: pos.top, left: pos.left }}>
          {!d && <div className="algo-loading">Loading…</div>}
          {d && (
            <>
              <div className="why-head">
                {d.symbol} · <b>{d.verdict}</b> · net {d.net_score >= 0 ? "+" : ""}{d.net_score}
              </div>
              {d.bull.length > 0 && (
                <div className="why-sec">
                  <span className="why-lbl up">▲ Bullish</span>
                  {d.bull.map((b, i) => (
                    <div className="why-item" key={i}><b>{b.point}</b> — {b.detail}</div>
                  ))}
                </div>
              )}
              {d.bear.length > 0 && (
                <div className="why-sec">
                  <span className="why-lbl dn">▼ Bearish</span>
                  {d.bear.map((b, i) => (
                    <div className="why-item" key={i}><b>{b.point}</b> — {b.detail}</div>
                  ))}
                </div>
              )}
              {d.impact.length > 0 && (
                <div className="why-sec">
                  <span className="why-lbl news">◆ News impact</span>
                  {d.impact.map((n, i) => (
                    <div className="why-item" key={i}>
                      {n.title} <span style={{ color: n.short_term >= 0 ? "#6fd39a" : "#e59089" }}>
                        (ST {n.short_term >= 0 ? "+" : ""}{n.short_term}, LT {n.long_term >= 0 ? "+" : ""}{n.long_term})
                      </span>
                    </div>
                  ))}
                </div>
              )}
              {d.news.length > 0 && (
                <div className="why-sec">
                  <span className="why-lbl news">◆ Headlines</span>
                  {d.news.map((h, i) => <div className="why-item" key={i}>{h}</div>)}
                </div>
              )}
              {d.impact.length === 0 && d.news.length === 0 && (
                <div className="why-item muted">No recent news impact.</div>
              )}
            </>
          )}
        </div>
      )}
    </span>
  );
}
