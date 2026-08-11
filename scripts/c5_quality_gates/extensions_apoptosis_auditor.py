#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
extensions_apoptosis_auditor.py - Apoptosis & Pruning Analysis Engine for Issue #5.
Scans `babylon60/extensions` to measure import reachability from core entrypoints.
"""

import ast
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXT_DIR = REPO_ROOT / "babylon60" / "extensions"

def find_all_python_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]

def collect_imports_from_file(file_path: Path) -> set[str]:
    imports = set()
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content, filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
    except Exception:
        pass
    return imports

def audit_extensions_reachability():
    print("======================================================================")
    print(" ✂️  BABYLON-60 APOPTOSIS ENGINE — ISSUE #5 EXTENSIONS REACHABILITY SCAN")
    print("======================================================================")
    
    if not EXT_DIR.exists():
        print("[-] Extensions directory not found.")
        return

    ext_subdirs = [d.name for d in EXT_DIR.iterdir() if d.is_dir()]
    all_ext_files = find_all_python_files(EXT_DIR)
    
    print(f"[*] Total Extension Subdirectories : {len(ext_subdirs)}")
    print(f"[*] Total Extension Python Files   : {len(all_ext_files)}")

    # Scan external callers (core, scripts, services, tests)
    caller_dirs = [
        REPO_ROOT / "babylon60" / "core",
        REPO_ROOT / "babylon60" / "engine",
        REPO_ROOT / "babylon60" / "memory",
        REPO_ROOT / "babylon60" / "services",
        REPO_ROOT / "scripts",
        REPO_ROOT / "services",
        REPO_ROOT / "tests",
        REPO_ROOT / "kimi_nexus",
    ]

    all_caller_imports = set()
    for c_dir in caller_dirs:
        if c_dir.exists():
            for p in find_all_python_files(c_dir):
                all_caller_imports.update(collect_imports_from_file(p))

    used_subdirs = set()
    unused_subdirs = set()

    for sub in ext_subdirs:
        target_import = f"babylon60.extensions.{sub}"
        # Check if imported anywhere in active codebase
        is_used = any(imp == target_import or imp.startswith(f"{target_import}.") for imp in all_caller_imports)
        if is_used:
            used_subdirs.add(sub)
        else:
            unused_subdirs.add(sub)

    print("\n--- AUDIT RESULTS ---")
    print(f"  Active Extension Subdirectories   : {len(used_subdirs)} / {len(ext_subdirs)}")
    print(f"  Candidate Apoptosis Subdirectories : {len(unused_subdirs)} / {len(ext_subdirs)}")

    print("\n[✓] ACTIVE SUBDIRECTORIES (KEEP):")
    for s in sorted(used_subdirs):
        print(f"  • babylon60.extensions.{s}")

    print("\n[✂️] UNUSED CANDIDATES FOR APOPTOSIS:")
    for s in sorted(unused_subdirs)[:15]:
        print(f"  - babylon60.extensions.{s}")
    if len(unused_subdirs) > 15:
        print(f"  ... and {len(unused_subdirs) - 15} more.")

    do_purge = "--purge" in sys.argv
    if do_purge:
        print("\n🔥 EXECUTING APOPTOSIS PURGE (--purge active)...")
        purged_count = 0
        import shutil
        for sub in unused_subdirs:
            target_dir = EXT_DIR / sub
            if target_dir.exists():
                shutil.rmtree(target_dir)
                purged_count += 1
        print(f"[✓] APOPTOSIS COMPLETE: {purged_count} unused subdirectories purged.")
        print(f"[✓] Remaining Active Subdirectories: {len(used_subdirs)} ({', '.join(sorted(used_subdirs))})")
    else:
        print("\n======================================================================")
        print("  RECOMMENDATION: Apoptosis sweep prepared. Run with --purge to prune.")
        print("======================================================================")

if __name__ == "__main__":
    audit_extensions_reachability()
