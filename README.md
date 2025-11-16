# Naked Web

Naked Web is a focused toolkit that wraps Google Custom Search and modern scraping primitives so agents (or humans) can pull search results, raw HTML, assets, and paginated slices with one cohesive API.

## Highlights

- Google Custom Search JSON API integration with automatic content enrichment per result
- First class scraping with optional Selenium (undetected-chromedriver) rendering for JS heavy pages
- **Enhanced stealth mode** with anti-detection for bot-protected sites (Reddit, LinkedIn, etc.)
- Asset harvesting (CSS, JS, images, media, links) plus line/char HTML pagination
- Site crawler + asset download helpers so you can build custom cloning flows
- Structured content extraction (meta tags, headings, paragraphs, inline styles, CSS, fonts)
- Context-rich asset metadata (alt text, captions, snippets, anchor text) for every stylesheet/script/image/link
- Regex/glob search helpers over crawled text plus asset/link contexts

## Install

```bash
pip install -e .
# add JS rendering support (installs selenium + undetected-chromedriver)
pip install -e .[selenium]
```

## Config basics

```python
from naked_web import NakedWebConfig

cfg = NakedWebConfig(
    google_api_key="YOUR_KEY",
    google_cse_id="YOUR_CSE_ID",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)
```

### Stealth Selenium rendering

When `use_stealth=True`, Naked Web uses enhanced anti-detection measures including CDP script injection, mouse simulation, and realistic scrolling. For sites with sophisticated bot detection (Reddit, LinkedIn, etc.), use stealth mode:

```python
snap = fetch_page("https://reddit.com/r/Python/", cfg=cfg, use_stealth=True)
```

See [STEALTH.md](STEALTH.md) for detailed documentation on anti-detection features.

**Key stealth configuration:**

- `selenium_headless`: toggle windowed browsing (default `False` to avoid headless fingerprints)
- `selenium_window_size`: specify the viewport (defaults to `1366,768`)
- `selenium_page_load_timeout` / `selenium_wait_timeout`: manage waits and timeouts
- `humanize_delay_range`: random delay range (seconds) inserted before navigation and scrolls
- `crawl_delay_range`: delays between page fetches (defaults to 1.0-2.5s to avoid volume detection)

These options live on `NakedWebConfig` so you can set them globally for both the CLI helpers and library calls.

## Search with optional scraping

```python
from naked_web import SearchClient

client = SearchClient(cfg)
resp = client.search(
    "python selenium scraping",
    max_results=3,
    include_page_content=True,
    use_js_for_pages=False,
)
```

Each entry contains title, snippet, url, score, and optional cleaned content + HTTP status.

## Scrape single pages

```python
from naked_web import fetch_page

# Basic HTTP fetch
snap = fetch_page("https://example.com", cfg=cfg, use_js=False)

# With basic Selenium rendering
snap = fetch_page("https://example.com", cfg=cfg, use_js=True)

# With enhanced stealth mode (recommended for bot-protected sites)
snap = fetch_page("https://example.com", cfg=cfg, use_stealth=True)

print(snap.text[:500])
print(snap.assets.stylesheets)
```

## Structured content bundles

```python
from naked_web import extract_content

bundle = extract_content(snap, include_inline_styles=True)
print(bundle.headings[:3])
print(bundle.css_links)
```

Or fetch + extract + paginate in a single call:

```python
from naked_web import collect_page

package = collect_page(
    "https://example.com",
    use_js=True,
    include_line_chunks=True,
    include_char_chunks=True,
    line_chunk_size=250,
    char_chunk_size=4000,
    pagination_chunk_limit=5,
)
```

## Paginate HTML

```python
from naked_web import get_html_lines, get_html_chars

chunk = get_html_lines(snap, start_line=100, num_lines=50)
print(chunk["next_start"], chunk["has_more"])
```

# Build custom clones

Use `crawl_site` to gather pages and `download_assets` to persist files wherever you like:

```python
from naked_web import crawl_site, download_assets

pages = crawl_site(
    "https://example.com",
    cfg=cfg,
    max_pages=10,
    max_depth=2,
    max_duration=15,
    delay_range=(0.5, 1.5),
)
for url, snapshot in pages.items():
    # write snapshot.html + snapshot.assets via your own logic
    download_assets(snapshot, output_dir="./mirror/assets", cfg=cfg)
```

## Pattern search + contextual matches

After crawling, use `find_text_matches` for glob/regex searches across page text (or raw HTML) and `find_asset_matches` to inspect any asset/link metadata with controllable context windows:

