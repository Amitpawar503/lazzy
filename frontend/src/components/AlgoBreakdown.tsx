import { useEffect, useState } from "react";
import { api, type StockSignal } from "../api";

// Full per-algorithm breakdown for one stock (shared by Signals + Screeners).
export default function AlgoBreakdown({ symbol }: { symbol: string }) {
  const [sig, setSig] = useState<StockSignal | null>(null);
  useEffect(() => {
    let alive = true;
    api.stockSignal(symbol).then((s) => alive && setSig(s)).catch(() => alive && setSig(null));
    return () => {
      alive = false;
    };
  }, [symbol]);
  if (!sig) return <div className="algo-loading">Loading algorithms…</div>;
  return (
    <div className="algo-breakdown">
      {sig.algos.map((a) => (
        <div key={a.algo} className="algo-chip">
          <span className={a.signal > 0 ? "dot up" : a.signal < 0 ? "dot dn" : "dot nu"} />
          <span className="algo-name">{a.algo}</span>
          <span className="algo-detail">{a.detail}</span>
          <span className="algo-str">
            {a.signal > 0 ? "+" : a.signal < 0 ? "−" : "•"}
            {a.strength > 0 ? ` ${(a.strength * 100).toFixed(0)}%` : ""}
          </span>
        </div>
      ))}
    </div>
  );
}
