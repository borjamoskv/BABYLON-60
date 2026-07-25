import asyncio
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from babylon60.database import core as dbcore


@dataclass
class ApexClaim:
    claim_id: str
    payload: dict[str, Any]
    prev_hash: str
    confidence: str
    lamport_t: int


class Moskv1Kernel:
    def __init__(self, db_path: str = "apex_cortex.db") -> None:
        self.db_path = db_path
        self._write_queue: asyncio.Queue[ApexClaim] = asyncio.Queue()
        self._lamport_clock: int = 0
        self._last_hash: str = "0000000000000000000000000000000000000000000000000000000000000000"
        self._boot_sequence()

    def _boot_sequence(self) -> None:
        try:
            conn = dbcore.connect_sync(self.db_path, synchronous="FULL")
            try:
                conn.execute(
                    "\n                    CREATE TABLE IF NOT EXISTS master_ledger (\n                        claim_id TEXT PRIMARY KEY,\n                        payload JSON NOT NULL,\n                        prev_hash TEXT UNIQUE NOT NULL,\n                        current_hash TEXT UNIQUE NOT NULL,\n                        cortex_taint TEXT NOT NULL,\n                        lamport_t INTEGER NOT NULL\n                    )\n                "
                )
                cursor = conn.execute("SELECT MAX(lamport_t), current_hash FROM master_ledger")
                row = cursor.fetchone()
                if row and row[0] is not None:
                    self._lamport_clock = row[0]
                    self._last_hash = row[1]
            finally:
                conn.close()
        except (sqlite3.DatabaseError, OSError, ValueError):
            raise RuntimeError("FAIL-FAST: Fallo catastrófico en boot BFT.")

    async def ingest_entropy(self, payload: dict[str, Any], confidence: str = "C5") -> str:
        self._lamport_clock += 1
        claim = ApexClaim(
            claim_id=f"evt_{self._lamport_clock}_{int(datetime.now(timezone.utc).timestamp())}",
            payload=payload,
            prev_hash=self._last_hash,
            confidence=confidence,
            lamport_t=self._lamport_clock,
        )
        await self._write_queue.put(claim)
        return claim.claim_id

    def _compute_hash(self, claim: ApexClaim) -> str:
        data = f"{claim.prev_hash}:{json.dumps(claim.payload, sort_keys=True)}:{claim.lamport_t}"
        return hashlib.sha3_256(data.encode("utf-8")).hexdigest()

    async def bft_state_loop(self) -> None:
        print("[MOSKV-1] KERNEL IGNITION: BFT_STATE_LOOP ACTIVATED.")
        try:
            while True:
                claim = await self._write_queue.get()
                if claim.confidence not in ("C4", "C5"):
                    print(f"[-] Anergía detectada en {claim.claim_id}. Purgando.")
                    self._write_queue.task_done()
                    continue
                current_hash = self._compute_hash(claim)
                taint_signature = (
                    f"[CORTEX-TAINT:borjamoskv:bft_loop:{datetime.now(timezone.utc).isoformat()}:{current_hash[:16]}]"
                )
                try:
                    db = await dbcore.connect(self.db_path, synchronous="FULL")
                    try:
                        await db.execute(
                            "INSERT INTO master_ledger (claim_id, payload, prev_hash, current_hash, cortex_taint, lamport_t) VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                claim.claim_id,
                                json.dumps(claim.payload),
                                claim.prev_hash,
                                current_hash,
                                taint_signature,
                                claim.lamport_t,
                            ),
                        )
                        self._last_hash = current_hash
                        print(f"[+] Cristalizado: {claim.claim_id} -> {current_hash[:8]}")
                    finally:
                        await db.close()
                except sqlite3.IntegrityError:
                    print(f"[!] Idempotency Lock disparado para {claim.claim_id}. Entropía abortada.")
                except sqlite3.DatabaseError:
                    raise RuntimeError("FAIL-FAST: BFT Ledger corrompido.")
                self._write_queue.task_done()
        except asyncio.CancelledError:
            print("[MOSKV-1] KERNEL SHUTDOWN: SIGTERM RECIBIDO.")


async def _main() -> None:
    kernel = Moskv1Kernel()
    loop_task = asyncio.create_task(kernel.bft_state_loop())
    await kernel.ingest_entropy({"action": "kernel_bootstrap", "status": "C5-REAL", "target": "master_ledger"})
    await asyncio.sleep(0.5)
    loop_task.cancel()


if __name__ == "__main__":
    asyncio.run(_main())
