"""Pagination helpers that work on HTML snapshots or raw text."""

from __future__ import annotations

from typing import Dict, Optional

from .core.models import CharSlice, LineSlice, PageSnapshot


def _slice_lines(text: str, start_line: int, num_lines: int) -> LineSlice:
    if start_line < 0:
        start_line = 0
    lines = text.splitlines()
    total_lines = len(lines)
    if start_line >= total_lines:
        return LineSlice("", start_line, start_line, total_lines, False, True, None, None)

    end_line = min(start_line + max(1, num_lines), total_lines)
    content = "\n".join(lines[start_line:end_line])
    return LineSlice(
        content=content,
        start_line=start_line,
        end_line=end_line - 1,
        total_lines=total_lines,
        has_more=end_line < total_lines,
        is_end=end_line >= total_lines,
        next_start=end_line if end_line < total_lines else None,
        prev_start=max(0, start_line - num_lines) if start_line > 0 else None,
    )


def get_html_lines(snapshot: PageSnapshot, start_line: int = 0, num_lines: int = 50) -> Dict[str, object]:
    slice_obj = _slice_lines(snapshot.html, start_line, num_lines)
    return slice_obj.to_dict()


def slice_text_lines(text: str, start_line: int = 0, num_lines: int = 50) -> Dict[str, object]:
    return _slice_lines(text, start_line, num_lines).to_dict()


def _slice_chars(text: str, start: int, length: int) -> CharSlice:
    if start < 0:
        start = 0
    total_size = len(text)
    if start >= total_size:
        return CharSlice("", start, start, total_size, False, True, None, None)

    end = min(start + max(1, length), total_size)
    chunk = text[start:end]
    return CharSlice(
        content=chunk,
        start=start,
        end=end,
        total_size=total_size,
        has_more=end < total_size,
        is_end=end >= total_size,
        next_start=end if end < total_size else None,
        prev_start=max(0, start - length) if start > 0 else None,
    )


def get_html_chars(snapshot: PageSnapshot, start: int = 0, length: int = 5000) -> Dict[str, object]:
    return _slice_chars(snapshot.html, start, length).to_dict()


def slice_text_chars(text: str, start: int = 0, length: int = 5000) -> Dict[str, object]:
    return _slice_chars(text, start, length).to_dict()
