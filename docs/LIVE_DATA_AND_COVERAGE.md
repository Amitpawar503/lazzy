# Live Data, Performance & Coverage

This doc answers the follow-up asks: make loading fast/async, move from EOD/sample
to live data (with 1-year history cached + live current price), and check
fundamentals/technicals coverage against Moneycontrol's scanners.

---

## 1. Performance (done)

The screeners were slow / momentum "wouldn't load" because **every stock triggered
its own yfinance network call**, synchronously, twice (once for momentum, once for
seasonal with a different history length). Fixes shipped:

- **`LIVE_DATA` flag (default off)** — offline uses a fast deterministic synthetic
  series; **no network at all**, so screens load instantly.
- **One long OHLCV series per symbol**, cached; all consumers (momentum 260,
  seasonal ~780, signals) **slice** from it — no duplicate fetches.
- **Per-symbol signal cache** (`compute_signals_cached`) shared by screeners,
  scorecard and stock detail.
- **Parallel computation** across the universe with a thread pool.

Result (sample universe, cold → warm): momentum **~1.3s → ~0.1s**, scorecard
**~0.01s** warm. First call warms the cache; everything after is instant until TTL.

---

## 2. Live data plan

### What each researched source gives us

| Source | Live NSE/BSE? | History | Streaming? | Free? | Verdict |
|--------|---------------|---------|-----------|-------|---------|
| **yfinance** | ~1-min delayed | 1y+ daily free | no | yes | **Primary free** for history + near-live |
| **jugaad-data** (`NSELive`) | near-real-time quote | bhavcopy/EOD | no | yes | Good NSE quote + EOD |
| **NSE India JSON** (`/api/quote-equity`) | near-real-time | limited | no | yes* | Needs cookies/headers; rate-limited; ToS caveats |
| **Tapetide MCP** | live LTP quote, batch ≤20 | ~8y OHLCV | no | 50 calls/day | Great data, tiny free quota → cache hard |
| **londonstrategicedge/lse-data** | — | US/FX/crypto only | yes (WS) | — | **No NSE/BSE** → not useful |
| **livetennisapi/polymarket-tennis** | — | — | — | — | Unrelated (tennis betting) |
| **Perplexity Finance** | yes | yes | — | via partners | Sources via **Zerodha/Paytm** partnerships, **not a public free API** |
| **Broker websockets** (Zerodha Kite, Fyers, Upstox, Dhan) | **tick, zero-delay** | yes | **yes (WS)** | needs paid API + login | The only true no-delay path (Phase 6) |

\*Unofficial; respect ToS and rate limits.

### The architecture we implemented

1. **1-year history, cached** — `LIVE_DATA=true` fetches ~2y daily OHLCV via
   yfinance; with `DATA_STORE_DIR` set it's **persisted to JSON on disk** and
   refreshed at most once/day. Off → deterministic synthetic. All reads slice the
   one cached series.
2. **Near-live current price** — `/api/quotes?symbols=…` (batch) and the
   per-symbol provider poll yfinance `fast_info` (2s cache) when live, else last
   close. Old data lives in cache/JSON exactly as you asked; only the current
   quote is fetched live.
3. **Streaming / buffering** — `/api/stream/quotes?symbols=…` is a **Server-Sent
   Events** stream that pushes buffered quote updates on an interval (near-live,
   seconds). Demo jitter when offline so movement is visible.
4. **Zero-delay ticks** — a broker websocket adapter (Kite/Fyers/Upstox/Dhan) is
   the Phase-6 add-on; those need an API key + daily login (creds already in
   `.env.example`). No free source gives true tick data without a broker.

**To turn on live data locally:**

Option A — **Financial Modeling Prep (full NSE market, recommended):**
```env
DATA_PROVIDER=fmp
FMP_API_KEY=<your key>          # financialmodelingprep.com
UNIVERSE_LIMIT=750             # how many stocks (by market cap) to load
DATA_STORE_DIR=./data_store    # optional: cache history as JSON on disk
```
The universe is built from FMP's stock-screener (sector + market cap) merged with
full-exchange quotes (1-day change); per-symbol EOD history comes from
`historical-price-full`. This gives the **complete NSE market** (up to
`UNIVERSE_LIMIT` names) instead of the ~149 bundled samples.

