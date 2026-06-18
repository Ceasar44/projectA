from datetime import datetime
from typing import Any


def isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def count_attr(value: Any) -> int:
    if value is None:
        return 0
    try:
        return len(value)
    except TypeError:
        return 0
