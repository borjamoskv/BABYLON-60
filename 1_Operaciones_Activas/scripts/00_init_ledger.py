# C5-REAL EXERGY CERTIFIED
import sqlite3
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cortex_env import get_bft_key

CORTEX_DIR = ".cortex"
DB_PATH = os.path.join(CORTEX_DIR, "cortex.db")

def init_bft_ledger_tables(conn: sqlite3.Connection) -> None:
    """Single source of truth for SQLite BFT Master Ledger schema and triggers (Ω11, Ω12, R10)."""
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS bft_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        agent_id TEXT,
        lamport_t INTEGER,
        payload_hash TEXT,
        step_index INTEGER,
        domain INTEGER,
        primitive INTEGER,
        modifier INTEGER,
        prev_hash TEXT NOT NULL UNIQUE,
        current_hash TEXT,
        cortex_taint TEXT NOT NULL
    );

    CREATE TRIGGER IF NOT EXISTS prevent_ledger_update
    BEFORE UPDATE ON bft_ledger
    BEGIN
        SELECT RAISE(ABORT, 'EpistemicHalt: Modificación de ledger inmutable prohibida / Ledger updates are forbidden (Ω11).');
    END;

    CREATE TRIGGER IF NOT EXISTS prevent_ledger_delete
    BEFORE DELETE ON bft_ledger
    BEGIN
        SELECT RAISE(ABORT, 'EpistemicHalt: Borrado de ledger inmutable prohibido / Ledger deletions are forbidden (Ω11).');
    END;
    """)

def init_ledger() -> None:
    # Validate BFT key presence via cortex_env (Ω25)
    get_bft_key()

    if not os.path.exists(CORTEX_DIR):
        os.makedirs(CORTEX_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    init_bft_ledger_tables(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM bft_ledger")
    if cursor.fetchone()[0] == 0:
        print("[IGNICIÓN] Inicializando Bloque Génesis del Master Ledger...")
        cursor.execute(
            """INSERT INTO bft_ledger (agent_id, lamport_t, payload_hash, prev_hash, cortex_taint)
               VALUES (?, ?, ?, ?, ?)""",
            (
                "ROOT_OPERATOR_UID0",
                0,
                "GENESIS_PAYLOAD",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "CORTEX-TAINT:borjamoskv:genesis:2026",
            ),
        )

    conn.commit()
    conn.close()
    print(f"Master Ledger inicializado en {DB_PATH}. WAL activo. Inmutabilidad enforzada (Ω11).")

if __name__ == "__main__":
    init_ledger()
