"""Profile path and copy helpers for persistent browser state."""

from __future__ import annotations

import fnmatch
import os
import shutil
from pathlib import Path
from typing import Iterable, Set

_VOLATILE_PROFILE_PATTERNS = (
    "SingletonLock",
    "SingletonSocket",
    "SingletonCookie",
    "DevToolsActivePort",
    "LOCK",
    "lockfile",
    "*.tmp",
    "*.log",
)


def get_default_playwright_profile_path() -> Path:
    """Resolve the default persistent Playwright profile path for the current OS."""
    env_path = os.environ.get("NAKEDWEB_PROFILE_DIR")
    if env_path:
        return Path(env_path).expanduser()

    if os.name == "nt":
        home = Path.home()
        local_app_data = os.environ.get("LOCALAPPDATA")
        base_dir = Path(local_app_data).expanduser() if local_app_data else home / "AppData" / "Local"
        return base_dir / ".nakedweb" / "browser_profile"

    xdg_state_home = os.environ.get("XDG_STATE_HOME")
    if xdg_state_home:
        return Path(xdg_state_home).expanduser() / "nakedweb" / "browser_profile"

    home = Path.home()
    legacy_dir = home / ".nakedweb" / "browser_profile"
    if legacy_dir.exists():
        return legacy_dir

    return home / ".local" / "state" / "nakedweb" / "browser_profile"


def _ignore_volatile_profile_entries(_: str, names: Iterable[str]) -> Set[str]:
    """Skip lock files and other ephemeral Chromium files when copying profiles."""
    ignored: Set[str] = set()
    for name in names:
        if any(fnmatch.fnmatch(name, pattern) for pattern in _VOLATILE_PROFILE_PATTERNS):
            ignored.add(name)
    return ignored


def copy_profile_tree(source: Path, destination: Path, clean_destination: bool = True) -> None:
    """Copy a browser profile directory while skipping volatile runtime files."""
    src = Path(source).expanduser().resolve()
    dst = Path(destination).expanduser().resolve()

    if not src.exists():
        raise FileNotFoundError(f"Profile source does not exist: {src}")
    if not src.is_dir():
        raise NotADirectoryError(f"Profile source is not a directory: {src}")

    if clean_destination and dst.exists():
        shutil.rmtree(dst)

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        src,
        dst,
        dirs_exist_ok=True,
        ignore=_ignore_volatile_profile_entries,
    )
