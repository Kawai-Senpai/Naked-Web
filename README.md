<p align="center">
  <h1 align="center">Naked Web</h1>
  <p align="center">
    <strong>The Swiss Army Knife for Web Scraping, Search, and Browser Automation</strong>
  </p>
  <p align="center">
    <em>Dual-engine power: Selenium + Playwright - unified under one clean API.</em>
  </p>
</p>

<p align="center">
  <a href="#-installation">Installation</a> &bull;
  <a href="#-quick-start">Quick Start</a> &bull;
  <a href="#-features-at-a-glance">Features</a> &bull;
  <a href="#-scraping-engine-selenium">Selenium</a> &bull;
  <a href="#-automation-engine-playwright">Playwright</a> &bull;
  <a href="#-using-autobrowser-as-an-ai-agent-tool">Agent Tool</a> &bull;
  <a href="#-google-search-integration">Search</a> &bull;
  <a href="#-site-crawler">Crawler</a> &bull;
  <a href="#-configuration">Config</a>
</p>

---

## What is Naked Web?

Naked Web is a **production-grade Python toolkit** that combines web scraping, search, and full browser automation into a single cohesive library. It wraps two powerful browser engines - **Selenium** (via undetected-chromedriver) and **Playwright** - so you can pick the right tool for every job without juggling separate libraries.

| Capability | Engine | Use Case |
|---|---|---|
| **HTTP Scraping** | `requests` + `BeautifulSoup` | Fast, lightweight page fetching |
| **JS Rendering** | Selenium (undetected-chromedriver) | Bot-protected sites, stealth scraping |
| **Browser Automation** | Playwright | Click, type, scroll, extract - full control |
| **Google Search** | Google CSE JSON API | Search with optional content enrichment |
| **Site Crawling** | Built-in BFS crawler | Multi-page crawling with depth/duration limits |

---

## Why Naked Web?

- **Two engines, one API** - Selenium for stealth, Playwright for automation. No need to choose.
- **Anti-detection built in** - CDP script injection, mouse simulation, realistic scrolling, profile persistence.
- **Zero-vision automation** - Playwright's `AutoBrowser` indexes every interactive element by number. Click `[3]`, type into `[7]` - no screenshots, no coordinates, no CSS selectors needed.
- **Structured extraction** - Meta tags, headings, paragraphs, inline styles, assets with rich context metadata.
- **HTML pagination** - Line-based and character-based chunking for feeding content to LLMs.
- **Pydantic models everywhere** - Typed, validated, serializable data from every operation.

---

## Installation

```bash
# Core (HTTP scraping, search, content extraction, crawling)
pip install naked-web

# + Selenium engine (stealth scraping, JS rendering, bot bypass)
pip install naked-web[selenium]

# + Playwright engine (browser automation, DOM interaction)
pip install naked-web[automation]
playwright install chromium

# Everything
pip install naked-web[all]
playwright install chromium
```

**Requirements:** Python 3.9+

**Core dependencies:** `requests`, `beautifulsoup4`, `lxml`, `pydantic`

**Optional dependencies:**
- **Selenium engine:** `selenium`, `undetected-chromedriver`
- **Playwright engine:** `playwright`

---

## Features at a Glance

### Scraping & Fetching
- Plain HTTP fetch with `requests` + `BeautifulSoup`
- Selenium JS rendering with undetected-chromedriver
- Enhanced stealth mode (CDP injection, mouse simulation, realistic scrolling)
- Persistent browser profiles for bot detection bypass
- `robots.txt` compliance (optional)
- Configurable timeouts, delays, and user agents

