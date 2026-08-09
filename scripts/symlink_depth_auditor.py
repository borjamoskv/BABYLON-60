# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""Symlink Depth Auditor (INV_C5_12 Enforcer).

Checks all symbolic links in the repository to ensure relative symlinks
pointing to sibling projects maintain a depth of exactly two levels (`../../...`).
"""

import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).parents[1]


def is_valid_sibling_symlink(target: str) -> bool:
    if not target.startswith(".."):
        return True
    parts = Path(target).parts
    return len(parts) >= 2 and parts[0] == ".." and parts[1] == ".."


def audit_symlinks(root: Path = REPO_ROOT) -> list[tuple[Path, str]]:
    violations = []
    EXCLUDE_DIRS = {"node_modules", ".git", ".venv", "target", "__pycache__", "dist", "build"}
    for path in root.rglob("*"):
        if any(part in EXCLUDE_DIRS for part in path.parts) or not path.is_symlink():
            continue
        target = os.readlink(path)
        if not is_valid_sibling_symlink(target):
            violations.append((path, target))
    return violations


def main() -> int:
    print("🔍 Auditing Symbolic Link Depths (INV_C5_12)...")
    violations = audit_symlinks(REPO_ROOT)
    if violations:
        print(f"🔴 Found {len(violations)} INV_C5_12 violations:", file=sys.stderr)
        for path, target in violations:
            print(f"  - {path.relative_to(REPO_ROOT)} -> {target}", file=sys.stderr)
        return 1
    print("🟢 All symbolic links conform to INV_C5_12 depth standard.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
