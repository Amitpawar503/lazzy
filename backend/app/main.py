"""FastAPI application entrypoint.

Run:  uvicorn app.main:app --reload --port 8000   (from the backend/ directory)
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.routers import (
    ai, fiidii, health, heatmap, impact, news, screener, signals, stock,
    strategies, stream, style,
)

# Show INFO logs (Dhan/news hits + fallbacks) in the terminal.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

settings = get_settings()

# Loud startup banner so it's obvious which data provider is actually active and
# why — the #1 reason for "still showing sample data" is a missing token.
_prov = settings.provider()
_log = logging.getLogger("lazzy")
_log.info("=" * 64)
_log.info("Lazzy Markets starting — DATA_PROVIDER=%s (effective: %s)",
          settings.data_provider, _prov)
if _prov == "dhan":
    if not settings.dhan_access_token:
        _log.warning("DHAN_ACCESS_TOKEN is NOT set → Dhan calls will be skipped and "
                     "the app will serve SAMPLE data. Set DHAN_CLIENT_ID + "
                     "DHAN_ACCESS_TOKEN in .env to get live data.")
    else:
        _log.info("Dhan creds present (client_id=%s). Live feed/history/depth will be "
                  "hit on demand — watch for [dhan] log lines.",
                  "set" if settings.dhan_client_id else "MISSING")
elif _prov == "fmp" and not settings.fmp_api_key:
    _log.warning("DATA_PROVIDER=fmp but FMP_API_KEY is not set → serving SAMPLE data.")
_log.info("=" * 64)

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Indian market intelligence platform — heatmaps, FII/DII activity, and more.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(heatmap.router)
app.include_router(fiidii.router)
app.include_router(signals.router)
app.include_router(screener.router)
app.include_router(news.router)
app.include_router(impact.router)
app.include_router(ai.router)
app.include_router(stock.router)
app.include_router(strategies.router)
app.include_router(style.router)
app.include_router(stream.router)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "app": settings.app_name,
        "version": __version__,
        "docs": "/docs",
        "endpoints": [
            "/api/heatmap/360",
            "/api/heatmap/sectors",
            "/api/fiidii/flows",
            "/api/fiidii/activity",
            "/api/signals/scorecard",
            "/api/signals/{symbol}",
            "/api/screener?dimension=momentum",
            "/api/news",
            "/api/impact/events",
            "/api/ai/providers",
            "/api/quotes?symbols=RELIANCE,TCS",
            "/api/stream/quotes?symbols=RELIANCE",
            "/api/depth/{symbol}",
        ],
    }
