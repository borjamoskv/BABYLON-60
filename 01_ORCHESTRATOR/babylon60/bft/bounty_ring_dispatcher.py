# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized Bounty Ring Dispatcher
"""bounty_ring_dispatcher.py - Despachador de tramas B60IPC por dominios canónicos.

Consume tramas binarias B60IPC empaquetadas por el BountyFeedTransducer y las
enruta a colas lock-free / asíncronas dedicadas para su análisis especializado
(DeFi_Bytecode_Scraper, webkit-memory-audit, SAGA-1 Sentinel) sin I/O síncrono
en la ruta caliente (INV_C5_SHM).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import logging
import hashlib
from typing import Deque, Dict, List, Optional

from babylon60.bft.exergy_binary_ipc import unpack_agent_message, SharedManifestFFIWriter
from babylon60.transducers.bounty_feed_transducer import BountyAdvisory, BountyDomain

logger = logging.getLogger("babylon60.bft.bounty_dispatcher")


@dataclass
class BountyDispatchTelemetry:
    """Métricas operativas de la ruta de despacho lock-free."""

    total_frames_received: int = 0
    total_dispatched: int = 0
    total_corrupted_dropped: int = 0
    evm_dispatches: int = 0
    native_dispatches: int = 0
    ai_dispatches: int = 0
    general_dispatches: int = 0


class BountyRingDispatcher:
    """Despachador en memoria para eventos B60IPC segregados por vector causal."""

    def __init__(self, queue_capacity: int = 2_048) -> None:
        self._capacity = queue_capacity
        self._telemetry = BountyDispatchTelemetry()

        # Bridge C-FFI para persistencia causal lock-free (64B)
        self._ffi_writer = SharedManifestFFIWriter()

        # Colas en memoria segregadas por dominio canónico
        self._evm_queue: Deque[BountyAdvisory] = deque(maxlen=self._capacity)
        self._native_queue: Deque[BountyAdvisory] = deque(maxlen=self._capacity)
        self._ai_queue: Deque[BountyAdvisory] = deque(maxlen=self._capacity)
        self._general_queue: Deque[BountyAdvisory] = deque(maxlen=self._capacity)

    @property
    def telemetry(self) -> BountyDispatchTelemetry:
        """Retorna el estado de telemetría del despachador."""
        return self._telemetry

    def dispatch_frame(self, raw_frame: bytes) -> Optional[BountyAdvisory]:
        """Desempaqueta una trama B60IPC y la enruta a su atractor causal."""
        self._telemetry.total_frames_received += 1

        try:
            sender, recipient, payload, lamport_t = unpack_agent_message(raw_frame)
        except (ValueError, Exception) as exc:
            self._telemetry.total_corrupted_dropped += 1
            logger.warning("Trama B60IPC corrupta rechazada sin pánico: %s", exc)
            return None

        advisory = BountyAdvisory.from_dict(payload)

        # Anclaje C-FFI Termodinámico (Lock-Free Seqlock)
        payload_hash = hashlib.sha3_256(raw_frame).digest()
        self._ffi_writer.publish(lamport_t, payload_hash)

        self._route_advisory(advisory)
        self._telemetry.total_dispatched += 1
        return advisory

    def _route_advisory(self, advisory: BountyAdvisory) -> None:
        """Enruta la oportunidad a la cola del subsistema correspondiente."""
        if advisory.domain == BountyDomain.DOMAIN_EVM:
            self._evm_queue.append(advisory)
            self._telemetry.evm_dispatches += 1
        elif advisory.domain == BountyDomain.DOMAIN_NATIVE:
            self._native_queue.append(advisory)
            self._telemetry.native_dispatches += 1
        elif advisory.domain == BountyDomain.DOMAIN_AI:
            self._ai_queue.append(advisory)
            self._telemetry.ai_dispatches += 1
        else:
            self._general_queue.append(advisory)
            self._telemetry.general_dispatches += 1

    def drain_domain(self, domain: BountyDomain) -> List[BountyAdvisory]:
        """Extrae de forma exhaustiva todos los advisories pendientes de un dominio."""
        target_queue: Deque[BountyAdvisory]
        if domain == BountyDomain.DOMAIN_EVM:
            target_queue = self._evm_queue
        elif domain == BountyDomain.DOMAIN_NATIVE:
            target_queue = self._native_queue
        elif domain == BountyDomain.DOMAIN_AI:
            target_queue = self._ai_queue
        else:
            target_queue = self._general_queue

        items: List[BountyAdvisory] = list(target_queue)
        target_queue.clear()
        return items

    def get_queue_depths(self) -> Dict[str, int]:
        """Retorna la profundidad instantánea de cada cola."""
        return {
            "evm": len(self._evm_queue),
            "native": len(self._native_queue),
            "ai": len(self._ai_queue),
            "general": len(self._general_queue),
        }
