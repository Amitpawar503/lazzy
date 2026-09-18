"""Provider shared helpers."""
from __future__ import annotations

# Map an API `timeframe` param to the return field on an instrument row.
TIMEFRAME_FIELD = {"1d": "ret_1d", "1w": "ret_1w", "1m": "ret_1m"}


def return_field(timeframe: str) -> str:
    return TIMEFRAME_FIELD.get(timeframe, "ret_1d")
