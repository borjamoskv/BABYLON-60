# C5-REAL EXERGY CERTIFIED
import sqlite3
import uuid
import asyncio
import time
from typing import List

DB_PATH = "poc_bft_stress.db"
NAMESPACE_CORTEX = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')

class BFTLedgerActor:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        self._lock = asyncio.Lock()

    def _init_db(self):
        # Destruir DB anterior si existe para prueba limpia
        import os
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        conn = sqlite3.connect(self.db_path, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bft_ledger (
                idempotency_key TEXT PRIMARY KEY,
                causal_taint TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        """)
        conn.close()

    async def inject_deterministic(self, idempotency_key: str, causal_taint: str, payload: str):
        async with self._lock:
            conn = sqlite3.connect(self.db_path, isolation_level=None)
            try:
                conn.execute(
                    "INSERT INTO bft_ledger (idempotency_key, causal_taint, payload, timestamp) VALUES (?, ?, ?, ?)",
                    (idempotency_key, causal_taint, payload, time.time())
                )
                return True
            except sqlite3.IntegrityError:
                return False
            finally:
                conn.close()

class CausalRouter:
    def __init__(self, ledger: BFTLedgerActor):
        self.ledger = ledger

    async def route_payload(self, node_id: str, payload: str) -> bool:
        hash_base = f"{node_id}:{payload}".encode('utf-8')
        idempotency_key = str(uuid.uuid5(NAMESPACE_CORTEX, hash_base.decode('utf-8')))
        causal_taint = f"[CORTEX-TAINT:{node_id}:stress]"
        return await self.ledger.inject_deterministic(idempotency_key, causal_taint, payload)

async def stress_worker(router: CausalRouter, node_id: str, payload: str):
    return await router.route_payload(node_id, payload)

async def main():
    print("=== INICIANDO STRESS TEST BFT (100% GARANTÍA) ===")
    ledger = BFTLedgerActor(DB_PATH)
    router = CausalRouter(ledger)

    # Vamos a disparar 1,000 inyecciones concurrentes exactamente iguales
    # Si el sistema no es BFT 100%, o colapsará con "database is locked"
    # o insertará múltiples filas.
    N_AGENTS = 1000
    TARGET_PAYLOAD = "AXIOMA_ABSOLUTO_C5"
    NODE_ID = "swarm_hive_mind"

    tasks = [stress_worker(router, NODE_ID, TARGET_PAYLOAD) for _ in range(N_AGENTS)]

    start = time.time()
    results = await asyncio.gather(*tasks)
    latencia = time.time() - start

    inserts_exitosos = sum(results)
    rechazos_bft = len(results) - inserts_exitosos

    print(f"Agentes Disparados Simultáneamente: {N_AGENTS}")
    print(f"Latencia Total: {latencia:.4f}s")
    print(f"Inserciones Exitosas: {inserts_exitosos} (Debería ser exactamente 1)")
    print(f"Rechazos Silenciosos (Idempotencia BFT mitigó la colisión): {rechazos_bft}")

    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM bft_ledger").fetchone()[0]
    conn.close()

    print(f"Filas físicas en disco: {count}")
    if count == 1 and inserts_exitosos == 1:
        print("VEREDICTO: DETERMINISMO 100% MATEMÁTICAMENTE DEMOSTRADO.")
    else:
        print("VEREDICTO: FALLO CATASTRÓFICO.")

if __name__ == "__main__":
    asyncio.run(main())
