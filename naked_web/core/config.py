"""Global configuration for Naked Web."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

# Use a realistic Chrome user agent to avoid bot detection
# Update this periodically to match current browser versions
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


@dataclass(slots=True)
class NakedWebConfig:
    """Holds API credentials and runtime knobs for the toolkit."""

    google_api_key: Optional[str] = None
    google_cse_id: Optional[str] = None

    user_agent: str = DEFAULT_USER_AGENT
    request_timeout: int = 20
    max_text_chars: int = 20000
    respect_robots_txt: bool = False
    max_asset_bytes: int = 5_000_000
    asset_context_chars: int = 320
    crawl_delay_range: Tuple[float, float] = (1.0, 2.5)
    selenium_headless: bool = False
    selenium_window_size: str = "1366,768"
    selenium_page_load_timeout: int = 35
    selenium_wait_timeout: int = 15
    humanize_delay_range: Tuple[float, float] = (1.25, 2.75)
    
    # Browser profile persistence for anti-detection
    # If not specified, creates `.nakedweb/browser_profile/` in current working directory
    # This path will be auto-populated from default template on first use
    selenium_profile_path: Optional[str] = None

    def ensure_google_ready(self) -> None:
        if not self.google_api_key or not self.google_cse_id:
            raise RuntimeError(
                "Google Custom Search requires both google_api_key and google_cse_id to be set"
            )
