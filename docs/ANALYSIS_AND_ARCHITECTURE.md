# Indian Market Intelligence Platform — Repo Analysis & Architecture Blueprint

> Working name: **Lazzy Markets** (project lives in the `lazzy` repo, `develop` branch).
> This document (1) analyzes the 20+ reference repositories, (2) maps what each contributes to
> our goals, and (3) proposes a concrete, phased architecture for the platform we want to build.

---

## 1. What we are building (goals restated)

A retail-grade Indian market (NSE/BSE/NFO) intelligence platform with these **screens/modules**:

| # | Screen / Module | Core idea |
|---|-----------------|-----------|
| 1 | **Best stocks — sector-wise** | Top ranked stocks per sector |
| 2 | **Best stocks — cap-wise** | Large / mid / small / micro cap leaders |
| 3 | **Best stocks — momentum-wise** | RSI/MACD/Supertrend/ROC/relative-strength ranking |
| 4 | **Seasonal stocks** | Month/quarter historical seasonality winners |
| 5 | **360° market view heatmap** | Whole-market treemap (by mcap, colored by return) |
| 6 | **Sector-wise heatmap** | Sector performance grid + drilldown |
| 7 | **DII / FII / investor activity** | Net flows + which stocks institutions added/exited |
| 8 | **News feed** | Aggregated Indian + global market news |
| 9 | **News impact (short & long term)** | Per-event impact scoring on affected stocks |
| — | **Per-screen "Top N" control** | Every screen lets the user choose how many rows to show |
| — | **AI layer** | Multi-agent reasoning on top, using *free* LLM providers |

A recurring theme in the request: the **event → affected-companies graph**.
Example: *"If Tata Sons gets listed, which companies hold its stock, what is the impact on them,
and how do they behave?"* → we need an entity/relationship model (holdings, parent/subsidiary,
supplier/customer, index membership) so a single news event can fan out to impacted tickers with
a short-term vs long-term impact score.

---

## 2. Repository analysis

Grouped by the role each repo plays for us. For every repo: **what it is**, **stack**, and
**what we take from it** (idea, algorithm, or code pattern — not necessarily code).

### 2.1 Multi-agent AI research frameworks (the "brain")

| Repo | Stack | What it does | What we take |
|------|-------|--------------|--------------|
| **TauricResearch/TradingAgents** | Python, LangGraph; OpenAI/Gemini/Claude/Groq/Ollama | Hierarchical agent "trading firm": Analyst team (fundamentals, sentiment, news, technical) → Bull/Bear researcher debate → Trader → Risk/Portfolio manager. Multi-market incl. India via `.NS`/`.BO`. Backtesting + decision logging. | **The reference architecture for our AI layer.** Analyst→debate→synthesis pattern; point-in-time discipline; provider-agnostic LLM config. |
| **svsairevanth/indian-stock-ai-agent** | Python, OpenAI Agents SDK, GPT-4o, yfinance, VADER/TextBlob | 10 agents (fundamental, technical, sentiment, macro, bull/bear debate, risk, portfolio) → weighted score (F30/T25/S15/M15/Debate15) → PDF report. | **Weighted scoring formula** and agent role split tuned for India. Report generation pattern. |
| **hopit-ai/india-trade-cli** ("Vibe Trading") | Python 3.11, FastAPI, Electron+React, Gemini/Claude/OpenAI/Ollama | 7 parallel analyst agents (technical, fundamental, options, news, sentiment, sector, risk) + bull/bear debate → 3 risk-profiled plans (aggressive/neutral/conservative). 58-strategy library, options analytics, Telegram. | **Sector + options agents**, three-risk-profile output, CLI command surface (`analyze`, `morning-brief`, `flows`, `deals`). Free-LLM support (Gemini/Ollama). |
| **rooneyrulz/agentic-stock-research-system** | Python, LangChain/LangGraph, Streamlit, OpenAI, Bright Data MCP | 4 agents (Stock Finder → Market Data → News Analyst → Recommendation) + supervisor. Filters by mcap & momentum; entry/exit + confidence. | **Stock Finder agent** = our screener→shortlist pipeline. Supervisor orchestration + confidence scoring. |

