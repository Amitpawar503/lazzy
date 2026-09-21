"""Map internal bare symbols → Yahoo Finance tickers, and skip dead ones.

Yahoo uses the ``.NS`` suffix for NSE. A few internal names don't map 1:1
(ampersands, renamed/merged/delisted companies), so we keep a small override map
and a skip set. Skipped symbols quietly keep their bundled sample row instead of
spamming "possibly delisted" errors.
"""
from __future__ import annotations

import logging
from typing import Optional

# Internal symbol → correct Yahoo ticker suffix-less form (before adding .NS).
# Only needed where the bare symbol differs from Yahoo's.
_OVERRIDE: dict[str, str] = {
    # ampersands are preserved (M&M → M&M.NS) — handled below, not here
}

# Delisted / merged / no-longer-on-Yahoo → skip live fetch, keep sample data.
KNOWN_DELISTED: set[str] = {
    "SANGHIIND",   # merged into Ambuja Cements (2024)
    "DFMFOODS",    # delisted
    "SASTASUNDR",  # delisted
    "TAKE",        # Take Solutions — delisted
}


def quiet_yfinance_logging() -> None:
    """yfinance logs an ERROR per failed/delisted symbol, which floods the
    console. Raise its level so only real problems surface."""
    for name in ("yfinance", "yfinance.data", "yfinance.utils"):
        logging.getLogger(name).setLevel(logging.CRITICAL)


def yf_ticker(symbol: str) -> Optional[str]:
    """Return the Yahoo ticker for an internal symbol, or None to skip it.

    Preserves ``&`` (Yahoo uses e.g. ``M&M.NS``). Returns None for known-dead
    symbols so callers keep sample data without an error."""
    s = (symbol or "").upper().strip()
    if not s or s in KNOWN_DELISTED:
        return None
    base = _OVERRIDE.get(s, s)
    return f"{base}.NS"
