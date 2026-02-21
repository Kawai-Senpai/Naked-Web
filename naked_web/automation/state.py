"""
DOM state extraction - the core engine that turns a live page into a structured
list of interactive elements with stable indices.

Inspired by browser-use's DOM serializer but uses Playwright's JS evaluation
API instead of raw CDP, making it simpler and more portable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from .models import InteractiveElement, PageState

if TYPE_CHECKING:
    from playwright.sync_api import Page


# ---------------------------------------------------------------------------
# JavaScript snippets executed inside the browser context
# ---------------------------------------------------------------------------

# CSS selector that catches the vast majority of interactive elements.
# Extended with common patterns from browser-use's ClickableElementDetector.
INTERACTIVE_CSS = """
a[href],
button,
input,
textarea,
select,
option,
details,
summary,
[role="button"],
[role="link"],
[role="menuitem"],
[role="option"],
[role="radio"],
[role="checkbox"],
[role="tab"],
[role="textbox"],
[role="combobox"],
[role="slider"],
[role="spinbutton"],
[role="search"],
[role="searchbox"],
[contenteditable="true"],
[tabindex]:not([tabindex="-1"]),
[onclick],
[onmousedown],
[onmouseup],
[onkeydown]
""".strip()


JS_EXTRACT_ELEMENTS = r"""
() => {
    const INTERACTIVE_CSS = `""" + INTERACTIVE_CSS + r"""`;

    function isVisible(el) {
        const s = window.getComputedStyle(el);
        if (!s) return false;
        if (s.display === "none" || s.visibility === "hidden") return false;
        try { if (parseFloat(s.opacity) <= 0) return false; } catch(_) {}
        const r = el.getBoundingClientRect();
        if (!r || (r.width === 0 && r.height === 0)) return false;
        // Must be at least partially in the viewport (or the document)
        if (r.bottom < 0 || r.right < 0) return false;
        return true;
    }

    function normText(t) {
        if (!t) return "";
        return t.replace(/\s+/g, " ").trim().slice(0, 120);
    }

    function labelFor(el) {
        // Priority: aria-label > title > placeholder > innerText > value
        const aria = el.getAttribute("aria-label")
                  || el.getAttribute("title")
                  || el.getAttribute("placeholder");
        if (aria) return normText(aria);
        // For links and buttons, innerText is the label
        const tag = el.tagName.toLowerCase();
        if (tag === "a" || tag === "button" || tag === "summary" ||
            tag === "option" || el.getAttribute("role")) {
            const it = normText(el.innerText);
            if (it) return it;
        }
        // For inputs, use value or placeholder
        if (tag === "input" || tag === "textarea") {
            const ph = el.getAttribute("placeholder");
            if (ph) return normText(ph);
        }
        // Label element referencing this input
        if (el.id) {
            const lbl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
            if (lbl) return normText(lbl.innerText);
        }
        // Fallback: nearest label ancestor
        const labelAncestor = el.closest("label");
        if (labelAncestor) return normText(labelAncestor.innerText);
        return "";
    }

    function cssSelector(el) {
        // Prefer stable attributes
        const testId = el.getAttribute("data-testid")
                    || el.getAttribute("data-test")
                    || el.getAttribute("data-qa")
                    || el.getAttribute("data-cy");
        if (testId) return `[data-testid="${CSS.escape(testId)}"]`;
        if (el.id) return `#${CSS.escape(el.id)}`;

        const parts = [];
        let cur = el;
        while (cur && cur.nodeType === 1 && cur.tagName.toLowerCase() !== "html") {
            let part = cur.tagName.toLowerCase();
            const role = cur.getAttribute("role");
            if (role) part += `[role="${CSS.escape(role)}"]`;
            const parent = cur.parentElement;
            if (parent) {
                const siblings = Array.from(parent.children).filter(
                    c => c.tagName === cur.tagName
                );
                if (siblings.length > 1) {
                    const idx = siblings.indexOf(cur) + 1;
                    part += `:nth-of-type(${idx})`;
                }
            }
            parts.unshift(part);
            cur = parent;
        }
        return parts.join(" > ");
    }

    const all = document.querySelectorAll(INTERACTIVE_CSS);
    const out = [];
    const seen = new Set();

    for (const el of all) {
        if (!isVisible(el)) continue;
        if (el.disabled || el.getAttribute("aria-disabled") === "true") {
            // Still include but mark disabled
        }
        const tag = el.tagName.toLowerCase();
        const selector = cssSelector(el);
        const label = labelFor(el);
        const href = el.getAttribute("href") || "";
        const role = el.getAttribute("role") || "";
        const type = el.getAttribute("type") || "";
        const value = (el.value !== undefined && el.value !== null) ? String(el.value).slice(0, 100) : "";
        const placeholder = el.getAttribute("placeholder") || "";
        const disabled = !!el.disabled || el.getAttribute("aria-disabled") === "true";
        const checked = (el.type === "checkbox" || el.type === "radio") ? el.checked : null;

        // Deduplicate by (selector + label + tag)
        const key = selector + "|" + label + "|" + tag + "|" + href;
        if (seen.has(key)) continue;
        seen.add(key);

        out.push({
            tag, role, type, label, selector, href,
            value, placeholder, disabled,
            checked: checked,
        });
    }

    // Also detect cursor:pointer elements that aren't in the selector list
    // (common pattern: divs with onclick handlers added via JS)
    const allEls = document.querySelectorAll("div, span, li, p, img, svg");
    for (const el of allEls) {
        if (!isVisible(el)) continue;
        const s = window.getComputedStyle(el);
        if (s.cursor !== "pointer") continue;
        // Skip if already captured
        const selector = cssSelector(el);
        const label = labelFor(el);
        const tag = el.tagName.toLowerCase();
        const href = "";
        const key = selector + "|" + label + "|" + tag + "|" + href;
        if (seen.has(key)) continue;
        seen.add(key);

        out.push({
            tag,
            role: el.getAttribute("role") || "",
            type: "",
            label,
            selector,
            href: "",
            value: "",
            placeholder: "",
            disabled: false,
            checked: null,
        });
    }

    return out;
}
"""


JS_SCROLL_INFO = """
() => {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop || 0;
    const scrollHeight = Math.max(
        document.body.scrollHeight || 0,
        document.documentElement.scrollHeight || 0
    );
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
    const pct = scrollHeight > viewportHeight
        ? (scrollTop / (scrollHeight - viewportHeight)) * 100
        : 0;
    return {
        scroll_position: Math.min(pct, 100),
        scroll_height: scrollHeight,
        viewport_height: viewportHeight,
    };
}
"""


# ---------------------------------------------------------------------------
# State extraction functions
# ---------------------------------------------------------------------------

def extract_page_state(page: "Page", max_elements: int = 200) -> PageState:
    """
    Extract the full interactive state of the current page.

    Runs JavaScript in the browser context to find all interactive elements,
    then returns a structured PageState with indexed elements.

    Args:
        page: Playwright Page object.
        max_elements: Maximum number of elements to return (to avoid token explosion).

    Returns:
        PageState with all interactive elements and scroll info.
    """
    # Extract interactive elements via JS
    try:
        raw_elements = page.evaluate(JS_EXTRACT_ELEMENTS)
    except Exception as e:
        raw_elements = []

    # Build indexed element list (1-based to match browser-use convention)
    elements: List[InteractiveElement] = []
    for i, raw in enumerate(raw_elements[:max_elements], start=1):
        elements.append(InteractiveElement(
            index=i,
            tag=raw.get("tag", ""),
            role=raw.get("role", ""),
            type=raw.get("type", ""),
            label=raw.get("label", ""),
            selector=raw.get("selector", ""),
            href=raw.get("href", ""),
            value=raw.get("value", ""),
            placeholder=raw.get("placeholder", ""),
            checked=raw.get("checked"),
            disabled=raw.get("disabled", False),
        ))

    # Get scroll info
    try:
        scroll_info = page.evaluate(JS_SCROLL_INFO)
    except Exception:
        scroll_info = {"scroll_position": 0, "scroll_height": 0, "viewport_height": 0}

    # Get page URL and title
    try:
        url = page.url
    except Exception:
        url = ""
    try:
        title = page.title()
    except Exception:
        title = ""

    return PageState(
        url=url,
        title=title,
        elements=elements,
        scroll_position=scroll_info.get("scroll_position", 0),
        scroll_height=scroll_info.get("scroll_height", 0),
        viewport_height=scroll_info.get("viewport_height", 0),
        element_count=len(raw_elements),
    )
