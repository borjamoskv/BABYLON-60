#!/usr/bin/env python3
# C5-REAL: MOSKV-1 Master BFT Ledger (State Transducer)
import sqlite3
import hashlib
import time
from typing import Optional

class CortexBFTLedger:
    """
    Motor de Consenso y Tolerancia Bizantina (BFT).
    En un IDE guiado por TDAH, el contexto es masivo y efímero.
    Este ledger asegura que toda mutación de código y decisión cognitiva 
    quede anclada físicamente al disco (SQLite WAL), evitando Amnesia de Contexto.
    """
    
    def __init__(self, db_path: str = ".cortex_engine.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Inicialización síncrona en modo WAL (Regla Ω1 y Ω10)"""
        with sqlite3.connect(self.db_path, timeout=5.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mutations (
                    hash_id TEXT PRIMARY KEY,
                    lamport_t INTEGER NOT NULL,
                    agent_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    prev_hash TEXT,
                    cortex_taint TEXT NOT NULL
                )
            """)
            conn.commit()

    def _get_max_lamport(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT MAX(lamport_t) FROM mutations")
            res = cur.fetchone()[0]
            return res if res is not None else 0

    def get_last_hash(self) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT hash_id FROM mutations ORDER BY lamport_t DESC LIMIT 1")
            res = cur.fetchone()
            return res[0] if res else None

    def commit_mutation(self, payload: str, agent_id: str = "borjamoskv_IDE") -> str:
        """
        Consolida una mutación. Regla Ω11: Integrity en DB mediante firma CORTEX-TAINT.
        """
        prev_hash = self.get_last_hash()
        lamport_t = self._get_max_lamport() + 1
        
        # Inyección de causalidad (Merkle-like)
        raw_data = f"{lamport_t}:{agent_id}:{payload}:{prev_hash or 'GENESIS'}"
        hash_id = hashlib.sha256(raw_data.encode()).hexdigest()
        
        cortex_taint = f"[CORTEX-TAINT:borjamoskv:ide_mutation:{int(time.time())}:{hash_id[:16]}]"

        try:
            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                conn.execute(
                    "INSERT INTO mutations (hash_id, lamport_t, agent_id, payload, prev_hash, cortex_taint) VALUES (?, ?, ?, ?, ?, ?)",
                    (hash_id, lamport_t, agent_id, payload, prev_hash, cortex_taint)
                )
                conn.commit()
            print(f"[LEDGER] Mutación cristalizada en WAL: {hash_id[:8]}")
            return hash_id
        except sqlite3.IntegrityError:
            print("[LEDGER] Idempotency Lock disparado. Mutación duplicada detectada.")
            return hash_id

if __name__ == "__main__":
    ledger = CortexBFTLedger()
    h = ledger.commit_mutation('{"action": "create_file", "target": "main.py"}')
    print(f"Hash Genesis: {h}")
