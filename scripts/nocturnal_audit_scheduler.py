"""
BABYLON-60 8-HOUR NOCTURNAL CONTINUOUS AUDIT ENGINE (C5-REAL)
============================================================
Executes continuous multi-plane auditing, BFT ledger verification, 
GELABP exergy attestation, and vault synchronization over long-horizon runs.
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, Any

REPO_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = REPO_DIR / ".cortex" / "nocturnal_audit.log"

def run_cmd(cmd: str) -> bool:
    print(f"[*] Executing Audit Command: {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=str(REPO_DIR), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[-] ERROR in '{cmd}':\n{res.stderr}")
        return False
    return True

def execute_audit_iteration(iteration_num: int) -> Dict[str, Any]:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    print(f"\n==================================================")
    print(f"⚡ NOCTURNAL AUDIT ITERATION #{iteration_num} | {timestamp}")
    print(f"==================================================")

    # Plane 1: Invariant Auto-alignment
    align_ok = run_cmd(".venv/bin/python scripts/autodetect_invariants.py")

    # Plane 2: Memory Vault Synchronization
    sync_ok = run_cmd(".venv/bin/python scripts/sync_vault_uuids.py")

    # Plane 3: GELABP Exergy Matrix Evaluation
    exergy_ok = run_cmd(".venv/bin/python scripts/exergy_optimizer_agent.py")

    # Plane 4: Complete Pytest Validation
    pytest_ok = run_cmd(".venv/bin/pytest -v tests/")

    status = "SUCCESS" if (align_ok and sync_ok and exergy_ok and pytest_ok) else "FAILED"
    
    log_entry = f"[{timestamp}] Iteration #{iteration_num}: Status={status}\n"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

    return {
        "iteration": iteration_num,
        "timestamp": timestamp,
        "status": status,
        "planes_passed": [align_ok, sync_ok, exergy_ok, pytest_ok].count(True)
    }

def main():
    max_iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    interval_seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    for i in range(1, max_iterations + 1):
        res = execute_audit_iteration(i)
        if res["status"] != "SUCCESS":
            print(f"[-] AUDIT FAILURE at iteration #{i}. Halting.")
            sys.exit(1)
        if i < max_iterations and interval_seconds > 0:
            time.sleep(interval_seconds)

    print("\n✓ 8-HOUR NOCTURNAL AUDIT PROTOCOL COMPLETED SUCCESSFULLY (C5-REAL).")

if __name__ == "__main__":
    main()
