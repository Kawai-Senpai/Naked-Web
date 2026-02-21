"""
Browser action executor - click, type, navigate, scroll, extract content.

All actions operate on the current page and return ActionResult objects
with success/error information.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

from .models import ActionResult

if TYPE_CHECKING:
    from playwright.sync_api import Page
    from .state import PageState


# ---------------------------------------------------------------------------
# JavaScript helpers
# ---------------------------------------------------------------------------

JS_EXTRACT_MARKDOWN = r"""
() => {
    // Lightweight DOM-to-text extractor that preserves structure
    function nodeToText(node, depth) {
        if (depth > 50) return "";
        if (node.nodeType === 3) {  // Text node
            return node.textContent.replace(/\s+/g, " ");
        }
        if (node.nodeType !== 1) return "";

        const tag = node.tagName.toLowerCase();
        // Skip non-content elements
        if (["script", "style", "noscript", "svg", "meta", "link", "head"].includes(tag)) return "";
        // Skip hidden elements
        const s = window.getComputedStyle(node);
        if (s.display === "none" || s.visibility === "hidden") return "";

        let children = "";
        for (const child of node.childNodes) {
            children += nodeToText(child, depth + 1);
        }

        // Apply tag-specific formatting
        switch (tag) {
            case "h1": return "\n# " + children.trim() + "\n";
            case "h2": return "\n## " + children.trim() + "\n";
            case "h3": return "\n### " + children.trim() + "\n";
            case "h4": return "\n#### " + children.trim() + "\n";
            case "h5": return "\n##### " + children.trim() + "\n";
            case "h6": return "\n###### " + children.trim() + "\n";
            case "p": return "\n" + children.trim() + "\n";
            case "br": return "\n";
            case "hr": return "\n---\n";
            case "li": return "\n- " + children.trim();
            case "blockquote": return "\n> " + children.trim() + "\n";
            case "pre":
            case "code":
                return "\n```\n" + children.trim() + "\n```\n";
            case "a":
                const href = node.getAttribute("href") || "";
                const text = children.trim();
                if (href && text) return `[${text}](${href})`;
                return text;
            case "img":
                const alt = node.getAttribute("alt") || "";
                const src = node.getAttribute("src") || "";
                if (src.startsWith("data:")) return "";  // Skip base64
                return alt ? `![${alt}](${src})` : "";
            case "strong": case "b": return "**" + children.trim() + "**";
            case "em": case "i": return "*" + children.trim() + "*";
            case "table": return "\n" + children + "\n";
            case "tr": return children.trim() + "\n";
            case "th": return "| **" + children.trim() + "** ";
            case "td": return "| " + children.trim() + " ";
            case "div": case "section": case "article": case "main":
            case "aside": case "nav": case "header": case "footer":
                return "\n" + children;
            default:
                return children;
        }
    }

    const body = document.body;
    if (!body) return "";
    let text = nodeToText(body, 0);

    // Clean up excessive whitespace
    text = text.replace(/\n{3,}/g, "\n\n");
    text = text.replace(/[ \t]+/g, " ");
    return text.trim();
}
"""


JS_EXTRACT_LINKS = r"""
() => {
    const links = [];
    const seen = new Set();
    document.querySelectorAll("a[href]").forEach(a => {
        const href = a.href;
        const text = (a.innerText || a.getAttribute("aria-label") || "").trim().slice(0, 100);
        if (!href || seen.has(href)) return;
        if (href.startsWith("javascript:") || href.startsWith("data:")) return;
        seen.add(href);
        links.push({ text, href });
    });
    return links;
}
"""


# ---------------------------------------------------------------------------
# Action functions
# ---------------------------------------------------------------------------

def navigate(page: "Page", url: str, timeout: int = 30000) -> ActionResult:
    """Navigate to a URL."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        return ActionResult(
            success=True,
            message=f"Navigated to {url}",
        )
    except Exception as e:
        return ActionResult(
            success=False,
            error=f"Navigation failed: {str(e)}",
        )