### Browser Automation (Playwright)
- Launch Chromium, Firefox, or WebKit
- Navigate, click, type, scroll, send keyboard shortcuts
- DOM state extraction with indexed interactive elements
- Content extraction as clean Markdown
- Link extraction across the page
- Dropdown selection, screenshots, JavaScript execution
- Multi-tab management (open, switch, close, list)
- Persistent profile support (cookies, localStorage survive sessions)
- **Built-in stealth** - anti-detection JS injection (`navigator.webdriver` masking, plugin mocking, Chrome runtime spoofing)
- **Anti-detection Chrome flags** - 15+ flags to reduce automation fingerprint
- **Headless/visible switching** - `relaunch()` to toggle headless mode mid-session (for CAPTCHA solving, user handover, visual debugging)

### Search & Discovery
- Google Custom Search JSON API integration
- Automatic content enrichment per search result
- Optional JS rendering for search result pages

### Content Extraction
- Structured bundles: meta tags, headings, paragraphs, inline styles, CSS/font links
- Asset harvesting: stylesheets, scripts, images, media, fonts, links
- Rich context metadata per asset (alt text, captions, snippets, anchor text, source position)

### Crawling & Analysis
- Breadth-first site crawler with depth, page count, and duration limits
- Configurable crawl delays to avoid rate limiting
- Regex/glob pattern search across crawled page text and HTML
- Asset pattern matching with contextual windows

### Pagination
- Line-based HTML chunking with `next_start` / `has_more` cursors
- Character-based HTML chunking for LLM-sized windows
- Works on both HTML snapshots and raw text

---

## Quick Start

```python
from naked_web import NakedWebConfig, fetch_page

cfg = NakedWebConfig()

# Simple HTTP fetch
snap = fetch_page("https://example.com", cfg=cfg)
print(snap.text[:500])
print(snap.assets.images)

# With Selenium JS rendering
snap = fetch_page("https://example.com", cfg=cfg, use_js=True)

# With full stealth mode (bot-protected sites)
snap = fetch_page("https://example.com", cfg=cfg, use_stealth=True)
```

---

## Scraping Engine (Selenium)

NakedWeb's Selenium integration uses **undetected-chromedriver** with layered anti-detection measures. Perfect for sites like Reddit, LinkedIn, and other bot-protected targets.

### Basic JS Rendering

```python
from naked_web import fetch_page, NakedWebConfig

cfg = NakedWebConfig()
snap = fetch_page("https://reddit.com/r/Python/", cfg=cfg, use_js=True)
print(snap.text[:500])
```

### Stealth Mode

When `use_stealth=True`, NakedWeb activates the full anti-detection suite:

```python
snap = fetch_page("https://reddit.com/r/Python/", cfg=cfg, use_stealth=True)
```

**What stealth mode does:**

| Layer | Technique |
|---|---|
| **CDP Injection** | Masks `navigator.webdriver`, mocks plugins, languages, and permissions |
| **Mouse Simulation** | Random, human-like cursor movements across the viewport |
| **Realistic Scrolling** | Variable-speed scrolling with pauses and occasional scroll-backs |
| **Enhanced Headers** | Proper `Accept-Language`, viewport config, plugin mocking |
| **Profile Persistence** | Reuse cookies, history, and cache across sessions |

### Advanced: Direct Driver Control

```python
from naked_web.utils.stealth import setup_stealth_driver, inject_stealth_scripts
from naked_web import NakedWebConfig

cfg = NakedWebConfig(
    selenium_headless=False,
    selenium_window_size="1920,1080",
    humanize_delay_range=(1.5, 3.5),
)

driver = setup_stealth_driver(cfg, use_profile=False)
try:
    driver.get("https://example.com")
    html = driver.page_source
finally:
    driver.quit()
```

### Stealth Fetch Helper

```python
from naked_web.utils.stealth import fetch_with_stealth
from naked_web import NakedWebConfig

cfg = NakedWebConfig(
    selenium_headless=False,
    humanize_delay_range=(1.5, 3.5),
)

html, headers, status, final_url = fetch_with_stealth(
    "https://www.reddit.com/r/Python/",
    cfg=cfg,
    perform_mouse_movements=True,
    perform_realistic_scrolling=True,
)
print(f"Fetched {len(html)} chars from {final_url}")
```

