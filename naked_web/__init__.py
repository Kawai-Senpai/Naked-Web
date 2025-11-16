"""Public API surface for Naked Web."""

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

__all__ = [
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
]
