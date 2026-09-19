import { useEffect, useMemo, useState } from "react";
import { api, type EventList, type ImpactedStock, type MarketEvent } from "../api";

function dirColor(v: number) {
  return v > 2 ? "#4fb477" : v < -2 ? "#d0645a" : "var(--muted)";
}

// small centered diverging bar in -100..100
function ImpactBar({ v }: { v: number }) {
  const pct = Math.min(100, Math.abs(v));
  const pos = v >= 0;
  return (
    <div className="scorebar">
      <div className="sb-track">
        <div className="sb-zero" />
        <div
          className={`sb-fill ${pos ? "pos" : "neg"}`}
          style={{ width: `${pct / 2}%`, [pos ? "left" : "right"]: "50%" } as any}
        />
      </div>
      <span className="sb-num" style={{ color: dirColor(v) }}>
        {v >= 0 ? "+" : ""}{v}
      </span>
    </div>
  );
}

function ImpactRow({ im }: { im: ImpactedStock }) {
  return (
    <div className="imp-row">
      <span className="imp-stock">
        <b>{im.symbol}</b>
        <span className="sig-name">{im.name}</span>
      </span>
      <span className={`rel rel-${im.relation}`}>{im.relation}</span>
      <span className="imp-bar"><ImpactBar v={im.short_term} /></span>
      <span className="imp-bar"><ImpactBar v={im.long_term} /></span>
      <span className="imp-why">{im.rationale}</span>
    </div>
  );
}

export default function NewsImpact() {
  const [data, setData] = useState<EventList | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [selId, setSelId] = useState<string | null>(null);

  useEffect(() => {
    api.events().then((d) => {
      setData(d);
      setSelId(d.events[0]?.id ?? null);
    }).catch((e) => setErr(String(e)));
  }, []);

  const sel: MarketEvent | undefined = useMemo(
    () => data?.events.find((e) => e.id === selId),
    [data, selId]
  );

  return (
    <section>
      <div className="screen-head">
        <div>
          <h2>News Impact — Event Fan-out</h2>
          <p className="sub">
            Pick an event to see which companies are affected, the short- vs
            long-term impact, and which are <em>not</em> materially impacted.
          </p>
        </div>
      </div>

      {err && <div className="error">Failed to load: {err}</div>}

      <div className="impact-layout">
        <aside className="event-list">
          {data?.events.map((e) => (
            <button
              key={e.id}
              className={`event-item ${e.id === selId ? "on" : ""}`}
              onClick={() => setSelId(e.id)}
            >
              <span className={`kind kind-${e.kind}`}>{e.kind}</span>
              <span className="event-title">{e.title}</span>
              <span className="event-meta">{e.entity} · {e.date}</span>
            </button>
          ))}
        </aside>

        <div className="event-detail">
          {sel && (
            <>
              <h3>{sel.title}</h3>
              <p className="event-summary">{sel.summary}</p>
              <div className="imp-head">
                <span>Company</span>
                <span>Relation</span>
                <span>Short term</span>
                <span>Long term</span>
                <span>Why</span>
              </div>
              {sel.impacted.map((im) => (
                <ImpactRow key={im.symbol} im={im} />
              ))}
              <p className="src-note">
                Impact = relation strength × event magnitude, split into an
                immediate (price/sentiment) and a structural (fundamental) horizon.
              </p>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