### Browser Profile Persistence

Fresh browsers are a red flag for bot detectors. NakedWeb supports **persistent browser profiles** so cookies, history, and cache survive across sessions.

**Warm up a profile:**

```bash
# Create the shared default profile with organic browsing history
python scripts/warmup_profile.py

# Custom profile with longer warm-up
python scripts/warmup_profile.py --profile "profiles/reddit" --duration 3600

# Warm the same shared profile with Playwright
python scripts/warmup_playwright_profile.py --duration 3600

# Export/import the warmed profile for another Linux or Windows machine
python scripts/browser_profile_bundle.py

# Reapply a backed-up profile into the default OS-specific profile location
./reapply_browser_profile.sh        # Linux/macOS
reapply_browser_profile.bat         # Windows
```

**Use the warmed profile:**

```python
cfg = NakedWebConfig()  # Uses default warmed profile automatically
snap = fetch_page("https://www.reddit.com/r/Python/", cfg=cfg, use_js=True)
```

By default that shared profile resolves to:
- Windows: `%LOCALAPPDATA%\.nakedweb\browser_profile`
- Linux: `$XDG_STATE_HOME/nakedweb/browser_profile` or `~/.local/state/nakedweb/browser_profile`
- Override: `NAKEDWEB_PROFILE_DIR=/custom/path`

**Custom profile path:**

```python
cfg = NakedWebConfig(selenium_profile_path="profiles/reddit")
snap = fetch_page("https://www.reddit.com/r/Python/", cfg=cfg, use_js=True)
```

**Profile rotation for heavy workloads:**

```python
import random
from pathlib import Path

profiles = list(Path("profiles").glob("reddit_*"))
cfg = NakedWebConfig(
    selenium_profile_path=str(random.choice(profiles)),
    crawl_delay_range=(10.0, 30.0),
)
```

> Profiles store cookies, history, localStorage, cache, and more. Keep them secure and don't commit them to version control.

---

## Automation Engine (Playwright)

The `AutoBrowser` class provides **full browser automation** powered by Playwright. It extracts every interactive element on the page and assigns each a numeric index - so you can click, type, and interact without writing CSS selectors or using vision models.

### Launch and Navigate

```python
from naked_web.automation import AutoBrowser

browser = AutoBrowser(headless=True, browser_type="chromium")
browser.launch()
browser.navigate("https://example.com")
```

### DOM State Extraction

Get a structured snapshot of every interactive element on the page:

```python
state = browser.get_state()
print(state.to_text())
```

**Example output:**

```
URL: https://example.com
Title: Example Domain
Scroll: 0% (800px viewport, 1200px total)
Interactive elements (3 total):
  [1] a "More information..." -> https://www.iana.org/domains/example
  [2] input type="text" placeholder="Search..."
  [3] button "Submit"
```

### Interact by Index

```python
browser.click(1)                          # Click element [1]
browser.type_text(2, "hello world")       # Type into element [2]
browser.scroll(direction="down", amount=2) # Scroll down 2 pages
browser.send_keys("Enter")               # Press Enter
browser.select_option(4, "Option A")     # Select dropdown option
```

### Extract Content

```python
# Page content as clean Markdown
result = browser.extract_content()
print(result.extracted_content)

# All links on the page
links = browser.extract_links()
print(links.extracted_content)

# Take a screenshot
browser.screenshot("page.png")

# Run arbitrary JavaScript
result = browser.evaluate_js("document.title")
print(result.extracted_content)
```

### Multi-Tab Management

```python
browser.new_tab("https://google.com")    # Open new tab
tabs = browser.list_tabs()               # List all tabs
browser.switch_tab(0)                    # Switch to first tab
browser.close_tab(1)                     # Close second tab
```

### Persistent Profiles (Playwright)

