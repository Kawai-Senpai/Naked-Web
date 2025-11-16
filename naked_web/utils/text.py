"""Text and HTML cleanup helpers."""

from __future__ import annotations

import re
from typing import Optional

from bs4 import BeautifulSoup

__all__ = ["clean_text_from_html", "trim_text"]


def clean_text_from_html(html: str, max_chars: Optional[int]) -> str:
    """Strip scripts/styles, collapse whitespace, and clamp length."""

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    if max_chars and len(text) > max_chars:
        return text[:max_chars] + "..."
    return text


def trim_text(value: Optional[str], limit: int = 200) -> Optional[str]:
    """Normalize whitespace and trim to the requested limit."""

    if not value:
        return None
    text = re.sub(r"\s+", " ", value).strip()
    if not text:
        return None
    if len(text) > limit:
        return text[:limit] + "..."
    return text
