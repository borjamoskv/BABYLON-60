<![CDATA[# ⚡ CORTEX RAM GUARD

**Sovereign macOS memory pressure daemon — native Swift, zero runtime.**

A compiled, zero-dependency watchdog that prevents macOS swap death by enforcing graduated memory pressure response, per-app RSS budgets, and predictive swap exhaustion alerts.

Built for power users running heavy IDE + browser + agent workloads.

---

## The Problem

macOS handles memory pressure by swapping aggressively to disk. On machines with 16-18GB RAM running Electron IDEs, multiple browser instances, and background agents, swap can silently balloon to 30GB+, grinding the system to a halt.

By the time you notice, `WindowServer` is at 30fps.

**RAM Guard fixes this by acting before you notice.**

## How It Works

```
┌─────────────────────────────────────────────────┐
│              CORTEX RAM GUARD v3.0              │
├──────────┬──────────┬──────────┬────────────────┤
│ 🟢 GREEN │ 🟡 YELLOW│ 🟠 ORANGE│ 🔴 RED         │
│ Monitor  │ Cull     │ Kill+    │ Emergency      │
│ only     │ excess   │ Purge    │ Purge          │
│ 120s     │ 60s      │ 30s      │ 15s            │
├──────────┴──────────┴──────────┴────────────────┤
│  Thresholds scale to physical RAM automatically │
│  18GB → Y:9GB  O:14.4GB  R:21.6GB              │
│  32GB → Y:16GB O:25.6GB  R:38.4GB              │
└─────────────────────────────────────────────────┘
```

### Features

| Feature | Description |
|---------|-------------|
| **Native ARM64 binary** | 1.6 MB compiled. No Python, no Node, no shell runtime. |
| **Mach VM APIs** | `host_statistics64` for page-level memory stats. `sysctl` for swap. |
| **Per-app RSS budgets** | Set max memory per app group (Node, Python, Renderer, Comet). |
| **Predictive alerts** | Linear extrapolation warns you N minutes before RED. |
| **Memory leak detection** | Flags monotonically increasing swap across sample window. |
| **Process ancestry logging** | Every kill logs `PID(cmd)←PPID(parent)` chain. |
| **Self-health monitoring** | Auto-alerts if its own RSS exceeds limit. |
| **Editable whitelist** | Never kills processes matching patterns in `whitelist.conf`. |
| **Hot-reload config** | Changes to `config.conf` picked up without restart. |
| **Batched notifications** | Groups macOS notifications to avoid spam. |
| **Process snapshots** | Periodic TSV dumps of top-30 processes. |
| **Log rotation** | Auto-compresses old logs, deletes after 14 days. |

## Installation

### Homebrew (recommended)

```bash
brew install borjamoskv/tap/ramguard
```

### From source

```bash
git clone https://github.com/borjamoskv/cortex-ram-guard.git
cd cortex-ram-guard
make install
```

Requires Swift 5.9+ (included with Xcode 15+).

### Legacy shell script

The original `cortex-ram-guard.sh` is preserved in the `legacy/` directory for systems where compilation isn't available.

## Usage

```bash
ramguard status      # Current memory state + per-app RSS
ramguard purge       # Manual immediate purge
ramguard logs        # Tail today's log
ramguard stats       # 7-day kill/purge history
ramguard install     # Install/restart launchd daemon
ramguard uninstall   # Stop and unload daemon
```

### Example output

```
═══════════════════════════════════════════════
  CORTEX RAM GUARD v3.0 (Swift)
═══════════════════════════════════════════════
  RAM:       18GB  │  Free: 75MB
  Swap:      3570MB  │  🟢 GREEN
  Compressed:2100MB  │  Wired: 4200MB
  Thresholds: Y=9000 O=14400 R=21600
───────────────────────────────────────────────
  Comet            3 procs    150MB RSS  (budget 1500MB)
  Node            42 procs    890MB RSS  (budget 2000MB)
  Renderer         8 procs    620MB RSS  (budget 1800MB)
  Python           2 procs    129MB RSS  (budget 1200MB)
───────────────────────────────────────────────
  Total procs: 500
  Today: kills=27 purges=2 freed=13400MB
═══════════════════════════════════════════════
```

## Configuration

Edit `~/.cortex/ram-guard/config.conf`:

```bash
# Pressure thresholds (multiplier × RAM_GB → threshold in MB)
YELLOW_MULT=500
ORANGE_MULT=800
RED_MULT=1200

# Per-app RSS budgets (MB)
BUDGET_COMET_MB=1500
BUDGET_NODE_MB=2000
BUDGET_RENDERER_MB=1800
BUDGET_PYTHON_MB=1200

# CPU thresholds for killing hot processes
CPU_KILL_PYTHON=60
CPU_KILL_NODE=70

# Process count limits
MAX_NODE_PROCS=80
MAX_RENDERER_PROCS=12

# Predictive alert: warn when projected time to RED < N minutes
PREDICT_ALERT_MIN=15
```

Changes are picked up automatically — no restart needed.

## Architecture

```
Sources/RamGuard/
├── CLI.swift              # ArgumentParser subcommands
├── Config.swift           # Hot-reloadable config parser
├── Daemon.swift           # Main loop + graduated response
├── Logger.swift           # Structured logging + rotation
├── MemoryMonitor.swift    # Mach VM + sysctl memory APIs
└── ProcessManager.swift   # Process enum, ancestry, kill
```

Key design decisions:
- **No shell-out for memory stats.** Direct `host_statistics64` and `sysctl` calls.
- **Process enumeration via `ps aux`** for reliable cross-version compatibility, with `kinfo_proc` for PPID ancestry.
- **Foundation-only.** No AppKit, no SwiftUI. Runs headless as a launchd agent.
- **Config backward-compatible** with the shell version's `config.conf` format.

## Graduated Response

| Level | Trigger | Actions |
|-------|---------|---------|
| 🟢 **GREEN** | Swap < threshold | Monitor only. Restore Spotlight if throttled. |
| 🟡 **YELLOW** | Swap > 0.5× RAM | Cull excess processes. Kill stale renderers. Enforce RSS budgets. |
| 🟠 **ORANGE** | Swap > 0.8× RAM | Kill hot CPU processes. Purge disk cache. macOS notification. |
| 🔴 **RED** | Swap > 1.2× RAM | Emergency purge. Lower CPU kill thresholds. Throttle Spotlight. |

## Files

```
~/.cortex/ram-guard/
├── config.conf            # Tunable configuration
├── whitelist.conf         # Protected processes
├── guard.pid              # Daemon PID
├── stats-YYYY-MM-DD.json  # Daily statistics
├── logs/
│   └── ram-guard-YYYY-MM-DD.log
└── snapshots/
    └── snap-HHMM.tsv      # Process snapshots
```

## Requirements

- macOS 13+ (Ventura or later)
- Apple Silicon or Intel
- Swift 5.9+ (only for building from source)
- No runtime dependencies

## Uninstall

```bash
ramguard uninstall
# or: brew uninstall ramguard
rm -rf ~/.cortex/ram-guard
```

## License

MIT

---

*Built by [borjamoskv](https://github.com/borjamoskv) — because 18GB should be enough for anybody.*
]]>
