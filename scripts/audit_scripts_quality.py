#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
audit_scripts_quality.py - Pre-commit and CI Quality Gate Auditor & Auto-Healer for scripts/
Verifies AST syntax integrity, Shebang Line 1 compliance, hardcoded path anti-patterns,
and artifact leakage. Supports --fix for in-situ instant auto-remediation.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
SHEBANG = "#!/usr/bin/env python3"

BANNER = """# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""

# Forbidden anti-patterns
BANNED_PATTERNS = [
    (re.compile(r"os\.kill\([^)]*SIGKILL\)"), "Dangerous SIGKILL self-termination in exception path"),
    (re.compile(r"except\s*:\s*pass"), "Swallowed raw exception handler without logging"),
    (re.compile(r"/Users/[a-zA-Z0-9_\-]+/"), "Hardcoded absolute user home path (use Path.home())"),
]

ALLOWED_DATA_EXTENSIONS = {".py", ".sh", ".json", ".db", ".sqlite", ".md"}


def auto_fix_script(py_file: Path) -> bool:
    """Performs in-situ atomic remediation of Shebang placement and header formatting."""
    content = py_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    if not lines:
        return False

    if lines[0].strip() == SHEBANG:
        return False  # Already compliant

    # Strip existing shebangs
    new_lines = [line for line in lines if line.strip() != SHEBANG]
    body = "\n".join(new_lines).strip()

    if "# BABYLON-60" in body:
        remediated = f"{SHEBANG}\n{body}\n"
    else:
        remediated = f"{SHEBANG}\n{BANNER}{body}\n"

    # AST Integrity Check before committing write
    try:
        ast.parse(remediated, filename=str(py_file))
        py_file.write_text(remediated, encoding="utf-8")
        print(f"  [⚡ IN-SITU FIX] Remediated Shebang & Header in: {py_file.name}")
        return True
    except SyntaxError as e:
        print(f"  [!] Auto-remediation failed AST gate for {py_file.name}: {e}")
        return False


def audit_scripts(auto_fix: bool = False) -> bool:
    print("============================================================")
    print(f" 🛡️  BABYLON-60 QUALITY AUDITOR & AUTO-HEALER (MODE: {'IN-SITU AUTO-FIX' if auto_fix else 'READ-ONLY'})")
    print("============================================================")

    py_files = sorted(SCRIPTS_DIR.rglob("*.py"))
    sh_files = sorted(SCRIPTS_DIR.rglob("*.sh"))
    total_files = len(py_files) + len(sh_files)

    print(f"[*] Auditing {len(py_files)} Python scripts and {len(sh_files)} Shell scripts...\n")

    passed_shebang = 0
    passed_ast = 0
    passed_patterns = 0
    violations = []
    remediated_count = 0

    # 1. Audit Python Shebangs, AST Syntax, and Banned Anti-Patterns
    for py_file in py_files:
        rel_path = py_file.name
        content = py_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        # A. Shebang Check
        if lines and lines[0].strip() == SHEBANG:
            passed_shebang += 1
        else:
            if auto_fix:
                if auto_fix_script(py_file):
                    passed_shebang += 1
                    remediated_count += 1
                else:
                    violations.append(f"[FAIL Shebang] {rel_path}: Missing or displaced Shebang on Line 1")
            else:
                violations.append(f"[FAIL Shebang] {rel_path}: Missing or displaced Shebang on Line 1")

        # B. AST Parsing Check
        try:
            ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            passed_ast += 1
        except SyntaxError as e:
            violations.append(f"[FAIL AST Syntax] {rel_path}:{e.lineno} - Syntax error: {e.msg}")

        # C. Banned Patterns Check
        file_violations = 0
        current_lines = py_file.read_text(encoding="utf-8").splitlines()
        for pattern, reason in BANNED_PATTERNS:
            for idx, line in enumerate(current_lines, 1):
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
    if auto_fix:
        print(f"  In-Situ Auto-Remediations  : {remediated_count} scripts fixed in-place")

    if leaked_artifacts:
        print(f"\n  [!] Non-script artifacts detected in scripts/: {leaked_artifacts}")

    if violations:
        print("\n--- VIOLATION DETAILS ---")
        for v in violations:
            print(f"  ❌ {v}")
        print("============================================================\n")
        return False

    print("\n[✓] ALL SCRIPTS PASSED QUALITY & AUTO-HEALING AUDIT!")
    print("============================================================\n")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="BABYLON-60 Quality Auditor & Auto-Healer")
    parser.add_argument("--fix", action="store_true", help="Enable in-situ atomic remediation")
    args = parser.parse_args()

    success = audit_scripts(auto_fix=args.fix)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
