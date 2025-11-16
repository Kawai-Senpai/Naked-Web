"""Shared utility helpers for Naked Web."""

from .browser import simulate_human_scroll, wait_for_document_ready
from .text import clean_text_from_html, trim_text
from .timing import clamp_bounds, compute_delay, jitter_backoff, maybe_sleep

__all__ = [
    "clean_text_from_html",
    "trim_text",
    "wait_for_document_ready",
    "simulate_human_scroll",
    "maybe_sleep",
    "compute_delay",
    "clamp_bounds",
    "jitter_backoff",
]
