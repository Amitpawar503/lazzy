"""FastAPI application entrypoint.

Run:  uvicorn app.main:app --reload --port 8000   (from the backend/ directory)
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.routers import (
    ai, fiidii, health, heatmap, impact, news, screener, signals, stock,
    strategies, stream, style,
)

settings = get_settings()

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
