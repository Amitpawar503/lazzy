// Squarified treemap layout (Bruls, Huizing, van Wijk).
// Input: items with a numeric `value`; output: same items with x/y/w/h in px.

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}
export interface Sized<T> {
  item: T;
  value: number;
}
export interface Placed<T> extends Rect {
  item: T;
}

export function squarify<T>(
  items: Sized<T>[],
  width: number,
  height: number
): Placed<T>[] {
  const total = items.reduce((s, i) => s + i.value, 0) || 1;
  const scale = (width * height) / total;
  const scaled = items
    .map((i) => ({ item: i.item, value: i.value * scale }))
    .sort((a, b) => b.value - a.value);

  const out: Placed<T>[] = [];
  let rect: Rect = { x: 0, y: 0, w: width, h: height };
  let row: typeof scaled = [];

  const shortest = () => Math.min(rect.w, rect.h);

  const worst = (r: typeof scaled, side: number) => {
    if (r.length === 0) return Infinity;
    const sum = r.reduce((s, i) => s + i.value, 0);
    const max = Math.max(...r.map((i) => i.value));
    const min = Math.min(...r.map((i) => i.value));
    const s2 = sum * sum;
    const side2 = side * side;
    return Math.max((side2 * max) / s2, s2 / (side2 * min));
  };

  const layoutRow = (r: typeof scaled) => {
    const sum = r.reduce((s, i) => s + i.value, 0);
    if (rect.w >= rect.h) {
      const rw = sum / rect.h;
      let y = rect.y;
      for (const it of r) {
        const h = it.value / rw;
        out.push({ item: it.item, x: rect.x, y, w: rw, h });
        y += h;
      }
      rect = { x: rect.x + rw, y: rect.y, w: rect.w - rw, h: rect.h };
    } else {
      const rh = sum / rect.w;
      let x = rect.x;
      for (const it of r) {
        const w = it.value / rh;
        out.push({ item: it.item, x, y: rect.y, w, h: rh });
        x += w;
      }
      rect = { x: rect.x, y: rect.y + rh, w: rect.w, h: rect.h - rh };
    }
  };

  for (const it of scaled) {
    const side = shortest();
    const withIt = [...row, it];
    if (row.length === 0 || worst(withIt, side) <= worst(row, side)) {
      row = withIt;
    } else {
      layoutRow(row);
      row = [it];
    }
  }
  if (row.length) layoutRow(row);
  return out;
}
