from __future__ import annotations

from fastapi import APIRouter

from app.ai.providers import list_providers

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/providers", summary="Free AI providers and which are configured")
def providers() -> dict:
    return list_providers()
