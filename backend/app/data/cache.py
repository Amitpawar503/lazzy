"""Tiny TTL cache. Uses Redis when configured, else an in-process dict.

Keeps us polite to rate-limited sources (NSE, Tapetide free tier = 50/day).
"""
from __future__ import annotations

import json
import time
from typing import Any, Callable

from app.config import get_settings

_mem: dict[str, tuple[float, Any]] = {}
_redis = None


def _get_redis():
    global _redis
    if _redis is not None:
        return _redis
    url = get_settings().redis_url
    if not url:
        return None
    try:
        import redis  # type: ignore

        _redis = redis.Redis.from_url(url, decode_responses=True)
        _redis.ping()
        return _redis
    except Exception:
        return None


def cached(key: str, ttl: int, producer: Callable[[], Any]) -> Any:
    """Return cached value for `key` or compute + store it with `ttl` seconds."""
    r = _get_redis()
    if r is not None:
        try:
            hit = r.get(key)
            if hit is not None:
                return json.loads(hit)
        except Exception:
            pass
        value = producer()
        try:
            r.setex(key, ttl, json.dumps(value, default=str))
        except Exception:
            pass
        return value

    # in-memory fallback
    now = time.time()
    entry = _mem.get(key)
    if entry and entry[0] > now:
        return entry[1]
    value = producer()
    _mem[key] = (now + ttl, value)
    return value
