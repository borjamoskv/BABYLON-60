# ============================================================================
# BABYLON-60 Saga Contract Guard
# █ SAGA_CONTRACT | Distributed Transaction Isolation & Proposal Guards
# ============================================================================
# STATE: C5-REAL (Zero-Anergy, Immutable State Machine, Cryptographic Hash)
# ============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
import hashlib
import json
from typing import Any, Mapping

__all__ = ["SagaStatus", "SagaWriteProposal"]


class SagaStatus(Enum):
    PENDING = auto()
    COMMITTED = auto()
    REVERTED = auto()
    HALTED = auto()


@dataclass(frozen=True)
class SagaWriteProposal:
    proposal_id: str
    target: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    status: SagaStatus = SagaStatus.PENDING

    def get_payload_hash(self) -> str:
        """P1: Delta de Evidencia (Hash Criptográfico SHA-256)"""
        # Se requiere que el payload sea serializable a JSON de forma determinista
        serialized = json.dumps(dict(self.payload), sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def is_valid(self) -> bool:
        """P3: Invariante Contractual - Prevención de campos corruptos"""
        if not self.proposal_id or not self.target:
            return False
        if not isinstance(self.status, SagaStatus):
            return False
        return True
    
    def transition_to(self, new_status: SagaStatus) -> SagaWriteProposal:
        """
        P3: Control rígido de transiciones (Máquina de Estados Inmutable).
        Previene mutaciones arbitrarias en memoria.
        """
        # Solo se permite transicionar desde PENDING
        if self.status != SagaStatus.PENDING:
            raise ValueError(f"[FATAL] Illegal state transition from {self.status.name} to {new_status.name}")
        
        # Enforce inmutabilidad creando una nueva instancia determinista
        return SagaWriteProposal(
            proposal_id=self.proposal_id,
            target=self.target,
            payload=self.payload,
            status=new_status
        )
