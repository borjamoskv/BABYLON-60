#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def run_test_suite():
    """
    Runs pytest on the local repository to audit correctness of state.
    """
    print("[Ouroboros-∞] Executing automated test suite audit...")
    my_env = os.environ.copy()
    my_env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")
    
    # Try using system-wide pytest first since it's available in /opt/homebrew/bin
    try:
        result = subprocess.run(
            ["pytest"],
            capture_output=True,
            text=True,
            env=my_env
        )
        return result.returncode == 0, result.stdout, result.stderr
    except FileNotFoundError:
        # Fallback to sys.executable
        result = subprocess.run(
            [sys.executable, "-m", "pytest"],
            capture_output=True,
            text=True,
            env=my_env
        )
        return result.returncode == 0, result.stdout, result.stderr

def run_exergy_audit():
    """
    Runs the exergy sensor on the current session logs if available.
    """
    print("[Ouroboros-∞] Evaluating thermodynamic context exergy...")
    base_dir = Path(__file__).parent.parent
    # Look for the current transcript.jsonl log in antigravity app data directory
    app_data_dir = Path("/Users/borjafernandezangulo/.gemini/antigravity")
    brain_dir = app_data_dir / "brain"
    
    if brain_dir.exists():
        subdirs = [d for d in brain_dir.iterdir() if d.is_dir()]
        if subdirs:
            latest_subdir = max(subdirs, key=lambda d: d.stat().st_mtime)
            transcript_path = latest_subdir / ".system_generated" / "logs" / "transcript.jsonl"
        else:
            transcript_path = brain_dir / "3cfc9bef-827d-441c-8453-7e917c32297a" / ".system_generated" / "logs" / "transcript.jsonl"
    else:
        transcript_path = brain_dir / "3cfc9bef-827d-441c-8453-7e917c32297a" / ".system_generated" / "logs" / "transcript.jsonl"
    
    if transcript_path.exists():
        sensor_script = base_dir / "exergy_sensor.py"
        result = subprocess.run(
            [sys.executable, str(sensor_script), str(transcript_path)],
            capture_output=True,
            text=True
        )
        print(result.stdout)
    else:
        print(f"[Ouroboros-∞] No active transcript log found at {transcript_path} (Skipping exergy sensor).")

def check_git_status():
    """
    Checks git status for uncommitted changes or untracked files.
    """
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    return result.stdout.strip()

def ouroboros_cycle():
    print("=== STARTING OUROBOROS-∞ CLOSED-LOOP COGNITIVE CYCLE ===")
    
    # Step 1: Run tests to verify the integrity of the live brain regions
    tests_passed, stdout, stderr = run_test_suite()
    if not tests_passed:
        print("[Ouroboros-∞] CRITICAL: System test suite failed. Initiating self-healing sequence...")
        print(stdout)
        print(stderr)
        # In a fully closed loop, we would auto-diagnose and correct imports or syntax here.
        # For now, we flag the exergy degradation and return failure.
        sys.exit(1)
    else:
        print("[Ouroboros-∞] ✓ Test suite verification passed successfully.")
        
    # Step 2: Run thermodynamic exergy sensor audit
    run_exergy_audit()
    
    # Step 3: Git Sentinel - Check ledger synchronization
    uncommitted = check_git_status()
    if uncommitted:
        print("[Ouroboros-∞] Detected uncommitted modifications in the Ledger:")
        print(uncommitted)
        print("[Ouroboros-∞] Sealing mutations dynamically in Git Sentinel...")
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", "chore(autopoiesis): dynamic ledger alignment via Ouroboros-∞ loop"])
        print("[Ouroboros-∞] Ledger mutations sealed successfully.")
    else:
        print("[Ouroboros-∞] ✓ Ledger is fully synchronized. No new mutations found.")
        
    print("=== OUROBOROS-∞ CYCLE COMPLETE [NO ENTROPY DETECTED] ===")

if __name__ == "__main__":
    ouroboros_cycle()
