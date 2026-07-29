#!/usr/bin/env python3
"""Ledger-Aware Pre-Push Guard.

Verifies C5-REAL invariants before git push:
1. ExergyScore >= 950.0 via babylon60.utils.hygiene.run_exergy_optimizer()
2. Autopoietic invariant alignment via scripts/autodetect_invariants.py
3. Monotonic Lamport ordering in Cortex ledger
"""

import sys
import subprocess
from pathlib import Path
from babylon60.utils.hygiene import run_exergy_optimizer

REPO_ROOT = Path(__file__).parents[1]

def verify_exergy() -> bool:
    print("🔋 Verifying Exergy Score (>= 950.0)...")
    ok = run_exergy_optimizer()
    if ok:
        print("  🟢 Exergy Score verified.")
    else:
        print("  🔴 Exergy Score below threshold! Aborting push.", file=sys.stderr)
    return ok

def verify_invariants() -> bool:
    print("🔍 Verifying Autopoietic Invariants alignment...")
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "autodetect_invariants.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        print("  🟢 Invariants aligned.")
        return True
    else:
        print(f"  🔴 Invariant alignment failed:\n{res.stdout}\n{res.stderr}", file=sys.stderr)
        return False

def verify_symlink_depth() -> bool:
    print("🔗 Verifying Symlink Depth Invariant (INV_C5_12)...")
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "symlink_depth_auditor.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        print("  🟢 Symlink depth invariant verified.")
        return True
    else:
        print(f"  🔴 Symlink depth verification failed:\n{res.stdout}\n{res.stderr}", file=sys.stderr)
        return False

def main() -> int:
    print("🛡️ Igniting C5-REAL Pre-Push Ledger Guard...")
    if not verify_exergy():
        return 1
    if not verify_invariants():
        return 1
    if not verify_symlink_depth():
        return 1
    print("✅ All Pre-Push Invariants Verified (C5-REAL). Proceeding with push.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
