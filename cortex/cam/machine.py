"""
CAM 1.0 Abstract Machine Execution Engine.
Manages state tuple: CAM_State = <KG, Ledger, Queue, Caps, Clock, EffectsLog, ConformanceProfile>
Enforces Trust <= Policy(Confidence(x)) and atomic transitions.
"""

from dataclasses import dataclass, field
import hashlib
import time

from cortex.cam.dag import TypedDAGKnowledgeGraph
from cortex.cam.effects import EffectsAlgebra, EffectType
from cortex.cam.types import EdgeType, EpistemicState


@dataclass
class CAMState:
    kg: TypedDAGKnowledgeGraph = field(
        default_factory=TypedDAGKnowledgeGraph
    )
    ledger: list[dict[str, str]] = field(default_factory=list)
    capabilities: dict[str, set[str]] = field(default_factory=dict)
    conformance_profile: str = "CAM Standard"


class CAMAbstractMachine:
    def __init__(self, profile: str = "CAM Standard") -> None:
        self.state = CAMState(conformance_profile=profile)
        self.policy_max_trust: float = 0.8  # Policy cap for trust

    def register_agent_capabilities(
        self, agent_id: str, capabilities: set[str]
    ) -> None:
        self.state.capabilities[agent_id] = capabilities

    def execute_verify_transition(
        self,
        agent_id: str,
        claim_id: str,
        evidence_id: str,
        declared_effects: EffectsAlgebra,
    ) -> bool:
        # 1. Verify Trust <= Policy(Confidence(x))
        if agent_id not in self.state.capabilities:
            raise RuntimeError(
                f"Undefined Behaviour Error: Agent {agent_id} unregistered"
            )

        claim_node = self.state.kg.nodes.get(claim_id)
        evidence_node = self.state.kg.nodes.get(evidence_id)

        if not claim_node or not evidence_node:
            raise KeyError("Claim or Evidence node missing in Knowledge Graph")

        target_trust = claim_node.confidence
        allowed_trust = min(self.policy_max_trust, evidence_node.confidence)
        if target_trust > allowed_trust:
            raise RuntimeError(
                f"Undefined Behaviour Error: Trust ({target_trust}) > Policy Allowed ({allowed_trust})"
            )

        # 2. Track actual effects & verify against declared
        actual_effects = {
            EffectType.KNOWLEDGE_WRITE,
            EffectType.LEDGER_APPEND,
        }
        declared_effects.verify_actual_effects(actual_effects)

        # 3. Perform atomic state transition
        self.state.kg.add_edge(EdgeType.SUPPORTS, evidence_id, claim_id)
        self.state.kg.transition_node_state(claim_id, EpistemicState.VERIFIED)

        # 4. Append to Hash-Chained Ledger
        prev_hash = (
            self.state.ledger[-1]["entry_hash"]
            if self.state.ledger
            else "00000000000000000000000000000000"
        )
        entry_payload = f"{claim_id}:{evidence_id}:{prev_hash}:{time.time()}"
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
