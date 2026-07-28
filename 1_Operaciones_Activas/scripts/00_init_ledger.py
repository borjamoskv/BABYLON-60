# C5-REAL EXERGY CERTIFIED
import os
import sqlite3
import hashlib

DB_PATH = os.getenv("CORTEX_BFT_DB", "master_ledger.db")

def hash_payload(lamport_t: int, agent_id: str, prev_hash: str) -> str:
    data = f"{lamport_t}:{agent_id}:{prev_hash}".encode("utf-8")
    return hashlib.sha3_256(data).hexdigest()

def init_ledger() -> None:
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bft_ledger (
            lamport_t INTEGER PRIMARY KEY,
            agent_id TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            prev_hash TEXT NOT NULL,
            cortex_taint TEXT NOT NULL
        )
    """)
    # Immutable Ledger triggers (Ω11)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS bft_ledger_no_update
        BEFORE UPDATE ON bft_ledger
        BEGIN
            SELECT RAISE(ABORT, 'Modificación de ledger inmutable prohibida (Ω11)');
        END;
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS bft_ledger_no_delete
        BEFORE DELETE ON bft_ledger
        BEGIN
            SELECT RAISE(ABORT, 'Borrado de ledger inmutable prohibido (Ω11)');
        END;
    """)

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM bft_ledger WHERE lamport_t = 0")
    if cursor.fetchone()[0] == 0:
        genesis_agent = "ROOT_OPERATOR_UID0"
        genesis_hash = hash_payload(0, genesis_agent, "0" * 64)
        conn.execute(
            "INSERT INTO bft_ledger (lamport_t, agent_id, payload_hash, prev_hash, cortex_taint) VALUES (0, ?, ?, ?, 'CORTEX-TAINT:GENESIS')",
            (genesis_agent, genesis_hash, "0" * 64)
        )
        conn.commit()
    conn.close()

if __name__ == "__main__":
    init_ledger()
