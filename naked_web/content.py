"""Convenience helpers to pull structured content from a snapshot."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .core.config import NakedWebConfig
from .core.models import (
    HeadingBlock,
    MetaTag,
    PageContentBundle,
    PageSnapshot,
)
from .pagination import get_html_chars, get_html_lines
from .scrape import fetch_page


def extract_content(
    snapshot: PageSnapshot,
    include_meta: bool = True,
    include_headings: bool = True,
    include_paragraphs: bool = True,
    include_inline_styles: bool = False,
    include_links: bool = True,
    max_headings: int = 200,
    max_paragraphs: int = 400,
    min_paragraph_chars: int = 20,
) -> PageContentBundle:
    soup = BeautifulSoup(snapshot.html, "lxml")

    meta: List[MetaTag] = []
    if include_meta:
        for tag in soup.find_all("meta"):
            meta.append(
                MetaTag(
                    name=tag.get("name"),
                    property=tag.get("property"),
                    content=tag.get("content"),
                )
            )

    headings: List[HeadingBlock] = []
    if include_headings:
        for level in range(1, 7):
            for tag in soup.find_all(f"h{level}"):
                text = tag.get_text(separator=" ", strip=True)
                if not text:
                    continue
                headings.append(HeadingBlock(level=f"h{level}", text=text))
                if len(headings) >= max_headings:
                    break
            if len(headings) >= max_headings:
                break

    paragraphs: List[str] = []
    if include_paragraphs:
        for tag in soup.find_all("p"):
            text = tag.get_text(separator=" ", strip=True)
            if len(text) < min_paragraph_chars:
                continue
            paragraphs.append(text)
            if len(paragraphs) >= max_paragraphs:
                break

    inline_styles: List[str] = []
    if include_inline_styles:
        for tag in soup.find_all("style"):
            content = tag.get_text("\n", strip=True)
            if content:
                inline_styles.append(content)

    bundle = PageContentBundle(
        title=soup.title.string.strip() if soup.title and soup.title.string else None,
        meta=meta,
        headings=headings,
        paragraphs=paragraphs,
        inline_styles=inline_styles,
        css_links=snapshot.assets.stylesheets,
        font_links=snapshot.assets.fonts,
        links=snapshot.assets.links if include_links else [],
    )
    return bundle


def _gather_line_chunks(snapshot: PageSnapshot, chunk: int, limit: Optional[int]) -> List[Dict[str, Any]]:
    start = 0
    chunks: List[Dict[str, Any]] = []
    while True:
        data = get_html_lines(snapshot, start_line=start, num_lines=chunk)
        if not data.get("content"):
            break
        chunks.append(data)
        if not data.get("has_more"):
            break
        if limit is not None and len(chunks) >= limit:
            break
        next_start = data.get("next_start")
        if next_start is None:
            break
        start = next_start
    return chunks


def _gather_char_chunks(snapshot: PageSnapshot, chunk: int, limit: Optional[int]) -> List[Dict[str, Any]]:
    start = 0
    chunks: List[Dict[str, Any]] = []
    while True:
        data = get_html_chars(snapshot, start=start, length=chunk)
        if not data.get("content"):
            break
        chunks.append(data)
        if not data.get("has_more"):
            break
        if limit is not None and len(chunks) >= limit:
            break
        next_start = data.get("next_start")
        if next_start is None:
            break
        start = next_start
    return chunks


def collect_page(
    url: str,
    cfg: Optional[NakedWebConfig] = None,
    use_js: bool = False,
    include_content_bundle: bool = True,
    include_line_chunks: bool = False,
    include_char_chunks: bool = False,
    line_chunk_size: int = 200,
    char_chunk_size: int = 5000,
    pagination_chunk_limit: Optional[int] = None,
    **content_kwargs,
) -> Dict[str, Any]:
    cfg = cfg or NakedWebConfig()
    snapshot = fetch_page(url, cfg=cfg, use_js=use_js)
    payload: Dict[str, Any] = {
        "snapshot": snapshot.to_dict(),
    }
    if include_content_bundle:
        bundle = extract_content(snapshot, **content_kwargs)
        payload["content"] = bundle.to_dict()
    if include_line_chunks:
        payload["line_chunks"] = _gather_line_chunks(snapshot, line_chunk_size, pagination_chunk_limit)
    if include_char_chunks:
        payload["char_chunks"] = _gather_char_chunks(snapshot, char_chunk_size, pagination_chunk_limit)
    return payload
