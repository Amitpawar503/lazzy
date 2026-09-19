from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import StyleSections
from app.services.style_sections import style_sections

router = APIRouter(prefix="/api/style", tags=["style"])


@router.get("/sections", response_model=StyleSections, summary="Style Picks — 6 sections + style consensus")
def sections() -> StyleSections:
    return style_sections()
