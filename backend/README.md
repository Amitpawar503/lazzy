# Lazzy Markets — Backend (FastAPI)

Indian market intelligence API. Slice 1: **360° heatmap**, **sector heatmap**,
**FII/DII activity**. Falls back to bundled sample data when live sources are
unavailable, so it runs with zero config.

## Run

```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # optional
pip install -r requirements.txt
cp ../.env.example ../.env                              # optional
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive API docs.

## Endpoints

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/heatmap/360` | `timeframe=1d\|1w\|1m`, `top_n=1..500`, `sector` | 360° treemap (size=mcap, colour=return) |
| GET | `/api/heatmap/sectors` | `timeframe` | Market-cap-weighted sector heatmap |
| GET | `/api/fiidii/flows` | — | FII/DII net cash-flow series + cumulative |
| GET | `/api/fiidii/activity` | `top_n=1..100` | Stocks institutions added / removed |
| GET | `/meta` | — | Universe size, sectors, timeframes |
| GET | `/health` | — | Liveness |

Every screen honours the **Top-N** requirement via `top_n`.

## Layout

```
app/
  config.py              env-driven settings (no hard-coded secrets)
  data/
    cache.py             TTL cache (Redis or in-memory)
    universe.py          instrument rows (live yfinance → sample fallback)
    sample_data.py       bundled NSE universe + flows + holding deltas
    providers/           yfinance_provider, fiidii_provider, base
  services/              heatmap.py, fiidii.py  (the algorithms)
  routers/               heatmap.py, fiidii.py, health.py
  models/schemas.py      response contracts
  main.py                app + CORS + routers
```

## Wiring live data (next)

- `data/universe.py` already tries yfinance (`.NS`) and falls back to sample.
- `data/providers/fiidii_provider.py` has TODO hooks for NSE / Tapetide MCP —
  both should go through `cache.py` (Tapetide free tier = 50 calls/day).
