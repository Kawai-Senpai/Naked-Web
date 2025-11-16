"""Minimal smoke test for pagination helpers and live fetching.

The script now fetches a real page (defaults to https://www.google.com, but
override with the first CLI arg or NAKED_WEB_SMOKE_URL) before running parsing
helpers. If the live fetch fails, a synthetic HTML payload is used as backup.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from naked_web import (
    NakedWebConfig,
    extract_content,
    fetch_page,
    get_html_chars,
    get_html_lines,
    slice_text_chars,
    slice_text_lines,
)
from naked_web.core.models import PageAssets, PageSnapshot


DEFAULT_URL = os.getenv("NAKED_WEB_SMOKE_URL", "https://www.google.com")


def build_snapshot(html: str) -> PageSnapshot:
    return PageSnapshot(
        url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        headers={"content-type": "text/html"},
        html=html,
        text=html,
        assets=PageAssets(),
        js_rendered=False,
        timestamp=0.0,
    )


def main() -> None:
    target_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL

    try:
        live_snap = fetch_page(target_url, cfg=NakedWebConfig(), use_js=False)
        if live_snap.error:
            raise RuntimeError(live_snap.error)
        snap = live_snap
        print(
            f"Live fetch OK: {target_url} -> status {snap.status_code} (final={snap.final_url})"
        )
    except Exception as exc:
        print(f"Live fetch failed ({exc}); falling back to synthetic HTML.")
        html = "\n".join(f"<p>Line {idx}</p>" for idx in range(1, 21))
        snap = build_snapshot(html)

    lines_slice = get_html_lines(snap, start_line=5, num_lines=5)
    chars_slice = get_html_chars(snap, start=0, length=120)
    text_lines = slice_text_lines(snap.html, start_line=0, num_lines=3)
    text_chars = slice_text_chars(snap.html, start=50, length=80)
    content_bundle = extract_content(snap, include_inline_styles=True)

    print("HTML lines slice:", lines_slice)
    print("HTML chars slice:", chars_slice)
    print("Text lines slice:", text_lines)
    print("Text chars slice:", text_chars)
    print("Headings extracted:", [h.model_dump() for h in content_bundle.headings][:5])


if __name__ == "__main__":
    main()
