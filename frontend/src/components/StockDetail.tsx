import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, type Factor, type StockDetail as SD } from "../api";
import { fmtPct, fmtCr } from "../color";

function FactorBox({ title, cls, items }: { title: string; cls: string; items: Factor[] }) {
  return (
    <div className="factor-box">
      <h4 className={cls}>{title} <span>({items.length})</span></h4>
      {items.length === 0 && <div className="factor-none">—</div>}
      {items.map((it, i) => (
        <div className="factor-item" key={i}><b>{it.label}</b> — {it.detail}</div>
      ))}
    </div>
  );
}

// ---- context so any row can open the detail modal ----
const Ctx = createContext<(symbol: string) => void>(() => {});
export const useStockDetail = () => useContext(Ctx);

function verdictClass(v: string) {
  if (v.includes("Strong Buy")) return "v-strong-buy";
  if (v === "Buy") return "v-buy";
  if (v.includes("Strong Sell")) return "v-strong-sell";
  if (v === "Sell") return "v-sell";
  return "v-neutral";
}

function Fund({ label, value, good }: { label: string; value: string; good?: boolean | null }) {
  return (
    <div className="fund">
      <span className="fund-k">{label}</span>
      <span className={`fund-v ${good === true ? "gp" : good === false ? "gn" : ""}`}>{value}</span>
    </div>
  );
}

