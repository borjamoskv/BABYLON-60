# [C5-REAL] Exergy-Maximized

"""CORTEX Hypervisor - BeliefObject Contract (RFC-BABYLON60-NATIVE-AI v0.1).

Immutable cognitive units for the Belief Layer. The BeliefObject is the
unifying atom between the quad-model Cognitive Handoff.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

__all__ = [
    "BeliefConfidence",
    "BeliefObject",
    "BeliefStatus",
    "BeliefVerdict",
    "ProvenanceEnvelope",
    "BeliefRelations",
    "VerdictAction",
]




class BeliefConfidence(str, Enum):
    """Epistemic confidence level - maps to CORTEX C1→C5 scale."""

    C1_HYPOTHESIS = "C1"
    C2_TENTATIVE = "C2"
    C3_PROBABLE = "C3"
    C4_CONFIRMED = "C4"
    C5_AXIOMATIC = "C5"


class BeliefStatus(str, Enum):
    """Lifecycle state of a belief in the cognitive layer."""

    ACTIVE = "active"
    QUARANTINED = "quarantined"
    DEPRECATED = "deprecated"
    CONTESTED = "contested"
    SUBSUMED = "subsumed"
    DISCARDED = "discarded"
    ORPHANED = "orphaned"


class VerdictAction(str, Enum):
    """Actions the CognitiveHandoff can take on a belief."""

    ACCEPT = "accept"
    QUARANTINE = "quarantine"
    REVISE = "revise"
    SKIP = "skip"
    ESCALATE = "escalate"




def _now_iso() -> str:
    """Current UTC time as ISO 8601 string."""
    return datetime.fromtimestamp(time.time(), tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class ProvenanceEnvelope:
    """Provenance Envelope matching RFC-BABYLON60-NATIVE-AI."""

    source_hash: str = ""
    source_type: str = "agent"  # 'agent' | 'tool' | 'human'
    tenant_id: str = "default"
    signer_id: str = "system"
    signature: str = ""
    cortex_taint: str = "taint:system:0000:none:000"
    created_at: str = field(default_factory=_now_iso)
    was_generated_by: str = ""




@dataclass(frozen=True)
class BeliefRelations:
    """ATMS graph relations."""

    entails: tuple[str, ...] = ()
    discards: tuple[str, ...] = ()




def _uuid7() -> str:
    """Generate a UUID v7 (time-sortable) as string."""
    ts = datetime.fromtimestamp(time.time(), tz=timezone.utc).strftime("%Y%m%d%H%M%S")
    uid = uuid.uuid4().hex
    return f"{ts}-{uid[:16]}"


@dataclass(frozen=True)
class BeliefObject:
    """Immutable cognitive unit - the atom of the Belief Layer (RFC Compliant)."""

    proposition: str
    """The belief statement in natural language."""

    project: str
    """Project namespace this belief belongs to."""

    tenant_id: str = "default"
    """Multi-tenant isolation key."""

    belief_id: str = field(default_factory=_uuid7)
    """Time-sortable unique identifier."""

    semantic_embedding: tuple[float, ...] = ()
    """L2 vector projection."""

    state: BeliefStatus = BeliefStatus.ACTIVE
    """Lifecycle state in the cognitive layer."""

    confidence_score: float = 0.5
    """P(H|E) scalar value."""

    variance: float = 0.0
    """Ignorance quantification."""

    decay_rate: float = 0.05
    """Logarithmic epistemic fading."""

    provenance: ProvenanceEnvelope = field(default_factory=ProvenanceEnvelope)
    """Provenance context."""

    relations: BeliefRelations = field(default_factory=BeliefRelations)
    """ATMS relations."""

    created_at: str = field(default_factory=_now_iso)
    """When this belief was first created."""

    revised_at: str | None = None
    """When this belief was last revised. None if never revised."""

    revision_count: int = 0
    """Number of times this belief has been revised."""

    arbitrated_by: str | None = None
    """Model identifier that last judged this belief (e.g., 'opus', 'deep_think')."""

    @property
    def id(self) -> str:
        return self.belief_id

    @property
    def content(self) -> str:
        return self.proposition

    @property
    def status(self) -> BeliefStatus:
        return self.state

    def is_axiomatic(self) -> bool:
        return self.confidence_score >= 0.95

    def is_quarantined(self) -> bool:
        return self.state == BeliefStatus.QUARANTINED

    def to_dict(self) -> dict:
        """Serialize to dict for SQLite/JSON storage."""
        return {
            "belief_id": self.belief_id,
            "proposition": self.proposition,
            "semantic_embedding": list(self.semantic_embedding),
            "state": self.state.value,
            "confidence_score": self.confidence_score,
            "variance": self.variance,
            "decay_rate": self.decay_rate,
            "provenance": {
                "source_hash": self.provenance.source_hash,
                "source_type": self.provenance.source_type,
                "tenant_id": self.provenance.tenant_id,
                "signer_id": self.provenance.signer_id,
                "signature": self.provenance.signature,
                "cortex_taint": self.provenance.cortex_taint,
                "created_at": self.provenance.created_at,
                "was_generated_by": self.provenance.was_generated_by,
            },
            "relations": {
                "entails": list(self.relations.entails),
                "discards": list(self.relations.discards),
            },
            "created_at": self.created_at,
            "revised_at": self.revised_at,
            "revision_count": self.revision_count,
            "arbitrated_by": self.arbitrated_by,
            "project": self.project,
            "tenant_id": self.tenant_id,
            "id": self.belief_id,
            "content": self.proposition,
            "status": self.state.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> BeliefObject:
        """Deserialize from dict (SQLite/JSON)."""
        prov_data = data.get("provenance", {})
        if isinstance(prov_data, list):
            prov_data = {}

        prov = ProvenanceEnvelope(
            source_hash=prov_data.get("source_hash", ""),
            source_type=prov_data.get("source_type", "agent"),
            tenant_id=prov_data.get("tenant_id", "default"),
            signer_id=prov_data.get("signer_id", "system"),
            signature=prov_data.get("signature", ""),
            cortex_taint=prov_data.get("cortex_taint", "taint:system:0000:none:000"),
            created_at=prov_data.get("created_at", _now_iso()),
            was_generated_by=prov_data.get("was_generated_by", ""),
        )

        rel_data = data.get("relations", {})
        rels = BeliefRelations(
            entails=tuple(rel_data.get("entails", data.get("supported_by", []))),
            discards=tuple(rel_data.get("discards", data.get("contradicts", []))),
        )

        return cls(
            belief_id=data.get("belief_id", data.get("id", _uuid7())),
            proposition=data.get("proposition", data.get("content", "")),
            semantic_embedding=tuple(data.get("semantic_embedding", [])),
            state=BeliefStatus(str(data.get("state", data.get("status", "active")))),
            confidence_score=float(data.get("confidence_score", 0.5)),
            variance=float(data.get("variance", 0.0)),
            decay_rate=float(data.get("decay_rate", 0.05)),
            provenance=prov,
            relations=rels,
            created_at=data.get("created_at", _now_iso()),
            revised_at=data.get("revised_at"),
            revision_count=data.get("revision_count", 0),
            arbitrated_by=data.get("arbitrated_by"),
            project=data.get("project", "default"),
            tenant_id=data.get("tenant_id", "default"),
        )




@dataclass(frozen=True)
class BeliefVerdict:
    """Result of the CognitiveHandoff processing a belief."""

    action: VerdictAction
    model: str = "unknown"
    contradictions: tuple[str, ...] = ()
    revised_belief: BeliefObject | None = None
    cost_tokens: int = 0
    reason: str = ""
