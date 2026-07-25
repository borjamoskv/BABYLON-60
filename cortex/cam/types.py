# C5-REAL EXERGY CERTIFIED
"""
CAM 2.0 Epistemic States, 5D Vector Types, Hypergraph Edges, and Non-Commutative Capabilities.
"""

from dataclasses import dataclass, field
import enum
import math
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

class EdgeOrder(enum.Enum):
    FIRST_ORDER_CAUSAL = "1ST_ORDER_CAUSAL"
    SECOND_ORDER_FEEDBACK = "2ND_ORDER_FEEDBACK"

class EdgeType(enum.Enum):
    SUPPORTS = "supports"
    REFUTES = "refutes"
    DERIVES_FROM = "derives_from"
    SUPERSEDES = "supersedes"
    DEPENDS_ON = "depends_on"
    INVALIDATES = "invalidates"
    IMPLEMENTS = "implements"

@dataclass
class Epistemic5D:
    truth: float = 1.0  # Ground truth factor [0, 1]
    confidence: float = 1.0  # Reasoning confidence [0, 1]
    authority: float = 1.0  # Source authority weight [0, 1]
    relevance: float = 1.0  # Context alignment [0, 1]
    decay_lambda: float = 0.01  # Half-life decay constant
    timestamp: float = field(default_factory=time.time)

    def current_freshness(self, current_time: float | None = None) -> float:
        now = current_time if current_time is not None else time.time()
        elapsed = max(0.0, now - self.timestamp)
        return math.exp(-self.decay_lambda * elapsed)

    def composite_trust(self, current_time: float | None = None) -> float:
        freshness = self.current_freshness(current_time)
        return self.truth * self.confidence * self.authority * self.relevance * freshness

@dataclass
class KGNode:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_type: NodeType = NodeType.OBSERVATION
    state: EpistemicState = EpistemicState.MEASURED
    epistemic_5d: Epistemic5D = field(default_factory=Epistemic5D)
    lamport_t: int = 0
    content: str = ""
    created_at: float = field(default_factory=time.time)

@dataclass
class KGEdge:
    edge_type: EdgeType
    source_id: str
    target_id: str
    order: EdgeOrder = EdgeOrder.FIRST_ORDER_CAUSAL
    created_at: float = field(default_factory=time.time)

@dataclass
class AdjudicationRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    claim_a_id: str = ""
    claim_b_id: str = ""
    winning_claim_id: str = ""
    dissenting_branch_id: str = ""
    rationale: str = ""
    timestamp: float = field(default_factory=time.time)
