#!/usr/bin/env python3
import subprocess
import sys


def evaluate_exergy(diff_str: str | None = None) -> float:
    print("⚡ [C5-REAL] Exergy Optimization Agent (INV_C5_14)")

    if diff_str is not None:
        diff = diff_str
    else:
        try:
            diff = subprocess.check_output(["git", "show", "HEAD", "--", ".", ":!tests/", ":!*.md"], text=True)
        except OSError as e:
            print(f"Failed to fetch commit diff: {e}")
            return 0.0

    score = 1000.0

    # File-specific checks on additions (+) in diff
    lines = diff.splitlines()
    current_file = ""
    for line in lines:
        if line.startswith("--- a/") or line.startswith("+++ b/"):
            current_file = line[6:]
            continue

        if not line.startswith("+") or line.startswith("+++"):
            continue

        added_code = line[1:]

        # Penalize floating-point in database layer (INV_C5_18)
        if "babylon60/database/" in current_file and "float" in added_code.lower():
            print(f"⚠️ [ANERGY] Detected floating-point in database layer ({current_file}: Violation of INV_C5_18).")
            score -= 500.0

        # Penalize synchronous sleep in async code / core modules (INV_BFT_02)
        if "time.sleep(" in added_code and not current_file.startswith("tests/"):
            print(f"⚠️ [ANERGY] Detected synchronous sleep in {current_file} (Violation of INV_BFT_02).")
            score -= 200.0

        # Penalize broad exception handling
        if "except Exception:" in added_code:
            print(f"⚠️ [ANERGY] Detected broad exception catching in {current_file}.")
            score -= 150.0

    print(f"📊 GELABP Exergy Score: {score}/1000.0")
    return score


def evaluate_gelabp(diff: str) -> tuple[float, float, float, float, float, float]:
    score = evaluate_exergy(diff)
    return score, 950.0, 50.0, 1000.0, 1000.0, 0.0


if __name__ == "__main__":
    score = evaluate_exergy()
    if score < 700.0:
        print("🔴 [FAIL-FAST] Exergy score below 700.0/1000.0. Execution aborted.")
        sys.exit(1)
    else:
        print("🟢 Exergy optimal. Proceeding.")
        sys.exit(0)
