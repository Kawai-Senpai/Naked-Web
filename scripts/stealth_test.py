"""Test the stealth fetcher against a bot-detection challenge.

This script validates the enhanced stealth measures by attempting
to fetch pages with known bot detection systems.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from naked_web import NakedWebConfig

try:
    from naked_web.utils.stealth import fetch_with_stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test stealth fetcher against bot detection")
    parser.add_argument(
        "url",
        nargs="?",
        default="https://www.reddit.com/r/Python/comments/umpgn2/web_scraping_using_selenium_python/",
        help="URL to test (defaults to Reddit thread with bot detection)",
    )
    parser.add_argument(
        "--no-mouse",
        action="store_true",
        help="Disable mouse movement simulation",
    )
    parser.add_argument(
        "--no-scroll",
        action="store_true",
        help="Disable realistic scrolling",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Save fetched HTML to file",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (less recommended for anti-detection)",
    )
    return parser.parse_args()


def main() -> None:
    if not STEALTH_AVAILABLE:
        print("Error: Stealth module requires selenium extras.")
        print("Install with: pip install -e .[selenium]")
        sys.exit(1)
    
    args = parse_args()
    
    cfg = NakedWebConfig(
        selenium_headless=args.headless,
        selenium_window_size="1920,1080",
        selenium_page_load_timeout=45,
        selenium_wait_timeout=20,
        humanize_delay_range=(1.5, 3.5),
    )
    
    print(f"Testing stealth fetcher on: {args.url}")
    print(f"Headless mode: {args.headless}")
    print(f"Mouse movements: {not args.no_mouse}")
    print(f"Realistic scrolling: {not args.no_scroll}")
    print()
    
    try:
        html, headers, status_code, final_url = fetch_with_stealth(
            args.url,
            cfg=cfg,
            perform_mouse_movements=not args.no_mouse,
            perform_realistic_scrolling=not args.no_scroll,
        )
        
        print(f"✓ Fetch successful!")
        print(f"  Status: {status_code}")
        print(f"  Final URL: {final_url}")
        print(f"  HTML length: {len(html):,} chars")
        print()
        
        # Check for common bot detection indicators
        bot_indicators = [
            ("Prove your humanity", "Reddit bot challenge"),
            ("Access Denied", "Generic access block"),
            ("Checking your browser", "Cloudflare check"),
            ("Challenge page", "reCAPTCHA or similar"),
            ("Please verify you are a human", "CAPTCHA challenge"),
        ]
        
        detected = False
        for indicator, description in bot_indicators:
            if indicator.lower() in html.lower():
                print(f"⚠ Bot detection indicator found: {description}")
                print(f"   Search term: '{indicator}'")
                detected = True
        
        if not detected:
            print("✓ No obvious bot detection indicators found!")
            print("  Content appears to have loaded successfully.")
        
        print()
        
        # Show snippet of content
        text_content = html[:500].strip()
        print("Content preview (first 500 chars):")
        print("-" * 60)
        print(text_content)
        print("-" * 60)
        
        # Save if requested
        if args.output:
            args.output.write_text(html, encoding="utf-8")
            print(f"\n✓ Saved full HTML to: {args.output}")
        
    except Exception as exc:
        print(f"✗ Fetch failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
