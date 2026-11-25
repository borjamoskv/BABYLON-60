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

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GIT_HOOKS_DIR = REPO_ROOT / ".git" / "hooks"
PRE_COMMIT_HOOK_PATH = GIT_HOOKS_DIR / "pre-commit"

PRE_COMMIT_SCRIPT = r"""#!/bin/sh
# BABYLON-60 Sovereign Pre-Commit Quality Gate (C5-REAL Hardened)
set -e

echo "🛡️  [C5-GATE] Running BABYLON-60 Quality Gate Auditor..."

# [GATE 0] Gitleaks Staged Secrets Protection (Ring-0 Gate)
if command -v gitleaks >/dev/null 2>&1; then
    echo "🔒 [OPSEC-Ω] Running Gitleaks staged secrets scan..."
    gitleaks protect --staged --config=.gitleaks.toml --verbose
    if [ $? -ne 0 ]; then
        echo "❌ [OPSEC-Ω] Pre-commit rejected: Plaintext secret or API key detected in staged diff."
        echo "   Remediation: Remove the sensitive credential, use environment variables or .env.example."
        exit 1
    fi
    echo "✓ [OPSEC-Ω] Staged secrets scan PASSED."
else
    echo "⚠️  [OPSEC-Ω] Warning: gitleaks binary not found in PATH. Skipping staged scan."
fi

# [GATE 1] Lean 4 Axiomatic Attestation
LEAN_FILES=$(git diff --cached --name-only | grep '\.lean$' || true)
if [ -n "$LEAN_FILES" ]; then
    echo "📐 [LEAN-4] Lean 4 files detected in staging. Enforcing Axiomatic Attestation..."
    REPO_DIR=$(pwd)
    if [ -d "proof/lean" ]; then
        cd proof/lean
    elif [ -d "docs/proof/lean" ]; then
        cd docs/proof/lean
    else
        echo "❌ Lean project directory not found."
        exit 1
    fi
    LAKE_OUTPUT=$(lake build 2>&1)
    if [ $? -ne 0 ]; then
        echo "❌ Lean 4 build failed. Cognitive Proof of Work rejected."
        echo "$LAKE_OUTPUT"
        exit 1
    fi
    if echo "$LAKE_OUTPUT" | grep -q "declaration uses 'sorry'"; then
        echo "❌ Lean 4 attestation contains 'sorry'. Vacuous proof rejected."
        exit 1
    fi
    echo "✓ [LEAN-4] Lean 4 Axiomatic Attestation PASSED."
    cd "$REPO_DIR"
fi

# [GATE 2] DevSecOps & AST Quality Audit
python3 scripts/runner.py audit
if [ $? -ne 0 ]; then
    echo "❌ Pre-commit quality audit failed. Commit aborted."
    exit 1
fi

echo "✓ [C5-GATE] All Pre-commit Quality Gates PASSED."
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
