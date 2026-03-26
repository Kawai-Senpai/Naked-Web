"""Public API surface for Naked Web."""

__version__ = "1.3.1a0"

from .core.config import NakedWebConfig
from .content import collect_page, extract_content
from .crawler import crawl_site, find_asset_matches, find_text_matches
from .pagination import (
    get_html_chars,
    get_html_lines,
    slice_text_chars,
    slice_text_lines,
)
from .scrape import download_assets, fetch_page
from .search import SearchClient
from .core.models import PageContentBundle, HeadingBlock, MetaTag

# Stealth functions now come from utils
from .utils import (
    copy_profile_tree,
    fetch_with_stealth,
    get_default_playwright_profile_path,
    inject_stealth_scripts,
    random_mouse_movement,
    random_scroll_pattern,
    setup_stealth_driver,
)

# Optional automation module (requires playwright)
try:
    from .automation import AutoBrowser, ActionResult as BrowserActionResult, PageState, InteractiveElement, TabInfo
    _AUTOMATION_AVAILABLE = True
except ImportError:
    AutoBrowser = None  # type: ignore
    BrowserActionResult = None  # type: ignore
    PageState = None  # type: ignore
    InteractiveElement = None  # type: ignore
    TabInfo = None  # type: ignore
    _AUTOMATION_AVAILABLE = False

__all__ = [
    "__version__",
    "NakedWebConfig",
    "SearchClient",
    "fetch_page",
    "download_assets",
    "extract_content",
    "collect_page",
    "crawl_site",
    "find_text_matches",
    "find_asset_matches",
    "get_html_lines",
    "get_html_chars",
    "slice_text_lines",
    "slice_text_chars",
    "PageContentBundle",
    "MetaTag",
    "HeadingBlock",
    # Stealth exports (may be None if selenium not installed)
    "copy_profile_tree",
    "fetch_with_stealth",
    "get_default_playwright_profile_path",
    "inject_stealth_scripts",
    "random_mouse_movement",
    "random_scroll_pattern",
    "setup_stealth_driver",
    # Automation exports (may be None if playwright not installed)
    "AutoBrowser",
    "BrowserActionResult",
    "PageState",
    "InteractiveElement",
    "TabInfo",
]
