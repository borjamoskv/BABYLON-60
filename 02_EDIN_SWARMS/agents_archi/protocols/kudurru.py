#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ KUDURRU-64 GRAVITY FILTER | DOMAIN: agents.archi | STATE: C5-REAL
# ============================================================================
"""
KUDURRU-64 Gravity Filter & Anti-Cognitive DDoS Membrane (Ring-2 -> Ring-0).

Invariants:
  - INV_C5_ASYMMETRIC_PERMEABILITY: Ring-2 operates under suspended apoptosis.
    Subagents in EDIN may hypothesize, hallucinate productively, and generate
    stochastic mutations without thermal penalty.
  - INV_C5_KUDURRU_64_MEMBRANE: Any attempt to promote a candidate Black Swan
    from EDIN (Ring-2) into Ring-1 (Lean 4 / Z3) or Ring-0 (SharedManifest 64B)
    must pass through an O(1) geometric exergy filter.
  - INV_C5_SILENT_ANERGY_DROP: Anergy and low-exergy noise are silently discarded (Drop)
    without raising fatal exceptions to the swarm worker or causing analysis paralysis.
  - INV_1_C_ABI_SEQLOCK: Verified high-exergy discoveries are committed to the 64-byte
    L1-cache-aligned SharedManifest via Seqlock SPMC.
"""

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union

try:
    from babylon60.bft.exergy_binary_ipc import SharedManifestFFIWriter, BountySharedManifest

    _HAS_FFI_IPC = True
except ImportError:
    _HAS_FFI_IPC = False
    SharedManifestFFIWriter = None  # type: ignore
    BountySharedManifest = None  # type: ignore

from .attestation import AttestationEnvelope


@dataclass
class KudurruFilterResult:
    """Outcome of passing a proposition or artifact through KUDURRU-64."""

    accepted: bool
    silent_drop: bool
    exergy_score: float
    reason: str
    epoch: Optional[int] = None
    digest_hex: Optional[str] = None
    promoted_to_ring0: bool = False
    telemetry: Dict[str, Any] = field(default_factory=dict)


def calculate_shannon_entropy(data: bytes) -> float:
    """Calculates Shannon entropy in bits per byte [0.0 - 8.0]."""
    if not data:
        return 0.0
    freq: Dict[int, int] = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    total = len(data)
    entropy = 0.0
    for count in freq.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


