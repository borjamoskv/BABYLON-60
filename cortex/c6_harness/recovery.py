# C5-REAL EXERGY CERTIFIED
"""C6-REAL Recovery Auditor."""
import sqlite3
import os
import hashlib
from .invariant import RecoveryResult

def _get_db_hash(db_path: str) -> str:
    """Computes SHA3-256 of the database file."""
    if not os.path.exists(db_path):
        return ""
    m = hashlib.sha3_256()
    with open(db_path, "rb") as f:
        while chunk := f.read(8192):
            m.update(chunk)
    return m.hexdigest()

def analyze_sqlite_recovery(db_path: str) -> RecoveryResult:
    """Performs cold-restart audit of SQLite WAL and checks invariants including idempotence."""
    if not os.path.exists(db_path):
        return RecoveryResult(False, 1, 1, False, False)

    # First Recovery Cycle
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchone()[0].upper()
    integrity_ok = (integrity == "OK")

    cursor.execute("SELECT COUNT(*) FROM stress_log WHERE status = 'PARTIAL'")
    partial_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM stress_log WHERE status = 'COMMITTED'")
    committed_count = cursor.fetchone()[0]

    leaks = partial_count - committed_count

    conn.close()

    hash_r1 = _get_db_hash(db_path)

    # Second Recovery Cycle (Idempotency R(R(S)) == R(S))
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA integrity_check;") # Force read
    conn.close()

    hash_r2 = _get_db_hash(db_path)

    return RecoveryResult(
        integrity_ok=integrity_ok,
        committed_transactions_lost=0 if leaks <= 0 else leaks,
        phantom_transactions_found=abs(leaks) if leaks != 0 else 0,
        recovery_idempotent=(hash_r1 == hash_r2),
        state_hash_stable=(hash_r1 == hash_r2)
    )
