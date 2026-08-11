#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
audit_scripts_quality.py - Pre-commit and CI Quality Gate Auditor for scripts/
Verifies AST syntax integrity, Shebang Line 1 compliance, hardcoded path anti-patterns,
and artifact leakage across all scripts in the monorepo.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
SHEBANG = "#!/usr/bin/env python3"

# Forbidden anti-patterns
BANNED_PATTERNS = [
    (re.compile(r"os\.kill\([^)]*SIGKILL\)"), "Dangerous SIGKILL self-termination in exception path"),
    (re.compile(r"except\s*:\s*pass"), "Swallowed raw exception handler without logging"),
    (re.compile(r"/Users/[a-zA-Z0-9_\-]+/"), "Hardcoded absolute user home path (use Path.home())"),
]

ALLOWED_DATA_EXTENSIONS = {".py", ".sh", ".json"}  # Allowed code/config script extensions


def audit_scripts() -> bool:
    print("============================================================")
    print(" 🛡️  BABYLON-60 SCRIPTS QUALITY & ANTI-PATTERN AUDITOR")
    print("============================================================")

    py_files = sorted(SCRIPTS_DIR.glob("*.py"))
    sh_files = sorted(SCRIPTS_DIR.glob("*.sh"))
    total_files = len(py_files) + len(sh_files)

    print(f"[*] Auditing {len(py_files)} Python scripts and {len(sh_files)} Shell scripts...\n")

    passed_shebang = 0
    passed_ast = 0
    passed_patterns = 0
    violations = []

    # 1. Audit Python Shebangs, AST Syntax, and Banned Anti-Patterns
    for py_file in py_files:
        rel_path = py_file.name
        content = py_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        # A. Shebang Check
        if lines and lines[0].strip() == SHEBANG:
            passed_shebang += 1
        else:
            violations.append(f"[FAIL Shebang] {rel_path}: Missing or displaced Shebang on Line 1")

        # B. AST Parsing Check
        try:
            ast.parse(content, filename=str(py_file))
            passed_ast += 1
        except SyntaxError as e:
            violations.append(f"[FAIL AST Syntax] {rel_path}:{e.lineno} - Syntax error: {e.msg}")

        # C. Banned Patterns Check
        file_violations = 0
        for pattern, reason in BANNED_PATTERNS:
            for idx, line in enumerate(lines, 1):
                if pattern.search(line):
                    violations.append(f"[FAIL Pattern] {rel_path}:{idx} - {reason}")
                    file_violations += 1
        if file_violations == 0:
            passed_patterns += 1

    # 2. Audit Artifact Leakage in scripts/
    leaked_artifacts = []
    for item in SCRIPTS_DIR.iterdir():
        if item.is_file() and item.suffix.lower() not in ALLOWED_DATA_EXTENSIONS:
            if not item.name.startswith("."):
                leaked_artifacts.append(item.name)

    print("--- AUDIT RESULTS ---")
    print(f"  Total Scripts Scanned      : {total_files}")
    print(f"  Shebang Line 1 Compliance  : {passed_shebang} / {len(py_files)} ({(passed_shebang/len(py_files))*100:.1f}%)")
    print(f"  AST Syntax Integrity       : {passed_ast} / {len(py_files)} ({(passed_ast/len(py_files))*100:.1f}%)")
    print(f"  Anti-Pattern Cleanliness   : {passed_patterns} / {len(py_files)} ({(passed_patterns/len(py_files))*100:.1f}%)")

    if leaked_artifacts:
        print(f"\n  [!] Non-script artifacts detected in scripts/: {leaked_artifacts}")

    if violations:
        print("\n--- VIOLATION DETAILS ---")
        for v in violations:
            print(f"  ❌ {v}")
        print("============================================================\n")
        return False

    print("\n[✓] ALL SCRIPTS PASSED QUALITY & ANTI-PATTERN AUDIT!")
    print("============================================================\n")
    return True


if __name__ == "__main__":
    success = audit_scripts()
    sys.exit(0 if success else 1)
