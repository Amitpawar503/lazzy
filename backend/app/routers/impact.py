from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import EventList, MarketEvent
from app.services.impact import get_event, list_events

router = APIRouter(prefix="/api/impact", tags=["news-impact"])


@router.get("/events", response_model=EventList, summary="Market events + impacted companies")
def events(
    session: str = Query("all", pattern="^(all|daily|weekly|monthly)$"),
) -> EventList:
    return list_events(session=session)


@router.get("/events/{event_id}", response_model=MarketEvent, summary="One event's impact fan-out")
def event(event_id: str) -> MarketEvent:
    ev = get_event(event_id)
    if ev is None:
        raise HTTPException(status_code=404, detail="event not found")
    return ev