Stay logged in across sessions:

```python
browser = AutoBrowser(
    headless=False,
    user_data_dir="profiles/my_session",
    browser_type="chromium",
)
browser.launch()
# Cookies, localStorage, history all persist to disk
browser.navigate("https://example.com")
# ... interact ...
browser.close()  # Data flushed to profile directory
```

### Stealth & Anti-Detection (Playwright)

AutoBrowser includes built-in stealth to bypass bot detection. No extra configuration needed - stealth scripts are injected automatically on every page load.

**What's injected:**

| Signal | Behavior |
|---|---|
| `navigator.webdriver` | Returns `undefined` instead of `true` |
| `navigator.plugins` | Mocked with 3 realistic Chrome plugins |
| `navigator.languages` | Returns `["en-US", "en"]` |
| `navigator.hardwareConcurrency` | Returns `8` instead of headless default |
| `navigator.platform` | Returns `"Win32"` |
| `navigator.connection` | Mocked with realistic 4G network info |
| `window.chrome.runtime` | Present (headless Chrome normally omits this) |
| `Permissions API` | Patched to return real notification state |
| User-Agent | Cleaned of `HeadlessChrome` marker |

**Chrome flags applied automatically:**
- `--disable-blink-features=AutomationControlled` - hides automation signal
- `--disable-infobars` - no "Chrome is being controlled" bar
- `--no-default-browser-check`, `--no-first-run` - skip first-run dialogs
- `--disable-extensions` - no extension fingerprint
- Plus 10+ additional anti-detection flags

```python
# Stealth is always active - just use AutoBrowser normally
browser = AutoBrowser(headless=True)
browser.launch()
browser.navigate("https://bot-protected-site.com")
# navigator.webdriver is undefined, plugins are mocked, etc.
```

### Headless/Visible Switching (Relaunch)

Switch between headless and visible mode mid-session without losing your state. The persistent profile preserves cookies, localStorage, and session data across the switch.

**Use cases:**
- CAPTCHA solving - switch to visible, let the user solve it, switch back
- Visual debugging - see what the browser is doing
- User handover - show the browser to a user, let them interact, take back control

```python
browser = AutoBrowser(headless=True, user_data_dir="profiles/session")
browser.launch()
browser.navigate("https://example.com")

# Hit a CAPTCHA or need user interaction?
browser.relaunch(headless=False)   # Window pops up visible on screen
# User solves CAPTCHA or interacts with the page...

browser.relaunch(headless=True)    # Back to headless, cookies preserved
browser.extract_content()          # Continue automation normally
```

**What happens during relaunch:**
1. Current URL is saved
2. Browser closes (profile data flushed to disk)
3. Browser relaunches with the new headless setting and same profile
4. Navigates back to the saved URL
5. All cookies, localStorage, and session data are preserved

### Supported Browsers

| Engine | Install Command |
|---|---|
| Chromium | `playwright install chromium` |
| Firefox | `playwright install firefox` |
| WebKit | `playwright install webkit` |

```python
browser = AutoBrowser(browser_type="firefox")
```

### Full AutoBrowser API

| Method | Description |
|---|---|
| `launch()` | Start the browser |
| `close()` | Close browser and clean up |
| `relaunch(headless)` | Close and relaunch with different headless setting (preserves URL and session) |
| `navigate(url)` | Go to a URL |
| `go_back()` | Navigate back in history |
| `get_state(max_elements)` | Extract interactive DOM elements with indices |
| `click(index)` | Click element by index |
| `type_text(index, text, clear)` | Type into an input element |
| `scroll(direction, amount)` | Scroll up/down by pages |
| `send_keys(keys)` | Send keyboard shortcuts |
| `select_option(index, value)` | Select dropdown option |
| `wait(seconds)` | Wait for dynamic content |
| `extract_content()` | Extract page as Markdown |
| `extract_links()` | Extract all page links |
| `screenshot(path)` | Save screenshot to file |
| `evaluate_js(expression)` | Run JavaScript in page |
| `new_tab(url)` | Open a new tab |
| `switch_tab(tab_index)` | Switch to a tab |
| `close_tab(tab_index)` | Close a tab |
| `list_tabs()` | List all open tabs |
| `get_current_url()` | Get the current page URL |
| `get_current_title()` | Get the current page title |
| `is_launched` | Property: whether the browser is running |

