#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ "$(id -u)" -eq 0 ]]; then
  SUDO=()
else
  SUDO=(sudo)
fi

log() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$*"
}

have_system_browser() {
  local candidate
  for candidate in google-chrome google-chrome-stable chromium chromium-browser; do
    if command -v "$candidate" >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

playwright_installed() {
  "$PYTHON_BIN" -m playwright --help >/dev/null 2>&1
}

pip_supports_break_system_packages() {
  "$PYTHON_BIN" -m pip help install 2>/dev/null | grep -q -- '--break-system-packages'
}

log "Installing Ubuntu browser automation packages"
"${SUDO[@]}" apt-get update
"${SUDO[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  bash \
  ca-certificates \
  curl \
  gnupg \
  xdg-utils \
  xterm \
  python3-pip \
  gnome-keyring \
  libsecret-1-0

PIP_INSTALL_ARGS=(-U)
if pip_supports_break_system_packages; then
  PIP_INSTALL_ARGS+=(--break-system-packages)
fi

log "Installing global Python browser automation packages"
"${SUDO[@]}" "$PYTHON_BIN" -m pip install "${PIP_INSTALL_ARGS[@]}" \
  pip \
  setuptools \
  wheel \
  playwright \
  selenium \
  undetected-chromedriver

if ! playwright_installed; then
  printf 'ERROR: Playwright CLI is still unavailable through %s\n' "$PYTHON_BIN" >&2
  exit 1
fi

log "Installing Playwright OS dependencies for Chromium"
"${SUDO[@]}" "$PYTHON_BIN" -m playwright install-deps chromium

log "Installing Playwright Chromium browser"
"$PYTHON_BIN" -m playwright install chromium

if ! SYSTEM_BROWSER="$(have_system_browser)"; then
  log "No system Chrome/Chromium found; trying to install one for Selenium"
  if ! "${SUDO[@]}" "$PYTHON_BIN" -m playwright install chrome; then
    if ! "${SUDO[@]}" apt-get install -y chromium-browser; then
      "${SUDO[@]}" apt-get install -y chromium || true
    fi
  fi
fi

SYSTEM_BROWSER="$(have_system_browser || true)"

log "Install complete"
printf 'Python binary: %s\n' "$PYTHON_BIN"
if [[ -n "$SYSTEM_BROWSER" ]]; then
  printf 'System browser for Selenium: %s\n' "$SYSTEM_BROWSER"
else
  printf 'WARNING: No system Chrome/Chromium detected. Playwright is ready, but Selenium may still need a browser install.\n'
fi
printf '\nNext recommended commands:\n'
printf '  cd "%s"\n' "$SCRIPT_DIR"
printf '  python3 -m pip install -e ".[all]" --break-system-packages\n'
printf '  ./reapply_browser_profile.sh\n'
printf '  python scripts/warmup_playwright_profile.py --duration 300\n'
