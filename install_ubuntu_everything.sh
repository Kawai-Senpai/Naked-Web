#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
NAKEDWEB_DIR="${NAKEDWEB_DIR:-$SCRIPT_DIR}"
DEFAULT_INFINITE_CODE_DIR="$SCRIPT_DIR/../../MCP/Infinite-code"
VENV_DIR="${VENV_DIR:-$NAKEDWEB_DIR/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ -n "${INFINITE_CODE_DIR:-}" ]]; then
  INFINITE_CODE_DIR="$(cd -- "$INFINITE_CODE_DIR" && pwd)"
elif [[ -d "$DEFAULT_INFINITE_CODE_DIR" ]]; then
  INFINITE_CODE_DIR="$(cd -- "$DEFAULT_INFINITE_CODE_DIR" && pwd)"
else
  INFINITE_CODE_DIR=""
fi

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

log "Installing Ubuntu packages"
"${SUDO[@]}" apt-get update
"${SUDO[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  bash \
  ca-certificates \
  curl \
  git \
  xdg-utils \
  xterm \
  build-essential \
  pkg-config \
  python3 \
  python-is-python3 \
  python3-dev \
  python3-pip \
  python3-venv \
  nodejs \
  npm \
  gnome-keyring \
  libsecret-1-0

log "Creating virtual environment at $VENV_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"
VENV_PYTHON="$VENV_DIR/bin/python"

log "Upgrading pip tooling"
"$VENV_PYTHON" -m pip install --upgrade pip setuptools wheel

log "Installing local NakedWeb with all extras"
(
  cd "$NAKEDWEB_DIR"
  "$VENV_PYTHON" -m pip install -e ".[all]"
)

if [[ -n "$INFINITE_CODE_DIR" && -f "$INFINITE_CODE_DIR/requirements.txt" ]]; then
  log "Installing Infinite-code requirements from $INFINITE_CODE_DIR"
  "$VENV_PYTHON" -m pip install -r "$INFINITE_CODE_DIR/requirements.txt"
else
  log "Infinite-code repo not found automatically; skipping its requirements"
  printf 'Set INFINITE_CODE_DIR=/path/to/Infinite-code and rerun if you want that installed too.\n'
fi

log "Installing Playwright OS dependencies for Chromium"
"${SUDO[@]}" "$VENV_PYTHON" -m playwright install-deps chromium

log "Installing Playwright Chromium browser"
"$VENV_PYTHON" -m playwright install chromium

if ! SYSTEM_BROWSER="$(have_system_browser)"; then
  log "No system Chrome/Chromium found; trying to install one for Selenium"
  if ! "${SUDO[@]}" "$VENV_PYTHON" -m playwright install chrome; then
    if ! "${SUDO[@]}" apt-get install -y chromium-browser; then
      "${SUDO[@]}" apt-get install -y chromium || true
    fi
  fi
fi

SYSTEM_BROWSER="$(have_system_browser || true)"

log "Install complete"
printf 'Virtualenv: %s\n' "$VENV_DIR"
printf 'Activate: source "%s/bin/activate"\n' "$VENV_DIR"
printf 'NakedWeb dir: %s\n' "$NAKEDWEB_DIR"
if [[ -n "$INFINITE_CODE_DIR" ]]; then
  printf 'Infinite-code dir: %s\n' "$INFINITE_CODE_DIR"
fi
if [[ -n "$SYSTEM_BROWSER" ]]; then
  printf 'System browser for Selenium: %s\n' "$SYSTEM_BROWSER"
else
  printf 'WARNING: No system Chrome/Chromium detected. Playwright is ready, but Selenium may still need a browser install.\n'
fi
printf '\nNext recommended commands:\n'
printf '  source "%s/bin/activate"\n' "$VENV_DIR"
printf '  cd "%s"\n' "$NAKEDWEB_DIR"
printf '  ./reapply_browser_profile.sh\n'
printf '  python scripts/warmup_playwright_profile.py --duration 300\n'