---

## Google Search Integration

Search the web via Google Custom Search JSON API with optional page content enrichment:

```python
from naked_web import SearchClient, NakedWebConfig

cfg = NakedWebConfig(
    google_api_key="YOUR_KEY",
    google_cse_id="YOUR_CSE_ID",
)

client = SearchClient(cfg)

# Basic search
resp = client.search("python web scraping", max_results=5)
for r in resp["results"]:
    print(f"{r['title']} - {r['url']}")

# Search + fetch page content for each result
resp = client.search(
    "python selenium scraping",
    max_results=3,
    include_page_content=True,
    use_js_for_pages=False,
)
```

Each result contains: `title`, `snippet`, `url`, `score`, and optionally `content`, `status_code`, `final_url`.

---

## Structured Content Extraction

Pull structured data from any fetched page:

```python
from naked_web import fetch_page, extract_content, NakedWebConfig

cfg = NakedWebConfig()
snap = fetch_page("https://example.com", cfg=cfg)

bundle = extract_content(
    snap,
    include_meta=True,
    include_headings=True,
    include_paragraphs=True,
    include_inline_styles=True,
    include_links=True,
)

print(bundle.title)
print(bundle.meta)          # List of MetaTag objects
print(bundle.headings)      # List of HeadingBlock objects (level + text)
print(bundle.paragraphs)    # List of paragraph strings
print(bundle.css_links)     # Stylesheet URLs
print(bundle.font_links)    # Font URLs
print(bundle.inline_styles) # Raw CSS from <style> tags
```

### One-Shot: Fetch + Extract + Paginate

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

---

## Asset Harvesting

Every fetched page comes with a full `PageAssets` breakdown:

```python
snap = fetch_page("https://example.com", cfg=cfg)

snap.assets.stylesheets       # CSS file URLs
snap.assets.scripts           # JS file URLs
snap.assets.images            # Image URLs (including srcset)
snap.assets.media             # Video/audio URLs
snap.assets.fonts             # Font file URLs (.woff, .woff2, .ttf, etc.)
snap.assets.links             # All anchor href URLs
```

Each category also has a `*_details` list with rich `AssetContext` metadata:

```python
for img in snap.assets.image_details:
    print(img.url)        # Resolved absolute URL
    print(img.alt)        # Alt text
    print(img.caption)    # figcaption text (if inside <figure>)
    print(img.snippet)    # Raw HTML snippet of the tag
    print(img.context)    # Surrounding text content
    print(img.position)   # Source line number
    print(img.attrs)      # All HTML attributes as dict
```

### Download Assets

```python
from naked_web import download_assets

download_assets(snap, output_dir="./mirror/assets", cfg=cfg)
```

---

## HTML Pagination

Split large HTML into manageable chunks for LLM consumption:

```python
from naked_web import get_html_lines, get_html_chars, slice_text_lines, slice_text_chars

# Line-based pagination
chunk = get_html_lines(snap, start_line=0, num_lines=50)
print(chunk["content"])
print(chunk["has_more"])      # True if more lines exist
print(chunk["next_start"])    # Starting line for next chunk

# Character-based pagination
chunk = get_html_chars(snap, start=0, length=4000)
print(chunk["content"])
print(chunk["next_start"])

# Also works on raw text strings
chunk = slice_text_lines("your raw text here", start_line=0, num_lines=100)
chunk = slice_text_chars("your raw text here", start=0, length=5000)
```

---

