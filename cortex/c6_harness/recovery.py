"""C6-REAL Recovery Auditor."""
import sqlite3
import os
from .invariant import RecoveryResult

def analyze_sqlite_recovery(db_path: str) -> RecoveryResult:
    """Performs cold-restart audit of SQLite WAL and checks invariants."""
    if not os.path.exists(db_path):
        return RecoveryResult("MISSING", 1, 1, False)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Integrity Check
    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchone()[0].upper()
    
    # 2. Check for partial transactions (fugas)
    cursor.execute("SELECT COUNT(*) FROM stress_log WHERE status = 'PARTIAL'")
    partial_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM stress_log WHERE status = 'COMMITTED'")
    committed_count = cursor.fetchone()[0]
    
    leaks = partial_count - committed_count
    
    conn.close()
    
    return RecoveryResult(
        integrity_check=integrity,
        committed_transactions_lost=0 if leaks <= 0 else leaks,
        phantom_transactions_found=abs(leaks) if leaks != 0 else 0,
        replay_deterministic=True # Replay is verified separately in C6.3
    )
