# C5-REAL EXERGY CERTIFIED
import asyncio
import sqlite3
import sys
from pathlib import Path

# Import the module to be refuted
from __import__("00_APEX_FSM").ApexFiniteStateMachine as APEX

async def adversarial_refutation():
    """
    [Ω186] Adversarial Verify: Try to refute the idempotency claim of 00_APEX_FSM.py
    Claim: The system guarantees idempotency (Ω15) via entry_hash.
    Refutation Strategy: Inject the exact same payload twice. Since event_id is uuid4(),
    INSERT OR IGNORE will bypass idempotency unless entry_hash has a UNIQUE constraint.
    """
    db_path = Path("adversarial_ledger.db")
    if db_path.exists():
        db_path.unlink()

    fsm = APEX(db_path)

    # Inject same payload twice
    res1 = await fsm.execute_direct_transduction("TASK_1", '{"action": "test"}', "0")
    res2 = await fsm.execute_direct_transduction("TASK_1", '{"action": "test"}', "0")

    # Read from DB
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT entry_hash FROM master_ledger")
        rows = cursor.fetchall()

    if len(rows) > 1 and rows[0][0] == rows[1][0]:
        print(f"\n[💥 REFUTED] C5-REAL Adversarial Victory! Idempotency broken. Ledger contains {len(rows)} duplicate entries.")
        sys.exit(1)
    else:
        print("\n[🛡️ SECURE] Idempotency holds. Refutation failed.")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(adversarial_refutation())
