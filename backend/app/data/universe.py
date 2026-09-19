"""Universe access: returns instrument rows, live when possible else sample.

An instrument row: {symbol, name, sector, market_cap_cr, cap_class,
ret_1d, ret_1w, ret_1m, [last_price]}.
"""
from __future__ import annotations

from app.config import get_settings
from app.data.cache import cached
from app.data.sample_data import sample_universe


def _load() -> list[dict]:
    settings = get_settings()
    prov = settings.provider()
    base = sample_universe()

    if prov == "fmp":
        try:
            from app.data.live_providers import fmp_universe

            rows = fmp_universe()
            if rows:
                return rows
        except Exception:
            pass
    elif prov == "yfinance":
        try:
            from app.data.providers.yfinance_provider import enrich_universe

            live = enrich_universe(base)
            if live:
                return live
        except Exception:
            pass

    if not settings.allow_sample_fallback and prov != "sample":
        raise RuntimeError("live universe unavailable and sample fallback disabled")
    return base


def get_universe() -> list[dict]:
    ttl = get_settings().cache_ttl_seconds
    return cached("universe:v3", ttl, _load)


def sectors() -> list[str]:
    return sorted({r["sector"] for r in get_universe()})