def click_element(page: "Page", index: int, state: "PageState") -> ActionResult:
    """
    Click an interactive element by its index from the last state snapshot.

    Args:
        page: Playwright Page object.
        index: 1-based index from the PageState.elements list.
        state: The last PageState snapshot (needed to resolve the selector).

    Returns:
        ActionResult with success/error info.
    """
    # Find the element in the state
    element = None
    for el in state.elements:
        if el.index == index:
            element = el
            break

    if element is None:
        return ActionResult(
            success=False,
            error=f"Element index {index} not found. Max index is {len(state.elements)}. Run state extraction again.",
        )

    if element.disabled:
        return ActionResult(
            success=False,
            error=f"Element [{index}] ({element.tag} \"{element.label}\") is disabled.",
        )

    selector = element.selector
    if not selector:
        return ActionResult(
            success=False,
            error=f"Element [{index}] has no selector. Cannot click.",
        )

    try:
        locator = page.locator(selector).first
        # Scroll into view first
        locator.scroll_into_view_if_needed(timeout=5000)
        locator.click(timeout=10000)
        return ActionResult(
            success=True,
            message=f"Clicked [{index}] {element.tag} \"{element.label}\"",
        )
    except Exception as e:
        # Retry with force click
        try:
            page.locator(selector).first.click(force=True, timeout=5000)
            return ActionResult(
                success=True,
                message=f"Force-clicked [{index}] {element.tag} \"{element.label}\"",
            )
        except Exception as e2:
            return ActionResult(
                success=False,
                error=f"Click failed on [{index}] {element.tag} \"{element.label}\": {str(e2)}",
            )


def type_text(
    page: "Page",
    index: int,
    text: str,
    state: "PageState",
    clear: bool = True,
) -> ActionResult:
    """
    Type text into an input element by index.

    Args:
        page: Playwright Page object.
        index: 1-based index from PageState.elements.
        text: Text to type.
        state: Last PageState snapshot.
        clear: Whether to clear existing content before typing (default True).

    Returns:
        ActionResult.
    """
    element = None
    for el in state.elements:
        if el.index == index:
            element = el
            break

    if element is None:
        return ActionResult(
            success=False,
            error=f"Element index {index} not found. Max index is {len(state.elements)}. Run state extraction again.",
        )

    selector = element.selector
    if not selector:
        return ActionResult(
            success=False,
            error=f"Element [{index}] has no selector. Cannot type.",
        )

    try:
        locator = page.locator(selector).first
        locator.scroll_into_view_if_needed(timeout=5000)

        if clear:
            locator.fill(text, timeout=10000)
        else:
            locator.click(timeout=5000)
            page.keyboard.type(text)

        return ActionResult(
            success=True,
            message=f"Typed \"{text[:50]}{'...' if len(text) > 50 else ''}\" into [{index}] {element.tag} \"{element.label}\"",
        )
    except Exception as e:
        # Fallback: click then keyboard type
        try:
            locator = page.locator(selector).first
            locator.click(timeout=5000)
            if clear:
                page.keyboard.press("Control+a")
                page.keyboard.press("Backspace")
            page.keyboard.type(text)
            return ActionResult(
                success=True,
                message=f"Typed (keyboard) \"{text[:50]}{'...' if len(text) > 50 else ''}\" into [{index}] {element.tag}",
            )
        except Exception as e2:
            return ActionResult(
                success=False,
                error=f"Type failed on [{index}] {element.tag}: {str(e2)}",
            )


def scroll_page(page: "Page", direction: str = "down", amount: float = 1.0) -> ActionResult:
    """
    Scroll the page.

    Args:
        page: Playwright Page object.
        direction: "down" or "up".
        amount: Number of pages to scroll (0.5 = half page, 1.0 = full page, 999 = to bottom/top).

    Returns:
        ActionResult.
    """
    try:
        if amount >= 100:
            # Scroll to absolute top or bottom
            if direction == "down":
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                return ActionResult(success=True, message="Scrolled to bottom of page")
            else:
                page.evaluate("window.scrollTo(0, 0)")
                return ActionResult(success=True, message="Scrolled to top of page")

        viewport_height = page.evaluate("window.innerHeight || 768")
        scroll_px = int(viewport_height * amount)

        if direction == "up":
            scroll_px = -scroll_px

        page.evaluate(f"window.scrollBy(0, {scroll_px})")
        return ActionResult(
            success=True,
            message=f"Scrolled {direction} by {abs(scroll_px)}px ({amount} pages)",
        )
    except Exception as e:
        return ActionResult(success=False, error=f"Scroll failed: {str(e)}")


