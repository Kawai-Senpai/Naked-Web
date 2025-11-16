"""Enhanced stealth scraper with anti-detection measures.

This module extends the base scraping capabilities with additional
anti-fingerprinting and behavioral humanization techniques to bypass
sophisticated bot detection systems.
"""

from __future__ import annotations

import random
import time
from typing import Any, Dict, Optional, Tuple

from ..core.config import NakedWebConfig
from ..scrape import _SELENIUM_AVAILABLE


def inject_stealth_scripts(driver: Any) -> None:
    """Inject JavaScript to mask automation signals."""
    
    stealth_js = """
    // Remove webdriver property
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    
    // Remove chrome automation flags
    window.navigator.chrome = {
        runtime: {},
    };
    
    // Mock permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    
    // Mock plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5]
    });
    
    // Mock languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en']
    });
    """
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': stealth_js
    })


def random_mouse_movement(driver: Any) -> None:
    """Simulate random mouse movements to appear human-like."""
    
    if not _SELENIUM_AVAILABLE:
        return
    
    try:
        from selenium.webdriver.common.action_chains import ActionChains
        
        actions = ActionChains(driver)
        
        # Get viewport dimensions
        viewport_width = driver.execute_script("return window.innerWidth")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        # Perform 3-5 random movements
        num_moves = random.randint(3, 5)
        for _ in range(num_moves):
            x_offset = random.randint(0, viewport_width)
            y_offset = random.randint(0, viewport_height)
            
            # Move to random position with randomized duration
            actions.move_by_offset(
                x_offset - viewport_width // 2,
                y_offset - viewport_height // 2
            )
            actions.pause(random.uniform(0.1, 0.5))
        
        actions.perform()
    except Exception:
        pass  # Fail silently if mouse simulation fails


def random_scroll_pattern(driver: Any) -> None:
    """Simulate realistic scrolling behavior with pauses."""
    
    try:
        # Get total page height
        total_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        # Scroll in chunks with random pauses
        current_position = 0
        while current_position < total_height:
            # Random scroll distance (between 20% and 60% of viewport)
            scroll_distance = random.randint(
                int(viewport_height * 0.2),
                int(viewport_height * 0.6)
            )
            
            current_position += scroll_distance
            driver.execute_script(f"window.scrollTo(0, {min(current_position, total_height)});")
            
            # Random pause between scrolls (0.5 to 2 seconds)
            time.sleep(random.uniform(0.5, 2.0))
            
            # Occasionally scroll back up slightly (like a real user)
            if random.random() < 0.15:  # 15% chance
                scroll_back = random.randint(50, 150)
                current_position = max(0, current_position - scroll_back)
                driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(0.3, 1.0))
    except Exception:
        pass


