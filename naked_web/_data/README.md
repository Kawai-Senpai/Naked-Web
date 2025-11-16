# Browser Profile Data

This directory contains browser profile data used for anti-bot-detection.

## What's in here?

### `default_profile/`
The library's default Chrome profile with pre-warmed cookies and browsing history.
This profile is automatically used when `use_default_profile=True` (default setting)
and no custom profile path is specified.

**Important:** This directory should NOT be committed to version control if it contains
real browsing data. The `.gitignore` already excludes `_data/` directory.

## How to create/update profiles

### Create the default profile:
```bash
python scripts/warmup_profile.py
```

This will:
1. Open a headful Chrome browser
2. Let you browse normally for 30 minutes (configurable)
3. Save all cookies, history, and localStorage to this directory
4. The profile will then be used automatically for all Selenium requests

### Create a custom profile:
```bash
python scripts/warmup_profile.py --profile "C:/my_profiles/custom"
```

Then use it in your code:
```python
from naked_web import NakedWebConfig, fetch_page

cfg = NakedWebConfig(
    selenium_profile_path="C:/my_profiles/custom"
)

result = fetch_page("https://example.com", cfg=cfg, use_js=True)
```

### Disable profile usage (not recommended):
```python
cfg = NakedWebConfig(
    use_default_profile=False  # Use fresh profile (more likely to be detected)
)
```

## Why use profiles?

Real browser profiles with organic browsing history are the most effective way to:
- Bypass sophisticated bot detection (Reddit, Twitter, etc.)
- Look like a genuine user (because you ARE a genuine user)
- Build trust over time as history accumulates
- Avoid CAPTCHA challenges

## Profile persistence across sessions

When you specify a custom `selenium_profile_path`, the profile is **persistent**.
Each time you use the library:
- New cookies are added
- Browsing history grows
- The profile becomes more "trusted" by websites

This is the recommended approach for long-term web scraping projects.

## Security note

Be careful with sensitive data:
- Don't commit profiles with logged-in sessions
- Don't share profile directories publicly
- Use separate profiles for different projects
- Consider encrypting profile directories if they contain credentials

## Profile structure

Chrome profile directories contain:
- `Cookies` - Session cookies and persistent cookies
- `History` - Browsing history database
- `Local Storage/` - localStorage data from websites
- `Preferences` - Browser settings and flags
- `Cache/` - Cached resources (images, scripts, etc.)

All of these contribute to making the browser look "real" to bot detection systems.
