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
    signal_cache_ttl: int = 300          # per-symbol signal cache
    redis_url: Optional[str] = None      # e.g. redis://localhost:6379/0

    # --- Live data ---
    # OFF by default: use fast deterministic synthetic OHLCV (no network) so the
    # app is instant. Turn ON to fetch real quotes/history (yfinance/NSE).
    live_data: bool = False
    # Which market-data provider powers the universe/quotes/history:
    #   sample   -> bundled deterministic data (default, offline)
    #   fmp      -> Financial Modeling Prep REST (needs FMP_API_KEY; full NSE market)
    #   dhan     -> DhanHQ v2 (needs a demat account: DHAN_CLIENT_ID + DHAN_ACCESS_TOKEN)
    #               Live Market Feed + 20-level Full Depth (websocket) + Daily Historical
    #   yfinance -> Yahoo Finance per-symbol (needs a symbol universe; slower)
    data_provider: str = "sample"
    fmp_base_url: str = "https://financialmodelingprep.com/api/v3"
    # Max stocks to pull for the full-market universe (ranked by market cap).
    universe_limit: int = 750
    history_days: int = 400              # ~1 trading year+ retained per symbol
    # Directory to persist per-symbol OHLCV history as JSON (disk cache). When
    # set, history is read from disk first and only refreshed when stale.
    data_store_dir: Optional[str] = None
    # Max parallel workers for per-symbol computation.
    compute_workers: int = 8
    # Fetch live news from free RSS feeds + Finnhub (falls back to sample offline).
    news_live: bool = True

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
    fmp_api_key: Optional[str] = None        # Financial Modeling Prep (full NSE market)
    # --- DhanHQ v2 (live NSE/BSE via a demat account) ---
    dhan_client_id: Optional[str] = None
    dhan_access_token: Optional[str] = None
    dhan_base_url: str = "https://api.dhan.co/v2"
    dhan_scrip_master_url: str = "https://images.dhan.co/api-data/api-scrip-master.csv"
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

    def provider(self) -> str:
        """Effective data provider: explicit data_provider wins; else yfinance
        when live_data is on; else sample."""
        p = (self.data_provider or "sample").lower()
        if p != "sample":
            return p
        return "yfinance" if self.live_data else "sample"


@lru_cache
def get_settings() -> Settings:
    return Settings()
