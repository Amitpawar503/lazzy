import { useRef, useState } from "react";
import { api, type Factor, type Reasoning } from "../api";

function Group({ title, cls, items }: { title: string; cls: string; items: Factor[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="why-sec">
      <span className={`why-lbl ${cls}`}>{title}</span>
      {items.map((it, i) => (
        <div className="why-item" key={i}>
          <b>{it.label}</b> — {it.detail}
        </div>
      ))}
    </div>
  );
}

// Rich hover reasoning: SWOT + corporate actions + orders + management + news.
export default function WhyCell({ symbol }: { symbol: string }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<Reasoning | null>(null);
  const [pos, setPos] = useState<{ top: number; left: number }>({ top: 0, left: 0 });
  const cache = useRef<Reasoning | null>(null);

  const enter = (e: React.MouseEvent) => {
    const r = (e.currentTarget as HTMLElement).getBoundingClientRect();
    setPos({ top: Math.min(r.top, window.innerHeight - 380), left: Math.max(12, r.left - 380) });
    setOpen(true);
    if (cache.current) return;
    api.reasoning(symbol).then((d) => { cache.current = d; setData(d); }).catch(() => {});
  };

  const d = data || cache.current;
  const f = d?.factors;
  return (
    <span className="why" onMouseEnter={enter} onMouseLeave={() => setOpen(false)}
          onClick={(e) => e.stopPropagation()}>
      <span className="why-trigger">ⓘ why</span>
      {open && (
        <div className="why-pop" style={{ top: pos.top, left: pos.left }}>
          {!d && <div className="algo-loading">Loading…</div>}
          {d && f && (
            <>
              <div className="why-head">{d.symbol} · <b>{d.verdict}</b> · net {d.net_score >= 0 ? "+" : ""}{d.net_score}</div>
              <Group title="✦ Strengths" cls="up" items={f.strengths} />
              <Group title="⚠ Weaknesses" cls="dn" items={f.weaknesses} />
              <Group title="◇ Opportunities" cls="op" items={f.opportunities} />
              <Group title="⚑ Threats" cls="dn" items={f.threats} />
              <Group title="₹ Corporate actions" cls="news" items={f.corporate_actions} />
              <Group title="📦 Order wins" cls="up" items={f.orders} />
              <Group title="👤 Management" cls="news" items={f.management} />
              {d.impact.length > 0 && (
                <div className="why-sec">
                  <span className="why-lbl news">◆ News impact</span>
                  {d.impact.map((n, i) => (
                    <div className="why-item" key={i}>
                      {n.title}{" "}
                      <span style={{ color: n.short_term >= 0 ? "#6fd39a" : "#e59089" }}>
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
            </>
          )}
        </div>
      )}
    </span>
  );
}
