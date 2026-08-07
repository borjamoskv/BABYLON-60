# C5-REAL EXERGY CERTIFIED
"""
Unit test suite for CAM 2.0 Evolutionary Abstract Machine Engine.
"""

from cortex.cam.effects import EffectsAlgebra, EffectType
from cortex.cam.hypergraph import CAM2Hypergraph
from cortex.cam.machine import CAMAbstractMachine
from cortex.cam.types import (
    EdgeOrder,
    EdgeType,
    Epistemic5D,
    EpistemicState,
    KGNode,
    NodeType,
)

def test_cam2_5d_epistemic_freshness_decay() -> None:
    epistemic = Epistemic5D(
        truth=1.0,
        confidence=0.9,
        authority=0.8,
        relevance=1.0,
        decay_lambda=0.1,  # Half-life decay constant
        timestamp=1000.0,
    )

    t0_trust = epistemic.composite_trust(current_time=1000.0)
    assert round(t0_trust, 4) == 0.7200  # 1.0 * 0.9 * 0.8 * 1.0 * 1.0

    t10_trust = epistemic.composite_trust(current_time=1010.0)
    # Freshness = exp(-0.1 * 10) = exp(-1.0) ~= 0.367879
    assert t10_trust < t0_trust
    assert round(t10_trust, 4) == round(0.7200 * 0.36787944117, 4)

def test_cam2_hypergraph_2nd_order_feedback_loop() -> None:
    graph = CAM2Hypergraph()
    n1 = graph.add_node(KGNode(node_type=NodeType.POLICY, state=EpistemicState.VERIFIED))
    n2 = graph.add_node(KGNode(node_type=NodeType.OBSERVATION, state=EpistemicState.MEASURED))

    # 1st-order causal edge: n1 -> n2
    graph.add_edge(EdgeType.DEPENDS_ON, n1, n2, EdgeOrder.FIRST_ORDER_CAUSAL)

    # 2nd-order feedback edge: n2 -> n1 (Allowed loop for adaptation)
    graph.add_edge(EdgeType.INVALIDATES, n2, n1, EdgeOrder.SECOND_ORDER_FEEDBACK)
    assert len(graph.edges) == 2

def test_cam2_adjudication_preserves_dissidence() -> None:
    graph = CAM2Hypergraph()
    claim_a = graph.add_node(KGNode(node_type=NodeType.CLAIM, content="Market Trend Up"))
    claim_b = graph.add_node(KGNode(node_type=NodeType.CLAIM, content="Market Trend Down"))

    adj = graph.adjudicate_conflict(
        claim_a_id=claim_a,
        claim_b_id=claim_b,
        winner_id=claim_a,
        rationale="Higher authority evidence provided for Claim A",
    )

    assert adj.winning_claim_id == claim_a
    assert adj.dissenting_branch_id == claim_b
    assert graph.nodes[claim_a].state == EpistemicState.VERIFIED
    assert graph.nodes[claim_b].state == EpistemicState.REFUTED
    # Dissenting node remains preserved in graph
    assert claim_b in graph.nodes

def test_cam2_machine_5d_trust_verification() -> None:
    machine = CAMAbstractMachine(profile="CAM 2.0 Evolutionary")
    machine.register_agent_capabilities("agent_alpha", {"Auditor", "Syscall_VERIFY"})

    ev_node = KGNode(
        node_type=NodeType.EVIDENCE,
        state=EpistemicState.MEASURED,
        epistemic_5d=Epistemic5D(truth=1.0, confidence=0.95, authority=0.9, timestamp=100.0),
    )
    cl_node = KGNode(
        node_type=NodeType.CLAIM,
        state=EpistemicState.ESTIMATED,
        epistemic_5d=Epistemic5D(truth=1.0, confidence=0.7, authority=0.8, timestamp=100.0),
    )

    ev_id = machine.state.graph.add_node(ev_node)
    cl_id = machine.state.graph.add_node(cl_node)

    fx = EffectsAlgebra(
        is_pure=False,
        declared_effects={EffectType.KNOWLEDGE_WRITE, EffectType.LEDGER_APPEND},
    )

    success = machine.execute_verify_transition(
        agent_id="agent_alpha",
        claim_id=cl_id,
        evidence_id=ev_id,
        declared_effects=fx,
        current_time=100.0,
    )

    assert success is True
    assert machine.state.graph.nodes[cl_id].state == EpistemicState.VERIFIED