function Modal({ symbol, onClose }: { symbol: string; onClose: () => void }) {
  const [d, setD] = useState<SD | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    setD(null);
    setErr(null);
    api.stock(symbol).then(setD).catch((e) => setErr(String(e)));
  }, [symbol]);

  useEffect(() => {
    const onEsc = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onEsc);
    return () => window.removeEventListener("keydown", onEsc);
  }, [onClose]);

  const f = d?.fundamentals;
  return (
    <div className="modal-back" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-x" onClick={onClose}>✕</button>
        {err && <div className="error">Failed: {err}</div>}
        {!d && !err && <div className="algo-loading">Loading {symbol}…</div>}
        {d && (
          <>
            <div className="sd-head">
              <div>
                <h2>{d.symbol} <span className="sd-name">{d.name}</span></h2>
                <div className="sd-sub">
                  {d.sector} · {d.cap_class} cap · {fmtCr(d.market_cap_cr)}
                  {d.quote.live ? <span className="live-dot"> ● LIVE</span> : <span className="sd-delayed"> · EOD/delayed</span>}
                </div>
              </div>
              <div className="sd-price">
                <span className="sd-last">₹{d.quote.last_price}</span>
                <span className={d.quote.change_pct_1d >= 0 ? "up" : "dn"}>{fmtPct(d.quote.change_pct_1d)}</span>
                <em className={`verdict ${verdictClass(d.verdict)}`}>{d.verdict} · net {d.net_score >= 0 ? "+" : ""}{d.net_score}</em>
              </div>
            </div>

            <div className="sd-52w">
              52w: ₹{d.quote.low_52w} — ₹{d.quote.high_52w}
              <span className="sd-52w-note"> ({d.quote.pct_from_52w_high}% from high)</span>
              <span className="sd-ret"> · 1W {fmtPct(d.quote.ret_1w)} · 1M {fmtPct(d.quote.ret_1m)}</span>
            </div>

            <div className="thesis">
              <div className="thesis-col bull">
                <h3>▲ Why it can go UP <span>({d.bull_points.length})</span></h3>
                {d.bull_points.map((p, i) => (
                  <div className="tp" key={i}>
                    <span className="tp-kind">{p.kind.replace("_", " ")}</span>
                    <span className="tp-point">{p.point}</span>
                    <span className="tp-detail">{p.detail}</span>
                  </div>
                ))}
              </div>
              <div className="thesis-col bear">
                <h3>▼ Why it can go DOWN <span>({d.bear_points.length})</span></h3>
                {d.bear_points.map((p, i) => (
                  <div className="tp" key={i}>
                    <span className="tp-kind">{p.kind.replace("_", " ")}</span>
                    <span className="tp-point">{p.point}</span>
                    <span className="tp-detail">{p.detail}</span>
                  </div>
                ))}
              </div>
            </div>

            {d.factors && (
              <div className="sd-section">
                <h3>Company factors (SWOT)</h3>
                <div className="swot-grid">
                  <FactorBox title="Strengths" cls="s-pos" items={d.factors.strengths} />
                  <FactorBox title="Weaknesses" cls="s-neg" items={d.factors.weaknesses} />
                  <FactorBox title="Opportunities" cls="s-op" items={d.factors.opportunities} />
                  <FactorBox title="Threats" cls="s-neg" items={d.factors.threats} />
                </div>
                {(d.factors.corporate_actions.length > 0 || d.factors.orders.length > 0 || d.factors.management.length > 0) && (
                  <div className="swot-grid" style={{ marginTop: 10 }}>
                    <FactorBox title="Corporate actions" cls="s-neu" items={d.factors.corporate_actions} />
                    <FactorBox title="Order wins / contracts" cls="s-pos" items={d.factors.orders} />
                    <FactorBox title="Management" cls="s-neu" items={d.factors.management} />
                  </div>
                )}
              </div>
            )}

            {f && (
              <div className="sd-section">
                <h3>Fundamentals</h3>
                <div className="fund-grid">
                  <Fund label="P/E" value={`${f.pe} (ind ${f.industry_pe})`} good={f.cheap_vs_industry ? true : f.expensive_vs_industry ? false : null} />
                  <Fund label="P/B" value={`${f.pb}`} />
                  <Fund label="ROE" value={`${f.roe}%`} good={f.roe >= 15} />
                  <Fund label="ROCE" value={`${f.roce}%`} good={f.roce >= 15} />
                  <Fund label="Sales growth" value={`${f.sales_growth_yoy}%`} good={f.sales_growth_yoy >= 10 ? true : f.sales_growth_yoy < 0 ? false : null} />
                  <Fund label="Profit growth" value={`${f.profit_growth_yoy}%`} good={f.profit_growth_yoy >= 10 ? true : f.profit_growth_yoy < 0 ? false : null} />
                  <Fund label="Op margin" value={`${f.operating_margin}%`} />
                  <Fund label="Net margin" value={`${f.net_profit_margin}%`} />
                  <Fund label="Debt/Equity" value={`${f.debt_to_equity}`} good={f.debt_to_equity < 0.5 ? true : f.debt_to_equity > 1 ? false : null} />
                  <Fund label="Current ratio" value={`${f.current_ratio}`} />
                  <Fund label="Div yield" value={`${f.dividend_yield}%`} good={f.dividend_yield >= 1.5} />
                  <Fund label="EPS" value={`₹${f.eps}`} />
                  <Fund label="Book value" value={`₹${f.book_value}`} />
                  <Fund label="Free cash flow" value={`₹${f.free_cash_flow_cr} cr`} good={f.free_cash_flow_cr > 0} />
                  <Fund label="Promoter" value={`${f.promoter_holding}%`} />
                  <Fund label="Pledge" value={`${f.promoter_pledge}%`} good={f.high_pledge ? false : true} />
                  <Fund label="FII" value={`${f.fii_holding}%`} />
                  <Fund label="DII" value={`${f.dii_holding}%`} />
                </div>
              </div>
            )}

            <div className="sd-section">
              <h3>Technicals — {d.bullish}▲ {d.bearish}▼ {d.neutral}• of {d.algos.length} algos</h3>
              <div className="algo-breakdown" style={{ background: "transparent", padding: 0 }}>
                {d.algos.map((a) => (
                  <div key={a.algo} className="algo-chip">
                    <span className={a.signal > 0 ? "dot up" : a.signal < 0 ? "dot dn" : "dot nu"} />
                    <span className="algo-name">{a.algo}</span>
                    <span className="algo-detail">{a.detail}</span>
                  </div>
                ))}
              </div>
            </div>
            <p className="src-note">Fundamentals are illustrative sample data in this build · not investment advice.</p>
          </>
        )}
      </div>
    </div>
  );
}

export function StockDetailProvider({ children }: { children: ReactNode }) {
  const [symbol, setSymbol] = useState<string | null>(null);
  return (
    <Ctx.Provider value={setSymbol}>
      {children}
      {symbol && <Modal symbol={symbol} onClose={() => setSymbol(null)} />}
    </Ctx.Provider>
  );
}
