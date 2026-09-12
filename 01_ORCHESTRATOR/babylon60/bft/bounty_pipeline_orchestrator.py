# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized Bounty Pipeline Orchestrator (Ω-Bounty-Ingest)
"""bounty_pipeline_orchestrator.py - Orquestador unificado del pipeline Ω-Bounty-Ingest.

Coordina de forma soberana y en un solo ciclo funtorial:
1. Ingestión asíncrona de feeds (GitHub Security Advisories, Code4rena).
2. Empaquetado binario B60IPC y filtrado O(1) de duplicados.
3. Despacho a colas de memoria lock-free (INV_C5_SHM).
4. Ejecución de los 3 especialistas de dominio (DeFi, WebKit, SAGA-1).
5. Emisión de recibos inmutables de atestación (Proof of Claim) con anclaje hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import time
from typing import TYPE_CHECKING, Dict, List, Mapping, Optional, Sequence

from babylon60.bft.bounty_claim_attester import BountyClaimAttester, BountyClaimReceipt
from babylon60.bft.bounty_ring_dispatcher import BountyRingDispatcher
from babylon60.bft.defi_bytecode_scraper import BytecodeAnalysisResult, DeFiBytecodeScraper
from babylon60.bft.saga1_ml_sentinel import Saga1MlSentinel, Saga1SentinelResult
from babylon60.bft.webkit_memory_connector import WebKitMemoryConnector, WebKitTriageResult
from babylon60.bft.bounty_cold_ledger import BountyColdLedger
from babylon60.transducers.bounty_feed_transducer import (
    BountyDomain,
    BountyFeedTransducer,
)

if TYPE_CHECKING:
    import httpx

logger = logging.getLogger("babylon60.bft.pipeline_orchestrator")

# Cota física de Landauer a temperatura ambiente (300 K): E = k_B * T * ln(2)
LANDAUER_BOUND_300K = 2.8705e-21  # Joules por bit disipado


@dataclass
class BountyCycleReport:
    """Reporte determinista y canónico del ciclo de ingestión y auditoría."""

    timestamp_utc: str
    frames_ingested: int
    queue_depths_pre_drain: Dict[str, int]
    evm_analyses: List[BytecodeAnalysisResult] = field(default_factory=list)
    native_triages: List[WebKitTriageResult] = field(default_factory=list)
    ai_sentinel_dicta: List[Saga1SentinelResult] = field(default_factory=list)
    claim_receipts: List[BountyClaimReceipt] = field(default_factory=list)
    total_elapsed_ms: float = 0.0
    landauer_dissipated_joules: float = 0.0
    manifest_telemetry: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        """Serializa el reporte a formato de diccionario estructurado."""
        return {
            "timestamp_utc": self.timestamp_utc,
            "frames_ingested": self.frames_ingested,
            "queue_depths_pre_drain": self.queue_depths_pre_drain,
            "evm_analyses": [r.to_dict() for r in self.evm_analyses],
            "native_triages": [r.to_dict() for r in self.native_triages],
            "ai_sentinel_dicta": [r.to_dict() for r in self.ai_sentinel_dicta],
            "claim_receipts": [r.to_dict() for r in self.claim_receipts],
            "total_elapsed_ms": self.total_elapsed_ms,
            "landauer_dissipated_joules": self.landauer_dissipated_joules,
            "manifest_telemetry": self.manifest_telemetry,
        }


class BountyPipelineOrchestrator:
    """Orquestador maestro de la cadena funtorial Ω-Bounty-Ingest."""

    def __init__(self, filter_capacity: int = 10_000, queue_capacity: int = 2_048) -> None:
        self.transducer = BountyFeedTransducer(filter_capacity=filter_capacity)
        self.dispatcher = BountyRingDispatcher(queue_capacity=queue_capacity)
        self.defi_scraper = DeFiBytecodeScraper()
        self.webkit_connector = WebKitMemoryConnector()
        self.ai_sentinel = Saga1MlSentinel()

        # Generador de Recibos y Sumidero de Persistencia (Cold Ledger)
        self.attester = BountyClaimAttester()
        self.cold_ledger = BountyColdLedger()
        self.cold_ledger.start()

    async def execute_cycle(
        self,
        client: Optional[httpx.AsyncClient] = None,
        per_page: int = 10,
        synthetic_items: Optional[Sequence[Mapping[str, object]]] = None,
        auto_attest_high_risk: bool = True,
        risk_threshold: float = 0.6,
    ) -> BountyCycleReport:
        """Ejecuta un ciclo completo de ingestión, triaje por dominios y atestación."""
        t0 = time.perf_counter()
        timestamp = datetime.now(timezone.utc).isoformat()

        # 1. Fase de Ingestión
        frames: List[bytes] = []
        if synthetic_items:
            frames = self.transducer.ingest_raw_advisories(synthetic_items)
        elif client:
            frames = await self.transducer.poll_live_network(client, per_page=per_page)

        # 2. Fase de Despacho en memoria lock-free
        for f in frames:
            self.dispatcher.dispatch_frame(f)

        pre_drain_depths = self.dispatcher.get_queue_depths()

        # 3. Fase de Drenaje y Especialistas de Dominio
        evm_batch = self.dispatcher.drain_domain(BountyDomain.DOMAIN_EVM)
        evm_results = self.defi_scraper.process_advisories(evm_batch) if evm_batch else []

        native_batch = self.dispatcher.drain_domain(BountyDomain.DOMAIN_NATIVE)
        native_results = self.webkit_connector.process_advisories(native_batch) if native_batch else []

        ai_batch = self.dispatcher.drain_domain(BountyDomain.DOMAIN_AI)
        ai_results = self.ai_sentinel.process_advisories(ai_batch) if ai_batch else []

        # 4. Fase de Atestación Criptográfica (Proof of Claim)
        receipts: List[BountyClaimReceipt] = []
        if auto_attest_high_risk:
            # Atestar hallazgos EVM
            for res in evm_results:
                if res.risk_score >= risk_threshold:
                    target_id = res.contract_address or "UNKNOWN-EVM-TARGET"
                    receipt = self.attester.generate_receipt(
                        advisory_id=target_id,
                        domain=BountyDomain.DOMAIN_EVM.value,
                        finding_summary="; ".join(res.findings),
                        risk_score=res.risk_score,
                        raw_payload=res.to_dict(),
                    )
                    receipts.append(receipt)
                    self.cold_ledger.enqueue_receipt(receipt)

            # Atestar hallazgos WebKit
            for res_nat in native_results:
                if res_nat.risk_score >= risk_threshold:
                    receipt = self.attester.generate_receipt(
                        advisory_id=res_nat.advisory_id,
                        domain=BountyDomain.DOMAIN_NATIVE.value,
                        finding_summary=f"{res_nat.vulnerability_class} en {res_nat.affected_subsystems}",
                        risk_score=res_nat.risk_score,
                        raw_payload=res_nat.to_dict(),
                    )
                    receipts.append(receipt)
                    self.cold_ledger.enqueue_receipt(receipt)

            # Atestar hallazgos AI
            for res_ai in ai_results:
                if res_ai.risk_score >= risk_threshold:
                    receipt = self.attester.generate_receipt(
                        advisory_id=res_ai.advisory_id,
                        domain=BountyDomain.DOMAIN_AI.value,
                        finding_summary=f"{res_ai.vulnerability_class.value} [{res_ai.taint_level}]",
                        risk_score=res_ai.risk_score,
                        raw_payload=res_ai.to_dict(),
                    )
                    receipts.append(receipt)
                    self.cold_ledger.enqueue_receipt(receipt)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        total_bits = sum(len(f) for f in frames) * 8
        landauer_joules = total_bits * LANDAUER_BOUND_300K

        # Telemetría de Anclaje C-ABI 64B (INV_C5_SHM)
        ffi = self.dispatcher.ffi_writer
        read_val = ffi.read()
        manifest_telemetry: Dict[str, object] = {
            "is_native": ffi.is_native,
            "status": "POISONED" if ffi.is_halted() else "RUNNING",
            "epoch_id": ffi.manifest.epoch_id,
            "seq": ffi.manifest.seq,
            "is_consistent": (ffi.manifest.seq % 2 == 0),
            "last_payload_hash": read_val[1].hex() if read_val else "",
        }

        return BountyCycleReport(
            timestamp_utc=timestamp,
            frames_ingested=len(frames),
            queue_depths_pre_drain=pre_drain_depths,
            evm_analyses=evm_results,
            native_triages=native_results,
            ai_sentinel_dicta=ai_results,
            claim_receipts=receipts,
            total_elapsed_ms=elapsed_ms,
            landauer_dissipated_joules=landauer_joules,
            manifest_telemetry=manifest_telemetry,
        )
