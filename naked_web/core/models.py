"""Shared Pydantic models for search and scraping outputs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str
    score: Optional[float] = None
    raw: Optional[Dict[str, Any]] = None
    content: Optional[str] = None


class AssetContext(BaseModel):
    url: str
    tag: str
    attribute: str
    attrs: Dict[str, str] = Field(default_factory=dict)
    alt: Optional[str] = None
    caption: Optional[str] = None
    text: Optional[str] = None
    context: Optional[str] = None
    position: Optional[int] = None
    snippet: Optional[str] = None


class PageAssets(BaseModel):
    stylesheets: List[str] = Field(default_factory=list)
    scripts: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    media: List[str] = Field(default_factory=list)
    fonts: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    stylesheet_details: List[AssetContext] = Field(default_factory=list)
    script_details: List[AssetContext] = Field(default_factory=list)
    image_details: List[AssetContext] = Field(default_factory=list)
    media_details: List[AssetContext] = Field(default_factory=list)
    font_details: List[AssetContext] = Field(default_factory=list)
    link_details: List[AssetContext] = Field(default_factory=list)


class PageSnapshot(BaseModel):
    url: str
    final_url: str
    status_code: int
    headers: Dict[str, str]
    html: str
    text: str
    assets: PageAssets
    js_rendered: bool
    timestamp: float
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class LineSlice(BaseModel):
    content: str
    start_line: int
    end_line: int
    total_lines: int
    has_more: bool
    is_end: bool
    next_start: Optional[int]
    prev_start: Optional[int]

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class CharSlice(BaseModel):
    content: str
    start: int
    end: int
    total_size: int
    has_more: bool
    is_end: bool
    next_start: Optional[int]
    prev_start: Optional[int]

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class MetaTag(BaseModel):
    name: Optional[str] = None
    property: Optional[str] = None
    content: Optional[str] = None


class HeadingBlock(BaseModel):
    level: str
    text: str


class PageContentBundle(BaseModel):
    title: Optional[str] = None
    meta: List[MetaTag] = Field(default_factory=list)
    headings: List[HeadingBlock] = Field(default_factory=list)
    paragraphs: List[str] = Field(default_factory=list)
    inline_styles: List[str] = Field(default_factory=list)
    css_links: List[str] = Field(default_factory=list)
    font_links: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
