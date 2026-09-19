# Lazzy Markets — Backend (FastAPI)

Indian market intelligence API. Slice 1: **360° heatmap**, **sector heatmap**,
**FII/DII activity**. Falls back to bundled sample data when live sources are
unavailable, so it runs with zero config.

## Run

Requires **Python 3.9+**. Using a virtual environment is strongly recommended so
the `uvicorn` command lands on your `PATH`:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate     # recommended
pip install -r requirements.txt                        # installs ALL deps (fastapi, pandas, …)
cp ../.env.example ../.env                              # optional
python -m uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive API docs.

### Troubleshooting

- **`zsh: command not found: uvicorn`** (common on macOS): a `pip3 install --user`
  puts the `uvicorn` script in `~/Library/Python/3.x/bin`, which usually isn't on
  `PATH`. Don't chase the PATH — just run it as a module:
  `python3 -m uvicorn app.main:app --port 8000`. (A venv, as above, avoids this
  entirely.)
- **`ModuleNotFoundError: fastapi` / `pandas`**: you only installed `uvicorn`. Run
  `pip install -r requirements.txt` to get every dependency.
- **`TypeError: unsupported operand type(s) for |`**: you're on an old build of the
  code with Python 3.9. This is fixed — pull the latest (type hints use
  `Optional[...]`, which 3.9 supports).

## Endpoints

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/heatmap/360` | `timeframe=1d\|1w\|1m`, `top_n=1..500`, `sector` | 360° treemap (size=mcap, colour=return) |
| GET | `/api/heatmap/sectors` | `timeframe` | Market-cap-weighted sector heatmap |
| GET | `/api/fiidii/flows` | — | FII/DII net cash-flow series + cumulative |
| GET | `/api/fiidii/activity` | `top_n=1..100` | Stocks institutions added / removed |
| GET | `/api/signals/scorecard` | `top_n`, `view=all\|bullish\|bearish`, `sort=score\|bullish\|bearish` | Multi-algo consensus per stock (+ve/−ve counts + net score) |
| GET | `/api/signals/{symbol}` | — | Per-algorithm breakdown for one stock |
| GET | `/api/screener` | `dimension=sector\|cap\|momentum\|seasonal`, `key`, `top_n` | Best stocks by dimension, each row with up/down algos + % |
| GET | `/api/news` | `category=all\|india\|global`, `ticker`, `limit` | Aggregated market news (entity-linked + sentiment) |
| GET | `/api/impact/events` | — | Market events + impacted companies (short/long term) |
| GET | `/api/impact/events/{id}` | — | One event's impact fan-out |
| GET | `/api/ai/providers` | — | Free AI providers and which are configured |
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