def go_back(page: "Page") -> ActionResult:
    """Navigate back in browser history."""
    try:
        page.go_back(wait_until="domcontentloaded", timeout=15000)
        return ActionResult(success=True, message="Navigated back")
    except Exception as e:
        return ActionResult(success=False, error=f"Go back failed: {str(e)}")


def send_keys(page: "Page", keys: str) -> ActionResult:
    """
    Send keyboard keys or shortcuts.

    Args:
        page: Playwright Page object.
        keys: Key combination (e.g., "Enter", "Escape", "Control+a", "Tab").

    Returns:
        ActionResult.
    """
    try:
        page.keyboard.press(keys)
        return ActionResult(success=True, message=f"Sent keys: {keys}")
    except Exception as e:
        return ActionResult(success=False, error=f"Send keys failed: {str(e)}")


def extract_content(page: "Page") -> ActionResult:
    """
    Extract the page content as clean markdown-like text.

    Returns:
        ActionResult with extracted_content containing the page text.
    """
    try:
        content = page.evaluate(JS_EXTRACT_MARKDOWN)
        if not content:
            content = "(Page appears empty or could not extract content)"
        return ActionResult(
            success=True,
            message="Content extracted",
            extracted_content=content,
        )
    except Exception as e:
        return ActionResult(
            success=False,
            error=f"Content extraction failed: {str(e)}",
        )


def extract_links(page: "Page") -> ActionResult:
    """
    Extract all links from the current page.

    Returns:
        ActionResult with extracted_content containing links as text.
    """
    try:
        links = page.evaluate(JS_EXTRACT_LINKS)
        if not links:
            return ActionResult(
                success=True,
                message="No links found on page",
                extracted_content="(No links found)",
            )

        lines = []
        for link in links:
            text = link.get("text", "").strip()
            href = link.get("href", "")
            if text:
                lines.append(f"- [{text}]({href})")
            else:
                lines.append(f"- {href}")

        content = f"Found {len(links)} links:\n" + "\n".join(lines)
        return ActionResult(
            success=True,
            message=f"Extracted {len(links)} links",
            extracted_content=content,
        )
    except Exception as e:
        return ActionResult(
            success=False,
            error=f"Link extraction failed: {str(e)}",
        )


def select_option(page: "Page", index: int, value: str, state: "PageState") -> ActionResult:
    """
    Select an option from a dropdown/select element by index.

    Args:
        page: Playwright Page object.
        index: 1-based index of the select element.
        value: The option value or label to select.
        state: Last PageState snapshot.

    Returns:
        ActionResult.
    """
    element = None
    for el in state.elements:
        if el.index == index:
            element = el
            break

    if element is None:
        return ActionResult(
            success=False,
            error=f"Element index {index} not found.",
        )

    selector = element.selector
    if not selector:
        return ActionResult(success=False, error=f"Element [{index}] has no selector.")

    try:
        locator = page.locator(selector).first
        # Try selecting by value first, then by label
        try:
            locator.select_option(value=value, timeout=5000)
        except Exception:
            locator.select_option(label=value, timeout=5000)

        return ActionResult(
            success=True,
            message=f"Selected \"{value}\" in [{index}] {element.tag}",
        )
    except Exception as e:
        return ActionResult(
            success=False,
            error=f"Select option failed on [{index}]: {str(e)}",
        )


def wait_for_page(page: "Page", seconds: float = 2.0) -> ActionResult:
    """
    Wait for a specified number of seconds (useful for dynamic content).

    Args:
        page: Playwright Page object.
        seconds: Number of seconds to wait (capped at 30).

    Returns:
        ActionResult.
    """
    import time
    actual = min(max(seconds, 0.1), 30.0)
    time.sleep(actual)
    return ActionResult(
        success=True,
        message=f"Waited {actual:.1f} seconds",
    )


def take_screenshot(page: "Page", path: str) -> ActionResult:
    """
    Take a screenshot of the current page and save to file.

    Args:
        page: Playwright Page object.
        path: File path to save the screenshot to.

    Returns:
        ActionResult.
    """
    try:
        page.screenshot(path=path, full_page=False)
        return ActionResult(
            success=True,
            message=f"Screenshot saved to {path}",
        )
    except Exception as e:
        return ActionResult(
            success=False,
            error=f"Screenshot failed: {str(e)}",
        )