```python
from naked_web import crawl_site, find_asset_matches, find_text_matches

pages = crawl_site("https://example.com/docs", cfg=cfg, max_pages=25, max_depth=3)

text_hits = find_text_matches(
    pages,
    patterns=["*privacy*", r"cookie policy"],
    use_regex=True,
    context_chars=90,
)

asset_hits = find_asset_matches(
    pages,
    patterns=["*.css", "*analytics*"],
    context_chars=140,
)

print(text_hits.get("https://example.com/docs/privacy"))
print(asset_hits.get("https://example.com/docs/privacy"))
```

Tune `cfg.asset_context_chars` if you need global control over how much surrounding HTML is captured for each asset/link snippet.

## Live fetch test

Quickly verify live fetching, JS rendering, and pagination:

```bash
python scripts/live_fetch_test.py https://example.com --mode both --inline-styles --output payload.json
```

## Local smoke test

Run the lightweight check script (hits a real site by default) to ensure helpers wire up:

```bash
python scripts/smoke_test.py
```

The script fetches `https://www.google.com` (override via `NAKED_WEB_SMOKE_URL` or a CLI arg), then instantiates core classes, exercises pagination helpers, and prints diagnostic output. If the live fetch fails, it falls back to a synthetic HTML payload.

## Enhanced Stealth Scraping

NakedWeb now includes enhanced anti-detection capabilities for sites with sophisticated bot detection (like Reddit, LinkedIn, etc.).

### What's New

The `naked_web.stealth` module provides:

1. **CDP Script Injection**: Masks `navigator.webdriver` and other automation signals
2. **Mouse Movement Simulation**: Random, human-like cursor movements across the viewport
3. **Realistic Scrolling**: Variable-speed scrolling with pauses and occasional scroll-backs
4. **Enhanced Headers**: Proper Accept-Language, viewport configuration, and plugin mocking

### Installation

Stealth features require the Selenium extras:

```bash
pip install -e .[selenium]
```

### Basic Usage

```python
from naked_web import NakedWebConfig
from naked_web.stealth import fetch_with_stealth

cfg = NakedWebConfig(
    selenium_headless=False,  # Windowed mode less detectable
    selenium_window_size="1920,1080",
    humanize_delay_range=(1.5, 3.5),  # Random delays
)

html, headers, status, final_url = fetch_with_stealth(
    "https://www.reddit.com/r/Python/",
    cfg=cfg,
    perform_mouse_movements=True,
    perform_realistic_scrolling=True,
)

print(f"Fetched {len(html)} chars from {final_url}")
```

### Advanced: Direct Driver Control

For maximum flexibility, use the driver setup directly:

```python
from naked_web.stealth import setup_stealth_driver, inject_stealth_scripts
from naked_web import NakedWebConfig

cfg = NakedWebConfig()
driver = setup_stealth_driver(cfg, use_profile=False)

try:
    driver.get("https://example.com")
    # Your custom interactions here
    html = driver.page_source
finally:
    driver.quit()
```

### Testing Against Bot Detection

Use the included test script to validate stealth capabilities:

```bash
# Test with default Reddit URL (known bot detection)
python scripts/stealth_test.py

# Test custom URL in windowed mode
python scripts/stealth_test.py "https://www.reddit.com/r/Python/" --no-headless

# Disable specific features for debugging
python scripts/stealth_test.py --no-mouse --no-scroll

# Save fetched HTML
python scripts/stealth_test.py --output reddit_test.html
```

The script will report:
- Fetch success/failure
- Bot detection indicators (e.g., "Prove your humanity")
- Content preview
- HTML saved to file (if `--output` specified)

### Configuration Tips

**For maximum stealth:**
- Disable headless mode (`selenium_headless=False`)
- Use realistic viewport sizes (1920x1080, 1366x768)
- Set longer humanize delays (2-4 seconds)
- Consider using residential proxies (not included in base library)
- Rotate user agents occasionally

**For Reddit specifically:**
- Authenticate with real accounts when possible
- Honor rate limits (add delays between requests)
- Consider using Reddit's official API instead

### Limitations

Even with these measures, some sites may still detect automation:

1. **TLS Fingerprinting**: Chrome's TLS signature can be identified
2. **Canvas/WebGL**: GPU rendering patterns differ in automated contexts
3. **Timing Analysis**: Perfect timing consistency can be suspicious
4. **IP Reputation**: Datacenter IPs are often flagged

For highly protected sites, consider:
- Residential proxy services with rotation
- Real browser profiles with existing cookies/history
- Playwright with additional stealth plugins
- Respecting site ToS and using official APIs

### Memory

Bot detection strategies and mitigation techniques are documented in memory:

```python
from naked_web.mcp_infinite_code import memory_search

results = memory_search(query="bot detection selenium")
```

This retrieves saved knowledge about fingerprinting vectors, bypass strategies, and platform-specific considerations.

