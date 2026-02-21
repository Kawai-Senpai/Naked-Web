"""Pydantic models for the web automation module."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InteractiveElement(BaseModel):
    """A single interactive element extracted from the page DOM."""

    index: int = Field(description="1-based index for referencing this element in actions")
    tag: str = Field(description="HTML tag name (a, button, input, etc.)")
    role: str = Field(default="", description="ARIA role if present")
    type: str = Field(default="", description="Input type attribute if present")
    label: str = Field(default="", description="Best human-readable label (aria-label, text, placeholder, etc.)")
    selector: str = Field(default="", description="CSS selector for re-locating the element")
    href: str = Field(default="", description="href attribute for links")
    value: str = Field(default="", description="Current value for inputs")
    placeholder: str = Field(default="", description="Placeholder text for inputs")
    checked: Optional[bool] = Field(default=None, description="Whether checkbox/radio is checked")
    disabled: bool = Field(default=False, description="Whether the element is disabled")
    tag_name: str = Field(default="", description="Full tag name as seen in DOM")

    def short_desc(self) -> str:
        """Return a compact one-line description for LLM consumption."""
        parts = [f"[{self.index}]", self.tag]
        if self.role:
            parts.append(f'role="{self.role}"')
        if self.type:
            parts.append(f'type="{self.type}"')
        if self.label:
            parts.append(f'"{self.label}"')
        if self.value:
            parts.append(f'val="{self.value[:40]}"')
        if self.placeholder:
            parts.append(f'placeholder="{self.placeholder[:40]}"')
        if self.href and self.tag == "a":
            parts.append(f"-> {self.href[:60]}")
        if self.checked is not None:
            parts.append("checked" if self.checked else "unchecked")
        if self.disabled:
            parts.append("(disabled)")
        return " ".join(parts)


class PageState(BaseModel):
    """Full page state snapshot with interactive elements."""

    url: str = Field(description="Current page URL")
    title: str = Field(description="Current page title")
    elements: List[InteractiveElement] = Field(default_factory=list, description="Interactive elements on the page")
    scroll_position: float = Field(default=0.0, description="Current scroll position as percentage (0-100)")
    scroll_height: int = Field(default=0, description="Total scrollable height in pixels")
    viewport_height: int = Field(default=0, description="Viewport height in pixels")
    element_count: int = Field(default=0, description="Total number of interactive elements found")

    def to_text(self, max_elements: int = 100) -> str:
        """Convert page state to a compact text representation for LLM consumption."""
        lines = [
            f"URL: {self.url}",
            f"Title: {self.title}",
            f"Scroll: {self.scroll_position:.0f}% ({self.viewport_height}px viewport, {self.scroll_height}px total)",
            f"Interactive elements ({self.element_count} total):",
        ]
        shown = self.elements[:max_elements]
        for el in shown:
            lines.append(f"  {el.short_desc()}")
        if self.element_count > max_elements:
            lines.append(f"  ... ({self.element_count - max_elements} more elements)")
        return "\n".join(lines)


class ActionResult(BaseModel):
    """Result of a browser action."""

    success: bool = Field(default=True, description="Whether the action succeeded")
    message: str = Field(default="", description="Human-readable result description")
    error: Optional[str] = Field(default=None, description="Error message if action failed")
    extracted_content: Optional[str] = Field(default=None, description="Content extracted from the page")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the action")

    def to_text(self) -> str:
        """Return a concise text summary."""
        if self.error:
            return f"ERROR: {self.error}"
        parts = []
        if self.message:
            parts.append(self.message)
        if self.extracted_content:
            parts.append(self.extracted_content)
        return "\n".join(parts) if parts else "OK"


class TabInfo(BaseModel):
    """Information about a browser tab."""

    tab_id: int = Field(description="Tab index (0-based)")
    url: str = Field(description="Current URL of the tab")
    title: str = Field(description="Current title of the tab")
    is_active: bool = Field(default=False, description="Whether this is the currently active tab")