### 2.2 Indian market data providers (the "fuel")

| Repo | Stack | What it does | What we take |
|------|-------|--------------|--------------|
| **jugaad-py/jugaad-data** | Python, pandas, Click CLI | Free NSE/BSE + RBI data: `stock_df()`, `NSELive().stock_quote()`, `bhavcopy_save()`, `bhavcopy_fo_save()`, index PE/TRI, F&O. Built-in caching to respect NSE. | **Primary free historical + bhavcopy source.** EOD ingestion, F&O chain, index PE for valuation context. |
| **Tapetide-hq/nse-bse-indian-stock-market-data-mcp** | Node MCP, Cloudflare Workers backend | 52 MCP tools over ~8,200 NSE/BSE cos: screeners (326 ratios), FII/DII 30-day flows + sector allocation, **heatmaps**, India VIX, option chains/IV, bulk/block deals, **point-in-time** membership for survivorship-safe backtests, broker-CSV import. Free tier 50 calls/day. | **FII/DII flows, heatmap data, point-in-time membership, ratio screener** — huge feature overlap. Use as an MCP data source (mind the 50/day free cap → cache aggressively). |
| **0xramm/Indian-Stock-Market-API** | Python Flask on Cloudflare Workers, yfinance | REST: `/search`, `/stock?symbol=&res=`, `/stock/list` — live price, %chg, volume, mcap, P/E, div yield, sector. NSE/BSE via `.NS`/`.BO`. | **Simple yfinance wrapper pattern** for quotes/mcap/sector — good fallback quote service and `res=num|val` formatting idea. |
| **ekanshsinghal/indian-stock-market** | Python Flask, MongoDB, React/Redux | Scrapes Moneycontrol for NSE/BSE → dashboard. (Archived; IP-block risk noted.) | **Moneycontrol scraping pattern** for fields APIs don't give — use only as last-resort, respect robots/ToS. |
| **pratiksampat/IndianStockTracker** | Python, Telepot, nsetools, Heroku | Telegram bot: price alerts on gain/loss % thresholds. | **Threshold-alert pattern** for our notifications module. |

### 2.3 Broker abstraction & execution (optional / later phase)

| Repo | Stack | What it does | What we take |
|------|-------|--------------|--------------|
| **sainipankaj15/All-In-One-Broker** | Go, gorilla/websocket | Unified interface over Jainam/Fyers/Tiqs/Zerodha/XTS: orders, portfolio, quotes, LTP, option chain, depth, Greeks, WS streaming. Reads creds from local JSON. | **Broker-abstraction interface design** (one API, many brokers). |
| **white-trade-loan/algo-trading-platform** | TS/Hono, SQLite(WAL), Redis, React19, Socket.IO, ZeroMQ | Self-hosted: unified API over **30+ brokers**, no-code flow builder, Python strategy host, options analytics (Vol surface, GEX, max pain), ₹1cr sandbox, MCP for NL trading, Argon2/Fernet/2FA. | **Reference for the execution + options-analytics + security tier** if we go live-trading. Flow-builder concept. |
| **marketcalls/openbull** | FastAPI, SQLAlchemy async, Postgres, Redis, ZeroMQ, React19+Plotly | Self-hosted options platform, 5 brokers (Upstox/Zerodha/Angel/Dhan/Fyers), 30 strategy templates, IV smile, 3D vol surface, GEX, max pain, OI, tick-driven sandbox. | **Options analytics dashboards** (IV smile, GEX, max pain) and plugin-per-broker architecture. Closest stack match if we pick Python+React. |
| **aakashlpin/kha-ching** ("SignalX") | Next.js/TS, Redis, Kite Connect | Automated intraday (straddle w/ skew, SLM), daily auth, mock mode. | **Intraday scheduling + square-off + mock-mode** patterns. |
| **srikar-kodakandla/fully-automated-nifty-options-trading** | Python, Selenium, Fyers API, cron | Supertrend+ADX → sell OTM + protective put spread, auto-close at 95% max profit. (Deprecated: Fyers v2→v3.) | **Supertrend+ADX signal** and spread construction logic (code is dated; port the idea). |

