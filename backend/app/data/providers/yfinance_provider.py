"""Live enrichment via yfinance (delayed quotes). Best-effort, never fatal.

Given a list of universe rows (with symbol/sector), fetch current price, market
cap, and 1d/1w/1m returns. Any failure returns None so callers fall back to the
bundled sample data. NSE symbols use the `.NS` suffix.
"""
from __future__ import annotations

from app.data.sample_data import cap_class


def enrich_universe(rows: list[dict]) -> list[dict] | None:
    try:
        import yfinance as yf  # type: ignore
        import pandas as pd  # noqa: F401
    except Exception:
        return None

    symbols = [f"{r['symbol'].replace('&', '')}.NS" for r in rows]
    try:
        data = yf.download(
            symbols, period="1mo", interval="1d", group_by="ticker",
            auto_adjust=True, progress=False, threads=True,
        )
    except Exception:
        return None
    if data is None or len(data) == 0:
        return None

    out: list[dict] = []
    for r in rows:
        yf_sym = f"{r['symbol'].replace('&', '')}.NS"
        try:
            close = data[yf_sym]["Close"].dropna()
            if len(close) < 2:
                raise ValueError("insufficient history")
            last = float(close.iloc[-1])
            ret_1d = (last / float(close.iloc[-2]) - 1) * 100
            ret_1w = (last / float(close.iloc[-min(6, len(close))]) - 1) * 100
            ret_1m = (last / float(close.iloc[0]) - 1) * 100
            # market cap: keep sample value (yfinance mcap needs per-ticker calls)
            mcap = r.get("market_cap_cr", 0)
            out.append({
                **r,
                "market_cap_cr": mcap,
                "cap_class": cap_class(mcap),
                "ret_1d": round(ret_1d, 2),
                "ret_1w": round(ret_1w, 2),
                "ret_1m": round(ret_1m, 2),
                "last_price": round(last, 2),
            })
        except Exception:
            out.append(r)  # keep sample row for this symbol
    return out
