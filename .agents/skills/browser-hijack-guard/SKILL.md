---
name: browser-hijack-guard
description: Audit and clean macOS Chromium browser hijacks involving Yahoo redirects, suspicious search providers, Smart AdBlocker, Urban VPN Proxy, X-VPN, stale browser session state, proxy/DNS signals, and related Brave, Chrome, Arc, Atlas, or Safari search issues.
---

# Browser Hijack Guard

Use this skill when the user reports repeated Yahoo redirects, unwanted search engine changes, suspicious browser extensions, Brave/Chrome/Arc/Atlas search hijacking, or asks to re-run the cleanup from Borja's browser incident.

## Quick Workflow

1. Prefer audit first:

```bash
~/.agents/skills/browser-hijack-guard/scripts/browser_hijack_guard.sh --audit
```

2. If suspicious entries are found and the user wants cleanup, run:

```bash
~/.agents/skills/browser-hijack-guard/scripts/browser_hijack_guard.sh --fix
```

3. Tell the user what was found, what was moved, and the exact backup folder created by the script.

## What The Script Does

- Checks Chromium `Web Data` search engines for Yahoo/searchtosearch/sendqueries/universal-searches patterns.
- Looks for known suspicious extension IDs:
  - `edgnfbghdldhjjdomhohjgjndfelcooh` Smart AdBlocker
  - `eppiocemhmnlbhjplcgkofciiegomcon` Urban VPN Proxy
  - `flaeifplnkmoagonpbjmedjcadegiigl` X-VPN
- Cleans `Preferences`, `Secure Preferences`, `History`, and session/local-storage state when run with `--fix`.
- Moves files to a timestamped backup folder instead of permanently deleting them.
- Reports proxy, DNS, Safari search provider, and running browser processes as audit signals.

## Safety Notes

- `--fix` closes Brave, Chrome, Arc, and ChatGPT Atlas before touching profile files.
- Do not delete the backup folder unless the user explicitly asks after confirming browsers work normally.
- If browsers are open or syncing reintroduces extensions, ask the user to review browser sync/extensions after the cleanup.
