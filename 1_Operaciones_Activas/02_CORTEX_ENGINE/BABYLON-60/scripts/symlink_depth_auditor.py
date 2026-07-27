# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""Symlink Depth Auditor (INV_C5_12 Enforcer).

Checks all symbolic links in the repository to ensure relative symlinks
pointing to sibling projects maintain a depth of exactly two levels (`../../...`).
"""

import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).parents[1]

def audit_symlinks(root: Path = REPO_ROOT) -> list[tuple[Path, str]]:
    violations = []
    for path in root.rglob("*"):
        if path.is_symlink():
            target = os.readlink(path)
            # If symlink points to sibling project (relative path starting with ..)
            if target.startswith(".."):
                parts = Path(target).parts
                # Check if it starts with ('..', '..') for depth 2
                if len(parts) >= 2 and parts[0] == ".." and parts[1] == "..":
                    continue
                else:
                    violations.append((path, target))
    return violations

def main() -> int:
    print("🔍 Auditing Symbolic Link Depths (INV_C5_12)...")
    violations = audit_symlinks()
    if violations:
        print(f"🔴 Found {len(violations)} INV_C5_12 violations:", file=sys.stderr)
        for path, target in violations:
            print(f"  - {path.relative_to(REPO_ROOT)} -> {target}", file=sys.stderr)
        return 1
    print("🟢 All symbolic links conform to INV_C5_12 depth standard.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
