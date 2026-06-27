---
name: Mac-Control-Ω
description: SINGULARITY — Daemon, Vision, UI DOM, and 19-Domain macOS Control
version: 14.1.0
author: borjamoskv
script: scripts/mac_control_omega.py
axioms:
- AX-042
- AX-044
- AX-046
- AX-047
- omega_0_singularity
- omega_1_byzantine
- C5-REAL
---

# MAC-CONTROL-Ω v14.1.0

**Status:** C5-REAL
**Scope:** 19 Domains, 90+ Methods, FastAPI Daemon (bearer auth), VLM auto-detect, BFS UI DOM traversal, Autonomous Triggers.

## Architecture

### 1. The Daemon (`omega_daemon.py`)
FastAPI on `127.0.0.1:8011`. Bearer-token auth. WebSocket telemetry. REST API for remote swarm execution.

### 2. UI Maestro (`ui_maestro.py`)
Iterative BFS accessibility DOM traversal (10K node cap). Click, find, and dump UI elements by name or role.

### 3. Vision Node (`vision_node.py`)
Auto-detect local VLM (llava → moondream → bakllava). Screenshot → analysis in one call.

### 4. Sovereign System (`sovereign_system.py`)
19 control domains:

| # | Domain | Class | Key Methods |
|---|--------|-------|-------------|
| 1 | AV_Out | `AVOutControl` | brightness, dark mode, resolution, volume, mute |
| 2 | Network | `NetworkControl` | wifi, IP, DNS flush, speed test |
| 3 | Bluetooth | `BluetoothControl` | on/off, status |
| 4 | Power | `PowerControl` | battery, lock, sleep, caffeinate |
| 5 | Process | `ProcessControl` | list, kill, launch, quit, frontmost |
| 6 | Filesystem | `FilesystemControl` | disk usage, search, SHA256, temp cleanup |
| 7 | Clipboard | `ClipboardControl` | get/set clipboard |
| 8 | Screenshot | `ScreenshotControl` | capture screen/window |
| 9 | Notification | `NotificationControl` | send, DnD toggle |
| 10 | Window | `WindowControl` | list, focus, minimize, tile, set bounds |
| 11 | Automation | `AutomationControl` | shortcuts, say, wallpaper, open URL, AppleScript, JXA |
| 12 | Telemetry | `TelemetryControl` | hostname, CPU, RAM, GPU, thermal, timezone, NTP |
| 13 | Security | `SecurityControl` | firewall, SIP, Gatekeeper, FileVault, ports, keychains |
| 14 | Defaults | `DefaultsControl` | read/write preferences, dock, Finder, screenshot format |
| **15** | **HID** | `HIDControl` | low-level Quartz mouse/keyboard injection |
| **16** | **Virtualization** | `VirtualizationControl` | colima, docker orchestration |
| **17** | **Comms** | `CommsControl` | iMessage SMS, Apple Mail bridge |
| **18** | **MediaRemote** | `MediaRemoteControl` | Now Playing daemon, Spotify, Apple Music control |
| **19** | **Triggers** | `TriggerControl` | Autonomous detached sentinels for condition/action loops |

---

## v14 Commands (NEW)

| Command | Action |
|:---|:---|
| `/mac-hid-click` | Quartz raw click at (x,y) |
| `/mac-hid-type` | Quartz raw keystroke injection |
| `/mac-colima` | Colima virtualization status/start/stop |
| `/mac-docker` | Docker container summary |
| `/mac-imessage` | Send iMessage |
| `/mac-media` | Now Playing playback control (play/pause/skip) |
| `/mac-telemetry` | Unified system status (CPU, RAM, Temp, OS) |
| `/mac-firewall` | Firewall status |
| `/mac-sip` | SIP status |
| `/mac-gatekeeper` | Gatekeeper status |
| `/mac-filevault` | FileVault encryption status |
| `/mac-ports` | Scan open listening ports |
| `/mac-keychains` | List keychains |
| `/mac-xprotect` | XProtect version |
| `/mac-login-items` | List login items |
| `/mac-datetime` | Current date/time/epoch |
| `/mac-events` | Today's calendar events |
| `/mac-reminders` | Incomplete reminders |
| `/mac-timer` | Fire notification after N seconds |
| `/mac-defaults-read` | Read macOS preference |
| `/mac-dock-autohide` | Toggle dock autohide |
| `/mac-finder-hidden` | Toggle Finder hidden files |
| `/mac-screenshot-format` | Set screenshot format (png/jpg/tiff/gif/pdf) |
| `/mac-screenshot-location` | Set screenshot save location |
| `/mac-trigger-add` | Add background trigger sentinel |
| `/mac-trigger-remove` | Kill a trigger sentinel by name |
| `/mac-trigger-list` | List active trigger sentinels |

## Legacy Commands (v10-v13)

`/mac-daemon`, `/mac-ui-tree`, `/mac-ui-click`, `/mac-ui-find`, `/mac-vision`, `/mac-info`,
`/mac-volume`, `/mac-brightness`, `/mac-battery`, `/mac-ps`, `/mac-kill`, `/mac-wifi`, `/mac-screenshot`,
`/mac-notify`, `/mac-copy`, `/mac-clipboard`, `/mac-dark-mode`, `/mac-lock`, `/mac-sleep`,
`/mac-windows`, `/mac-focus`, `/mac-tile`, `/mac-shortcut`, `/mac-say`, `/mac-test`, etc.

## Security & C5-REAL Invariants

- **C5-REAL Mandate**: All hardware/DOM mutations MUST declare C5-REAL. Zero simulation.
- **Guard Pattern**: Enforce Silicon-Verify (post-action physical state verification).
- **TCC**: UI Maestro requires `Accessibility`. Vision Node requires `Screen Recording`.
- **Daemon**: Binds `127.0.0.1:8011` (localhost only). Bearer token auth required.
- **Defaults**: Write operations whitelisted to safe domains only (Dock, Finder, Safari, Terminal, screencapture, etc.).
- **Injection-proof**: All subprocess calls use list-based `_run_safe()`. Shell strings sanitized via `_sanitize()`.

