"""Universe access: returns instrument rows, live when possible else sample.

An instrument row: {symbol, name, sector, market_cap_cr, cap_class,
ret_1d, ret_1w, ret_1m, [last_price]}.
"""
from __future__ import annotations

from app.config import get_settings
from app.data.cache import cached
from app.data.sample_data import sample_universe


def _provider_universe(prov: str, base: list[dict]) -> list[dict] | None:
    """Build the universe from one named provider, or None on failure."""
    try:
        if prov == "fmp":
            from app.data.live_providers import fmp_universe
            return fmp_universe()
        if prov == "dhan":
            from app.data.dhan_provider import dhan_universe
            return dhan_universe()
        if prov == "yfinance":
            from app.data.providers.yfinance_provider import enrich_universe
            return enrich_universe(base)
    except Exception:
        return None
    return None


def _load() -> list[dict]:
    settings = get_settings()
    base = sample_universe()

    # Try the effective provider, then the configured free fallback (e.g. Dhan
    # not subscribed → yfinance), then sample.
    tried: list[str] = []
    for prov in (settings.provider(), settings.data_provider_fallback):
        p = (prov or "").lower()
        if not p or p == "sample" or p in tried:
            continue
        tried.append(p)
        rows = _provider_universe(p, base)
        if rows:
            return rows

    if not settings.allow_sample_fallback and settings.provider() != "sample":
        raise RuntimeError("live universe unavailable and sample fallback disabled")
    return base


def get_universe() -> list[dict]:
    ttl = get_settings().cache_ttl_seconds
    return cached("universe:v3", ttl, _load)


def sectors() -> list[str]:
    return sorted({r["sector"] for r in get_universe()})
