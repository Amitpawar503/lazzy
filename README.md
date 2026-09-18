# Lazzy Markets

An Indian market (NSE/BSE/NFO) intelligence platform — heatmaps, best-stock
screeners, FII/DII activity, and news-impact analysis, with an AI layer built on
free LLM providers.

> **Status:** Slice 1 shipped — **360° market heatmap**, **sector heatmap**, and
> **FII/DII investor activity**, end-to-end (FastAPI backend + React frontend).
> Runs with zero config: live sources are used when available, else bundled
> sample data. See the roadmap for what's next.

## Repo layout

```
docs/ANALYSIS_AND_ARCHITECTURE.md   Analysis of 20+ reference repos + full blueprint
backend/                            FastAPI API (Python) — heatmaps + FII/DII
frontend/                           React + Vite + TypeScript UI (3 screens)
.env.example                        All config keys (LLM/data/broker) — optional
```

## Quick start

```bash
# 1) Backend  → http://localhost:8000/docs
cd backend && pip install -r requirements.txt && uvicorn app.main:app --port 8000

# 2) Frontend → http://localhost:5173  (in another terminal)
cd frontend && npm install && npm run dev
```

## What it does (Slice 1)

| Screen | Description | Top-N control |
|--------|-------------|---------------|
| **360° Market** | Treemap: box size = market cap, colour = return over 1d/1w/1m | ✅ `top_n` |
| **Sector Heatmap** | Market-cap-weighted return per sector, with top gainer/loser | timeframe |
| **FII/DII Activity** | Net institutional cash flows + stocks added / removed | ✅ `top_n` |

## Roadmap (see `docs/ANALYSIS_AND_ARCHITECTURE.md`)

- **Phase 1** — live data adapters (jugaad-data EOD/bhavcopy, Tapetide FII/DII, yfinance).
- **Phase 2** — best-stock screeners: sector / cap / momentum / seasonal (+ Top-N).
- **Phase 3** — news aggregation + event-graph impact scoring (short/long term).
- **Phase 4** — multi-agent AI layer (analysts → bull/bear debate → synthesis) on free LLMs.
- **Phase 5** — VectorBT backtests + tearsheets.
- **Phase 6** — broker abstraction + paper/live trading.

## Notes

- Not investment advice. Data may be delayed or illustrative.
- Secrets live in `.env` (git-ignored) or environment variables — never committed.
- Reference-repo credits and licensing notes are in the analysis doc.
