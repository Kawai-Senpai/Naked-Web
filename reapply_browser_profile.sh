#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SRC=${1:-"$SCRIPT_DIR/_browser_profile_backup"}

if [ ! -d "$SRC" ]; then
  echo
  echo "===== Reapply Browser Profile ====="
  echo
  echo "ERROR: Backup folder not found at $SRC"
  echo "Run the warmup/export flow first so there is a profile to restore."
  echo
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
else
  echo
  echo "===== Reapply Browser Profile ====="
  echo
  echo "ERROR: python3 or python is required."
  echo
  exit 1
fi

echo
echo "===== Reapply Browser Profile ====="
echo

"$PYTHON_BIN" - "$SCRIPT_DIR" "$SRC" <<'PY'
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
src = Path(sys.argv[2]).expanduser().resolve()

sys.path.insert(0, str(repo_root))

from naked_web.utils.profiles import copy_profile_tree, get_default_playwright_profile_path

dst = get_default_playwright_profile_path().resolve()

print(f"Source:  {src}")
print(f"Target:  {dst}")
print()
print("Copying profile data...")
copy_profile_tree(src, dst, clean_destination=True)
print("Done! Profile restored successfully.")
PY

echo
