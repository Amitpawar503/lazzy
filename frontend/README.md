# Lazzy Markets — Frontend (React + Vite + TypeScript)

Three screens: **360° Market** (squarified treemap), **Sector Heatmap**, and
**FII/DII Activity** — each with the Top-N / timeframe controls.

## Run

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxies /api → localhost:8000)
```

Start the backend (`uvicorn app.main:app --port 8000`) first; the Vite dev
server proxies `/api` to it.

## Structure

```
src/
  api.ts               typed client + response types
  color.ts             return→colour scale + formatters
  treemap.ts           squarified treemap layout
  components/
    Controls.tsx       Top-N + timeframe selectors
    Heatmap360.tsx     360° treemap (box=mcap, colour=return)
    SectorHeatmap.tsx  sector grid
    FiiDiiActivity.tsx flows chart + added/removed tables
  App.tsx              tab shell
  styles.css           dark theme
```