## Site Crawler

Breadth-first crawler with fine-grained controls:

```python
from naked_web import crawl_site, NakedWebConfig

cfg = NakedWebConfig(crawl_delay_range=(1.0, 2.5))

pages = crawl_site(
    "https://example.com",
    cfg=cfg,
    max_pages=20,
    max_depth=3,
    max_duration=60,            # Stop after 60 seconds
    same_domain_only=True,
    use_js=False,
    delay_range=(0.5, 1.5),     # Override per-crawl delay
)

for url, snapshot in pages.items():
    print(f"{url} - {snapshot.status_code} - {len(snapshot.text)} chars")
```

### Pattern Search Across Crawled Pages

```python
from naked_web import find_text_matches, find_asset_matches

# Search page text with regex or glob patterns
text_hits = find_text_matches(
    pages,
    patterns=["*privacy*", r"cookie\s+policy"],
    use_regex=True,
    context_chars=90,
)

# Search asset metadata
asset_hits = find_asset_matches(
    pages,
    patterns=["*.css", "*analytics*"],
    context_chars=140,
)

for url, matches in text_hits.items():
    print(f"{url}: {len(matches)} matches")
```

---

## Configuration

All settings live on `NakedWebConfig`:

```python
from naked_web import NakedWebConfig

cfg = NakedWebConfig(
    # --- Google Search ---
    google_api_key="YOUR_KEY",
    google_cse_id="YOUR_CSE_ID",

    # --- HTTP ---
    user_agent="Mozilla/5.0 ...",
    request_timeout=20,
    max_text_chars=20000,
    respect_robots_txt=False,

    # --- Assets ---
    max_asset_bytes=5_000_000,
    asset_context_chars=320,

    # --- Selenium ---
    selenium_headless=False,
    selenium_window_size="1366,768",
    selenium_page_load_timeout=35,
    selenium_wait_timeout=15,
    selenium_profile_path=None,     # Path to persistent Chrome profile

    # --- Humanization ---
    humanize_delay_range=(1.25, 2.75),
    crawl_delay_range=(1.0, 2.5),
)
```

| Setting | Default | Description |
|---|---|---|
| `user_agent` | Chrome 120 UA string | HTTP and Selenium user agent |
| `request_timeout` | `20` | HTTP request timeout (seconds) |
| `max_text_chars` | `20000` | Max cleaned text characters per page |
| `respect_robots_txt` | `False` | Check robots.txt before fetching |
| `selenium_headless` | `False` | Run Chrome in headless mode |
| `selenium_window_size` | `1366,768` | Browser viewport dimensions |
| `selenium_page_load_timeout` | `35` | Selenium page load timeout (seconds) |
| `selenium_wait_timeout` | `15` | Selenium element wait timeout (seconds) |
| `selenium_profile_path` | `None` | Persistent browser profile directory; defaults to NakedWeb's shared OS-specific profile path |
| `humanize_delay_range` | `(1.25, 2.75)` | Random delay before navigation/scroll (seconds) |
| `crawl_delay_range` | `(1.0, 2.5)` | Delay between crawler page fetches (seconds) |
| `asset_context_chars` | `320` | Characters of HTML context captured per asset |
| `max_asset_bytes` | `5000000` | Max size for downloaded assets |

---

## Scripts & Testing

```bash
# Live fetch test - verify HTTP, JS rendering, and pagination
python scripts/live_fetch_test.py https://example.com --mode both --inline-styles --output payload.json

# Smoke test - quick sanity check
python scripts/smoke_test.py

# Stealth test against bot detection
python scripts/stealth_test.py
python scripts/stealth_test.py "https://www.reddit.com/r/Python/" --no-headless
python scripts/stealth_test.py --no-mouse --no-scroll --output reddit.html

# Profile warm-up
python scripts/warmup_profile.py
python scripts/warmup_profile.py --profile profiles/reddit --duration 1800
python scripts/warmup_playwright_profile.py --duration 1800
python scripts/browser_profile_bundle.py
./reapply_browser_profile.sh
```

