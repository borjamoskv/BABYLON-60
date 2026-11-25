#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized

"""Core path definitions for BABYLON-60 / CORTEX engine."""

import os
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
CORTEX_DB = CORTEX_DIR / "cortex.db"

# Monorepo root paths (Sexagesimal Canonical Topology)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DOCS_DIR = REPO_ROOT / "docs"
ABZU_KERNEL_DIR = REPO_ROOT / "00_ABZU_KERNEL"
KISH_ENGINE_DIR = REPO_ROOT / "01_KISH_ENGINE"
EDIN_SWARMS_DIR = REPO_ROOT / "02_EDIN_SWARMS"
KERNEL_DIR = ABZU_KERNEL_DIR / "crates" / "babylon60-kernel"
STRIKE_DIR = ABZU_KERNEL_DIR / "crates" / "strike-rs"
# Legacy aliases (backward compat — will be purged in v5.0)
SHIELD_DIR = ABZU_KERNEL_DIR
CORTEX_ENGINE_DIR = KISH_ENGINE_DIR
AGENTS_ARCHI_DIR = EDIN_SWARMS_DIR

# Agent State Directory with Environmental Override
_env_agent_dir = os.environ.get("BABYLON_AGENT_DIR") or os.environ.get("CORTEX_AGENT_DIR")
AGENT_DIR = Path(_env_agent_dir).resolve() if _env_agent_dir else REPO_ROOT / ".agent"
