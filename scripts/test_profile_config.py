"""
Sanity-check the profile configuration without launching a browser.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from naked_web import NakedWebConfig, get_default_playwright_profile_path


def test_profile_config() -> None:
    """Print the current default and custom profile behavior."""
    print("\n" + "=" * 80)
    print("Testing Browser Profile Configuration")
    print("=" * 80 + "\n")

    cfg_default = NakedWebConfig()
    default_profile_path = get_default_playwright_profile_path().resolve()

    print("Default configuration")
    print(f"  selenium_profile_path: {cfg_default.selenium_profile_path}")
    print(f"  resolved default profile path: {default_profile_path}")
    print("  expected: Selenium and Playwright will use this shared path by default\n")

    custom_path = Path("profiles/reddit_profile").resolve()
    cfg_custom = NakedWebConfig(selenium_profile_path=str(custom_path))
    print("Custom profile path")
    print(f"  selenium_profile_path: {cfg_custom.selenium_profile_path}")
    print("  expected: Selenium will use the specified custom profile\n")

    template_path = Path(__file__).parent.parent / "naked_web" / "_data" / "default_profile"
    print("Optional seed template")
    print(f"  template path: {template_path}")
    print(f"  exists: {template_path.exists()}")
    if template_path.exists():
        contents = list(template_path.iterdir())
        print(f"  items in template directory: {len(contents)}")
    else:
        print("  no template present; fresh profiles will be created empty")

    print("\n" + "=" * 80)
    print("Configuration Tests Complete")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run: python scripts/warmup_profile.py")
    print("2. Or run: python scripts/warmup_playwright_profile.py")
    print("3. Use: python scripts/browser_profile_bundle.py to export/import profiles")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_profile_config()
