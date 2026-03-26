# Browser Profile Seed Data

This directory can hold optional seed profile data used to bootstrap a new
NakedWeb browser profile.

## What `default_profile/` means now

`default_profile/` is not the runtime profile location anymore.

Instead, NakedWeb now uses an OS-specific default profile path:
- Windows: `%LOCALAPPDATA%\.nakedweb\browser_profile`
- Linux: `$XDG_STATE_HOME/nakedweb/browser_profile` or `~/.local/state/nakedweb/browser_profile`
- Override: `NAKEDWEB_PROFILE_DIR=/custom/path`

If `naked_web/_data/default_profile/` exists and contains data, Selenium can use
it as a seed template the first time it creates a new working profile.

## When to use this folder

Use this folder only if you want a reusable starter template that gets copied
into fresh profiles. For most workflows, warming the shared default profile
directly is simpler.

## Recommended profile workflow

```bash
python scripts/warmup_profile.py
python scripts/warmup_playwright_profile.py
python scripts/browser_profile_bundle.py
```

- `warmup_profile.py` warms the shared default profile with Selenium/Chrome.
- `warmup_playwright_profile.py` warms the same profile with Playwright.
- `browser_profile_bundle.py` exports or imports the profile for transfer
  between Linux and Windows machines.

## Security note

- Do not commit real browser profiles with live sessions.
- Do not share profile directories publicly.
- Use separate profiles for separate projects when needed.
