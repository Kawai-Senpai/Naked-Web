"""
Selenium/Chrome browser profile warm-up tool.

This script opens a visible Chrome browser and lets you browse naturally so the
profile can build cookies, history, and local storage.

The default profile path is shared across NakedWeb's Selenium and Playwright
flows:
  - Windows: %LOCALAPPDATA%\\.nakedweb\\browser_profile
  - Linux:   $XDG_STATE_HOME/nakedweb/browser_profile or ~/.local/state/nakedweb/browser_profile
  - Override: NAKEDWEB_PROFILE_DIR=/custom/path

Usage:
    python scripts/warmup_profile.py
    python scripts/warmup_profile.py --profile /my/path
    python scripts/warmup_profile.py --duration 3600
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from naked_web.utils.profiles import get_default_playwright_profile_path

try:
    import undetected_chromedriver as uc
except ImportError:
    print("ERROR: undetected-chromedriver not installed.")
    print("Install with: pip install undetected-chromedriver")
    sys.exit(1)


def get_default_profile_path() -> Path:
    """Get the shared default persistent browser profile path."""
    return get_default_playwright_profile_path()


def warm_up_profile(profile_path: Path, duration_seconds: int = 1800) -> None:
    """
    Open a browser with the specified profile and wait for user interaction.

    Args:
        profile_path: Directory where Chrome profile data will be stored
        duration_seconds: How long to keep the browser open (default 30 minutes)
    """
    print(f"\n{'=' * 80}")
    print("Browser Profile Warm-Up Tool")
    print(f"{'=' * 80}\n")

    print(f"Profile directory: {profile_path}")
    print(f"Duration: {duration_seconds // 60} minutes ({duration_seconds} seconds)")
    print()

    profile_path.mkdir(parents=True, exist_ok=True)

    print("Setting up Chrome with profile...")

    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--start-maximized")

    try:
        driver = uc.Chrome(options=options, headless=False)
        print("\nBrowser launched successfully.")
        print("\n" + "=" * 80)
        print("INSTRUCTIONS:")
        print("=" * 80)
        print("1. Browse normally: Google, Reddit, news sites, etc.")
        print("2. Accept cookie banners when they appear.")
        print("3. Log in if you want this profile to keep those sessions.")
        print("4. Scroll, click around, and let history build up.")
        print()
        print("Suggested sites:")
        print("  - https://www.google.com")
        print("  - https://www.reddit.com")
        print("  - https://news.ycombinator.com")
        print("  - https://www.wikipedia.org")
        print()
        print(f"Browser will close automatically in {duration_seconds // 60} minutes.")
        print("Press Ctrl+C in this terminal to close early.")
        print("=" * 80 + "\n")

        driver.get("https://www.google.com")

        start_time = time.time()
        try:
            while True:
                elapsed = time.time() - start_time
                remaining = duration_seconds - elapsed
                if remaining <= 0:
                    break
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                print(f"\rTime remaining: {mins:02d}:{secs:02d}  ", end="", flush=True)
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nWarm-up interrupted by user.")

        print("\nClosing browser and saving profile...")
        driver.quit()

        print("\nProfile saved successfully.")
        print(f"Location: {profile_path}")
        print()

        if profile_path.resolve() == get_default_profile_path().resolve():
            print("This is NakedWeb's shared default profile path.")
            print("It will be used automatically when selenium_profile_path is not set.")
        else:
            print("To use this custom profile in code:")
            print(f'  cfg = NakedWebConfig(selenium_profile_path="{profile_path}")')

        print("\nThe Playwright warm-up tool and bundle tool can reuse the same directory.")
        print(f"{'=' * 80}\n")

    except Exception as exc:
        print(f"\nERROR: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Warm up a Chrome profile with organic browsing data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/warmup_profile.py
  python scripts/warmup_profile.py --profile /my_profiles/reddit_profile
  python scripts/warmup_profile.py --duration 3600
        """,
    )

    parser.add_argument(
        "--profile",
        type=str,
        help="Path to a custom profile directory. Default: shared OS-specific NakedWeb profile path.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=1800,
        help="How long to keep browser open in seconds (default: 1800 = 30 minutes)",
    )
    args = parser.parse_args()

    profile_path = (
        Path(args.profile).expanduser().resolve()
        if args.profile
        else get_default_profile_path().resolve()
    )
    warm_up_profile(profile_path, args.duration)


if __name__ == "__main__":
    main()