### 2.4 Backtesting, screening & "skills" (validation layer)

| Repo | Stack | What it does | What we take |
|------|-------|--------------|--------------|
| **marketcalls/vectorbt-backtesting-skills** | Python, VectorBT, Plotly, OpenAlgo ta | Agent skills to build/test strategies (IN/US/crypto). 12 templates (EMA X, RSI, Supertrend, MACD, Donchian), realistic costs, NIFTY50 benchmark, 7-panel plots, monthly heatmaps, Monte Carlo tearsheets. | **Backtesting engine + indicator library (OpenAlgo ta, 100+), monthly-return heatmap, tearsheet metrics.** |
| **javajack/skill-algotrader** | Python 3.10, Kite, Polars, Parquet | Bot-gen wizard, NSE universe fetcher, "fortress signals", Kelly sizing, regime detection, portfolio-heat limits, 30+ production gotchas (tick-size, T+1, VWAP resets). | **Kelly position sizing, market-regime detection, universe fetcher, India microstructure gotchas.** Polars+Parquet for fast vectorized compute. |
| **samyakjain0606/awesome-stock-skills** | Claude Code plugin skills | fetch-concalls (screener.in/BSE/NSE), growth-trigger (variant perception), NotebookLM, research-pipeline→PDF, publish (PDF/HTML/Netlify). | **Fundamental/concall ingestion + growth-trigger scoring** for the long-term impact side. |
| **h0i5/Foursight** | Next.js, Hono, Cloudflare (D1/KV), Highcharts | Paper trading on 2,000+ NSE stocks, live data, charts, watchlists, top movers. | **Paper-trading + watchlist + top-movers UX** and Cloudflare-edge deployment pattern. |

### 2.5 Cross-cutting takeaways

- **Data is free-tier-able** (jugaad-data + yfinance + Tapetide MCP) → no paid feed needed for v1.
- **The winning AI pattern is consistent** across 4 repos: *specialized analysts → bull/bear debate →
  weighted synthesis → risk-profiled recommendation.* We adopt it.
- **India microstructure matters**: T+1, tick size, VWAP daily reset, session timing, F&O expiry —
  captured in skill-algotrader's gotchas; bake into our data/validation layer.
- **Point-in-time / survivorship bias**: only Tapetide + TradingAgents handle it; we must, for any
  backtest to be trustworthy.

---

## 3. Proposed architecture

### 3.1 Layered view

```
┌──────────────────────────────────────────────────────────────────────┐
│  PRESENTATION  (web UI + REST/WebSocket API)                           │
│  Screens: sector · cap · momentum · seasonal · 360 heatmap ·           │
│           sector heatmap · FII/DII activity · news · news-impact       │
│  Every screen: Top-N selector, timeframe selector, algo selector       │
└───────────────▲──────────────────────────────────────────────────────┘
                │ JSON / WS
┌───────────────┴──────────────────────────────────────────────────────┐
│  INTELLIGENCE  (analysis + AI)                                         │
│  • Screener engine: momentum, cap, sector, seasonality rankers        │
│  • Heatmap builder (treemap aggregates)                                │
│  • FII/DII flow analyzer (added/removed detector)                      │
│  • News NLP: dedup → entity linking → sentiment → impact scoring       │
│  • Event graph: entity relationships (holdings/parent/index/supplier)  │
│  • Multi-agent AI (analysts → debate → synthesis) [free LLMs]          │
│  • Backtest/validation (VectorBT) + Kelly sizing + regime detection    │
└───────────────▲──────────────────────────────────────────────────────┘
                │
┌───────────────┴──────────────────────────────────────────────────────┐
│  DATA  (ingestion + storage + cache)                                   │
│  Adapters: jugaad-data · yfinance · Tapetide MCP · FMP MCP ·           │
│            NSE/BSE · Moneycontrol(scrape) · News RSS/APIs · brokers    │
│  Store: time-series (OHLCV) · fundamentals · flows · news · entities   │
│  Cache: Redis (respect NSE + Tapetide 50/day limits)                   │
│  Scheduler: EOD bhavcopy, intraday polling, news polling               │
└───────────────────────────────────────────────────────────────────────┘
```