---

## Using AutoBrowser as an AI Agent Tool

AutoBrowser is designed to be wrapped as a tool for AI agents (LLMs, MCP servers, function-calling APIs). Its index-based interaction model means **no vision, no screenshots, no CSS selectors** - just numbered elements.

### Why It Works for Agents

- **Structured state** - `get_state()` returns a text summary with numbered elements. The agent reads element `[3]` and calls `click(3)`. No parsing HTML or guessing coordinates.
- **Text in, text out** - Every method returns `ActionResult` with `.to_text()` for easy serialization to the agent.
- **Stateful** - The browser persists between tool calls. Open once, use many times.
- **Stealth built-in** - Agents can browse real websites without triggering bot detection.
- **User handover** - When the agent hits a CAPTCHA or needs human help, `relaunch(headless=False)` opens a visible window. The user interacts, then the agent takes back control.

### Example: MCP Tool Wrapper

```python
from naked_web.automation import AutoBrowser
from naked_web import get_default_playwright_profile_path

# Singleton instance - persists across tool calls
browser = AutoBrowser(
    headless=True,
    user_data_dir=str(get_default_playwright_profile_path()),
)

def browser_tool(action: str, **kwargs) -> str:
    """Single tool that handles all browser actions."""

    if action == "open":
        browser.launch()
        if kwargs.get("url"):
            browser.navigate(kwargs["url"])
        return "Browser opened"

    if action == "navigate":
        return browser.navigate(kwargs["url"]).to_text()

    if action == "state":
        return browser.get_state().to_text()

    if action == "click":
        return browser.click(kwargs["index"]).to_text()

    if action == "type":
        return browser.type_text(kwargs["index"], kwargs["text"]).to_text()

    if action == "extract_content":
        return browser.extract_content().to_text()

    if action == "show_browser":  # Hand over to user
        return browser.relaunch(headless=False).to_text()

    if action == "hide_browser":  # Take back from user
        return browser.relaunch(headless=True).to_text()

    if action == "close":
        return browser.close().to_text()
```

### Agent Workflow Example

```
Agent: browser_tool(action="open", url="https://example.com")
       -> "Browser launched. Navigated to https://example.com"

Agent: browser_tool(action="state")
       -> "URL: https://example.com\nElements:\n  [1] a 'More info'\n  [2] input 'Search'"

Agent: browser_tool(action="type", index=2, text="python web scraping")
       -> "Typed 'python web scraping' into element [2]"

Agent: browser_tool(action="click", index=3)  # Submit button
       -> "Clicked element [3]"

Agent: browser_tool(action="extract_content")
       -> "# Search Results\n1. Beautiful Soup...\n2. Scrapy..."
```

### CAPTCHA Handover Pattern

When the agent detects a CAPTCHA or needs user interaction:

```
Agent: browser_tool(action="show_browser")
       -> "Browser relaunched in visible mode at https://protected-site.com"

Agent: ask_user("Browser is visible. Please solve the CAPTCHA, then say 'done'.")
User:  "done"

Agent: browser_tool(action="hide_browser")
       -> "Browser relaunched in headless mode at https://protected-site.com"

Agent: browser_tool(action="extract_content")  # CAPTCHA solved, page loads
       -> "# Welcome to Protected Site..."
```

---

## Architecture

