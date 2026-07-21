"""
CAM 1.0 Epistemic States, Node Types, and Edge Types.
"""

from dataclasses import dataclass, field
import enum
import time
import uuid


class EpistemicState(enum.Enum):
    UNDEFINED = "Undefined"
    UNKNOWN = "Unknown"
    KNOWN_UNKNOWN = "KnownUnknown"
    MEASURED = "Measured"
    ESTIMATED = "Estimated"
    VERIFIED = "Verified"
    REFUTED = "Refuted"
    SUPERSEDED = "Superseded"
    IMPL_DEFINED = "ImplDefined"
    IMPOSSIBLE = "Impossible"


class NodeType(enum.Enum):
    OBSERVATION = "Observation"
    EVIDENCE = "Evidence"
    CLAIM = "Claim"
    INFERENCE = "Inference"
    DECISION = "Decision"
    ARTIFACT = "Artifact"
    INCIDENT = "Incident"
    POLICY = "Policy"


class EdgeType(enum.Enum):
    SUPPORTS = "supports"
    REFUTES = "refutes"
    DERIVES_FROM = "derives_from"
    SUPERSEDES = "supersedes"
    DEPENDS_ON = "depends_on"
    INVALIDATES = "invalidates"
    IMPLEMENTS = "implements"


@dataclass
class KGNode:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_type: NodeType = NodeType.OBSERVATION
    state: EpistemicState = EpistemicState.MEASURED
    confidence: float = 1.0
    lamport_t: int = 0
    content: str = ""
    created_at: float = field(default_factory=time.time)


@dataclass
class KGEdge:
    edge_type: EdgeType
    source_id: str
    target_id: str
    created_at: float = field(default_factory=time.time)
