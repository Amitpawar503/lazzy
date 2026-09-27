from __future__ import annotations

from fastapi import APIRouter

from app.services.govt import radar

router = APIRouter(prefix="/api/govt", tags=["govt"])


@router.get("/radar", summary="Govt of India + big-institution ownership & policy radar")
def govt_radar() -> dict:
    """Where the Govt of India (and LIC/EPFO/SUUTI/SBI MF) are buying vs selling,
    which sectors have policy tailwinds, and which stocks can rise on govt
    decisions (synthesized pick list)."""
    return radar()
