"""FastAPI application entrypoint.

Run: uvicorn app.main:app --reload  (from the backend/ directory)
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .ingest.pipeline import run_ingest
from .ingest.registry import seed_sources_if_empty
from .ingest.scheduler import start_scheduler, stop_scheduler
from .routers import jobs, resumes, sources, stream

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("app")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seeded = seed_sources_if_empty()
    if seeded:
        log.info("seeded %s career-page sources", seeded)
    start_scheduler()
    if settings.ingest_on_startup:
        # Run the first ingest in the background so startup isn't blocked.
        asyncio.create_task(_startup_ingest())
    yield
    stop_scheduler()


async def _startup_ingest():
    try:
        result = await run_ingest()
        log.info("startup ingest: %s new / %s fetched", result["inserted"], result["fetched"])
    except Exception:
        log.exception("startup ingest failed")


app = FastAPI(title=f"{settings.app_name} API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(resumes.router)
app.include_router(sources.router)
app.include_router(stream.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "ai_enabled": settings.ai_enabled,
        "ingest_interval_seconds": settings.ingest_interval_seconds,
    }


# --- Optionally serve the built frontend from the same origin ---------------
# If the frontend has been built (frontend/dist exists), mount it so the whole
# app is reachable on a single localhost URL (e.g. http://localhost:8000).
# During development you'd instead run the Vite dev server on :5173.
from pathlib import Path  # noqa: E402

from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if _DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/")
    def spa_root():
        return FileResponse(_DIST / "index.html")

    @app.get("/{full_path:path}")
    def spa_catch_all(full_path: str):
        # Serve real files if they exist, otherwise fall back to index.html
        # so client-side routing works. /api/* is handled by routers above.
        candidate = _DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_DIST / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "service": f"{settings.app_name} API",
            "docs": "/docs",
            "health": "/api/health",
            "hint": "Build the frontend (cd frontend && npm run build) to serve the UI here, "
                    "or run the Vite dev server on :5173.",
        }
