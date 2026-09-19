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
    s = get_settings()
    out = {
        "universe_size": len(uni),
        "sectors": sectors(),
        "timeframes": ["1d", "1w", "1m"],
        "sample_fallback": s.allow_sample_fallback,
        "provider": s.provider(),
        "configured_provider": s.data_provider,
        "live": s.provider() != "sample",
    }
    from app.config import get_provider_override
    if get_provider_override():
        out["provider_fallback_active"] = True
    if s.provider() == "dhan":
        try:
            from app.data import dhan_feed

            out["dhan_feed"] = dhan_feed.status()
        except Exception:
            pass
    return out
