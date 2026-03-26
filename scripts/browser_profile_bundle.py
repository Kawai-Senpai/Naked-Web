"""Interactive bundle/import tool for warmed Playwright browser profiles.

Use this script to:
1. Export the current warmed NakedWeb profile into a workspace-local bundle directory
2. Import a bundle back into the current machine's default profile location
3. Stage a profile copied from another machine or repo

The default bundle directory is `_browser_profile_bundle/` inside the current
working directory, so you can run it from any workspace where you want the
portable profile files to land.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add parent directory to path for local dev
sys.path.insert(0, str(Path(__file__).parent.parent))

from naked_web.utils.profiles import copy_profile_tree, get_default_playwright_profile_path


def default_bundle_dir() -> Path:
    """Return the default workspace-local profile bundle directory."""
    return Path.cwd() / "_browser_profile_bundle"


def prompt_path(label: str, default: Path) -> Path:
    """Prompt for a path with a default value."""
    raw = input(f"{label} [{default}]: ").strip()
    return Path(raw).expanduser().resolve() if raw else default.resolve()


def show_paths(profile_dir: Path, bundle_dir: Path) -> None:
    """Display the currently resolved paths."""
    print("\nResolved paths:")
    print(f"  Active profile: {profile_dir}")
    print(f"  Bundle dir:     {bundle_dir}")
    print()


def export_profile(profile_dir: Path, bundle_dir: Path) -> None:
    """Copy the active profile into the bundle directory."""
    if not profile_dir.exists():
        raise FileNotFoundError(
            f"No active profile found at {profile_dir}. Warm up the profile first."
        )
    copy_profile_tree(profile_dir, bundle_dir, clean_destination=True)
    print(f"\nExported profile bundle to: {bundle_dir}\n")


def import_profile(bundle_dir: Path, profile_dir: Path) -> None:
    """Copy a bundle directory into the active profile location."""
    if not bundle_dir.exists():
        raise FileNotFoundError(f"Bundle directory does not exist: {bundle_dir}")
    copy_profile_tree(bundle_dir, profile_dir, clean_destination=True)
    print(f"\nImported bundle into active profile: {profile_dir}\n")


def clone_external_profile(source_dir: Path, bundle_dir: Path) -> None:
    """Copy an arbitrary source profile into the bundle directory."""
    if not source_dir.exists():
        raise FileNotFoundError(f"Source profile does not exist: {source_dir}")
    copy_profile_tree(source_dir, bundle_dir, clean_destination=True)
    print(f"\nCopied source profile into bundle: {bundle_dir}\n")


def run_menu(profile_dir: Path, bundle_dir: Path) -> None:
    """Run the interactive menu loop."""
    while True:
        print("=" * 72)
        print("NakedWeb Browser Profile Bundle Tool")
        print("=" * 72)
        print("1. Show resolved paths")
        print("2. Export current active profile to workspace bundle")
        print("3. Import workspace bundle into the active profile")
        print("4. Copy another profile into the workspace bundle")
        print("5. Quit")
        print()
        print("Close all Chrome/Chromium/Playwright browser windows before copying.")
        print()

        choice = input("Select an option [1-5]: ").strip()
        if choice == "1":
            show_paths(profile_dir, bundle_dir)
        elif choice == "2":
            export_profile(profile_dir, bundle_dir)
        elif choice == "3":
            import_profile(bundle_dir, profile_dir)
        elif choice == "4":
            source_dir = prompt_path("Source profile directory", profile_dir)
            clone_external_profile(source_dir, bundle_dir)
        elif choice == "5":
            return
        else:
            print("\nInvalid option.\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bundle/import warmed NakedWeb browser profiles across Linux and Windows.",
    )
    parser.add_argument(
        "--action",
        choices=("show", "export", "import", "clone"),
        help="Run a single action instead of the interactive menu.",
    )
    parser.add_argument(
        "--profile-dir",
        type=str,
        default=None,
        help="Override the active profile path. Default: OS-specific NakedWeb profile location.",
    )
    parser.add_argument(
        "--bundle-dir",
        type=str,
        default=None,
        help="Override the workspace bundle directory. Default: ./_browser_profile_bundle",
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        default=None,
        help="Source profile directory for the 'clone' action.",
    )
    args = parser.parse_args()

    profile_dir = (
        Path(args.profile_dir).expanduser().resolve()
        if args.profile_dir
        else get_default_playwright_profile_path().resolve()
    )
    bundle_dir = (
        Path(args.bundle_dir).expanduser().resolve()
        if args.bundle_dir
        else default_bundle_dir().resolve()
    )

    if not args.action:
        run_menu(profile_dir, bundle_dir)
        return

    if args.action == "show":
        show_paths(profile_dir, bundle_dir)
    elif args.action == "export":
        export_profile(profile_dir, bundle_dir)
    elif args.action == "import":
        import_profile(bundle_dir, profile_dir)
    elif args.action == "clone":
        if not args.source_dir:
            raise SystemExit("--source-dir is required for --action clone")
        clone_external_profile(Path(args.source_dir).expanduser().resolve(), bundle_dir)


if __name__ == "__main__":
    main()
