// Diverging red→grey→green scale for returns, symmetric around 0.
// Colour-blind-safe-ish (teal/magenta could be swapped later).

export function returnColor(pct: number, maxAbs: number): string {
  const cap = Math.max(maxAbs, 0.5);
  const t = Math.max(-1, Math.min(1, pct / cap)); // -1..1
  if (t >= 0) {
    // grey → green
    const g = Math.round(120 + 90 * t);
    const r = Math.round(90 - 60 * t);
    const b = Math.round(90 - 60 * t);
    return `rgb(${r}, ${g}, ${b})`;
  }
  // grey → red
  const a = -t;
  const r = Math.round(120 + 100 * a);
  const g = Math.round(90 - 55 * a);
  const b = Math.round(90 - 55 * a);
  return `rgb(${r}, ${g}, ${b})`;
}

export function fmtPct(p: number): string {
  return `${p >= 0 ? "+" : ""}${p.toFixed(2)}%`;
}

export function fmtCr(cr: number): string {
  if (cr >= 100000) return `₹${(cr / 100000).toFixed(2)}L cr`;
  if (cr >= 1000) return `₹${(cr / 1000).toFixed(1)}k cr`;
  return `₹${cr.toFixed(0)} cr`;
}
