"""Core primitives (config + models) for Naked Web."""

from .config import NakedWebConfig
from .models import (
    AssetContext,
    CharSlice,
    HeadingBlock,
    LineSlice,
    MetaTag,
    PageAssets,
    PageContentBundle,
    PageSnapshot,
    SearchResult,
)

__all__ = [
    "NakedWebConfig",
    "SearchResult",
    "AssetContext",
    "PageAssets",
    "PageSnapshot",
    "LineSlice",
    "CharSlice",
    "MetaTag",
    "HeadingBlock",
    "PageContentBundle",
]