# Browser Profile Persistence Guide

## Overview

NakedWeb now supports **persistent browser profiles** to dramatically improve bot detection bypass. Instead of using a fresh browser every time (which looks suspicious), you can use profiles with real cookies, browsing history, and cached data.

## Why Use Profiles?

**The Problem:**
- Fresh browsers are immediately suspicious to bot detection systems
- No cookies = no session history = obvious bot
- Reddit, Twitter, and other sites detect this instantly

**The Solution:**
- Use real browser profiles with organic browsing history
- Cookies and cache persist across sessions
- Websites see a "real user" because you ARE a real user
- Trust builds over time as history accumulates

## Quick Start

### 1. Warm Up a Profile

Run the warm-up script to create an organic browsing profile:

```bash
# Create the default library profile (recommended)
python scripts/warmup_profile.py

# Or create a custom profile in your own directory
python scripts/warmup_profile.py --profile "C:/my_profiles/reddit_profile"

# Customize warm-up duration (default is 30 minutes)
python scripts/warmup_profile.py --duration 3600  # 1 hour
```

**What to do during warm-up:**
1. Browse normally - visit Google, Reddit, news sites
2. Search for random things
3. Read articles, scroll, click around
4. Optional: Log into accounts (if you want persistent logins)
5. Let it run for at least 15-30 minutes

The script will guide you through the process.

### 2. Use the Profile

#### Default Profile (Automatic)

By default, NakedWeb will automatically use the warmed profile:

```python
from naked_web import NakedWebConfig, fetch_page

cfg = NakedWebConfig()  # use_default_profile=True by default

# This will use the default warmed profile
result = fetch_page("https://www.reddit.com/r/Python/", cfg=cfg, use_js=True)
```

#### Custom Profile

Specify your own profile directory:

```python
cfg = NakedWebConfig(
    selenium_profile_path="C:/my_profiles/reddit_profile"
)

result = fetch_page("https://www.reddit.com/r/Python/", cfg=cfg, use_js=True)
```

#### Disable Profiles (Not Recommended)

To use a fresh browser every time:

```python
cfg = NakedWebConfig(
    use_default_profile=False
)
```

⚠️ **Warning:** This makes bot detection more likely!

## Profile Persistence

### How It Works

When you use a profile:
1. **First Request:** Browser loads existing cookies/history from profile
2. **During Browsing:** New data is added (cookies, cache, localStorage)
3. **After Closing:** All new data is saved back to profile directory
4. **Next Request:** Profile now contains MORE history = more trusted

### Long-Term Benefits

The more you use a profile, the better it becomes:
- Websites remember you as a "returning visitor"
- Session cookies persist (no need to re-login)
- Behavioral patterns look natural
- Trust score increases over time

## Best Practices

### Do's ✅

- **Create separate profiles for different purposes**
  ```bash
  python scripts/warmup_profile.py --profile profiles/reddit
  python scripts/warmup_profile.py --profile profiles/twitter
  python scripts/warmup_profile.py --profile profiles/news
  ```

- **Warm up profiles regularly**
  - Re-run the warm-up script monthly
  - Let it build fresh organic traffic

- **Use realistic delays**
  ```python
  cfg = NakedWebConfig(
      crawl_delay_range=(5.0, 15.0),  # Longer delays = more human
      selenium_profile_path="profiles/reddit"
  )
  ```

- **Keep profiles secure**
  - Don't commit profiles to git (already in .gitignore)
  - Don't share profiles publicly
  - Encrypt profile directories if they contain sensitive data

### Don'ts ❌

- **Don't use the same profile for high-frequency scraping**
  - Websites may detect unusual activity
  - Spread requests across time or use multiple profiles

- **Don't log into your personal accounts during warm-up**
  - Unless you specifically want those credentials in the profile
  - Create throwaway accounts instead

- **Don't reuse profiles across different IPs**
  - Sudden IP changes look suspicious
  - Create new profiles when changing network location

## Advanced Configuration

### Multiple Profiles Strategy

For serious projects, maintain a pool of profiles:

```python
import random
from pathlib import Path

def get_random_profile():
    """Rotate through multiple profiles"""
    profile_dir = Path("profiles")
    profiles = list(profile_dir.glob("reddit_*"))
    return str(random.choice(profiles))

cfg = NakedWebConfig(
    selenium_profile_path=get_random_profile(),
    crawl_delay_range=(10.0, 30.0)
)
```

### Profile Management Script

Create profiles in batch:

```bash
# Create 5 different Reddit profiles
for i in 1 2 3 4 5; do
    python scripts/warmup_profile.py --profile "profiles/reddit_$i" --duration 1800
done
```

### Combining with Proxies