Option B — **yfinance (per-symbol):**
```env
LIVE_DATA=true                 # == DATA_PROVIDER=yfinance
DATA_STORE_DIR=./data_store
```
(Requires `pip install yfinance`; network access to Yahoo.)

Both fall back to the bundled sample data if the network/key is unavailable, so
the app never breaks. The active provider is shown in the top bar and at `/meta`.

> Note: this cloud sandbox blocks outbound finance hosts (Yahoo/NSE/FMP CONNECT
> is denied by the egress proxy), so live fetching runs on **your** machine; the
> adapter's shape is verified here with mocked responses.

---

## 3. Fundamentals coverage vs Moneycontrol scanners

Moneycontrol groups fundamental scans as: Results, MC Curated, Ratio, P&L,
Balance Sheet, Cash Flow, Red Flags, Shareholding. Our `fundamentals` object (per
stock, shown in the stock-detail modal) already carries the underlying fields:

| MC category | Example scans | Our field(s) | Status |
|-------------|---------------|--------------|--------|
| Results / P&L | Quarterly profit/sales growth, margins | `sales_growth_yoy`, `profit_growth_yoy`, `operating_margin`, `net_profit_margin` | ✅ fields (sample data) |
| Ratio | Book value, PE, capital allocation | `pe`, `industry_pe`, `pb`, `book_value`, `roe`, `roce`, `eps` | ✅ |
| Balance Sheet | Debt/equity, debt-free, current ratio | `debt_to_equity`, `current_ratio` | ✅ |
| Cash Flow | Operating/free cash flow | `ocf_positive`, `free_cash_flow_cr` | ✅ |
| Red Flags | High pledge, falling sales | `high_pledge`, `promoter_pledge`, `falling_sales` | ✅ flags |
| Shareholding | FII/DII/promoter changes, pledge | `promoter_holding`, `fii_holding`, `dii_holding`, `public_holding`, `promoter_pledge` | ✅ (+ FII/DII screen has deltas) |
| Dividend | Yield | `dividend_yield` | ✅ |

**Gap:** values are **illustrative sample data** today. Phase-3 finish = wire real
fundamentals from **screener.in / Tapetide / FMP** into `fundamentals_for()` (same
shape, drop-in). Then the same scans become live filters.

---

## 4. Technicals coverage vs Moneycontrol scanners

MC technical scans: Breakout, Price, Intraday, Indicator, Range Breakout,
Candlestick, Moving Average, Volume & Delivery, SuperTrend & Parabolic SAR.

| MC scan family | Our algorithm(s) | Status |
|----------------|------------------|--------|
| Moving Average (Golden/Death cross, DMA) | SMA 20/50 crossover, EMA 12/26 crossover | ✅ |
| Indicator (RSI, MACD, ADX, MFI) | RSI, MACD, ADX/DI | ✅ (MFI/Stochastic: Stochastic ✅, MFI pending) |
| SuperTrend & Parabolic SAR | Supertrend | ✅ (PSAR pending) |
| Breakout / Price (52w/N-day highs, VWAP) | Donchian 20 breakout | ⚠️ partial (add 52w/VWAP scans) |
| Range Breakout (NR4/NR7, Bollinger) | Bollinger Bands | ⚠️ partial (add NR4/NR7) |
| Candlestick patterns | — | ❌ pending (add pattern detectors) |
| Volume & Delivery | — | ❌ pending (needs delivery data) |
| Intraday (Open=Low/High) | — | ❌ pending (needs intraday feed) |

Every algorithm already votes per stock (up/down + %) and feeds the consensus,
screeners and the stock-detail thesis. Adding the pending ones is incremental —
each is a new function in `services/signals.py` returning `(signal, strength,
detail)`.

---

## 5. Stock detail (propicks-style "why up / why down")

Clicking any stock (on screeners, signals, or news-impact) opens a modal with:
- live/EOD quote, 52-week range, verdict + net score;
- **Why it can go UP** and **Why it can go DOWN** — each point backed by a concrete
  fact (technical reading or fundamental figure);
- a full fundamentals grid and the 10-algo technical panel.

This mirrors investing.com/pro ProPicks' "bull/bear case" idea, built from our own
algo consensus + fundamentals so it's explainable and open-source.
