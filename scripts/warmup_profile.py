"""
Browser Profile Warm-Up Tool

This script opens a headful Chrome browser and waits for you to browse naturally.
Use it to generate organic cookies, browsing history, and localStorage data.

The profile will be saved to either:
1. Library's default profile (_data/default_profile/) - if no custom path provided
2. Your custom directory - if you specify a path

Usage:
    python scripts/warmup_profile.py                    # Create/update default profile
    python scripts/warmup_profile.py --profile /path    # Create/update custom profile
    python scripts/warmup_profile.py --duration 3600    # Warm up for 1 hour
"""

import argparse
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from naked_web import NakedWebConfig

# Check if selenium is available
try:
    import undetected_chromedriver as uc
except ImportError:
    print("ERROR: undetected-chromedriver not installed!")
    print("Install with: pip install undetected-chromedriver")
    sys.exit(1)


def get_default_profile_path() -> Path:
    """Get the path to the library's default profile directory."""
    # Get the library's root directory
    lib_root = Path(__file__).parent.parent / "naked_web"
    profile_dir = lib_root / "_data" / "default_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    return profile_dir


def warm_up_profile(profile_path: Path, duration_seconds: int = 1800):
    """
    Open a browser with the specified profile and wait for user interaction.
    
    Args:
        profile_path: Directory where Chrome profile data will be stored
        duration_seconds: How long to keep the browser open (default 30 minutes)
    """
    print(f"\n{'='*80}")
    print("Browser Profile Warm-Up Tool")
    print(f"{'='*80}\n")
    
    print(f"Profile Directory: {profile_path}")
    print(f"Duration: {duration_seconds // 60} minutes ({duration_seconds} seconds)")
    print()
    
    # Ensure profile directory exists
    profile_path.mkdir(parents=True, exist_ok=True)
    
    print("Setting up Chrome with profile...")
    
    # Configure Chrome options
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--start-maximized")
    
    # Create driver
    try:
        driver = uc.Chrome(options=options, headless=False)
        print("\n✓ Browser launched successfully!")
        print("\n" + "="*80)
        print("INSTRUCTIONS:")
        print("="*80)
        print("1. Browse normally - visit Reddit, Google, news sites, etc.")
        print("2. Log into accounts if you want (optional)")
        print("3. Click around, scroll, read articles")
        print("4. Let the browser build organic history and cookies")
        print()
        print("Suggested sites to visit:")
        print("  - https://www.google.com  (search for random things)")
        print("  - https://www.reddit.com  (browse popular subreddits)")
        print("  - https://news.ycombinator.com  (tech news)")
        print("  - https://www.wikipedia.org  (read random articles)")
        print()
        print(f"Browser will close automatically in {duration_seconds // 60} minutes")
        print("Or you can close it manually when done (Ctrl+C in this terminal)")
        print("="*80 + "\n")
        
        # Navigate to a starter page
        driver.get("https://www.google.com")
        
        # Wait for the specified duration
        start_time = time.time()
        try:
            while True:
                elapsed = time.time() - start_time
                remaining = duration_seconds - elapsed
                
                if remaining <= 0:
                    break
                
                # Print progress every 60 seconds
                if int(elapsed) % 60 == 0:
                    mins_remaining = int(remaining // 60)
                    print(f"⏱  Time remaining: {mins_remaining} minutes...")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n✓ Warm-up interrupted by user")
        
        print("\n" + "="*80)
        print("Closing browser and saving profile...")
        driver.quit()
        
        print("\n✓ Profile saved successfully!")
        print(f"✓ Location: {profile_path}")
        print("\n" + "="*80)
        print("Profile is now ready to use!")
        print()
        
        if profile_path == get_default_profile_path():
            print("This is the DEFAULT profile - will be used automatically")
            print("when selenium_profile_path is not specified in config.")
        else:
            print("To use this profile, set in your code:")
            print(f'  cfg = NakedWebConfig(selenium_profile_path="{profile_path}")')
        
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Warm up a Chrome profile with organic browsing data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create/update the default library profile (recommended)
  python scripts/warmup_profile.py
  
  # Create a custom profile in a specific directory
  python scripts/warmup_profile.py --profile "C:/my_profiles/reddit_profile"
  
  # Warm up for 1 hour instead of default 30 minutes
  python scripts/warmup_profile.py --duration 3600
        """
    )
    
    parser.add_argument(
        "--profile",
        type=str,
        help="Path to custom profile directory (uses library default if not specified)"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        default=1800,
        help="How long to keep browser open in seconds (default: 1800 = 30 minutes)"
    )
    
    args = parser.parse_args()
    
    # Determine profile path
    if args.profile:
        profile_path = Path(args.profile).resolve()
    else:
        profile_path = get_default_profile_path()
    
    # Run warm-up
    warm_up_profile(profile_path, args.duration)


if __name__ == "__main__":
    main()