### 3.2 Recommended stack

The reference repos cluster on **Python (data/AI) + React/TS (UI)**. The existing `lazzy` repo is
an unrelated Spring Boot 1.5 / Java 8 game POC. Two viable paths — see the decision in §6:

- **Path A (recommended): Python + React.** FastAPI backend (matches openbull / hopit-ai /
  agentic systems), Polars/pandas + VectorBT for compute, React+Vite+Tailwind+Plotly/Highcharts
  frontend. Best library fit; almost every reference repo is directly reusable.
- **Path B: Keep Java/Spring Boot** for the API/orchestration and call a **Python sidecar**
  (FastAPI microservice) for data science + LLM agents. Reuses the existing repo skeleton but adds
  a polyglot boundary. Heavier.

### 3.3 Data model (core entities)

- `instrument` (symbol, isin, exchange, name, sector, industry, mcap, cap_class)
- `ohlcv` (instrument_id, date, o/h/l/c/v, adj factors) — time-series
- `fundamental` (instrument_id, period, ratios[], shareholding)
- `flow` (date, fii_net, dii_net, per-instrument add/remove deltas)
- `news` (id, source, url, ts, title, body, entities[], sentiment, topics[])
- `entity_relation` (from_entity, to_entity, type: holds/parent/subsidiary/index_member/supplier/customer, weight)
- `impact` (news_id, instrument_id, horizon: short|long, direction, magnitude, rationale)
- `signal` (instrument_id, algo, ts, score, rank)

The **event graph** (`entity_relation`) is what powers the "Tata Sons → who holds it → impact"
requirement. Seed it from shareholding data (Tapetide/screener), index membership (jugaad-data /
Tapetide point-in-time), and curated parent/subsidiary maps.

---

## 4. Module → algorithm mapping (how each screen is computed)

| Screen | Algorithm (sourced from repos) | Data needed | Top-N control |
|--------|-------------------------------|-------------|---------------|
| Sector-wise best | Rank within sector by composite score (return + RS + volume + fundamental) | OHLCV, sector, ratios | N per sector |
| Cap-wise best | Classify by mcap thresholds (large/mid/small/micro) → rank each bucket | mcap, OHLCV | N per bucket |
| Momentum | RSI, MACD, Supertrend, ROC, 12-1 relative strength (vectorbt/OpenAlgo ta) | OHLCV | Top N overall |
| Seasonal | Historical mean return by calendar month/quarter → rank stocks strong in current month (vectorbt monthly heatmap) | multi-year OHLCV | Top N |
| 360° heatmap | Treemap: box size = mcap, color = %return over timeframe | mcap + returns for whole universe | show top N by size |
| Sector heatmap | Aggregate constituent returns → sector grid; drill to constituents | sector map + returns | N constituents |
| FII/DII activity | Net flow trend + per-stock holding delta (added vs removed) detector | flows, shareholding deltas | Top N added/removed |
| News feed | Ingest RSS/APIs → dedup → classify → rank by recency/relevance | news sources | Top N |
| News impact | Entity-link → sentiment → propagate via event graph → short/long score | news + entity_relation | Top N impacted |

**Impact scoring (short vs long):** `impact = f(sentiment, source_credibility, event_type,
relation_weight, historical_reaction)`. Short-term weights price/sentiment/technical; long-term
weights fundamentals/growth-triggers (awesome-stock-skills variant-perception) — mirrors the
weighted-score split from svsairevanth (F/T/S/M/Debate).

