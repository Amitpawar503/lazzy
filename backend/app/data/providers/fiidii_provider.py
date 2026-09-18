"""FII/DII flows + institutional holding-change data.

v1 uses bundled sample data. Live wiring (Phase 1 follow-up) can pull from:
  - NSE (https://www.nseindia.com/reports/fii-dii) — needs session cookies
  - Tapetide MCP `market_fii_dii_flows` (free tier: 50 calls/day → cache hard)
Both are behind `cached()` so we stay within rate limits.
"""
from __future__ import annotations

from app.config import get_settings
from app.data.cache import cached
from app.data.sample_data import sample_fii_dii, sample_holding_changes


def _load_flows() -> list[dict]:
    # TODO(phase1): try NSE / Tapetide here, then fall back.
    return sample_fii_dii()


def _load_holding_changes() -> list[dict]:
    # TODO(phase1): try Tapetide shareholding deltas here, then fall back.
    return sample_holding_changes()


def get_flows() -> list[dict]:
    ttl = get_settings().cache_ttl_seconds
    return cached("fiidii:flows:v1", ttl, _load_flows)


def get_holding_changes() -> list[dict]:
    ttl = get_settings().cache_ttl_seconds
    return cached("fiidii:holdings:v1", ttl, _load_holding_changes)
