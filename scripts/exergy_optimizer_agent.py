#!/usr/bin/env python3
import subprocess
import sys


def evaluate_exergy() -> float:
    print("⚡ [C5-REAL] Exergy Optimization Agent (INV_C5_14)")

    # 1. Check if the latest commit has structural anergy (e.g. TODOs in python files, floating point usage in db.py)
    try:
        # Get diff of the latest commit, excluding test files and markdown to prevent false positives from invariant descriptions
        diff = subprocess.check_output(["git", "show", "HEAD", "--", ".", ":!tests/", ":!*.md"], text=True)
    except Exception as e:
        print(f"Failed to fetch commit diff: {e}")
        return 0.0

    score = 1000.0

    # Penalize Green Theater or Anergy
    if "float" in diff.lower() and "database" in diff.lower():
        print("⚠️ [ANERGY] Detected floating-point in database layer (Violation of INV_C5_18).")
        score -= 500.0

    if "import time" in diff and "time.sleep" in diff:
        print("⚠️ [ANERGY] Detected synchronous sleep (Violation of INV_BFT_02).")
        score -= 200.0

    if "except Exception:" in diff:
        print("⚠️ [ANERGY] Detected broad exception catching.")
        score -= 150.0

    print(f"📊 GELABP Exergy Score: {score}/1000.0")
    return score


if __name__ == "__main__":
    score = evaluate_exergy()
    if score < 700.0:
        print("🔴 [FAIL-FAST] Exergy score below 700.0/1000.0. Execution aborted.")
        sys.exit(1)
    else:
        print("🟢 Exergy optimal. Proceeding.")
        sys.exit(0)
