"""Shared utility helpers for Naked Web."""

from .browser import simulate_human_scroll, wait_for_document_ready
from .profiles import copy_profile_tree, get_default_playwright_profile_path
from .text import clean_text_from_html, trim_text
from .timing import clamp_bounds, compute_delay, jitter_backoff, maybe_sleep

# Optional stealth imports - only available if selenium is installed
try:
    from .stealth import (
        fetch_with_stealth,
        inject_stealth_scripts,
        random_mouse_movement,
        random_scroll_pattern,
        setup_stealth_driver,
    )
    _STEALTH_AVAILABLE = True
except ImportError:
    _STEALTH_AVAILABLE = False
    fetch_with_stealth = None
    inject_stealth_scripts = None
    random_mouse_movement = None
    random_scroll_pattern = None
    setup_stealth_driver = None

__all__ = [
    "clean_text_from_html",
    "trim_text",
    "wait_for_document_ready",
    "simulate_human_scroll",
    "copy_profile_tree",
    "get_default_playwright_profile_path",
    "maybe_sleep",
    "compute_delay",
    "clamp_bounds",
    "jitter_backoff",
    # Stealth exports (may be None if selenium not installed)
    "fetch_with_stealth",
    "inject_stealth_scripts",
    "random_mouse_movement",
    "random_scroll_pattern",
    "setup_stealth_driver",
]