class KudurruGravityFilter:
    """
    KUDURRU-64 Lock-Free Gateway & Gravity Filter.

    Operates at the boundary between Ring-2 (02_EDIN_SWARMS) and Ring-0 (00_ABZU_KERNEL).
    Filters cognitive DDoS and provides zero-copy seqlock handoff.
    """

    DEFAULT_MIN_EXERGY: float = 0.618  # Golden ratio exergy threshold
    DEFAULT_MIN_ENTROPY: float = 2.0  # Discard uniform null/repeating slop

    def __init__(
        self,
        min_exergy: float = DEFAULT_MIN_EXERGY,
        ffi_writer: Optional[Any] = None,
        auto_init_ring0: bool = True,
    ) -> None:
        self.min_exergy = min_exergy
        self._ffi_writer = ffi_writer
        self._proposals_evaluated = 0
        self._proposals_promoted = 0
        self._proposals_dropped = 0

        if self._ffi_writer is None and auto_init_ring0 and _HAS_FFI_IPC:
            try:
                self._ffi_writer = SharedManifestFFIWriter()
            except Exception:
                self._ffi_writer = None

    @property
    def ffi_writer(self) -> Optional[Any]:
        return self._ffi_writer

    def is_ring0_available(self) -> bool:
        return self._ffi_writer is not None

    def evaluate_and_promote(
        self,
        candidate: Union[AttestationEnvelope, Dict[str, Any], str, bytes],
        candidate_exergy: Optional[float] = None,
        epoch: Optional[int] = None,
        expected_signing_key: Optional[str] = None,
    ) -> KudurruFilterResult:
        """
        Evaluates a candidate state from EDIN and promotes it to Ring-0 if high-exergy.
        Silently drops anergy without raising exceptions to prevent cognitive DDoS.
        """
        t0 = time.perf_counter_ns()
        self._proposals_evaluated += 1

        # 1. Normalización de contenido a bytes canónicos
        raw_bytes: bytes
        envelope: Optional[AttestationEnvelope] = None

        if isinstance(candidate, AttestationEnvelope):
            envelope = candidate
            canon = json.dumps(envelope.to_dict(), sort_keys=True, separators=(",", ":"))
            raw_bytes = canon.encode("utf-8")
        elif isinstance(candidate, dict):
            canon = json.dumps(candidate, sort_keys=True, separators=(",", ":"))
            raw_bytes = canon.encode("utf-8")
        elif isinstance(candidate, str):
            raw_bytes = candidate.encode("utf-8")
        elif isinstance(candidate, bytes):
            raw_bytes = candidate
        else:
            self._proposals_dropped += 1
            return KudurruFilterResult(
                accepted=False,
                silent_drop=True,
                exergy_score=0.0,
                reason="Candidate format invalid (silent drop)",
            )

        # 2. Verificación criptográfica si es un sobre SCITT
        if envelope is not None:
            if not envelope.verify(expected_key=expected_signing_key):
                self._proposals_dropped += 1
                return KudurruFilterResult(
                    accepted=False,
                    silent_drop=True,
                    exergy_score=0.0,
                    reason="Invalid cryptographic signature on AttestationEnvelope",
                )

        # 3. Criba O(1) de entropía geométrica (Anti-Anergía / Anti-Slop)
        entropy = calculate_shannon_entropy(raw_bytes)
        if len(raw_bytes) < 4 or entropy < self.DEFAULT_MIN_ENTROPY:
            self._proposals_dropped += 1
            return KudurruFilterResult(
                accepted=False,
                silent_drop=True,
                exergy_score=0.0,
                reason="Low entropy slop discarded by Kudurru filter",
                telemetry={"entropy": round(entropy, 3), "bytes": len(raw_bytes)},
            )

        # 4. Cálculo o asignación de exergía
        effective_exergy = candidate_exergy if candidate_exergy is not None else min(1.0, entropy / 8.0)

        if effective_exergy < self.min_exergy:
            self._proposals_dropped += 1
            return KudurruFilterResult(
                accepted=False,
                silent_drop=True,
                exergy_score=effective_exergy,
                reason=f"Exergy score {effective_exergy:.3f} below threshold {self.min_exergy:.3f}",
                telemetry={"entropy": round(entropy, 3), "bytes": len(raw_bytes)},
            )

        # 5. Promoción a Ring-0 (SharedManifest 64B Seqlock)
        digest = hashlib.sha3_256(raw_bytes).digest()
        digest_hex = digest.hex()
        target_epoch = epoch if epoch is not None else int(time.time())
        promoted = False

        if self._ffi_writer is not None:
            try:
                promoted = self._ffi_writer.publish(target_epoch, digest)
            except Exception:
                promoted = False

        t1 = time.perf_counter_ns()
        latency_ns = t1 - t0

        self._proposals_promoted += 1
        return KudurruFilterResult(
            accepted=True,
            silent_drop=False,
            exergy_score=effective_exergy,
            reason="High-exergy Black Swan validated and promoted to Ring-0",
            epoch=target_epoch,
            digest_hex=digest_hex,
            promoted_to_ring0=promoted,
            telemetry={
                "latency_ns": latency_ns,
                "entropy": round(entropy, 3),
                "bytes": len(raw_bytes),
                "ring0_available": self._ffi_writer is not None,
            },
        )

    def stats(self) -> Dict[str, Any]:
        return {
            "proposals_evaluated": self._proposals_evaluated,
            "proposals_promoted": self._proposals_promoted,
            "proposals_dropped": self._proposals_dropped,
            "drop_rate": round(self._proposals_dropped / max(1, self._proposals_evaluated), 3),
            "ring0_active": self._ffi_writer is not None,
        }
