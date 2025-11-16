"""Live fetch test harness for Naked Web.

This script hits a real URL with and without the stealth Selenium renderer (if installed),
extracts structured content, and demonstrates pagination helpers.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from naked_web import NakedWebConfig, collect_page


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exercise Naked Web fetch helpers")
    parser.add_argument("url", help="URL to fetch", nargs="?", default="https://example.com")
    parser.add_argument(
        "--mode",
        choices=["plain", "js", "both"],
        default="both",
        help="plain=HTTP only, js=stealth Selenium only, both=run both passes",
    )
    parser.add_argument("--line-chunk", type=int, default=200, help="Lines per pagination chunk (0 to disable)")
    parser.add_argument("--char-chunk", type=int, default=5000, help="Chars per pagination chunk (0 to disable)")
    parser.add_argument("--pagination-limit", type=int, default=3, help="Max pagination chunks to capture (per mode)")
    parser.add_argument("--max-headings", type=int, default=50)
    parser.add_argument("--max-paragraphs", type=int, default=200)
    parser.add_argument("--min-paragraph-chars", type=int, default=20)
    parser.add_argument(
        "--inline-styles",
        action="store_true",
        help="Capture inline <style> blocks in the structured content bundle",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to dump the entire response as JSON",
    )
    return parser.parse_args()


def mode_to_flags(mode: str) -> List[bool]:
    if mode == "plain":
        return [False]
    if mode == "js":
        return [True]
    return [False, True]


def main() -> None:
    args = parse_args()
    cfg = NakedWebConfig()
    payloads = []

    include_line_chunks = args.line_chunk > 0
    include_char_chunks = args.char_chunk > 0

    for use_js in mode_to_flags(args.mode):
        try:
            bundle = collect_page(
                url=args.url,
                cfg=cfg,
                use_js=use_js,
                include_content_bundle=True,
                include_line_chunks=include_line_chunks,
                include_char_chunks=include_char_chunks,
                line_chunk_size=max(1, args.line_chunk or 1),
                char_chunk_size=max(1, args.char_chunk or 1),
                pagination_chunk_limit=args.pagination_limit if args.pagination_limit > 0 else None,
                include_inline_styles=args.inline_styles,
                max_headings=args.max_headings,
                max_paragraphs=args.max_paragraphs,
                min_paragraph_chars=args.min_paragraph_chars,
            )
        except RuntimeError as exc:
            if use_js:
                print("Skipping JS run:", exc)
                continue
            raise
        payloads.append(bundle)

        snapshot = bundle["snapshot"]
        content = bundle.get("content", {})
        print("=== JS enabled" if use_js else "=== Plain HTTP")
        print("Status:", snapshot.get("status_code"), "Final URL:", snapshot.get("final_url"))
        print("HTML length:", len(snapshot.get("html", "")))
        print(
            "Meta tags:", len(content.get("meta", [])),
            "Headings:", len(content.get("headings", [])),
            "Paragraphs:", len(content.get("paragraphs", [])),
        )
        print(
            "CSS links:", len(content.get("css_links", [])),
            "Font links:", len(content.get("font_links", [])),
            "Inline styles:", len(content.get("inline_styles", [])),
        )
        if include_line_chunks:
            print("Line pagination chunks:", len(bundle.get("line_chunks", [])))
        if include_char_chunks:
            print("Char pagination chunks:", len(bundle.get("char_chunks", [])))
        first_heading = content.get("headings", [])[:1]
        if first_heading:
            print("Sample heading:", first_heading[0])
        asset_sample = snapshot.get("assets", {}).get("image_details", [])[:1]
        if asset_sample:
            print("Sample image context:", asset_sample[0])
        print()

    if args.output:
        args.output.write_text(json.dumps(payloads, indent=2), encoding="utf-8")
        print("Saved full payload to", args.output)


if __name__ == "__main__":
    main()
