r"""
Playwright Browser Profile Warm-Up Tool

Opens a HEADFUL (visible) Chromium browser using Playwright with the same
persistent profile that AutoBrowser / Infinite-code MCP browser tool uses.

Browse normally to:
  - Build organic cookies and history
  - Accept cookie banners on popular sites
  - Make search engines trust the fingerprint

The profile is saved to the same location AutoBrowser reads from:
  - Windows: %LOCALAPPDATA%\.nakedweb\browser_profile
  - Linux:   $XDG_STATE_HOME/nakedweb/browser_profile or ~/.local/state/nakedweb/browser_profile
  - Override: NAKEDWEB_PROFILE_DIR=/custom/path

Usage:
    python scripts/warmup_playwright_profile.py                      # default profile
    python scripts/warmup_playwright_profile.py --profile /my/path   # custom profile
    python scripts/warmup_playwright_profile.py --duration 3600      # 1 hour
    python scripts/warmup_playwright_profile.py --auto               # auto-warm with sites list

After warming up, the MCP browser tool will reuse the same cookies/history.
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Add parent directory to path for local dev
sys.path.insert(0, str(Path(__file__).parent.parent))

from naked_web.utils.profiles import copy_profile_tree, get_default_playwright_profile_path


def get_default_profile_path() -> Path:
    """Get the default NakedWeb/Playwright persistent profile path."""
    return get_default_playwright_profile_path()


def resolve_seed_profile_path(explicit_path: str | None = None) -> Path | None:
    """Resolve an optional seed profile path for first-time warmups."""
    candidates = []
    if explicit_path:
        candidates.append(Path(explicit_path).expanduser())

    for env_name in ("NAKEDWEB_SEED_PROFILE", "WEBAUTOMATION_PROFILE_DIR"):
        env_value = os.environ.get(env_name)
        if env_value:
            candidates.append(Path(env_value).expanduser())

    # Keep the old Windows path as a backward-compatible fallback.
    candidates.append(Path(r"E:\Python and AI\_My Projects\WebAutomation\profiles\webautomation"))

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def copy_from_seed_profile(profile_path: Path, source_path: str | None = None) -> bool:
    """Copy cookies/data from a seed profile if one is configured and ours is empty."""
    seed_profile = resolve_seed_profile_path(source_path)
    if seed_profile is None:
        return False

    # Check if our profile's Default folder is mostly empty (newly created)
    our_default = profile_path / "Default"
    has_history = (our_default / "History").exists() if our_default.exists() else False

    if has_history:
        print("  Profile already has browsing history, skipping seed-profile copy.")
        return False

    print(f"  Copying profile data from seed profile: {seed_profile}")
    try:
        copy_profile_tree(seed_profile, profile_path, clean_destination=True)
        print("  Done - seed profile data copied.")
        return True
    except Exception as e:
        print(f"  Warning: Could not copy seed profile: {e}")
        return False


# Sites to visit during auto-warmup (builds organic history + cookies)
AUTO_WARMUP_SITES = [
    "https://www.google.com",
    "https://www.google.com/search?q=weather+today",
    "https://www.google.com/search?q=latest+tech+news",
    "https://duckduckgo.com/?q=best+programming+languages+2026",
    "https://en.wikipedia.org/wiki/Main_Page",
    "https://en.wikipedia.org/wiki/Python_(programming_language)",
    "https://www.reddit.com",
    "https://news.ycombinator.com",
    "https://www.github.com",
    "https://stackoverflow.com",
    "https://www.youtube.com",
    "https://www.amazon.com",
    "https://www.bbc.com/news",
    "https://www.nytimes.com",
    "https://www.imdb.com",
]


def auto_warmup(context, duration_seconds: int = 300):
    """
    Automatically visit a list of common sites to build organic fingerprint.
    Uses a visible browser so captchas can be solved manually if needed.
    """
    import random

    page = context.pages[0] if context.pages else context.new_page()

    print(f"\n  Auto-warming {len(AUTO_WARMUP_SITES)} sites...")
    print("  If you see a captcha, solve it manually in the browser window.\n")

    for i, url in enumerate(AUTO_WARMUP_SITES, 1):
        try:
            print(f"  [{i}/{len(AUTO_WARMUP_SITES)}] {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=20000)

            # Random wait to simulate reading (2-6 seconds)
            wait_time = random.uniform(2.0, 6.0)
            time.sleep(wait_time)

            # Random scroll
            scroll_amount = random.randint(200, 800)
            page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            print(f"    Warning: {e}")
            continue

    print(f"\n  Auto-warmup complete! Visited {len(AUTO_WARMUP_SITES)} sites.")
    print("  You can continue browsing manually now.\n")


def warmup(
    profile_path: Path,
    duration_seconds: int = 1800,
    auto: bool = False,
    copy_wa: bool = False,
    copy_from: str | None = None,
):
    """
    Open a headful Playwright Chromium browser with the persistent profile.

    Args:
        profile_path: Directory for Chromium profile data.
        duration_seconds: How long to keep the browser open.
        auto: If True, auto-visit common sites first.
        copy_wa: If True, copy a detected seed profile first.
        copy_from: Optional explicit seed profile path.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright not installed!")
        print("Install with: pip install playwright && playwright install chromium")
        sys.exit(1)

    print(f"\n{'=' * 70}")
    print("  Playwright Profile Warm-Up Tool")
    print(f"{'=' * 70}\n")

    profile_path.mkdir(parents=True, exist_ok=True)
    print(f"  Profile:  {profile_path}")
    print(f"  Duration: {duration_seconds // 60} minutes ({duration_seconds}s)")
    print(f"  Auto:     {'Yes' if auto else 'No'}")
    print()

    # Optionally copy from WebAutomation
    if copy_wa or copy_from:
        copy_from_seed_profile(profile_path, copy_from)

    # Import stealth JS from AutoBrowser
    try:
        from naked_web.automation.browser import AutoBrowser
        stealth_js = AutoBrowser._STEALTH_JS
        user_agent = AutoBrowser._DEFAULT_USER_AGENT
        print("  Stealth: Using AutoBrowser stealth config")
    except ImportError:
        stealth_js = None
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
        print("  Stealth: Using fallback user agent")

    print(f"\n  Launching browser (headful)...\n")

    with sync_playwright() as pw:
        # Use installed Chrome channel for full browser experience
        # (address bar, new tabs, extensions all work naturally)
        # Falls back to bundled Chromium if Chrome isn't installed
        try:
            context = pw.chromium.launch_persistent_context(
                user_data_dir=str(profile_path),
                channel="chrome",  # Use installed Chrome for full UI
                headless=False,  # HEADFUL - visible browser
                viewport={"width": 1280, "height": 800},
                user_agent=user_agent,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                ],
                ignore_default_args=["--enable-automation"],  # Hide automation flag in Chrome
            )
            print("  Using installed Chrome (full browser UI)")
        except Exception:
            context = pw.chromium.launch_persistent_context(
                user_data_dir=str(profile_path),
                headless=False,
                viewport={"width": 1280, "height": 800},
                user_agent=user_agent,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                ],
            )
            print("  Using bundled Chromium (Chrome not found)")

        # Inject stealth scripts
        if stealth_js:
            context.add_init_script(stealth_js)

        # Navigate first page to Google
        page = context.pages[0] if context.pages else context.new_page()

        if auto:
            auto_warmup(context, duration_seconds)

        # Navigate to Google as starting point
        try:
            page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass

        print(f"{'=' * 70}")
        print("  INSTRUCTIONS:")
        print(f"{'=' * 70}")
        print("  1. Browse normally - Google, Reddit, YouTube, Wikipedia, etc.")
        print("  2. Accept cookie banners when they appear.")
        print("  3. Solve any captchas that show up.")
        print("  4. Scroll around, click links, read pages.")
        print("  5. Let it build organic history and cookies.")
        print()
        print(f"  Browser will auto-close in {duration_seconds // 60} minutes.")
        print("  Press Ctrl+C in this terminal to close early.")
        print(f"{'=' * 70}\n")

        start_time = time.time()
        try:
            while True:
                elapsed = time.time() - start_time
                remaining = duration_seconds - elapsed
                if remaining <= 0:
                    break

                mins = int(remaining) // 60
                secs = int(remaining) % 60
                print(f"\r  Time remaining: {mins:02d}:{secs:02d}  ", end="", flush=True)
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n  Interrupted by user.")

        print("\n  Closing browser and saving profile...")
        context.close()

    print(f"\n  Profile saved to: {profile_path}")
    print("  The MCP browser tool will now use these cookies and history.")
    print(f"{'=' * 70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Warm up Playwright browser profile for MCP browser tool",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Custom profile directory path. Default: OS-specific NakedWeb browser profile path.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=1800,
        help="Duration to keep browser open in seconds (default: 1800 = 30 min)",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-visit common sites to build organic fingerprint first",
    )
    parser.add_argument(
        "--copy-wa",
        action="store_true",
        help="Copy profile data from a detected seed profile before warming up",
    )
    parser.add_argument(
        "--copy-from",
        type=str,
        default=None,
        help="Explicit source profile directory to copy before warming up.",
    )
    args = parser.parse_args()

    profile_path = (
        Path(args.profile).expanduser().resolve()
        if args.profile
        else get_default_profile_path().resolve()
    )
    warmup(profile_path, args.duration, args.auto, args.copy_wa, args.copy_from)


if __name__ == "__main__":
    main()
