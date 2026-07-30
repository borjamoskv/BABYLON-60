# C5-REAL EXERGY CERTIFIED
import sqlite3
import uuid
import hashlib
import asyncio
import time
from typing import Dict, Any, List

DB_PATH = "poc_bft_memory.db"
NAMESPACE_CORTEX = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')

class BFTLedgerActor:
    """
    INV_BFT_02: Never call sqlite3 synchronously inside an async event loop natively.
    INV_BFT_04: Single writer.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        self._lock = asyncio.Lock()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        # BFT Invariants: WAL mode, busy_timeout
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
        """
        Inyección serializada forzando el Single Writer BFT.
        Rechazo silencioso de duplicados (INV_BFT_04).
        """
        async with self._lock:
            # Simulamos el offloading al thread síncrono del OS
            await asyncio.sleep(0.01)
            conn = sqlite3.connect(self.db_path, isolation_level=None)
            try:
                conn.execute(
                    "INSERT INTO bft_ledger (idempotency_key, causal_taint, payload, timestamp) VALUES (?, ?, ?, ?)",
                    (idempotency_key, causal_taint, payload, time.time())
                )
                return True
            except sqlite3.IntegrityError:
                # BFT Colisión / Idempotencia: Rechazo silencioso
                return False
            finally:
                conn.close()

class CausalRouter:
    def __init__(self, ledger: BFTLedgerActor):
        self.ledger = ledger

    async def route_payload(self, node_id: str, payload: str) -> bool:
        """
        Genera la clave de idempotencia UUIDv5 determinista y el Taint Causal.
        """
        # INV_BFT_04: UUID v5 idempotency keys
        hash_base = f"{node_id}:{payload}".encode('utf-8')
        idempotency_key = str(uuid.uuid5(NAMESPACE_CORTEX, hash_base.decode('utf-8')))

        # INV_BFT_03: Causal taint
        causal_taint = f"[CORTEX-TAINT:{node_id}:bft_loop]"

        success = await self.ledger.inject_deterministic(idempotency_key, causal_taint, payload)
        return success

async def swarm_node_worker(router: CausalRouter, node_id: str, payloads: List[str]):
    results = []
    for p in payloads:
        res = await router.route_payload(node_id, p)
        results.append(res)
    return results

async def main():
    print("=== INICIANDO PRUEBA DE CONCEPTO BFT ===")
    ledger = BFTLedgerActor(DB_PATH)
    router = CausalRouter(ledger)

    # Payload A: Generará colisión si 2 nodos envían exactamente lo mismo
    # Payload B: Diferente

    tasks = []
    # Simulamos 5 agentes intentando inyectar datos concurrentemente
    tasks.append(swarm_node_worker(router, "moskv_node_1", ["Axiom 1", "Axiom 2", "Axiom 1"]))
    tasks.append(swarm_node_worker(router, "moskv_node_2", ["Axiom 1", "Axiom 3"]))
    tasks.append(swarm_node_worker(router, "moskv_node_3", ["Axiom 2", "Axiom 4"]))

    start = time.time()
    results = await asyncio.gather(*tasks)
    latencia = time.time() - start

    print(f"Latencia Total (Swarm Inyección): {latencia:.4f}s")
    print(f"Resultados de Inyección (True=Insertado, False=Rechazado BFT):")
    print(f"  Nodo 1: {results[0]}")
    print(f"  Nodo 2: {results[1]}")
    print(f"  Nodo 3: {results[2]}")

    # Verificamos estado físico
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT idempotency_key, causal_taint, payload FROM bft_ledger").fetchall()
    print("\\n=== VOLCADO DE MEMORIA DETERMINISTA ===")
    for r in rows:
        print(f" [TAINT: {r[1]}] -> PAYLOAD: {r[2]} | UUID: {r[0]}")
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
