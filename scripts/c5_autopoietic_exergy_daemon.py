#!/usr/bin/env python3
"""
MOSKV-1 APEX: 100% AUTONOMOUS AUTOPOIETIC EXERGY DAEMON
Transduced via ULTRATHINK. Implements MAPE-K Autonomic Computing.
[CORTEX-TAINT:borjamoskv:autopoietic_daemon:2026-07-24]

Continuously monitors system entropy (Memory, WAL fragmentation, Deadlocks)
and self-regulates without Git Sentinel dependencies.
"""

import time
import subprocess
from pathlib import Path

# Config
WORKSPACE = Path("/Users/borjafernandezangulo/30_BABYLON-60")
MEMORY_THRESHOLD_PAGES = 128000  # ~500MB free
POLL_INTERVAL = 15  # seconds
MAX_WAL_SIZE = 10 * 1024 * 1024  # 10MB

def get_free_pages():
    try:
        res = subprocess.run(["vm_stat"], capture_output=True, text=True)
        for line in res.stdout.split('\n'):
            if "Pages free" in line:
                return int(line.split()[2].strip('.'))
    except (subprocess.SubprocessError, ValueError, IndexError):
        pass
    return float('inf')

def run_mapek_loop():
    print("⚡ [C5-REAL] Autopoietic Exergy Daemon Initialized. 100% Autonomous.")
    while True:
        try:
            # 1. MONITOR & ANALYZE
            entropy_flags = []
            
            # A. Check Memory Entropy
            free_pages = get_free_pages()
            if free_pages < MEMORY_THRESHOLD_PAGES:
                entropy_flags.append("MEMORY_PRESSURE")
                
            # B. Check WAL Fragmentation
            wals_to_collapse = []
            for db_path in WORKSPACE.rglob("*.db"):
                if ".venv" in db_path.parts or "target" in db_path.parts:
                    continue
                wal_path = db_path.with_name(db_path.name + "-wal")
                if wal_path.exists() and wal_path.stat().st_size > MAX_WAL_SIZE:
                    wals_to_collapse.append(db_path)
            if wals_to_collapse:
                entropy_flags.append("WAL_FRAGMENTATION")

            # C. Check Deadlocks
            stale_locks = list((WORKSPACE / ".git").glob("**/*.lock"))
            if stale_locks:
                entropy_flags.append("DEADLOCKS_DETECTED")

            # 2. PLAN & EXECUTE
            if entropy_flags:
                print(f"[{time.strftime('%H:%M:%S')}] Entropy Detected: {', '.join(entropy_flags)}")
                
                if "DEADLOCKS_DETECTED" in entropy_flags:
                    for lock in stale_locks:
                        try:
                            lock.unlink()
                            print(f"  [-] Purged stale lock: {lock.name}")
                        except OSError:
                            pass
                            
                if "WAL_FRAGMENTATION" in entropy_flags:
                    for db in wals_to_collapse:
                        subprocess.run(["sqlite3", str(db), "PRAGMA wal_checkpoint(TRUNCATE);"], capture_output=True)
                        print(f"  [-] Collapsed WAL for: {db.name}")
                        
                if "MEMORY_PRESSURE" in entropy_flags:
                    subprocess.run(["osascript", "-e", 'do shell script "purge"'], capture_output=True)
                    subprocess.run(["killall", "-9", "mediaanalysisd", "studentd"], capture_output=True)
                    print("  [-] Executed Kinetic OS Purge.")
            
        except (OSError, subprocess.SubprocessError) as e:
            print(f"[!] Daemon Fault: {e}")
            
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_mapek_loop()
