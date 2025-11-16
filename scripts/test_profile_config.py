"""
Test the profile system - demonstrates the feature without actually warming up
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from naked_web import NakedWebConfig

def test_profile_config():
    """Test that profile configuration works correctly"""
    
    print("\n" + "="*80)
    print("Testing Browser Profile Configuration")
    print("="*80 + "\n")
    
    # Test 1: Default behavior (use default profile)
    cfg1 = NakedWebConfig()
    print("Test 1: Default Configuration")
    print(f"  use_default_profile: {cfg1.use_default_profile}")
    print(f"  selenium_profile_path: {cfg1.selenium_profile_path}")
    print("  Expected: Will use library's default profile if it exists\n")
    
    # Test 2: Custom profile path
    custom_path = "C:/my_profiles/reddit_profile"
    cfg2 = NakedWebConfig(selenium_profile_path=custom_path)
    print("Test 2: Custom Profile Path")
    print(f"  selenium_profile_path: {cfg2.selenium_profile_path}")
    print("  Expected: Will use the specified custom profile\n")
    
    # Test 3: Disable profiles
    cfg3 = NakedWebConfig(use_default_profile=False)
    print("Test 3: Profiles Disabled")
    print(f"  use_default_profile: {cfg3.use_default_profile}")
    print(f"  selenium_profile_path: {cfg3.selenium_profile_path}")
    print("  Expected: Will use fresh browser profile (more likely to be detected)\n")
    
    # Test 4: Check default profile path
    lib_root = Path(__file__).parent.parent / "naked_web"
    default_profile_path = lib_root / "_data" / "default_profile"
    print("Test 4: Default Profile Location")
    print(f"  Path: {default_profile_path}")
    print(f"  Exists: {default_profile_path.exists()}")
    if not default_profile_path.exists():
        print("  ⚠ Warning: Run `python scripts/warmup_profile.py` to create it")
    else:
        # Check if it has any data
        contents = list(default_profile_path.iterdir())
        if len(contents) <= 1:  # Only .gitkeep
            print("  ⚠ Warning: Profile exists but is empty - needs warm-up")
        else:
            print(f"  ✓ Profile contains {len(contents)} items (looks warmed up)")
    
    print("\n" + "="*80)
    print("Configuration Tests Complete!")
    print("="*80)
    print("\nNext Steps:")
    print("1. Run: python scripts/warmup_profile.py")
    print("2. Browse for 15-30 minutes to build organic history")
    print("3. Then your library will automatically use the warmed profile")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_profile_config()