For maximum stealth:

```python
# Different profiles for different proxies/IPs
profiles = {
    "proxy1.example.com": "profiles/proxy1_profile",
    "proxy2.example.com": "profiles/proxy2_profile",
}

current_proxy = get_current_proxy()
cfg = NakedWebConfig(
    selenium_profile_path=profiles[current_proxy]
)
```

## Troubleshooting

### "Default profile not found" warning

**Solution:** Run the warm-up script:
```bash
python scripts/warmup_profile.py
```

### Browser crashes during warm-up

**Common causes:**
- Insufficient RAM (close other programs)
- Corrupted Chrome installation (reinstall Chrome)
- Profile directory permissions (check write access)

**Solution:** Delete the profile directory and try again:
```bash
rm -rf naked_web/_data/default_profile
python scripts/warmup_profile.py
```

### Still getting CAPTCHA with profiles

**Possible reasons:**
1. **Profile is too fresh** - Warm it up for longer (1-2 hours)
2. **IP reputation** - Your IP may be flagged (try residential proxy)
3. **Request patterns** - Increase delays between requests
4. **TLS fingerprinting** - Some sites detect Chrome automation at network level

**Additional steps:**
- Visit the target site manually during warm-up
- Log into an account (if appropriate)
- Interact with content (like, comment, upvote)
- Use longer delays: `crawl_delay_range=(30.0, 60.0)`

### Profile becomes corrupted

**Symptoms:** Browser crashes, login loops, blank pages

**Solution:** Delete and recreate:
```bash
rm -rf profiles/my_profile
python scripts/warmup_profile.py --profile profiles/my_profile
```

## Technical Details

### Profile Directory Structure

A Chrome profile contains:
```
default_profile/
├── Cookies              # Session and persistent cookies
├── History              # Browsing history database
├── Preferences          # Browser settings
├── Local Storage/       # Website localStorage data
├── Session Storage/     # Session-specific data
├── Cache/               # Cached images, scripts, etc.
└── ... (many more Chrome-specific files)
```

### How undetected-chromedriver Uses Profiles

When you specify a profile:
1. Chrome loads the profile directory at startup
2. All cookies, history, and settings are restored
3. Websites see a "returning visitor" with existing session
4. New data is written back to the profile directory
5. Next run uses the updated profile

### Security Considerations

**What's in a profile:**
- Cookies (may include authentication tokens)
- Browsing history (all visited URLs)
- localStorage (API keys, user preferences)
- Cached files (images, scripts)
- Form data (saved addresses, etc.)

**Security tips:**
- Encrypt profile directories with sensitive data
- Use throwaway accounts for warm-up
- Don't share profile directories
- Regularly audit what's stored in profiles
- Use separate profiles for different security levels

## Examples

### Example 1: Basic Usage

```python
from naked_web import NakedWebConfig, fetch_page

# Use default warmed profile
cfg = NakedWebConfig()
result = fetch_page("https://www.reddit.com/r/Python/", cfg=cfg, use_js=True)

if "captcha" not in result.html.lower():
    print("Success! No CAPTCHA detected")
```

### Example 2: Custom Profile Per Project

```python
# Project-specific profile
import os
from pathlib import Path

project_root = Path(__file__).parent
profile_path = project_root / ".browser_profile"

cfg = NakedWebConfig(
    selenium_profile_path=str(profile_path)
)

# Profile persists across all runs of this project
result = fetch_page(url, cfg=cfg, use_js=True)
```

### Example 3: Profile Rotation

```python
from pathlib import Path
import random
import time

class ProfilePool:
    def __init__(self, profile_dir="profiles"):
        self.profiles = list(Path(profile_dir).glob("profile_*"))
        self.last_used = {}
        
    def get_profile(self, min_cooldown=300):
        """Get a profile that hasn't been used recently"""
        now = time.time()
        available = [
            p for p in self.profiles
            if now - self.last_used.get(p, 0) > min_cooldown
        ]
        
        if not available:
            # Wait for cooldown
            time.sleep(min_cooldown)
            available = self.profiles
        
        profile = random.choice(available)
        self.last_used[profile] = now
        return str(profile)

# Usage
pool = ProfilePool()

for url in urls_to_scrape:
    cfg = NakedWebConfig(
        selenium_profile_path=pool.get_profile(),
        crawl_delay_range=(10.0, 20.0)
    )
    result = fetch_page(url, cfg=cfg, use_js=True)
    time.sleep(random.uniform(60, 120))  # Long delays between requests
```

## See Also

- [STEALTH.md](STEALTH.md) - Anti-detection features
- [README.md](README.md) - Main library documentation
- `scripts/warmup_profile.py` - Profile warm-up tool source code
