import sqlite3
import os
import sys

# Append root directory to path to import cortex_env
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cortex_env import get_bft_key

CORTEX_DIR = ".cortex"
DB_PATH = os.path.join(CORTEX_DIR, "cortex.db")


def init_ledger() -> None:
    # Validate BFT key presence via cortex_env (Ω25)
    bft_key = get_bft_key()

    if not os.path.exists(CORTEX_DIR):
        os.makedirs(CORTEX_DIR)

    # Conectar y establecer PRAGMAS físicos (Ω10)
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    cursor = conn.cursor()

    # Tolerancia a concurrencia extrema (WAL + Busy Timeout 5000ms)
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.execute("PRAGMA busy_timeout = 5000;")

    # Estructura del Ledger Inmutable (Ω11, Ω12)
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS bft_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        agent_id TEXT NOT NULL,
        lamport_t INTEGER NOT NULL,
        payload_hash TEXT NOT NULL,
        prev_hash TEXT NOT NULL,
        cortex_taint TEXT NOT NULL,
        UNIQUE(prev_hash),
        UNIQUE(lamport_t, agent_id)
    );

    -- Trigger de Inmutabilidad: Evita Updates
    CREATE TRIGGER IF NOT EXISTS prevent_ledger_update
    BEFORE UPDATE ON bft_ledger
    BEGIN
        SELECT RAISE(ABORT, 'EpistemicHalt: Modificación de ledger inmutable prohibida (Ω11).');
    END;

    -- Trigger de Inmutabilidad: Evita Deletes
    CREATE TRIGGER IF NOT EXISTS prevent_ledger_delete
    BEFORE DELETE ON bft_ledger
    BEGIN
        SELECT RAISE(ABORT, 'EpistemicHalt: Borrado de ledger inmutable prohibido (Ω11).');
    END;
    """)

    # Inyectar el bloque Génesis si está vacío
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
    print(
        f"Master Ledger inicializado en {DB_PATH}. WAL activo. Inmutabilidad enforzada (Ω11)."
    )


if __name__ == "__main__":
    init_ledger()
