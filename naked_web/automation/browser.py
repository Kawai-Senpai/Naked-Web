"""
Browser lifecycle manager - launch, manage pages/tabs, and close.

Provides the AutoBrowser class that wraps Playwright with a simple API
for web automation without vision capabilities.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import ActionResult, PageState, TabInfo
from .state import extract_page_state
from . import actions

logger = logging.getLogger("naked_web.automation")


class AutoBrowser:
    """
    High-level browser automation controller.

    Wraps Playwright's sync API to provide a clean interface for:
    - Navigating to URLs
    - Extracting interactive page state (elements with indices)
    - Clicking, typing, scrolling, sending keys
    - Extracting page content as markdown
    - Managing multiple tabs

    Usage::

        from naked_web.automation import AutoBrowser

        browser = AutoBrowser()
        browser.launch()
        browser.navigate("https://example.com")
        state = browser.get_state()
        print(state.to_text())
        browser.click(1)  # Click element with index 1
        browser.close()
    """

    # Realistic Chrome user agent (updated periodically)
    _DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    # Stealth JavaScript injected before every page load to mask automation signals
    _STEALTH_JS = """
    // Remove webdriver property
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });

    // Override the permissions API
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );

    // Mock plugins array (real Chrome has plugins)
    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            const plugins = [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
            ];
            plugins.length = 3;
            return plugins;
        },
        configurable: true
    });

    // Mock languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
        configurable: true
    });

    // Mock Chrome runtime (headless Chrome is missing this)
    if (!window.chrome) {
        window.chrome = {};
    }
    if (!window.chrome.runtime) {
        window.chrome.runtime = {
            connect: function() {},
            sendMessage: function() {},
        };
    }

    // Remove headless signals from navigator.userAgent
    // (Playwright already handles this via the user_agent context param, but just in case)
    const originalUserAgent = navigator.userAgent;
    if (originalUserAgent.includes('HeadlessChrome')) {
        Object.defineProperty(navigator, 'userAgent', {
            get: () => originalUserAgent.replace('HeadlessChrome', 'Chrome'),
            configurable: true
        });
    }

    // Fix missing connection info
    if (navigator.connection === undefined) {
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                rtt: 50,
                downlink: 10,
                saveData: false,
            }),
            configurable: true
        });
    }

    // Override hardware concurrency (headless sometimes reports 1)
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8,
        configurable: true
    });

    // Override platform if needed
    Object.defineProperty(navigator, 'platform', {
        get: () => 'Win32',
        configurable: true
    });
    """

    def __init__(
        self,
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 800,
        user_agent: Optional[str] = None,
        timeout: int = 30000,
        slow_mo: int = 0,
        browser_type: str = "chromium",
        user_data_dir: Optional[str] = None,
    ):
        """
        Initialize the browser configuration (does NOT launch yet).

        Args:
            headless: Run browser without visible window (default True).
            viewport_width: Browser viewport width in pixels.
            viewport_height: Browser viewport height in pixels.
            user_agent: Custom user agent string. None uses Playwright default.
            timeout: Default timeout for actions in milliseconds.
            slow_mo: Slow down actions by this many milliseconds (useful for debugging).
            browser_type: Which browser engine to use ("chromium", "firefox", "webkit").
            user_data_dir: Path to persistent browser profile directory.
                If set, uses launch_persistent_context so cookies, history,
                localStorage etc. survive across sessions. If None, uses a
                fresh temporary profile each time.
        """
        self._headless = headless
        self._viewport_width = viewport_width
        self._viewport_height = viewport_height
        self._user_agent = user_agent
        self._timeout = timeout
        self._slow_mo = slow_mo
        self._browser_type = browser_type
        self._user_data_dir = user_data_dir

        # Playwright objects (populated on launch)
        self._playwright: Any = None
        self._browser: Any = None  # None when using persistent context
        self._context: Any = None
        self._pages: List[Any] = []  # All open pages/tabs
        self._active_page_idx: int = 0  # Index into _pages
        self._persistent: bool = False  # True when using launch_persistent_context

        # Last extracted state (needed for click/type by index)
        self._last_state: Optional[PageState] = None
        self._launched = False

    @property
    def is_launched(self) -> bool:
        """Whether the browser is currently running."""
        return self._launched and (self._browser is not None or self._persistent)

    @property
    def page(self) -> Any:
        """Get the currently active Playwright Page object."""
        if not self._pages:
            raise RuntimeError("No pages open. Call launch() or new_tab() first.")
        return self._pages[self._active_page_idx]

    @property
    def last_state(self) -> Optional[PageState]:
        """The last extracted page state (None if never extracted)."""
        return self._last_state

    def launch(self) -> ActionResult:
        """
        Launch the browser. Must be called before any other action.

        When user_data_dir is set, uses launch_persistent_context so that
        cookies, history, localStorage, and other profile data persist
        across sessions (useful for captcha bypass, staying logged in, etc.).

        Returns:
            ActionResult indicating success or failure.
        """
        if self._launched:
            return ActionResult(success=True, message="Browser already launched")

        try:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()

            # Select browser engine
            engine = getattr(self._playwright, self._browser_type, None)
            if engine is None:
                engine = self._playwright.chromium

            # Resolve user agent: explicit > default stealth UA
            effective_ua = self._user_agent or self._DEFAULT_USER_AGENT

            # Common context arguments - look like a real Chrome browser
            context_args: Dict[str, Any] = {
                "viewport": {"width": self._viewport_width, "height": self._viewport_height},
                "user_agent": effective_ua,
                "locale": "en-US",
                "timezone_id": "Asia/Kolkata",
                "extra_http_headers": {
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Sec-Ch-Ua": '"Chromium";v="131", "Not_A Brand";v="24"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": '"Windows"',
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1",
                },
            }

            if self._user_data_dir:
                # ---------- PERSISTENT PROFILE MODE ----------
                # Ensure the profile directory exists
                profile_dir = Path(self._user_data_dir)
                profile_dir.mkdir(parents=True, exist_ok=True)

                # launch_persistent_context combines browser + context in one call
                # and persists cookies, history, localStorage, etc. to user_data_dir
                self._context = engine.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    headless=self._headless,
                    slow_mo=self._slow_mo,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars",
                        "--disable-background-networking",
                        "--disable-client-side-phishing-detection",
                        "--disable-component-update",
                        "--disable-sync",
                        "--disable-dev-shm-usage",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--no-pings",
                        "--disable-popup-blocking",
                        "--disable-domain-reliability",
                        "--disable-speech-synthesis-api",
                        "--metrics-recording-only",
                        "--enable-features=NetworkService,NetworkServiceInProcess",
                        "--enable-network-information-downlink-max",
                    ],
                    ignore_default_args=["--enable-automation"],
                    **context_args,
                )
                self._context.set_default_timeout(self._timeout)

                # Inject stealth scripts to mask automation signals
                self._context.add_init_script(self._STEALTH_JS)
                self._browser = None  # No separate browser object
                self._persistent = True

                # Persistent context opens a default page automatically
                existing_pages = self._context.pages
                if existing_pages:
                    self._pages = list(existing_pages)
                else:
                    self._pages = [self._context.new_page()]
                self._active_page_idx = 0
                self._launched = True

                logger.info(
                    f"Browser launched with persistent profile "
                    f"(headless={self._headless}, profile={profile_dir})"
                )
                return ActionResult(
                    success=True,
                    message=(
                        f"Browser launched ({self._browser_type}, headless={self._headless}, "
                        f"profile={profile_dir})"
                    ),
                )
            else:
                # ---------- EPHEMERAL MODE (original behavior) ----------
                self._browser = engine.launch(
                    headless=self._headless,
                    slow_mo=self._slow_mo,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars",
                        "--disable-background-networking",
                        "--disable-client-side-phishing-detection",
                        "--disable-component-update",
                        "--disable-sync",
                        "--disable-dev-shm-usage",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--no-pings",
                        "--disable-popup-blocking",
                        "--disable-domain-reliability",
                        "--disable-speech-synthesis-api",
                        "--metrics-recording-only",
                        "--enable-features=NetworkService,NetworkServiceInProcess",
                        "--enable-network-information-downlink-max",
                    ],
                    ignore_default_args=["--enable-automation"],
                )

                self._context = self._browser.new_context(**context_args)
                self._context.set_default_timeout(self._timeout)

                # Inject stealth scripts to mask automation signals
                self._context.add_init_script(self._STEALTH_JS)

                self._persistent = False

                # Create first page
                first_page = self._context.new_page()
                self._pages = [first_page]
                self._active_page_idx = 0
                self._launched = True

                logger.info(f"Browser launched (headless={self._headless}, engine={self._browser_type})")
                return ActionResult(success=True, message=f"Browser launched ({self._browser_type}, headless={self._headless})")

        except ImportError:
            return ActionResult(
                success=False,
                error="Playwright is not installed. Run: pip install playwright && playwright install chromium",
            )
        except Exception as e:
            return ActionResult(success=False, error=f"Failed to launch browser: {str(e)}")

    def close(self) -> ActionResult:
        """Close the browser and clean up resources.
        For persistent profiles, data is flushed to disk on close."""
        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()

            self._pages = []
            self._active_page_idx = 0
            self._last_state = None
            self._launched = False
            self._persistent = False

            logger.info("Browser closed")
            return ActionResult(success=True, message="Browser closed")
        except Exception as e:
            self._launched = False
            self._persistent = False
            return ActionResult(success=False, error=f"Error closing browser: {str(e)}")

    def _ensure_launched(self) -> Optional[ActionResult]:
        """Check if browser is launched, return error ActionResult if not."""
        if not self._launched or not self._pages:
            return ActionResult(
                success=False,
                error="Browser not launched. Call launch() first.",
            )
        return None

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate(self, url: str, timeout: int = 30000) -> ActionResult:
        """Navigate the current tab to a URL."""
        err = self._ensure_launched()
        if err:
            return err
        result = actions.navigate(self.page, url, timeout=timeout)
        if result.success:
            self._last_state = None  # Invalidate state
        return result

    def go_back(self) -> ActionResult:
        """Navigate back in browser history."""
        err = self._ensure_launched()
        if err:
            return err
        result = actions.go_back(self.page)
        if result.success:
            self._last_state = None
        return result

    # ------------------------------------------------------------------
    # State extraction
    # ------------------------------------------------------------------

    def get_state(self, max_elements: int = 200) -> PageState:
        """
        Extract the current page state with all interactive elements.

        Each element gets a 1-based index that can be used with click() and type_text().
        Always call this after navigation or actions that change the page.

        Args:
            max_elements: Maximum number of elements to include (default 200).

        Returns:
            PageState with indexed interactive elements.
        """
        err = self._ensure_launched()
        if err:
            return PageState(url="", title="ERROR: Browser not launched", elements=[])

        self._last_state = extract_page_state(self.page, max_elements=max_elements)
        return self._last_state

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------

    def click(self, index: int) -> ActionResult:
        """
        Click an interactive element by its index from the last get_state() call.

        Args:
            index: 1-based element index from PageState.elements.

        Returns:
            ActionResult.
        """
        err = self._ensure_launched()
        if err:
            return err
        if self._last_state is None:
            return ActionResult(
                success=False,
                error="No page state available. Call get_state() first.",
            )
        result = actions.click_element(self.page, index, self._last_state)
        if result.success:
            self._last_state = None  # Invalidate after click
        return result

    def type_text(self, index: int, text: str, clear: bool = True) -> ActionResult:
        """
        Type text into an input element by its index.

        Args:
            index: 1-based element index from PageState.elements.
            text: Text to type.
            clear: Whether to clear existing content first (default True).

        Returns:
            ActionResult.
        """
        err = self._ensure_launched()
        if err:
            return err
        if self._last_state is None:
            return ActionResult(
                success=False,
                error="No page state available. Call get_state() first.",
            )
        return actions.type_text(self.page, index, text, self._last_state, clear=clear)

    def scroll(self, direction: str = "down", amount: float = 1.0) -> ActionResult:
        """
        Scroll the page.

        Args:
            direction: "down" or "up".
            amount: Pages to scroll (0.5 = half, 1.0 = full, 999 = to end).

        Returns:
            ActionResult.
        """
        err = self._ensure_launched()
        if err:
            return err
        result = actions.scroll_page(self.page, direction=direction, amount=amount)
        if result.success:
            self._last_state = None
        return result

    def send_keys(self, keys: str) -> ActionResult:
        """
        Send keyboard keys or shortcuts.

        Args:
            keys: Key name or combination (e.g., "Enter", "Escape", "Control+a", "Tab").

        Returns:
            ActionResult.
        """
        err = self._ensure_launched()
        if err:
            return err
        return actions.send_keys(self.page, keys)

    def select_option(self, index: int, value: str) -> ActionResult:
        """
        Select an option from a dropdown element.

        Args:
            index: 1-based element index of the select element.
            value: Option value or label to select.

        Returns:
            ActionResult.
        """
        err = self._ensure_launched()
        if err:
            return err
        if self._last_state is None:
            return ActionResult(
                success=False,
                error="No page state available. Call get_state() first.",
            )
        return actions.select_option(self.page, index, value, self._last_state)

    def wait(self, seconds: float = 2.0) -> ActionResult:
        """Wait for a specified number of seconds."""
        return actions.wait_for_page(self.page if self._launched else None, seconds)

    # ------------------------------------------------------------------
    # Content extraction
    # ------------------------------------------------------------------

    def extract_content(self) -> ActionResult:
        """Extract page content as clean markdown-like text."""
        err = self._ensure_launched()
        if err:
            return err
        return actions.extract_content(self.page)

    def extract_links(self) -> ActionResult:
        """Extract all links from the current page."""
        err = self._ensure_launched()
        if err:
            return err
        return actions.extract_links(self.page)

    def screenshot(self, path: str) -> ActionResult:
        """Take a screenshot and save to file."""
        err = self._ensure_launched()
        if err:
            return err
        return actions.take_screenshot(self.page, path)

    # ------------------------------------------------------------------
    # Tab management
    # ------------------------------------------------------------------

    def new_tab(self, url: Optional[str] = None) -> ActionResult:
        """
        Open a new tab, optionally navigating to a URL.

        Args:
            url: URL to navigate to in the new tab. None opens a blank tab.

        Returns:
            ActionResult.
        """
        err = self._ensure_launched()
        if err:
            return err
        try:
            new_page = self._context.new_page()
            self._pages.append(new_page)
            self._active_page_idx = len(self._pages) - 1
            self._last_state = None

            if url:
                new_page.goto(url, wait_until="domcontentloaded")
                return ActionResult(success=True, message=f"Opened new tab #{self._active_page_idx} and navigated to {url}")
            return ActionResult(success=True, message=f"Opened new tab #{self._active_page_idx}")
        except Exception as e:
            return ActionResult(success=False, error=f"Failed to open new tab: {str(e)}")

    def switch_tab(self, tab_index: int) -> ActionResult:
        """
        Switch to a different tab by its index (0-based).

        Args:
            tab_index: 0-based tab index.

        Returns:
            ActionResult.
        """
        err = self._ensure_launched()
        if err:
            return err
        if tab_index < 0 or tab_index >= len(self._pages):
            return ActionResult(
                success=False,
                error=f"Tab index {tab_index} out of range. Have {len(self._pages)} tabs (0-{len(self._pages)-1}).",
            )
        self._active_page_idx = tab_index
        self._last_state = None
        self._pages[tab_index].bring_to_front()
        return ActionResult(success=True, message=f"Switched to tab #{tab_index}")

    def close_tab(self, tab_index: Optional[int] = None) -> ActionResult:
        """
        Close a tab. Defaults to the current tab.

        Args:
            tab_index: 0-based tab index to close. None closes current tab.

        Returns:
            ActionResult.
        """
        err = self._ensure_launched()
        if err:
            return err

        idx = tab_index if tab_index is not None else self._active_page_idx
        if idx < 0 or idx >= len(self._pages):
            return ActionResult(success=False, error=f"Tab index {idx} out of range.")

        if len(self._pages) <= 1:
            return ActionResult(success=False, error="Cannot close the last tab. Use close() to close the browser.")

        try:
            self._pages[idx].close()
            self._pages.pop(idx)
            # Adjust active page index
            if self._active_page_idx >= len(self._pages):
                self._active_page_idx = len(self._pages) - 1
            self._last_state = None
            return ActionResult(success=True, message=f"Closed tab #{idx}. Active tab is now #{self._active_page_idx}")
        except Exception as e:
            return ActionResult(success=False, error=f"Failed to close tab: {str(e)}")

    def list_tabs(self) -> List[TabInfo]:
        """List all open tabs with their URLs and titles."""
        tabs = []
        for i, p in enumerate(self._pages):
            try:
                url = p.url
            except Exception:
                url = "(closed)"
            try:
                title = p.title()
            except Exception:
                title = "(unknown)"
            tabs.append(TabInfo(
                tab_id=i,
                url=url,
                title=title,
                is_active=(i == self._active_page_idx),
            ))
        return tabs

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def evaluate_js(self, expression: str) -> ActionResult:
        """
        Execute arbitrary JavaScript in the current page and return the result.

        Args:
            expression: JavaScript expression to evaluate.

        Returns:
            ActionResult with the JS return value in extracted_content.
        """
        err = self._ensure_launched()
        if err:
            return err
        try:
            result = self.page.evaluate(expression)
            return ActionResult(
                success=True,
                message="JavaScript executed",
                extracted_content=str(result) if result is not None else "(undefined)",
            )
        except Exception as e:
            return ActionResult(success=False, error=f"JS evaluation failed: {str(e)}")

    def get_current_url(self) -> str:
        """Get the current page URL."""
        try:
            return self.page.url
        except Exception:
            return ""

    def get_current_title(self) -> str:
        """Get the current page title."""
        try:
            return self.page.title()
        except Exception:
            return ""