---

## 5. Configuration & secrets

All credentials/keys via **env vars or a git-ignored properties file** (never committed):

```env
# Free LLM providers (add any you have)
GROQ_API_KEY=
GEMINI_API_KEY=
TOGETHER_API_KEY=
HF_TOKEN=
NVIDIA_API_KEY=
CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_TOKEN=
BFL_API_KEY=
FAL_API_KEY=
# Data / news (optional, free tiers)
ALPHAVANTAGE_API_KEY=
FINNHUB_API_KEY=
NEWSAPI_KEY=
MARKETSTACK_KEY=
TAPETIDE_TOKEN=
# Broker creds (later phase; keep encrypted at rest)
KITE_API_KEY=  KITE_API_SECRET=
FYERS_APP_ID=  FYERS_SECRET=
```

**Free AI providers to wire in** (provider-agnostic router, à la TradingAgents): Groq (Llama/Mixtral,
fast), Google Gemini (free tier), Together AI, Hugging Face Inference, Cloudflare Workers AI,
NVIDIA NIM, and local **Ollama** as a no-key fallback. Others worth adding: **OpenRouter**
(free models), **Mistral** free tier, **Cerebras**, **GLM/Zhipu**, **Google AI Studio**.

**Data-site "logins":** for sites without official APIs (TradingView, Chartink, Screener.in,
Moneycontrol), prefer official/free APIs where they exist; where we must authenticate, store
session cookies/creds in the git-ignored config and respect each site's ToS/robots and rate limits.
Note the **IP-block risk** flagged by ekanshsinghal — cache hard, back off, and degrade gracefully.

---

## 6. Phased delivery plan

**Phase 0 — Foundation** (decision + skeleton)
- Pick stack (Path A vs B, §6 decision below), scaffold repo, config loader, `.env.example`.

**Phase 1 — Data layer**
- Adapters: jugaad-data (EOD/bhavcopy/F&O), yfinance quotes, Tapetide MCP (flows/heatmap/ratios).
- Storage (time-series + fundamentals + flows), Redis cache, EOD scheduler.

**Phase 2 — Screeners & heatmaps (the 9 screens, data-only)**
- Momentum/cap/sector/seasonal rankers; 360 + sector heatmaps; FII/DII add/remove detector.
- REST/WS API with per-screen Top-N + timeframe + algo params.

**Phase 3 — News + impact**
- News aggregation (RSS/APIs), dedup, entity linking, sentiment; build event graph; impact scoring.

**Phase 4 — AI layer**
- Provider-agnostic LLM router (free providers); analyst agents → bull/bear debate → synthesis;
  attach explanations/confidence to every screen and to news impact.

**Phase 5 — Validation & polish**
- VectorBT backtests + tearsheets for each algo; Kelly sizing/regime tags; UI dashboards.

**Phase 6 (optional) — Execution**
- Broker abstraction (All-In-One / openbull pattern), paper trading (Foursight), alerts.

---

## 7. Open decisions (need user input)

1. **Stack**: Path A (Python+React, greenfield, best fit) vs Path B (keep Java/Spring + Python sidecar).
2. **First slice to build**: which 1–2 screens to implement end-to-end first (recommend: 360°/sector
   heatmap + FII-DII activity, since data is readily free and visually high-impact).
3. **Live vs EOD** for v1 (recommend EOD + delayed quotes first; live feeds/brokers in Phase 6).
4. **Deployment target** (local self-host vs Cloudflare edge vs a VPS).

---

## 8. Attribution / licensing note

Reference repos carry their own licenses (MIT, Apache, GPL, or none). Where we **reuse code** we must
honor those licenses; where we only **reuse ideas/algorithms** there is no obligation but we credit
them here. Before vendoring any file, check that repo's LICENSE. Data-source ToS (NSE, Moneycontrol,
TradingView, Screener.in) govern scraping/redistribution — treat as compliance requirements.
