#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
install_git_hooks.py - Installs automated git pre-commit quality gate hook
Enforces scripts quality audit and AST verification prior to every git commit.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GIT_HOOKS_DIR = REPO_ROOT / ".git" / "hooks"
PRE_COMMIT_HOOK_PATH = GIT_HOOKS_DIR / "pre-commit"

PRE_COMMIT_SCRIPT = """#!/bin/sh
# BABYLON-60 Sovereign Pre-Commit Quality Gate
echo "🛡️  Running BABYLON-60 Quality Gate Auditor..."
python3 scripts/runner.py audit
if [ $? -ne 0 ]; then
    echo "❌ Pre-commit quality audit failed. Commit aborted."
    exit 1
fi
echo "✓ Pre-commit quality gate PASSED."
"""


def install_hooks() -> None:
    if not GIT_HOOKS_DIR.exists():
        print(f"[-] .git/hooks directory not found at {GIT_HOOKS_DIR}")
        return

    PRE_COMMIT_HOOK_PATH.write_text(PRE_COMMIT_SCRIPT, encoding="utf-8")
    os.chmod(PRE_COMMIT_HOOK_PATH, 0o755)
    print(f"[✓] Git pre-commit hook installed successfully at: {PRE_COMMIT_HOOK_PATH}")


if __name__ == "__main__":
    install_hooks()
