# ============================================================================
# BABYLON-60 Saga Contract Guard
# █ SAGA_CONTRACT | Distributed Transaction Isolation & Proposal Guards
# ============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

__all__ = ["SagaWriteProposal"]


@dataclass
class SagaWriteProposal:
    proposal_id: str
    target: str
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "PENDING"

    def is_valid(self) -> bool:
        return bool(self.proposal_id and self.target)
