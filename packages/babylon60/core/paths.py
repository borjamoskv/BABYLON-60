# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized

"""Core path definitions for BABYLON-60 / CORTEX engine."""

from pathlib import Path

# Base user directory & Antigravity / Gemini configuration roots
USER_HOME = Path.home()
CONFIG_DIR = USER_HOME / ".gemini" / "config"
SKILLS_DIR = CONFIG_DIR / "skills"

# CORTEX Engine Local Storage Directories
CORTEX_DIR = USER_HOME / ".cortex"
MEMORY_DIR = CORTEX_DIR / "memory"
DAEMON_DIR = CORTEX_DIR / "daemon"

# Subsystem Configuration & State Files
DAEMON_CONFIG_FILE = DAEMON_DIR / "config.json"
DAEMON_STATUS_FILE = DAEMON_DIR / "status.json"
SYNC_STATE_FILE = CORTEX_DIR / "sync_state.json"

# Monorepo root paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DOCS_DIR = REPO_ROOT / "docs"
KERNEL_DIR = REPO_ROOT / "crates" / "babylon60-kernel"
STRIKE_DIR = REPO_ROOT / "crates" / "strike-rs"
