"""Google Custom Search integration."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from .core.config import NakedWebConfig
from .core.models import SearchResult
from .scrape import fetch_page


class GoogleSearchClient:
    api_url = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, cfg: NakedWebConfig):
        self.cfg = cfg

    def search(self, query: str, max_results: int = 5, start_index: int = 1) -> List[SearchResult]:
        self.cfg.ensure_google_ready()

        params = {
            "key": self.cfg.google_api_key,
            "cx": self.cfg.google_cse_id,
            "q": query,
            "num": max(1, min(max_results, 10)),
            "start": max(1, start_index),
        }
        resp = requests.get(self.api_url, params=params, timeout=self.cfg.request_timeout)
        resp.raise_for_status()
        payload = resp.json()
        items = payload.get("items", [])

        results: List[SearchResult] = []
        for item in items[:max_results]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="google",
                    raw=item,
                )
            )
        return results


class SearchClient:
    """Unified interface for search + optional enrichment."""

    def __init__(self, cfg: Optional[NakedWebConfig] = None):
        self.cfg = cfg or NakedWebConfig()
        self.google = GoogleSearchClient(self.cfg)

    def search(
        self,
        query: str,
        max_results: int = 5,
        include_page_content: bool = False,
        use_js_for_pages: bool = False,
    ) -> Dict[str, Any]:
        results = self.google.search(query=query, max_results=max_results)
        serialized: List[Dict[str, Any]] = []
        for result in results:
            item = {
                "title": result.title,
                "url": result.url,
                "snippet": result.snippet,
                "source": result.source,
                "score": result.score,
            }
            if include_page_content and result.url:
                snap = fetch_page(result.url, cfg=self.cfg, use_js=use_js_for_pages)
                item["content"] = snap.text
                item["status_code"] = snap.status_code
                item["final_url"] = snap.final_url
                item["error"] = snap.error
            serialized.append(item)
        return {
            "query": query,
            "provider": "google",
            "results": serialized,
        }
