# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""bounty_cold_ledger.py - Sumidero de persistencia asíncrona para atestaciones L5.

Implementa un 'Cold Ledger Sink' fuera de la ruta caliente (INV_C5_SHM).
Consume instancias BountyClaimReceipt desde una cola thread-safe y las persiste
usando BFTSQLite con modo WAL.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Any, List, Optional

from babylon60.bft.bounty_claim_attester import BountyClaimReceipt
from babylon60.kernel.bft_sqlite import BFTSQLite, BFTDatabaseError

logger = logging.getLogger("babylon60.bft.bounty_cold_ledger")


class BountyColdLedger:
    """Sumidero de persistencia asíncrona (Cold Ledger) para recibos SCITT."""

    def __init__(self, db_path: str = "bounty_ledger.db", max_queue_size: int = 50_000) -> None:
        self._db_path = db_path
        self._sqlite = BFTSQLite(db_path=self._db_path)
        self._queue: queue.Queue[Optional[BountyClaimReceipt]] = queue.Queue(maxsize=max_queue_size)
        self._worker_thread: Optional[threading.Thread] = None
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """Inicializa la tabla de recibos criptográficos en el Cold Ledger."""
        schema = """
        CREATE TABLE IF NOT EXISTS bounty_claims (
            claim_id TEXT PRIMARY KEY,
            advisory_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            finding_summary TEXT NOT NULL,
            risk_score REAL NOT NULL,
            payload_hash TEXT NOT NULL,
            timestamp_utc TEXT NOT NULL,
            hardware_anchor TEXT NOT NULL,
            attestation_merkle_root TEXT NOT NULL
        );
        """
        self._sqlite.execute_with_backoff(schema)

    def start(self) -> None:
        """Enciende el daemon de drenaje termodinámico."""
        if self._worker_thread is not None and self._worker_thread.is_alive():
            return

        self._worker_thread = threading.Thread(target=self._drain_loop, daemon=True, name="ColdLedgerSink")
        self._worker_thread.start()
        logger.info(f"[ColdLedger] Sink asíncrono iniciado hacia {self._db_path}")

    def stop(self, timeout: float = 30.0) -> None:
        """Detiene el daemon de drenaje de forma ordenada (Apoptosis de I/O)."""
        self._queue.put(None)  # Sentinel para detener el thread
        if self._worker_thread is not None:
            self._worker_thread.join(timeout=timeout)

    def enqueue_receipt(self, receipt: BountyClaimReceipt) -> bool:
        """
        Encola un recibo para persistencia. No bloquea la ruta caliente.
        Retorna False si la cola está saturada (presión posterior termodinámica).
        """
        try:
            self._queue.put_nowait(receipt)
            return True
        except queue.Full:
            logger.error(f"[ColdLedger] COLA SATURADA. Descartando persistencia de {receipt.claim_id}.")
            return False

    def _drain_loop(self) -> None:
        """Bucle de consumo asíncrono. Mueve datos de RAM (cola) a SQLite WAL en lotes atómicos."""
        insert_query = """
        INSERT OR IGNORE INTO bounty_claims (
            claim_id, advisory_id, domain, finding_summary, risk_score,
            payload_hash, timestamp_utc, hardware_anchor, attestation_merkle_root
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        batch: List[tuple[Any, ...]] = []
        batch_receipts: List[BountyClaimReceipt] = []

        def _flush() -> None:
            if not batch:
                return
            try:
                self._sqlite.executemany_with_backoff(insert_query, batch)
                logger.debug(f"[ColdLedger] Lote de {len(batch)} recibos consolidado.")
            except BFTDatabaseError as e:
                logger.error(f"[ColdLedger] Fallo catastrófico persistiendo lote: {e}")
            finally:
                for _ in batch_receipts:
                    self._queue.task_done()
                batch.clear()
                batch_receipts.clear()

        running = True
        while running:
            receipt = self._queue.get()
            if receipt is None:
                _flush()
                self._queue.task_done()
                break

            params = (
                receipt.claim_id,
                receipt.advisory_id,
                receipt.domain,
                receipt.finding_summary,
                receipt.risk_score,
                receipt.payload_hash,
                receipt.timestamp_utc,
                receipt.hardware_anchor,
                receipt.attestation_merkle_root,
            )
            batch.append(params)
            batch_receipts.append(receipt)

            if len(batch) >= 500 or self._queue.empty():
                _flush()
