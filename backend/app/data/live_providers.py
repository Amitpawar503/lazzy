"""Live market-data providers (real data for the complete NSE market).

Providers, selected by `DATA_PROVIDER`:
  - fmp      : Financial Modeling Prep REST (needs FMP_API_KEY). Full NSE universe
               via the stock screener + full-exchange quotes; EOD history per symbol.
  - yfinance : Yahoo Finance per symbol (history/quote); universe still needs a
               symbol list (falls back to the bundled one).

Everything is best-effort and falls back to bundled sample data so the app never
breaks. NOTE: this sandbox blocks outbound finance hosts, so live fetching is
exercised on the user's machine; the code paths degrade cleanly here.

Internal symbols are bare (e.g. RELIANCE); FMP/yfinance use the `.NS` suffix.
"""
from __future__ import annotations

import httpx

from app.config import get_settings
from app.data.sample_data import cap_class

_TIMEOUT = 20.0


def _fmp_get(path: str, params: dict) -> list | dict | None:
    s = get_settings()
    if not s.fmp_api_key:
        return None
    params = {**params, "apikey": s.fmp_api_key}
    try:
        r = httpx.get(f"{s.fmp_base_url}{path}", params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def fmp_universe() -> list[dict] | None:
    """Full NSE universe via the FMP stock screener (sector + market cap) merged
    with full-exchange quotes (1-day change). Returns instrument rows or None."""
    s = get_settings()
    screener = _fmp_get("/stock-screener", {
        "exchange": "NSE", "isActivelyTrading": "true",
        "limit": max(50, s.universe_limit),
    })
    if not isinstance(screener, list) or not screener:
        return None

    # 1-day change % for the whole exchange (one call).
    quotes = _fmp_get("/quotes/NSE", {})
    chg = {}
    if isinstance(quotes, list):
        for q in quotes:
            sym = (q.get("symbol") or "").removesuffix(".NS")
            chg[sym] = q.get("changesPercentage") or 0.0

    rows = []
    for c in screener:
        fsym = c.get("symbol") or ""
        sym = fsym.removesuffix(".NS")
        mcap_abs = c.get("marketCap") or 0
        mcap_cr = round(mcap_abs / 1e7, 0)  # INR -> ₹ crore
        rows.append({
            "symbol": sym,
            "name": c.get("companyName") or sym,
            "sector": c.get("sector") or "—",
            "market_cap_cr": mcap_cr,
            "cap_class": cap_class(mcap_cr),
            "ret_1d": round(float(chg.get(sym, 0.0)), 2),
            "ret_1w": 0.0,   # filled lazily from history when a screen needs it
            "ret_1m": 0.0,
            "last_price": c.get("price"),
        })
    rows = [r for r in rows if r["market_cap_cr"] > 0]
    rows.sort(key=lambda r: r["market_cap_cr"], reverse=True)
    return rows[: s.universe_limit] or None


def fmp_history(symbol: str, days: int) -> list[dict] | None:
    """EOD OHLCV for a symbol as chronological records, or None."""
    data = _fmp_get(f"/historical-price-full/{symbol}.NS", {"timeseries": days})
    hist = data.get("historical") if isinstance(data, dict) else None
    if not hist:
        return None
    recs = [{
        "date": h["date"], "open": h.get("open"), "high": h.get("high"),
        "low": h.get("low"), "close": h.get("close"), "volume": h.get("volume") or 0,
    } for h in hist if h.get("close") is not None]
    recs.reverse()  # FMP returns newest-first
    return recs or None


def fmp_quote(symbol: str) -> dict | None:
    data = _fmp_get(f"/quote/{symbol}.NS", {})
    if isinstance(data, list) and data:
        q = data[0]
        return {"price": q.get("price"), "change_pct": q.get("changesPercentage"),
                "prev_close": q.get("previousClose")}
    return None
