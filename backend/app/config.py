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

    # --- Free / freemium LLM providers (Phase 4) ---
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None            # Google AI Studio (Gemini)
    together_api_key: Optional[str] = None
    hf_token: Optional[str] = None                  # Hugging Face Inference
    nvidia_api_key: Optional[str] = None            # NVIDIA NIM
    cloudflare_account_id: Optional[str] = None     # Cloudflare Workers AI
    cloudflare_api_token: Optional[str] = None
    openrouter_api_key: Optional[str] = None        # OpenRouter (has free models)
    mistral_api_key: Optional[str] = None           # Mistral (free tier)
    cerebras_api_key: Optional[str] = None          # Cerebras (fast, free tier)
    sambanova_api_key: Optional[str] = None         # SambaNova Cloud (free tier)
    glm_api_key: Optional[str] = None               # Zhipu GLM (free tier)
    bfl_api_key: Optional[str] = None               # Black Forest Labs (images)
    fal_api_key: Optional[str] = None               # fal.ai (images/media)
    ollama_base_url: Optional[str] = None           # local, no key (e.g. http://localhost:11434)

    # --- Data / news providers (optional free tiers) ---
    tapetide_token: Optional[str] = None
    alphavantage_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    newsapi_key: Optional[str] = None
    marketstack_key: Optional[str] = None

    # --- Data-site logins (no official API; optional, keep in .env only) ---
    tradingview_username: Optional[str] = None
    tradingview_password: Optional[str] = None
    chartink_username: Optional[str] = None
    chartink_password: Optional[str] = None
    screener_email: Optional[str] = None
    screener_password: Optional[str] = None
    moneycontrol_username: Optional[str] = None
    moneycontrol_password: Optional[str] = None

    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
