"""Central configuration, loaded from environment / .env.

Never hard-code secrets. Copy `.env.example` to `.env` and fill what you have;
every key is optional — the app degrades to free sources / sample data.
"""
from __future__ import annotations

from functools import lru_cache

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
    redis_url: str | None = None  # e.g. redis://localhost:6379/0

    # --- Free LLM providers (Phase 4; unused in this slice) ---
    groq_api_key: str | None = None
    gemini_api_key: str | None = None
    together_api_key: str | None = None
    hf_token: str | None = None
    nvidia_api_key: str | None = None
    cloudflare_account_id: str | None = None
    cloudflare_api_token: str | None = None
    openrouter_api_key: str | None = None

    # --- Data / news providers (optional free tiers) ---
    tapetide_token: str | None = None
    alphavantage_api_key: str | None = None
    finnhub_api_key: str | None = None
    newsapi_key: str | None = None

    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
