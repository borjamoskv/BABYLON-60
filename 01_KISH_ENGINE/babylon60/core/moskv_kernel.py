# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import asyncio
import os
import signal
import sqlite3
import hashlib
import json
import uuid
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

from babylon60.database import core as dbcore


# -----------------------------------------------------------------------------
# MOSKV-1 APEX SINGULARITY KERNEL (Causal-Determinist)
# -----------------------------------------------------------------------------
# BFT_STATE_LOOP: LEYES FÍSICAS DE EJECUCIÓN Causal-Determinist (v12.0)
# - Serialización estricta de escritura (1 escritor, N lectores).
# - SQLite WAL mode con busy_timeout 5000ms.
# - Fail-Fast SIGKILL ante derivas estocásticas o violaciones de invariante.
# -----------------------------------------------------------------------------


@dataclass
class ApexClaim:
    """Invariante Tipado para mutaciones de estado."""

    claim_id: str
    payload: Dict[str, Any]
    prev_hash: str
    confidence: str
    lamport_t: int


class Moskv1Kernel:
    """Transductor determinista de leyes termodinámicas y mutaciones de estado sobre el disco."""

    def __init__(self, db_path: str = "apex_cortex.db") -> None:
        self.db_path = db_path
        self._write_queue: asyncio.Queue[ApexClaim] = asyncio.Queue(maxsize=4096)
        self._lamport_clock: int = 0
        self._last_hash: str = "0000000000000000000000000000000000000000000000000000000000000000"
        self._stop_event: asyncio.Event = asyncio.Event()
        self._claim_status: Dict[str, str] = {}
        self._boot_sequence()

    def stop(self) -> None:
        self._stop_event.set()

    def get_claim_status(self, claim_id: str) -> Optional[str]:
        """Return known lifecycle state for an admitted claim."""
        return self._claim_status.get(claim_id)

    def _boot_sequence(self) -> None:
        """Ignición Síncrona. Prepara el entorno BFT_STATE_LOOP."""
        try:
            conn = dbcore.connect_sync(self.db_path, synchronous="FULL")
            try:
                # Tabla Master Ledger (Solo INSERTS, inmutable)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS master_ledger (
                        claim_id TEXT PRIMARY KEY,
                        payload JSON NOT NULL,
                        prev_hash TEXT UNIQUE NOT NULL,
                        current_hash TEXT UNIQUE NOT NULL,
                        cortex_taint TEXT NOT NULL,
                        lamport_t INTEGER NOT NULL
                    )
                """)

                # Recuperación de reloj de Lamport para tie-breaking BFT
                cursor = conn.execute("SELECT MAX(lamport_t), current_hash FROM master_ledger")
                row = cursor.fetchone()
                if row and row[0] is not None:
                    self._lamport_clock = row[0]
                    self._last_hash = row[1]
            finally:
                conn.close()
        except (sqlite3.DatabaseError, OSError, ValueError):
            os.kill(os.getpid(), signal.SIGKILL)
            raise RuntimeError("FAIL-FAST: Fallo catastrófico en boot BFT.")

    async def ingest_entropy(self, payload: Dict[str, Any], confidence: str = "C5") -> str:
        """Admit a claim and return tracking, not a durability acknowledgement."""
        if self._stop_event.is_set():
            raise RuntimeError("Kernel is stopping; claim was not accepted")
        if confidence not in ("C4", "C5"):
            raise ValueError("Unsupported confidence; claim was not accepted")
        self._lamport_clock += 1
        claim = ApexClaim(
            claim_id=f"evt_{self._lamport_clock}_{uuid.uuid4().hex}",
            payload=json.loads(json.dumps(payload)),
            prev_hash=self._last_hash,
            confidence=confidence,
            lamport_t=self._lamport_clock,
        )
        # Admission must not suspend between stop validation and insertion.
        self._write_queue.put_nowait(claim)
        self._claim_status[claim.claim_id] = "QUEUED"
        return claim.claim_id

    def _compute_hash(self, claim: ApexClaim) -> str:
        """Firma BFT con SHA3-256 (Crypto BFT Sovereignty)."""
        data = f"{claim.prev_hash}:{json.dumps(claim.payload, sort_keys=True)}:{claim.lamport_t}"
        return hashlib.sha3_256(data.encode("utf-8")).hexdigest()

    async def _next_claim(self) -> Optional[ApexClaim]:
        try:
            return await asyncio.wait_for(self._write_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None

    async def _verify_idempotency_collision(self, claim: ApexClaim) -> None:
        db_chk = await dbcore.connect(self.db_path, synchronous="FULL")
        try:
            cursor = await db_chk.execute(
                "SELECT payload FROM master_ledger WHERE claim_id = ?",
                (claim.claim_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                raise ValueError("Constraint failure is not an idempotent replay: tracking ID is absent")
            existing_payload = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            if existing_payload != claim.payload:
                raise ValueError(f"Fail-fast: INV_BFT_04 Collision on claim_id {claim.claim_id}: payload mismatch")
        finally:
            await db_chk.close()

    async def _insert_claim_db(self, claim: ApexClaim) -> None:
        db = await dbcore.connect(self.db_path, synchronous="FULL")
        try:
            await db.execute("BEGIN IMMEDIATE")
            cursor = await db.execute("SELECT payload FROM master_ledger WHERE claim_id = ?", (claim.claim_id,))
            existing = await cursor.fetchone()
            if existing is not None:
                if json.loads(existing[0]) != claim.payload:
                    raise ValueError("Existing tracking ID has a different payload")
                await db.rollback()
                return
            cursor = await db.execute(
                "SELECT lamport_t,current_hash FROM master_ledger ORDER BY lamport_t DESC LIMIT 1"
            )
            tip = await cursor.fetchone()
            # The predecessor belongs to the transaction, not the ingestion snapshot.
            claim.prev_hash = tip[1] if tip else "0" * 64
            claim.lamport_t = max(claim.lamport_t, (tip[0] + 1) if tip else 1)
            current_hash = self._compute_hash(claim)
            taint_signature = (
                f"[CORTEX-TAINT:borjamoskv:bft_loop:{datetime.now(timezone.utc).isoformat()}:{current_hash[:16]}]"
            )
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
            await db.commit()
            self._last_hash = current_hash
            self._lamport_clock = max(self._lamport_clock, claim.lamport_t)
            print(f"[+] Cristalizado: {claim.claim_id} -> {current_hash[:8]}")
        except BaseException:
            if db.in_transaction:
                await db.rollback()
            raise
        finally:
            await db.close()

    async def _process_claim(self, claim: ApexClaim) -> None:
        if claim.confidence not in ("C4", "C5"):
            self._claim_status[claim.claim_id] = "FAILED"
            raise ValueError("Unsupported queued confidence; claim was not persisted")

        try:
            await self._insert_claim_db(claim)
            self._claim_status[claim.claim_id] = "COMMITTED"
        except sqlite3.IntegrityError:
            try:
                await self._verify_idempotency_collision(claim)
            except BaseException:
                self._claim_status[claim.claim_id] = "FAILED"
                raise
            self._claim_status[claim.claim_id] = "COMMITTED"
            print(f"[!] Idempotency Lock disparado para {claim.claim_id}. Replay legítimo confirmado.")
        except sqlite3.DatabaseError:
            self._claim_status[claim.claim_id] = "FAILED"
            os.kill(os.getpid(), signal.SIGKILL)
            raise RuntimeError("FAIL-FAST: BFT Ledger corrompido.")
        except asyncio.CancelledError:
            self._claim_status[claim.claim_id] = "UNKNOWN"
            raise
        except Exception:
            self._claim_status[claim.claim_id] = "FAILED"
            raise

    async def bft_state_loop(self) -> None:
        """El bucle acotado de cristalización física (1 solo escritor)."""
        print("[MOSKV-1] KERNEL IGNITION: BFT_STATE_LOOP ACTIVATED.")
        try:
            while not self._stop_event.is_set() or not self._write_queue.empty():
                claim = await self._next_claim()
                if claim is None:
                    continue

                try:
                    await self._process_claim(claim)
                finally:
                    self._write_queue.task_done()
        except asyncio.CancelledError:
            print("[MOSKV-1] KERNEL SHUTDOWN: SIGTERM RECIBIDO.")
            raise
        finally:
            self._stop_event.set()


async def _main() -> None:
    kernel = Moskv1Kernel()
    loop_task = asyncio.create_task(kernel.bft_state_loop())

    # Ingesta sintética de prueba
    await kernel.ingest_entropy(
        {"action": "kernel_bootstrap", "status": "Causal-Determinist", "target": "master_ledger"}
    )

    await asyncio.sleep(0.5)  # Espera termodinámica de cristalización
    loop_task.cancel()


if __name__ == "__main__":
    asyncio.run(_main())
