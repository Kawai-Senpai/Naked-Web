"""HTTP fetching, Selenium rendering, and asset helpers."""

from __future__ import annotations

import contextlib
import hashlib
import random
import re
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .core.config import NakedWebConfig
from .core.models import AssetContext, PageAssets, PageSnapshot
from .utils.browser import simulate_human_scroll, wait_for_document_ready
from .utils.text import clean_text_from_html, trim_text
from .utils.timing import maybe_sleep

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.support.ui import WebDriverWait

    _SELENIUM_AVAILABLE = True
except Exception:
    _SELENIUM_AVAILABLE = False


def _allowed_by_robots(url: str, user_agent: str) -> bool:
    from urllib.robotparser import RobotFileParser

    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True




def _attrs_dict(tag) -> Dict[str, str]:
    attrs: Dict[str, str] = {}
    for key, value in getattr(tag, "attrs", {}).items():
        if isinstance(value, list):
            attrs[key] = " ".join(str(item) for item in value)
        else:
            attrs[key] = str(value)
    return attrs


def _figure_caption(tag) -> Optional[str]:
    figure = tag.find_parent("figure")
    if not figure:
        return None
    caption = figure.find("figcaption")
    if not caption:
        return None
    return trim_text(caption.get_text(" ", strip=True))


def _build_context(tag, attribute: str, url: str, snippet_limit: int, **extra) -> AssetContext:
    snippet_raw = tag.decode()
    snippet = trim_text(snippet_raw, snippet_limit)
    data = {
        "url": url,
        "tag": tag.name or "",
        "attribute": attribute,
        "attrs": _attrs_dict(tag),
        "position": getattr(tag, "sourceline", None),
        "snippet": snippet,
    }
    for key, value in extra.items():
        data[key] = value
    return AssetContext(**data)


