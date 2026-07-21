"""
CAM 2.0 Abstract Machine Execution Engine.
Manages state tuple: CAM_State = <Hypergraph, Ledger, Queue, Caps, Clock, EffectsLog, ConformanceProfile>
Enforces 5D Epistemic Trust (Truth, Confidence, Authority, Relevance, Freshness),
conflict adjudication, and effect cascade propagation.
"""

from dataclasses import dataclass, field
import hashlib
import time

from cortex.cam.effects import EffectsAlgebra, EffectType
from cortex.cam.hypergraph import CAM2Hypergraph
from cortex.cam.types import EdgeOrder, EdgeType, EpistemicState


@dataclass
class CAMState:
    graph: CAM2Hypergraph = field(default_factory=CAM2Hypergraph)
    ledger: list[dict[str, str]] = field(default_factory=list)
    capabilities: dict[str, set[str]] = field(default_factory=dict)
    conformance_profile: str = "CAM 2.0 Evolutionary"


class CAMAbstractMachine:
    def __init__(self, profile: str = "CAM 2.0 Evolutionary") -> None:
        self.state = CAMState(conformance_profile=profile)
        self.policy_max_trust: float = 0.8  # Policy cap for trust

    def register_agent_capabilities(
        self, agent_id: str, capabilities: set[str]
    ) -> None:
        self.state.capabilities[agent_id] = capabilities

    def evaluate_5d_trust(self, node_id: str, current_time: float | None = None) -> float:
        node = self.state.graph.nodes.get(node_id)
        if not node:
            raise KeyError(f"Node '{node_id}' not found in Hypergraph")
        return node.epistemic_5d.composite_trust(current_time)

    def execute_verify_transition(
        self,
        agent_id: str,
        claim_id: str,
        evidence_id: str,
        declared_effects: EffectsAlgebra,
        current_time: float | None = None,
    ) -> bool:
        if agent_id not in self.state.capabilities:
            raise RuntimeError(
                f"Undefined Behaviour Error: Agent {agent_id} unregistered"
            )

        claim_node = self.state.graph.nodes.get(claim_id)
        evidence_node = self.state.graph.nodes.get(evidence_id)

        if not claim_node or not evidence_node:
            raise KeyError("Claim or Evidence node missing in Hypergraph")

        target_trust = claim_node.epistemic_5d.composite_trust(current_time)
        allowed_trust = min(
            self.policy_max_trust, evidence_node.epistemic_5d.composite_trust(current_time)
        )
        if target_trust > allowed_trust:
            raise RuntimeError(
                f"Undefined Behaviour Error: Trust ({target_trust:.3f}) > Policy Allowed ({allowed_trust:.3f})"
            )

        # 2. Effect Cascade Verification
        actual_effects = {
            EffectType.KNOWLEDGE_WRITE,
            EffectType.LEDGER_APPEND,
        }
        declared_effects.verify_actual_effects(actual_effects)

        # 3. Atomic State Transition
        self.state.graph.add_edge(
            EdgeType.SUPPORTS, evidence_id, claim_id, EdgeOrder.FIRST_ORDER_CAUSAL
        )
        self.state.graph.nodes[claim_id].state = EpistemicState.VERIFIED

        # 4. Hash-Chained Ledger Append
        prev_hash = (
            self.state.ledger[-1]["entry_hash"]
            if self.state.ledger
            else "00000000000000000000000000000000"
        )
        now_ts = current_time if current_time is not None else time.time()
        entry_payload = f"{claim_id}:{evidence_id}:{prev_hash}:{now_ts}"
        entry_hash = hashlib.sha3_256(entry_payload.encode("utf-8")).hexdigest()

        self.state.ledger.append(
            {
                "claim_id": claim_id,
                "evidence_id": evidence_id,
                "prev_hash": prev_hash,
                "entry_hash": entry_hash,
            }
        )
        return True
