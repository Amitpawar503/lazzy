"""Application configuration loaded from environment variables.

All settings have sensible defaults so the app runs locally with zero config.
Set values via a `.env` file (see .env.example) or real environment variables.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Core ---
    app_name: str = "CareerHound"
    database_url: str = "sqlite:///./careerhound.db"
    # Comma-separated list of allowed CORS origins for the frontend.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Ingestion ---
    # How often (seconds) the scheduler polls all sources for new jobs.
    ingest_interval_seconds: int = 900  # 15 minutes
    # Run one ingest pass on startup so the DB is never empty.
    ingest_on_startup: bool = True
    # Max jobs fetched per source per poll (safety cap).
    ingest_max_per_source: int = 500
    # Polite delay (seconds) between HTTP calls to the same host.
    ingest_request_delay: float = 0.5

    # --- AI ---
    # If set, AI-powered matching/enhancement/extraction is enabled.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"
    # Cap AI usage so a poll doesn't fan out into thousands of LLM calls.
    ai_match_max_jobs: int = 40

    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ai_enabled(self) -> bool:
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
