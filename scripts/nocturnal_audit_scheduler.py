"""
BABYLON-60 8-HOUR NOCTURNAL CONTINUOUS AUDIT ENGINE (C5-REAL)
============================================================
Executes continuous multi-plane auditing, BFT ledger verification, 
GELABP exergy attestation, and vault synchronization over long-horizon runs.
"""

import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = REPO_DIR / ".cortex" / "nocturnal_audit.log"

def get_python_exe() -> str:
    for candidate in [sys.executable, str(REPO_DIR / ".venv" / "bin" / "python3"), "python3"]:
        if not candidate or not (Path(candidate).exists() if "/" in candidate else shutil.which(candidate)):
            continue
        try:
            res = subprocess.run([candidate, "-m", "pytest", "--version"], capture_output=True, text=True)
            if res.returncode == 0:
                return candidate
        except (FileNotFoundError, PermissionError, subprocess.SubprocessError, OSError):
            continue
    return sys.executable

def run_cmd(cmd: str | list[str]) -> bool:
    cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
    print(f"[*] Executing Audit Command: {cmd_str}")
    use_shell = isinstance(cmd, str)
    res = subprocess.run(cmd, shell=use_shell, cwd=str(REPO_DIR), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[-] ERROR in '{cmd_str}':\n{res.stderr}\n{res.stdout}")
        return False
    return True

def execute_audit_iteration(iteration_num: int) -> dict[str, Any]:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    print("\n==================================================")
    print(f"⚡ NOCTURNAL AUDIT ITERATION #{iteration_num} | {timestamp}")
    print("==================================================")

    py_exe = get_python_exe()

    # Plane 1: Invariant Auto-alignment
    align_ok = run_cmd([py_exe, "scripts/autodetect_invariants.py"])

    # Plane 2: Memory Vault Synchronization
    sync_ok = run_cmd([py_exe, "scripts/sync_vault_uuids.py"])

    # Plane 3: GELABP Exergy Matrix Evaluation
    exergy_ok = run_cmd([py_exe, "scripts/exergy_optimizer_agent.py"])

    # Plane 4: Complete Pytest Validation
    pytest_ok = run_cmd([py_exe, "-m", "pytest", "-v", "tests/", "-k", "not test_nocturnal_audit_scheduler"])

    # Plane 5: Secret Swarm Audit
    secret_ok = run_cmd([py_exe, "scripts/secret_swarm_auditor.py"])

    status = "SUCCESS" if (align_ok and sync_ok and exergy_ok and pytest_ok and secret_ok) else "FAILED"
    
    log_entry = f"[{timestamp}] Iteration #{iteration_num}: Status={status} (Planes: {[align_ok, sync_ok, exergy_ok, pytest_ok, secret_ok].count(True)}/5)\n"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

    return {
        "iteration": iteration_num,
        "timestamp": timestamp,
        "status": status,
        "planes_passed": [align_ok, sync_ok, exergy_ok, pytest_ok, secret_ok].count(True)
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
