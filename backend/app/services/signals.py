"""Multi-algorithm signal consensus.

For each stock we run a panel of classic algorithms (from the reference repos:
vectorbt-skills, OpenAlgo ta, skill-algotrader). Each casts a vote:
  signal = +1 (bullish) / -1 (bearish) / 0 (neutral), plus a strength in 0..1.

We then report, per stock: how many algos are positive vs negative, and the net
conviction score (-100..+100). This powers the "in front of each stock, how many
algos are +ve / -ve and how much" screen.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.data.ohlcv import get_ohlcv
from app.data.universe import get_universe

# ------------------------------- indicators --------------------------------- #

def _sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d = s.diff()
    up = d.clip(lower=0).rolling(n).mean()
    dn = (-d.clip(upper=0)).rolling(n).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def _supertrend(df: pd.DataFrame, n: int = 10, mult: float = 3.0) -> pd.Series:
    hl2 = (df["high"] + df["low"]) / 2
    atr = _atr(df, n)
    upper = hl2 + mult * atr
    lower = hl2 - mult * atr
    close = df["close"].to_numpy(copy=True)
    up = upper.to_numpy(copy=True)
    lo = lower.to_numpy(copy=True)
    trend = np.ones(len(df))  # 1 = up, -1 = down
    for i in range(1, len(df)):
        if np.isnan(up[i]) or np.isnan(lo[i]):
            trend[i] = trend[i - 1]
            continue
        if close[i] > up[i - 1]:
            trend[i] = 1
        elif close[i] < lo[i - 1]:
            trend[i] = -1
        else:
            trend[i] = trend[i - 1]
            if trend[i] == 1:
                lo[i] = max(lo[i], lo[i - 1])
            else:
                up[i] = min(up[i], up[i - 1])
    return pd.Series(trend, index=df.index)


def _adx(df: pd.DataFrame, n: int = 14):
    h, l, c = df["high"], df["low"], df["close"]
    up = h.diff()
    dn = -l.diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([(h - l), (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / n, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1 / n, adjust=False).mean()
    return adx, plus_di, minus_di


def _last(s: pd.Series):
    s = s.dropna()
    return float(s.iloc[-1]) if len(s) else None


def _clip01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


# --------------------------------- algos ------------------------------------ #
# Each returns (signal, strength, detail).

def algo_sma_cross(df):
    fast, slow = _sma(df["close"], 20), _sma(df["close"], 50)
    f, s = _last(fast), _last(slow)
    if f is None or s is None:
        return 0, 0.0, "insufficient data"
    gap = (f - s) / s * 100
    sig = 1 if gap > 0 else -1 if gap < 0 else 0
    return sig, _clip01(abs(gap) / 5), f"SMA20 {'>' if gap>0 else '<'} SMA50 by {abs(gap):.1f}%"


def algo_ema_cross(df):
    fast, slow = _ema(df["close"], 12), _ema(df["close"], 26)
    f, s = _last(fast), _last(slow)
    if f is None or s is None:
        return 0, 0.0, "insufficient data"
    gap = (f - s) / s * 100
    sig = 1 if gap > 0 else -1 if gap < 0 else 0
    return sig, _clip01(abs(gap) / 4), f"EMA12 {'>' if gap>0 else '<'} EMA26 by {abs(gap):.1f}%"


def algo_rsi(df):
    r = _last(_rsi(df["close"], 14))
    if r is None:
        return 0, 0.0, "insufficient data"
    if r < 30:
        return 1, _clip01((30 - r) / 30), f"RSI {r:.0f} (oversold)"
    if r > 70:
        return -1, _clip01((r - 70) / 30), f"RSI {r:.0f} (overbought)"
    # mild momentum bias around 50
    sig = 1 if r > 55 else -1 if r < 45 else 0
    return sig, _clip01(abs(r - 50) / 50), f"RSI {r:.0f}"


def algo_macd(df):
    macd = _ema(df["close"], 12) - _ema(df["close"], 26)
    signal = _ema(macd, 9)
    hist = macd - signal
    h = _last(hist)
    if h is None:
        return 0, 0.0, "insufficient data"
    px = _last(df["close"]) or 1
    sig = 1 if h > 0 else -1 if h < 0 else 0
    return sig, _clip01(abs(h) / (px * 0.02)), f"MACD hist {h:+.2f}"


def algo_supertrend(df):
    t = _last(_supertrend(df))
    if t is None:
        return 0, 0.0, "insufficient data"
    return int(t), 0.8, f"Supertrend {'up' if t > 0 else 'down'}"


def algo_bollinger(df):
    mid = _sma(df["close"], 20)
    std = df["close"].rolling(20).std()
    upper, lower = mid + 2 * std, mid - 2 * std
    c, u, lo, m = _last(df["close"]), _last(upper), _last(lower), _last(mid)
    if None in (c, u, lo, m):
        return 0, 0.0, "insufficient data"
    if c < lo:
        return 1, _clip01((lo - c) / (m - lo + 1e-9)), "below lower band (mean-revert up)"
    if c > u:
        return -1, _clip01((c - u) / (u - m + 1e-9)), "above upper band (mean-revert down)"
    return 0, 0.1, "within bands"


def algo_roc(df):
    c = df["close"]
    if len(c) < 13:
        return 0, 0.0, "insufficient data"
    roc = (c.iloc[-1] / c.iloc[-13] - 1) * 100
    sig = 1 if roc > 0 else -1 if roc < 0 else 0
    return sig, _clip01(abs(roc) / 10), f"12-day ROC {roc:+.1f}%"


def algo_adx(df):
    adx, pdi, mdi = _adx(df)
    a, p, m = _last(adx), _last(pdi), _last(mdi)
    if None in (a, p, m):
        return 0, 0.0, "insufficient data"
    if a < 20:
        return 0, 0.1, f"ADX {a:.0f} (no trend)"
    sig = 1 if p > m else -1
    return sig, _clip01(a / 50), f"ADX {a:.0f}, {'+DI>-DI' if p>m else '-DI>+DI'}"


def algo_donchian(df):
    hi = df["high"].rolling(20).max()
    lo = df["low"].rolling(20).min()
    c, h20, l20 = _last(df["close"]), _last(hi), _last(lo)
    if None in (c, h20, l20):
        return 0, 0.0, "insufficient data"
    rng = h20 - l20 + 1e-9
    pos = (c - l20) / rng
    if pos > 0.9:
        return 1, _clip01((pos - 0.9) / 0.1), "near 20d high (breakout)"
    if pos < 0.1:
        return -1, _clip01((0.1 - pos) / 0.1), "near 20d low (breakdown)"
    return 0, 0.1, f"mid-range ({pos*100:.0f}%)"


def algo_stochastic(df):
    low = df["low"].rolling(14).min()
    high = df["high"].rolling(14).max()
    k = 100 * (df["close"] - low) / (high - low).replace(0, np.nan)
    kv = _last(k.rolling(3).mean())
    if kv is None:
        return 0, 0.0, "insufficient data"
    if kv < 20:
        return 1, _clip01((20 - kv) / 20), f"%K {kv:.0f} (oversold)"
    if kv > 80:
        return -1, _clip01((kv - 80) / 20), f"%K {kv:.0f} (overbought)"
    return 0, 0.1, f"%K {kv:.0f}"


ALGOS = [
    ("SMA Crossover", algo_sma_cross),
    ("EMA Crossover", algo_ema_cross),
    ("RSI", algo_rsi),
    ("MACD", algo_macd),
    ("Supertrend", algo_supertrend),
    ("Bollinger Bands", algo_bollinger),
    ("Momentum (ROC)", algo_roc),
    ("ADX / DI", algo_adx),
    ("Donchian Breakout", algo_donchian),
    ("Stochastic", algo_stochastic),
]


# --------------------------------- scoring ---------------------------------- #

def compute_signals(symbol: str, drift_hint: float = 0.0) -> dict:
    df = get_ohlcv(symbol, drift_hint=drift_hint)
    results = []
    for name, fn in ALGOS:
        try:
            sig, strength, detail = fn(df)
        except Exception as e:  # never let one algo break the row
            sig, strength, detail = 0, 0.0, f"error: {e}"
        results.append(
            {"algo": name, "signal": int(sig),
             "strength": round(float(strength), 3), "detail": detail}
        )
    total = len(results)
    bullish = sum(1 for r in results if r["signal"] > 0)
    bearish = sum(1 for r in results if r["signal"] < 0)
    neutral = total - bullish - bearish
    net_score = round(
        100 * sum(r["signal"] * r["strength"] for r in results) / total, 1
    )
    if net_score >= 40:
        verdict = "Strong Buy"
    elif net_score >= 10:
        verdict = "Buy"
    elif net_score <= -40:
        verdict = "Strong Sell"
    elif net_score <= -10:
        verdict = "Sell"
    else:
        verdict = "Neutral"
    return {
        "symbol": symbol,
        "total_algos": total,
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral,
        "net_score": net_score,     # -100..+100
        "verdict": verdict,
        "algos": results,
    }


def scorecard(top_n: int = 20, view: str = "all", sort: str = "score") -> dict:
    uni = get_universe()
    rows = []
    for r in uni:
        res = compute_signals(r["symbol"], drift_hint=r.get("ret_1m", 0.0))
        rows.append(
            {
                "symbol": r["symbol"],
                "name": r["name"],
                "sector": r["sector"],
                "cap_class": r["cap_class"],
                "bullish": res["bullish"],
                "bearish": res["bearish"],
                "neutral": res["neutral"],
                "total_algos": res["total_algos"],
                "net_score": res["net_score"],
                "verdict": res["verdict"],
            }
        )
    if view == "bullish":
        rows = [r for r in rows if r["net_score"] > 0]
    elif view == "bearish":
        rows = [r for r in rows if r["net_score"] < 0]

    if sort == "bullish":
        rows.sort(key=lambda r: (r["bullish"], r["net_score"]), reverse=True)
    elif sort == "bearish":
        rows.sort(key=lambda r: (r["bearish"], -r["net_score"]), reverse=True)
    else:  # score
        rows.sort(key=lambda r: r["net_score"], reverse=True)

    return {
        "algos": [name for name, _ in ALGOS],
        "count": min(len(rows), max(1, top_n)),
        "rows": rows[: max(1, top_n)],
    }
