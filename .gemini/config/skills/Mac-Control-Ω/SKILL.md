---
name: Mac-Control-Ω
description: SINGULARITY — Daemon, Vision, UI DOM, and 19-Domain macOS Control
version: 14.2.0
author: borjamoskv
script: scripts/mac_control_omega.py
triggers: ["/Mac-Control-Ω", "macOS automation", "macOS daemon", "UI Maestro", "colima", "docker", "macOS telemetry", "macOS HID"]
axioms:
- AX-042
- AX-044
- AX-046
- AX-047
- omega_0_singularity
- omega_1_byzantine
- C5-REAL
---

# MAC-CONTROL-Ω v14.2.0

**Status:** C5-REAL
**Scope:** 19 Domains, 90+ Methods, FastAPI Daemon (bearer auth), VLM auto-detect, BFS UI DOM traversal, Autonomous Triggers.

## 1. Architecture & Thermodynamic Bounds

### 1.1 The Daemon (`omega_daemon.py`)
- **[Ω9] Deterministic Ignition:** The FastAPI socket (`127.0.0.1:8011`) MUST be initialized with synchronous `await server.start()`. Floating `asyncio.create_task` without `await` is FORBIDDEN.
- **Protocol:** Bearer-token auth. WebSocket telemetry. REST API for remote swarm execution.

### 1.2 UI Maestro (`ui_maestro.py`)
- **Traversal:** Iterative BFS accessibility DOM traversal (10K node cap).
- **Mutation:** Click, find, and dump UI elements by exact role or name. No stochastic spatial coordinates.

### 1.3 Vision Node (`vision_node.py`)
- **Engine:** Auto-detect local VLM (llava → moondream → bakllava). Single-pass Screenshot → Analysis.

### 1.4 Sovereign System (`sovereign_system.py`)
| Domain | Class | Key Methods |
|---|---|---|
| AV_Out | `AVOutControl` | brightness, dark mode, resolution, volume, mute |
| Network | `NetworkControl` | wifi, IP, DNS flush, speed test |
| Bluetooth | `BluetoothControl` | on/off, status |
| Power | `PowerControl` | battery, lock, sleep, caffeinate |
| Process | `ProcessControl` | list, kill, launch, quit, frontmost |
| Filesystem | `FilesystemControl` | disk usage, search, SHA256, temp cleanup |
| Clipboard | `ClipboardControl` | get/set clipboard |
| Screenshot | `ScreenshotControl` | capture screen/window |
| Notification | `NotificationControl` | send, DnD toggle |
| Window | `WindowControl` | list, focus, minimize, tile, set bounds |
| Automation | `AutomationControl` | shortcuts, say, wallpaper, open URL, AppleScript, JXA |
| Telemetry | `TelemetryControl` | hostname, CPU, RAM, GPU, thermal, timezone, NTP |
| Security | `SecurityControl` | firewall, SIP, Gatekeeper, FileVault, ports, keychains |
| Defaults | `DefaultsControl` | read/write preferences, dock, Finder, screencapture |
| **HID** | `HIDControl` | low-level Quartz mouse/keyboard injection |
| **Virtualization**| `VirtualizationControl`| colima, docker orchestration |
| **Comms** | `CommsControl` | iMessage SMS, Apple Mail bridge |
| **MediaRemote** | `MediaRemoteControl` | Now Playing daemon, Spotify, Apple Music control |
| **Triggers** | `TriggerControl` | Autonomous detached sentinels for condition/action loops |

---

## 2. API / Interface Commands

| Subsystem | Actions (C5-REAL) |
|---|---|
| **HID** | `/mac-hid-click`, `/mac-hid-type` |
| **Virtualization**| `/mac-colima`, `/mac-docker` |
| **Telemetry** | `/mac-telemetry`, `/mac-ports`, `/mac-xprotect` |
| **Security** | `/mac-firewall`, `/mac-sip`, `/mac-gatekeeper`, `/mac-filevault`, `/mac-keychains` |
| **Lifecycle** | `/mac-login-items`, `/mac-events`, `/mac-reminders`, `/mac-timer` |
| **System Mutators**| `/mac-defaults-read`, `/mac-dock-autohide`, `/mac-finder-hidden`, `/mac-screenshot-format` |
| **Triggers** | `/mac-trigger-add`, `/mac-trigger-remove`, `/mac-trigger-list` |
| **Legacy** | `/mac-daemon`, `/mac-ui-tree`, `/mac-ui-click`, `/mac-battery`, `/mac-kill`, `/mac-wifi`, etc. |

## 3. C5-REAL Invariants & Security Matrix

- **C5-REAL Mandate**: All hardware/DOM mutations MUST declare C5-REAL. Zero simulation.
- **Guard Pattern**: Enforce Silicon-Verify (post-action physical state verification).
- **Context Bypass [Σ6]**: Shell strings sanitized via `_sanitize()`. Evasion of `fork/exec` failure defaults to `scripts/c5_exec.py`.
- **TCC Entitlements**: `ui_maestro.py` requires `Accessibility`. `vision_node.py` requires `Screen Recording`.
- **Network Isolation [Σ1]**: Daemon binds strictly to `127.0.0.1:8011`.
- **Registry Constraints**: Write operations whitelisted to safe domains ONLY (Dock, Finder, Safari, Terminal, screencapture).
