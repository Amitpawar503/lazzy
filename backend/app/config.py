"""Central configuration, loaded from environment / .env.

Never hard-code secrets. Copy `.env.example` to `.env` and fill what you have;
every key is optional — the app degrades to free sources / sample data.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    # --- App ---
    app_name: str = "Lazzy Markets"
    env: str = "dev"
    # Comma-separated origins for CORS; "*" in dev.
    cors_origins: str = "*"

    # --- Data behaviour ---
    # If True, when a live source fails we fall back to bundled sample data so
    # the UI always renders. Set False to surface errors instead.
    allow_sample_fallback: bool = True
    cache_ttl_seconds: int = 300
    redis_url: Optional[str] = None  # e.g. redis://localhost:6379/0

    # --- Free LLM providers (Phase 4; unused in this slice) ---
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    together_api_key: Optional[str] = None
    hf_token: Optional[str] = None
    nvidia_api_key: Optional[str] = None
    cloudflare_account_id: Optional[str] = None
    cloudflare_api_token: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    # --- Data / news providers (optional free tiers) ---
    tapetide_token: Optional[str] = None
    alphavantage_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    newsapi_key: Optional[str] = None

    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