def setup_stealth_driver(cfg: NakedWebConfig) -> Any:
    """
    Create a stealth-configured Chrome driver with anti-detection measures.
    
    Profile Strategy (Copy-on-Use):
    1. Default profile (naked_web/_data/default_profile/) is a TEMPLATE - never used directly
    2. If cfg.selenium_profile_path provided: use that path (copy template if doesn't exist)
    3. If not provided: use `.nakedweb/browser_profile/` in current working directory
    4. Working profile accumulates cookies/history over time
    5. Template stays pristine
    
    Args:
        cfg: Configuration with optional profile path
    
    Returns:
        Configured Chrome driver with profile loaded
    """
    
    if not _SELENIUM_AVAILABLE:
        raise RuntimeError(
            "Selenium + undetected-chromedriver are not installed. Run `pip install -e .[selenium]`."
        )
    
    import undetected_chromedriver as uc
    import shutil
    import os
    from pathlib import Path
    
    options = uc.ChromeOptions()
    
    # Get default template path
    lib_root = Path(__file__).parent.parent
    default_template_path = lib_root / "_data" / "default_profile"
    
    # Determine working profile path
    if cfg.selenium_profile_path:
        # User specified custom path
        working_profile_path = Path(cfg.selenium_profile_path)
    else:
        # Auto-create in current working directory
        working_profile_path = Path.cwd() / ".nakedweb" / "browser_profile"
    
    # Copy template to working path if it doesn't exist
    if not working_profile_path.exists():
        print(f"Creating new browser profile at: {working_profile_path}")
        
        if default_template_path.exists() and list(default_template_path.iterdir()):
            # Template exists and has content - copy it
            print(f"  Copying template from: {default_template_path}")
            working_profile_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(
                default_template_path,
                working_profile_path,
                ignore=shutil.ignore_patterns('.gitkeep'),  # Don't copy .gitkeep
                dirs_exist_ok=True
            )
            print("  ✓ Profile created from template")
        else:
            # No template available - create empty profile
            print("  ⚠ Warning: No template found - creating empty profile")
            print("    Run `python scripts/warmup_profile.py` to create a warmed template")
            working_profile_path.mkdir(parents=True, exist_ok=True)
    else:
        print(f"Using existing browser profile: {working_profile_path}")
    
    # Configure Chrome to use working profile
    options.add_argument(f"--user-data-dir={working_profile_path}")
    options.add_argument("--profile-directory=Default")
    
    # User agent
    options.add_argument(f"--user-agent={cfg.user_agent}")
    
    # Essential flags
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Language and locale
    options.add_argument("--lang=en-US,en;q=0.9")
    
    # Window size (realistic desktop resolution)
    if cfg.selenium_window_size:
        options.add_argument(f"--window-size={cfg.selenium_window_size}")
    
    # Headless mode (less recommended for anti-detection)
    if cfg.selenium_headless:
        options.add_argument("--headless=new")
    
    # Create driver with undetected-chromedriver (it handles most anti-detection automatically)
    driver = uc.Chrome(options=options, headless=cfg.selenium_headless)
    driver.set_page_load_timeout(cfg.selenium_page_load_timeout)
    driver.implicitly_wait(cfg.selenium_wait_timeout)
    
    # Inject stealth scripts via CDP IMMEDIATELY after driver creation
    # This must happen before any navigation!
    try:
        inject_stealth_scripts(driver)
    except Exception as e:
        # CDP might not be available in all configurations
        print(f"Warning: Could not inject stealth scripts: {e}")
    
    return driver


def fetch_with_stealth(
    url: str,
    cfg: Optional[NakedWebConfig] = None,
    perform_mouse_movements: bool = True,
    perform_realistic_scrolling: bool = True,
) -> Tuple[str, Dict[str, str], int, str]:
    """
    Fetch a page using stealth Selenium with enhanced anti-detection.
    
    Args:
        url: Target URL to fetch
        cfg: Configuration object
        perform_mouse_movements: Simulate random mouse movements
        perform_realistic_scrolling: Perform realistic scroll patterns
    
    Returns:
        Tuple of (html, headers, status_code, final_url)
    """
    
    cfg = cfg or NakedWebConfig()
    driver = None
    
    try:
        driver = setup_stealth_driver(cfg)
        
        # Initial delay before navigation
        time.sleep(random.uniform(*cfg.humanize_delay_range))
        
        # Navigate to page
        driver.get(url)
        
        # Wait for page to be fully loaded
        from .browser import wait_for_document_ready
        wait_for_document_ready(driver, cfg.selenium_wait_timeout)
        
        # Simulate mouse movements
        if perform_mouse_movements:
            time.sleep(random.uniform(0.5, 1.5))
            random_mouse_movement(driver)
        
        # Realistic scrolling pattern
        if perform_realistic_scrolling:
            time.sleep(random.uniform(1.0, 2.0))
            random_scroll_pattern(driver)
        
        # Final delay before extracting content
        time.sleep(random.uniform(*cfg.humanize_delay_range))
        
        # Extract page source
        html = driver.page_source
        final_url = driver.current_url
        headers = {"x-nakedweb-final-url": final_url}
        
        return html, headers, 200, final_url
        
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


__all__ = [
    "inject_stealth_scripts",
    "random_mouse_movement",
    "random_scroll_pattern",
    "setup_stealth_driver",
    "fetch_with_stealth",
]
