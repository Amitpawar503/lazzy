"""Thin, pluggable LLM client.

Wraps the Anthropic SDK but isolates the rest of the app from it. If no API key
is configured, `is_enabled()` is False and callers fall back to non-AI paths.
Swapping providers means changing only this file.
"""
from __future__ import annotations

import json
import logging

from ..config import get_settings

log = logging.getLogger("ai")
settings = get_settings()


def is_enabled() -> bool:
    return settings.ai_enabled


def complete_json(system: str, prompt: str, max_tokens: int = 1500) -> dict | None:
    """Ask the model for JSON and parse it. Returns None on any failure."""
    if not settings.ai_enabled:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        msg = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
        return _extract_json(text)
    except Exception as e:  # network, auth, rate limit, parse — all non-fatal
        log.warning("AI call failed: %s", e)
        return None


def complete_text(system: str, prompt: str, max_tokens: int = 1200) -> str | None:
    if not settings.ai_enabled:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        msg = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in msg.content if getattr(block, "type", "") == "text").strip()
    except Exception as e:
        log.warning("AI call failed: %s", e)
        return None


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    # Strip markdown code fences if present.
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None
