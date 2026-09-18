from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.data.universe import get_universe, sectors

router = APIRouter(tags=["meta"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "app": get_settings().app_name}


@router.get("/meta")
def meta() -> dict:
    uni = get_universe()
    return {
        "universe_size": len(uni),
        "sectors": sectors(),
        "timeframes": ["1d", "1w", "1m"],
        "sample_fallback": get_settings().allow_sample_fallback,
    }
