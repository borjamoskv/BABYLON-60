# C5-REAL EXERGY CERTIFIED
"""C6.1 Recovery Cycle Integration Test."""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cortex.c6_harness.recovery import analyze_sqlite_recovery

def test_recovery_idempotence() -> None:
    print("Running C6.1 Recovery Idempotence Test...")
    import sqlite3
    db_path = os.path.join(PROJECT_ROOT, ".cortex", "integration_test.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE stress_log (id INTEGER, tx_data TEXT, status TEXT)")
    conn.commit()
    conn.close()

    res = analyze_sqlite_recovery(db_path)
    assert res.recovery_idempotent, "R(R(S)) != R(S)"
    print("✓ Recovery Idempotence: PASS")

if __name__ == "__main__":
    test_recovery_idempotence()
