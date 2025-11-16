"""Timing and throttling helpers shared across the toolkit."""

from __future__ import annotations

import random
import time
from typing import Tuple

__all__ = [
    "clamp_bounds",
    "compute_delay",
    "jitter_backoff",
    "maybe_sleep",
]


def clamp_bounds(bounds: Tuple[float, float]) -> Tuple[float, float]:
    """Normalize a `(low, high)` tuple ensuring sane, non-negative values."""

    low, high = bounds
    if high < low:
        low, high = high, low
    low = max(0.0, low)
    high = max(low, high)
    return low, high


def compute_delay(bounds: Tuple[float, float]) -> float:
    """Compute a randomized delay duration within the supplied bounds."""

    low, high = clamp_bounds(bounds)
    if high <= 0:
        return 0.0
    if low == high:
        return low
    return random.uniform(low, high)


def maybe_sleep(bounds: Tuple[float, float]) -> float:
    """Sleep for a randomized duration, returning the actual delay used."""

    duration = compute_delay(bounds)
    if duration <= 0:
        return 0.0
    time.sleep(duration)
    return duration


def jitter_backoff(attempt: int, base: float = 0.5, max_delay: float = 5.0) -> float:
    """Return an exponential backoff delay with jitter for retries."""

    attempt = max(0, attempt)
    delay = min(max_delay, base * (2 ** attempt))
    jitter = random.uniform(0, delay * 0.25)
    return min(max_delay, delay + jitter)