```
naked_web/
  __init__.py              # Public API surface
  scrape.py                # HTTP fetch, Selenium rendering, asset extraction
  search.py                # Google Custom Search client
  content.py               # Structured content extraction
  crawler.py               # BFS site crawler + pattern search
  pagination.py            # Line/char-based HTML pagination
  core/
    config.py              # NakedWebConfig dataclass
    models.py              # Pydantic models (PageSnapshot, PageAssets, etc.)
  utils/
    browser.py             # Selenium helpers (scroll, wait)
    profiles.py            # Cross-platform profile path/copy helpers
    stealth.py             # Anti-detection (CDP injection, mouse, scrolling)
    text.py                # Text cleaning utilities
    timing.py              # Delay/jitter helpers
  automation/              # Playwright-based browser automation
    browser.py             # AutoBrowser class
    actions.py             # Click, type, scroll, extract, screenshot
    state.py               # DOM state extraction engine
    models.py              # ActionResult, PageState, InteractiveElement, TabInfo
```

---

## Public API Reference

### Core Scraping

| Export | Description |
|---|---|
| `NakedWebConfig` | Global configuration dataclass |
| `fetch_page(url, cfg, use_js, use_stealth)` | Fetch a single page (HTTP / Selenium / Stealth) |
| `download_assets(snapshot, output_dir, cfg)` | Download assets from a snapshot to disk |
| `extract_content(snapshot, ...)` | Extract structured content bundle |
| `collect_page(url, ...)` | One-shot fetch + extract + paginate |

### Search

| Export | Description |
|---|---|
| `SearchClient(cfg)` | Google Custom Search with content enrichment |

### Crawling

| Export | Description |
|---|---|
| `crawl_site(url, cfg, ...)` | BFS crawler with depth/duration/throttle controls |
| `find_text_matches(pages, patterns, ...)` | Regex/glob search across crawled page text |
| `find_asset_matches(pages, patterns, ...)` | Regex/glob search across asset metadata |

### Pagination

| Export | Description |
|---|---|
| `get_html_lines(snapshot, start_line, num_lines)` | Line-based HTML pagination |
| `get_html_chars(snapshot, start, length)` | Character-based HTML pagination |
| `slice_text_lines(text, start_line, num_lines)` | Line-based raw text pagination |
| `slice_text_chars(text, start, length)` | Character-based raw text pagination |

### Stealth (Selenium)

| Export | Description |
|---|---|
| `fetch_with_stealth(url, cfg, ...)` | Full stealth fetch with humanization |
| `setup_stealth_driver(cfg, ...)` | Create a stealth-configured Chrome driver |
| `inject_stealth_scripts(driver)` | Inject CDP anti-detection scripts |
| `random_mouse_movement(driver)` | Simulate human-like mouse movements |
| `random_scroll_pattern(driver)` | Simulate realistic scrolling behavior |

### Automation (Playwright)

| Export | Description |
|---|---|
| `AutoBrowser` | Full browser automation controller |
| `BrowserActionResult` | Result model for browser actions |
| `PageState` | Page state with indexed interactive elements |
| `InteractiveElement` | Single interactive DOM element model |
| `TabInfo` | Browser tab information model |

### Models

| Export | Description |
|---|---|
| `PageSnapshot` | Complete page fetch result (HTML, text, assets, metadata) |
| `PageAssets` | Categorized asset URLs with context details |
| `AssetContext` | Rich metadata for a single asset |
| `PageContentBundle` | Structured content (meta, headings, paragraphs, styles) |
| `MetaTag` | Parsed meta tag |
| `HeadingBlock` | Heading level + text |
| `LineSlice` / `CharSlice` | Pagination result models |
| `SearchResult` | Single search result entry |

---

## Limitations & Notes

- **TLS fingerprinting** - Chrome's TLS signature can be identified by advanced detectors.
- **Canvas/WebGL** - GPU rendering patterns may differ in automated contexts.
- **IP reputation** - Datacenter IPs are often flagged. Consider residential proxies for heavy use.
- **Selenium and Playwright are optional** - Core HTTP scraping works without either engine installed.
- **Google Search requires API keys** - Get them from the [Google Custom Search Console](https://programmablesearchengine.google.com/).

---

## Author

Built by **[Ranit Bhowmick](https://ranitbhowmick.com)**

---

## License

MIT
