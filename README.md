# Naked Web

Naked Web is a focused toolkit that wraps Google Custom Search and modern scraping primitives so agents (or humans) can pull search results, raw HTML, assets, and paginated slices with one cohesive API.

## Highlights

- Google Custom Search JSON API integration with automatic content enrichment per result
- First class scraping with optional Selenium (undetected-chromedriver) rendering for JS heavy pages
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
    user_agent="Mozilla/5.0 (compatible; NakedWeb/1.0)"
)
```

### Stealth Selenium rendering

When `use_js=True`, Naked Web spins up an undetected-chromedriver powered Selenium session that mimics human browsing. Tune the following knobs if you need stricter controls:

- `selenium_headless`: toggle windowed browsing (default `False` to avoid headless fingerprints)
- `selenium_window_size`: specify the viewport (defaults to `1366,768`)
- `selenium_page_load_timeout` / `selenium_wait_timeout`: manage waits and timeouts
- `humanize_delay_range`: random delay range (seconds) inserted before navigation and scrolls

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

snap = fetch_page("https://example.com", cfg=cfg, use_js=False)
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
