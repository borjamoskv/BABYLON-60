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

REPO_ROOT = Path(__file__).absolute().parents[2]


def _is_confined_to_repo(path: Path, root: Path = REPO_ROOT) -> bool:
    try:
        return path.resolve().is_relative_to(root.resolve())
    except OSError:
        return False


def is_valid_sibling_symlink(target: str, link_path: Path | None = None, root: Path = REPO_ROOT) -> bool:
    if link_path is not None:
        try:
            resolved = (link_path.parent / target).resolve()
            if resolved.is_relative_to(root.resolve()):
                return True
        except OSError:
            return False
    if not target.startswith(".."):
        return True
    parts = Path(target).parts
    return len(parts) >= 2 and parts[0] == ".." and parts[1] == ".."


def audit_symlinks(root: Path = REPO_ROOT) -> list[tuple[Path, str]]:
    violations = []
    EXCLUDE_DIRS = {"node_modules", ".git", ".venv", "target", "__pycache__", "dist", "build", ".lake"}
    for path in root.rglob("*"):
        if any(part in EXCLUDE_DIRS for part in path.parts) or not path.is_symlink():
            continue
        if not _is_confined_to_repo(path.parent, root):
            violations.append((path, "<unconfined-parent>"))
            continue
        target = os.readlink(path)
        if not is_valid_sibling_symlink(target, path, root):
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
