# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
MOSKV-1 APEX: Swarm Workspace Lock Guard (INV_C5_22)
Enforces atomic lock acquisition (.cortex_thermal_lock) via O_EXCL kernel flags
before disk or git mutations across split clones (e.g. BABYLON-60 vs 30_BABYLON-60).
"""
import os
import sys
import time

LOCK_FILENAME = ".cortex_thermal_lock"
MAX_LOCK_AGE_SEC = 300.0

def verify_and_acquire_lock(workspace_dir: str) -> None:
    lock_path = os.path.join(workspace_dir, LOCK_FILENAME)

    # Check for stale lock under INV_C5_19 thermal hysteresis bounds
    if os.path.exists(lock_path):
        try:
            mtime = os.path.getmtime(lock_path)
            if time.time() - mtime > MAX_LOCK_AGE_SEC:
                print(f"[WARN] Stale lock detected at {lock_path}. Evicting under INV_C5_19.", file=sys.stderr)
                os.unlink(lock_path)
        except OSError:
            _ = None

    try:
        # Atomic O_CREAT | O_EXCL acquisition
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(f"PID:{os.getpid()}\nEPOCH:{time.time()}\n")
        print(f"[SUCCESS] Swarm Lock acquired atomically at {lock_path}.")
    except FileExistsError:
        print(f"[FAIL-FAST] Concurrent Swarm mutation blocked! Lock {lock_path} is active.", file=sys.stderr)
        sys.exit(1)

def release_lock(workspace_dir: str) -> None:
    lock_path = os.path.join(workspace_dir, LOCK_FILENAME)
    try:
        if os.path.exists(lock_path):
            os.unlink(lock_path)
            print(f"[SUCCESS] Swarm Lock released from {lock_path}.")
    except OSError:
        sys.exit(1)

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    verify_and_acquire_lock(target_dir)
    # Simulate immediate release after validation for verification hook
    release_lock(target_dir)
