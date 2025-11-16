"""Browser automation helpers that keep Selenium interactions human-like."""

from __future__ import annotations

import random
from typing import Any, Tuple

from .timing import clamp_bounds

__all__ = ["simulate_human_scroll", "wait_for_document_ready"]


def wait_for_document_ready(driver: Any, timeout: int) -> None:
    """Block until `document.readyState === complete` using Selenium waits."""

    try:
        from selenium.webdriver.support.ui import WebDriverWait
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Selenium is required for wait_for_document_ready") from exc

    WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")


def simulate_human_scroll(driver: Any, fraction_bounds: Tuple[float, float] = (0.2, 0.6)) -> None:
    """Scroll the page to a random fraction of the total height."""

    low, high = clamp_bounds(fraction_bounds)
    if high <= 0:
        return
    target = random.uniform(low, min(high, 1.0))
    driver.execute_script(
        "window.scrollTo(0, Math.floor(document.body.scrollHeight * arguments[0]));",
        target,
    )