def _extract_assets(html: str, base_url: str, context_limit: int) -> PageAssets:
    soup = BeautifulSoup(html, "lxml")

    def absolutify(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        return urljoin(base_url, value)

    stylesheets: List[str] = []
    scripts: List[str] = []
    images: List[str] = []
    media: List[str] = []
    fonts: List[str] = []
    links: List[str] = []
    stylesheet_details: List[AssetContext] = []
    script_details: List[AssetContext] = []
    image_details: List[AssetContext] = []
    media_details: List[AssetContext] = []
    font_details: List[AssetContext] = []
    link_details: List[AssetContext] = []

    font_exts = (".woff", ".woff2", ".ttf", ".otf", ".eot")

    for tag in soup.find_all("link"):
        rels = [rel.lower() for rel in (tag.get("rel") or [])]
        href = absolutify(tag.get("href"))
        if not href:
            continue
        if any("stylesheet" in rel for rel in rels):
            stylesheets.append(href)
            stylesheet_details.append(
                _build_context(
                    tag,
                    "href",
                    href,
                    context_limit,
                    context=trim_text(tag.get_text(" ", strip=True), context_limit),
                )
            )
        as_attr = (tag.get("as") or "").lower()
        if as_attr == "font" or "font" in rels or href.lower().endswith(font_exts):
            fonts.append(href)
            font_details.append(
                _build_context(
                    tag,
                    "href",
                    href,
                    context_limit,
                    context=trim_text(tag.get_text(" ", strip=True), context_limit),
                )
            )

    for tag in soup.find_all("script"):
        src = absolutify(tag.get("src"))
        if src:
            scripts.append(src)
            script_details.append(
                _build_context(
                    tag,
                    "src",
                    src,
                    context_limit,
                    text=trim_text(tag.get_text(" ", strip=True), context_limit),
                )
            )

    for tag in soup.find_all("img"):
        src = absolutify(tag.get("src"))
        if src:
            images.append(src)
            image_details.append(
                _build_context(
                    tag,
                    "src",
                    src,
                    context_limit,
                    alt=tag.get("alt"),
                    caption=_figure_caption(tag),
                    context=trim_text(
                        tag.parent.get_text(" ", strip=True) if tag.parent else None,
                        context_limit,
                    ),
                )
            )
        srcset = tag.get("srcset")
        if srcset:
            first = srcset.split(",")[0].strip().split(" ")[0]
            resolved = absolutify(first)
            if resolved:
                images.append(resolved)
                image_details.append(
                    _build_context(
                        tag,
                        "srcset",
                        resolved,
                        context_limit,
                        alt=tag.get("alt"),
                        caption=_figure_caption(tag),
                        context=trim_text(
                            tag.parent.get_text(" ", strip=True) if tag.parent else None,
                            context_limit,
                        ),
                    )
                )

    for tag in soup.find_all(["video", "audio", "source"]):
        src = absolutify(tag.get("src"))
        if src:
            media.append(src)
            media_details.append(
                _build_context(
                    tag,
                    "src",
                    src,
                    context_limit,
                    context=trim_text(
                        tag.parent.get_text(" ", strip=True) if tag.parent else None,
                        context_limit,
                    ),
                )
            )

    for tag in soup.find_all("a"):
        href = tag.get("href")
        if href and not href.startswith("#"):
            resolved = absolutify(href)
            if resolved:
                links.append(resolved)
                link_details.append(
                    _build_context(
                        tag,
                        "href",
                        resolved,
                        context_limit,
                        text=trim_text(tag.get_text(" ", strip=True), context_limit),
                        context=trim_text(
                            tag.parent.get_text(" ", strip=True) if tag.parent else None,
                            context_limit,
                        ),
                    )
                )

    def dedupe(items: Iterable[str]) -> List[str]:
        seen = set()
        ordered: List[str] = []
        for item in items:
            if item not in seen:
                seen.add(item)
                ordered.append(item)
        return ordered

    return PageAssets(
        stylesheets=dedupe(stylesheets),
        scripts=dedupe(scripts),
        images=dedupe(images),
        media=dedupe(media),
        fonts=dedupe(fonts),
        links=dedupe(links),
        stylesheet_details=stylesheet_details,
        script_details=script_details,
        image_details=image_details,
        media_details=media_details,
        font_details=font_details,
        link_details=link_details,
    )


def _fetch_with_requests(
    url: str,
    cfg: NakedWebConfig,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[str, Dict[str, str], int, str]:
    merged = {
        "User-Agent": cfg.user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    if headers:
        merged.update(headers)

    resp = requests.get(url, headers=merged, timeout=cfg.request_timeout)
    resp.raise_for_status()
    return resp.text, dict(resp.headers), resp.status_code, resp.url


def _fetch_with_selenium(url: str, cfg: NakedWebConfig) -> Tuple[str, Dict[str, str], int, str]:
    if not _SELENIUM_AVAILABLE:
        raise RuntimeError(
            "Selenium + undetected-chromedriver are not installed. Run `pip install -e .[selenium]`."
        )

    options = uc.ChromeOptions()
    options.add_argument(f"--user-agent={cfg.user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=en-US,en;q=0.9")
    if cfg.selenium_window_size:
        options.add_argument(f"--window-size={cfg.selenium_window_size}")
    if cfg.selenium_headless:
        options.add_argument("--headless=new")

    driver = None
    try:
        driver = uc.Chrome(options=options, headless=cfg.selenium_headless)
        driver.set_page_load_timeout(cfg.selenium_page_load_timeout)
        driver.implicitly_wait(cfg.selenium_wait_timeout)

        maybe_sleep(cfg.humanize_delay_range)
        driver.get(url)
        wait_for_document_ready(driver, cfg.selenium_wait_timeout)
        simulate_human_scroll(driver, (0.2, 0.6))
        maybe_sleep(cfg.humanize_delay_range)

        html = driver.page_source
        final_url = driver.current_url
        headers = {"x-nakedweb-final-url": final_url}
        return html, headers, 200, final_url
    finally:
        if driver:
            with contextlib.suppress(Exception):
                driver.quit()


def fetch_page(
    url: str,
    cfg: Optional[NakedWebConfig] = None,
    use_js: bool = False,
    extra_headers: Optional[Dict[str, str]] = None,
) -> PageSnapshot:
    cfg = cfg or NakedWebConfig()
    if cfg.respect_robots_txt and not _allowed_by_robots(url, cfg.user_agent):
        return PageSnapshot(
            url=url,
            final_url=url,
            status_code=0,
            headers={},
            html="",
            text="",
            assets=PageAssets(),
            js_rendered=use_js,
            timestamp=time.time(),
            error="Blocked by robots.txt",
        )

    try:
        if use_js:
            html, headers, status_code, final_url = _fetch_with_selenium(url, cfg)
        else:
            html, headers, status_code, final_url = _fetch_with_requests(url, cfg, extra_headers)

        text = clean_text_from_html(html, cfg.max_text_chars)
        assets = _extract_assets(html, final_url, cfg.asset_context_chars)
        return PageSnapshot(
            url=url,
            final_url=final_url,
            status_code=status_code,
            headers=headers,
            html=html,
            text=text,
            assets=assets,
            js_rendered=use_js,
            timestamp=time.time(),
            error=None,
        )
    except Exception as exc:
        return PageSnapshot(
            url=url,
            final_url=url,
            status_code=0,
            headers={},
            html="",
            text="",
            assets=PageAssets(),
            js_rendered=use_js,
            timestamp=time.time(),
            error=str(exc),
        )


def _unique_name(url: str) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix or ""
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    return f"asset-{digest}{suffix}"


def download_assets(
    snapshot: PageSnapshot,
    output_dir: str,
    include: Optional[Sequence[str]] = None,
    cfg: Optional[NakedWebConfig] = None,
) -> Dict[str, List[str]]:
    cfg = cfg or NakedWebConfig()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    include = include or ["stylesheets", "scripts", "images", "media", "fonts"]
    categories = {name: getattr(snapshot.assets, name, []) for name in include}
    saved: Dict[str, List[str]] = {name: [] for name in include}

    for category, urls in categories.items():
        for asset_url in urls:
            try:
                resp = requests.get(asset_url, timeout=cfg.request_timeout)
                resp.raise_for_status()
                if len(resp.content) > cfg.max_asset_bytes:
                    continue
                target_name = _unique_name(asset_url)
                target_path = output / target_name
                target_path.write_bytes(resp.content)
                saved[category].append(str(target_path))
            except Exception:
                continue

    return saved
