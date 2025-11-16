"""Simple crawling utilities that feed higher level automation."""

from __future__ import annotations

import fnmatch
import re
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

from .core.config import NakedWebConfig
from .core.models import AssetContext, PageSnapshot
from .scrape import fetch_page
from .utils.timing import clamp_bounds, maybe_sleep


def crawl_site(
    start_url: str,
    cfg: Optional[NakedWebConfig] = None,
    max_pages: int = 20,
    same_domain_only: bool = True,
    use_js: bool = False,
    max_depth: Optional[int] = 3,
    max_duration: Optional[float] = None,
    delay_range: Optional[Tuple[float, float]] = None,
) -> Dict[str, PageSnapshot]:
    """Breadth-first crawler with depth, duration, and throttle controls."""

    cfg = cfg or NakedWebConfig()
    visited: Dict[str, PageSnapshot] = {}
    queue: Deque[Tuple[str, int]] = deque([(start_url, 0)])
    origin = urlparse(start_url).netloc
    start_time = time.monotonic()
    raw_delay = delay_range if delay_range is not None else cfg.crawl_delay_range
    effective_delay = clamp_bounds(raw_delay)

    while queue and len(visited) < max_pages:
        if max_duration is not None and (time.monotonic() - start_time) > max_duration:
            break

        url, depth = queue.popleft()
        if url in visited or (max_depth is not None and depth > max_depth):
            continue

        if (len(visited) > 0) and (effective_delay[1] > 0):
            maybe_sleep(effective_delay)

        snap = fetch_page(url, cfg=cfg, use_js=use_js)
        visited[url] = snap

        if snap.error or not snap.assets.links:
            continue

        if max_depth is not None and depth >= max_depth:
            continue

        for link in snap.assets.links:
            parsed = urlparse(link)
            if same_domain_only and parsed.netloc and parsed.netloc != origin:
                continue
            if parsed.scheme not in ("http", "https", ""):
                continue
            if link in visited:
                continue
            if any(link == queued_url for queued_url, _ in queue):
                continue
            queue.append((link, depth + 1))

    return visited


def _compile_patterns(patterns: Sequence[str], use_regex: bool) -> List[Tuple[str, re.Pattern[str]]]:
    compiled: List[Tuple[str, re.Pattern[str]]] = []
    for pattern in patterns:
        if not pattern:
            continue
        regex = re.compile(pattern, re.IGNORECASE) if use_regex else re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        compiled.append((pattern, regex))
    return compiled


def _window(text: str, start: int, end: int, context_chars: int) -> str:
    if context_chars <= 0:
        return text[start:end]
    left = max(0, start - context_chars)
    right = min(len(text), end + context_chars)
    snippet = text[left:right]
    return re.sub(r"\s+", " ", snippet).strip()


def find_text_matches(
    pages: Dict[str, PageSnapshot],
    patterns: Sequence[str],
    *,
    use_regex: bool = False,
    context_chars: int = 120,
    target: str = "text",
) -> Dict[str, List[Dict[str, Any]]]:
    """Scan crawled pages for pattern hits with contextual windows."""

    compiled = _compile_patterns(patterns, use_regex)
    if not compiled:
        return {}

    target = target.lower()
    if target not in {"text", "html"}:
        raise ValueError("target must be either 'text' or 'html'")

    results: Dict[str, List[Dict[str, Any]]] = {}
    for url, snapshot in pages.items():
        haystack = snapshot.text if target == "text" else snapshot.html
        if not haystack:
            continue
        matches: List[Dict[str, Any]] = []
        for source, regex in compiled:
            for match in regex.finditer(haystack):
                matches.append(
                    {
                        "pattern": source,
                        "match": match.group(0),
                        "context": _window(haystack, match.start(), match.end(), context_chars),
                        "start": match.start(),
                        "end": match.end(),
                        "target": target,
                    }
                )
        if matches:
            results[url] = matches
    return results


def _clip(value: Optional[str], limit: int) -> Optional[str]:
    if not value:
        return None
    text = re.sub(r"\s+", " ", value).strip()
    if not text:
        return None
    if limit > 0 and len(text) > limit:
        return text[:limit] + "..."
    return text


_ASSET_DETAIL_ATTRS = {
    "stylesheets": "stylesheet_details",
    "scripts": "script_details",
    "images": "image_details",
    "media": "media_details",
    "fonts": "font_details",
    "links": "link_details",
}


def find_asset_matches(
    pages: Dict[str, PageSnapshot],
    patterns: Sequence[str],
    *,
    use_regex: bool = False,
    asset_types: Optional[Sequence[str]] = None,
    context_chars: int = 160,
) -> Dict[str, List[Dict[str, Any]]]:
    """Filter asset/link contexts across crawled pages using glob/regex patterns."""

    compiled = _compile_patterns(patterns, use_regex)
    if not compiled:
        return {}

    target_types = asset_types or list(_ASSET_DETAIL_ATTRS.keys())
    filtered_types = [name for name in target_types if name in _ASSET_DETAIL_ATTRS]
    if not filtered_types:
        return {}

    results: Dict[str, List[Dict[str, Any]]] = {}
    for url, snapshot in pages.items():
        matches: List[Dict[str, Any]] = []
        for asset_type in filtered_types:
            detail_attr = _ASSET_DETAIL_ATTRS[asset_type]
            details: Sequence[AssetContext] = getattr(snapshot.assets, detail_attr, [])
            for ctx in details:
                ctx_dict = ctx.model_dump()
                candidates = [
                    ("url", ctx_dict.get("url")),
                    ("text", ctx_dict.get("text")),
                    ("context", ctx_dict.get("context")),
                    ("snippet", ctx_dict.get("snippet")),
                    ("alt", ctx_dict.get("alt")),
                    ("caption", ctx_dict.get("caption")),
                ]
                for field_name, value in candidates:
                    if not value:
                        continue
                    for source, regex in compiled:
                        if regex.search(value):
                            ctx_dict["context"] = _clip(ctx_dict.get("context"), context_chars)
                            ctx_dict["snippet"] = _clip(ctx_dict.get("snippet"), context_chars)
                            matches.append(
                                {
                                    "pattern": source,
                                    "asset_type": asset_type,
                                    "field": field_name,
                                    "value": value,
                                    "asset": ctx_dict,
                                }
                            )
                            break
                    else:
                        continue
                    break
        if matches:
            results[url] = matches
    return results
