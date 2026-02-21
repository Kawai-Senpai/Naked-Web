"""
Web automation module for NakedWeb.

Provides Playwright-based browser automation with DOM state extraction,
interactive element indexing, and action execution - no vision needed.

Requires the `playwright` optional dependency:
    pip install naked-web[automation]
    playwright install chromium

Usage::

    from naked_web.automation import AutoBrowser

    browser = AutoBrowser(headless=True)
    browser.launch()
    browser.navigate("https://example.com")

    # Get interactive elements with indices
    state = browser.get_state()
    print(state.to_text())

    # Click element by index
    browser.click(1)

    # Type into input
    browser.type_text(2, "hello world")

    # Extract page content
    result = browser.extract_content()
    print(result.extracted_content)

    browser.close()
"""

from .browser import AutoBrowser
from .models import ActionResult, InteractiveElement, PageState, TabInfo

__all__ = [
    "AutoBrowser",
    "ActionResult",
    "InteractiveElement",
    "PageState",
    "TabInfo",
]
