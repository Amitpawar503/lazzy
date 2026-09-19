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
| **Best Stocks** | Screeners by **sector / cap / momentum / seasonal**; sector & cap show **subsections** (per sector / large-mid-small-micro), each row showing which algos push it up ▲ / down ▼ and by how much | ✅ `top_n` + dimension |
| **FII/DII Activity** | Net institutional cash flows + stocks added / removed | ✅ `top_n` |
| **Algo Signals** | 10 algorithms vote per stock — how many are +ve / −ve and the net conviction, with a per-algorithm drilldown | ✅ `top_n` + view/sort |
| **Ideas** | Categories **style / fundamentals / sector / cap**. **style** = 6 sections (Large/Mid/Small/Micro cap, Multibagger, Most Volatile-SIP), each ~25 stocks ranked by **styles-in-favour across all ~110 investor styles**, with a 👍/•/👎 consensus column. Fundamentals/sector/cap are backtested baskets. | category + section tabs |
| **Themes** | Thematic baskets (High Conviction, Bharat Bargains, Quality, Momentum, Seasonal, Dividend), backtested vs benchmark | — |
| **News** | Aggregated Indian & global headlines, entity-linked + sentiment-tagged | category filter |
| **News Impact** | Event → affected-companies fan-out with short- vs long-term impact (e.g. a Tata Sons listing: holders gain, TCS faces overhang, peers unaffected) | per-event |

The **Algo Signals** screen runs SMA/EMA crossovers, RSI, MACD, Supertrend,
Bollinger Bands, ROC momentum, ADX/DI, Donchian breakout, and Stochastic on each
stock, then reports the bullish/bearish/neutral counts and a net conviction
score (−100…+100). Click a row for every algorithm's reading.

**Click any stock** (on screeners, signals, or news-impact) → a detail modal with
a **"why it can go UP / why it can go DOWN"** thesis (each point backed by a
technical reading or a fundamental figure), a full **fundamentals** grid, the
52-week range, and the 10-algo technical panel.

Every screener/signals row also has a **Reasoning** column — hover it for a rich
tooltip: **SWOT** (strengths / weaknesses / opportunities / threats),
**corporate actions** (dividend / bonus / buyback / pledge), **order wins &
govt contracts**, **management** notes, and **news impact** (short/long-term) —
each with the concrete figure behind it (Moneycontrol #KnowBeforeYouInvest style).
The stock-detail modal shows the full SWOT grid too.

The **Ideas** tab (145 baskets) spans **style** (~110 investor personas — Icahn,
ARK, Buffett, Graham, Lynch, Greenblatt and many funds, each style-emulated on the
Indian universe), **fundamentals** (High ROE, Low Debt, Dividend, Undervalued,
Deep Value, Growth, Cash-flow, Quality, Institutional-favourites, GARP),
**sector**, **cap**, and **theme**. Every basket holds **5–25 stocks**, explains
*how it picks*, and is backtested with return + risk vs the benchmark. Filter by
category and search by investor/strategy name.

**Live data & speed:** off by default (fast synthetic data, no network). For the
**complete NSE market**, set `DATA_PROVIDER=fmp` + `FMP_API_KEY` (Financial
Modeling Prep — full universe via screener + quotes + EOD history, `UNIVERSE_LIMIT`
names by market cap); or `LIVE_DATA=true` for per-symbol yfinance. History is
cached to JSON (`DATA_STORE_DIR`); a near-live SSE stream (`/api/stream/quotes`)
buffers quotes. Everything falls back to sample data if the feed/key is missing.
Zero-delay ticks need a broker websocket (Phase 6). See
[`docs/LIVE_DATA_AND_COVERAGE.md`](docs/LIVE_DATA_AND_COVERAGE.md) for the data
sources researched, the performance fixes, and the fundamentals/technicals
coverage vs Moneycontrol's scanners.

## Roadmap (see `docs/ANALYSIS_AND_ARCHITECTURE.md`)

- **Phase 1** — live data adapters (jugaad-data EOD/bhavcopy, Tapetide FII/DII, yfinance).
- **Phase 2** — best-stock screeners: sector / cap / momentum / seasonal (+ Top-N). ✅ shipped
- **Phase 3** — news aggregation + event-graph impact scoring (short/long term). ✅ shipped (sample data; live RSS/API wiring next)
- **Phase 4** — multi-agent AI layer (analysts → bull/bear debate → synthesis) on free LLMs.
  _(Provider registry live at `/api/ai/providers`; agents next.)_
- **Phase 5** — VectorBT backtests + tearsheets.
- **Phase 6** — broker abstraction + paper/live trading.

## Notes

- Not investment advice. Data may be delayed or illustrative.
- Secrets live in `.env` (git-ignored) or environment variables — never committed.
- Reference-repo credits and licensing notes are in the analysis doc.
