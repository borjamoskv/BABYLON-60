"""
Unit test suite for CAM 1.0 / CAM 2.0 Abstract Machine Engine.
"""

import pytest
from cortex.cam.dag import TypedDAGKnowledgeGraph
from cortex.cam.effects import EffectsAlgebra, EffectType
from cortex.cam.machine import CAMAbstractMachine
from cortex.cam.types import EdgeType, Epistemic5D, EpistemicState, KGNode, NodeType


def test_cam_dag_acyclicity_and_states() -> None:
    dag = TypedDAGKnowledgeGraph()
    n1 = dag.add_node(
        KGNode(node_type=NodeType.EVIDENCE, state=EpistemicState.MEASURED)
    )
    n2 = dag.add_node(
        KGNode(node_type=NodeType.CLAIM, state=EpistemicState.ESTIMATED)
    )

    dag.add_edge(EdgeType.SUPPORTS, n1, n2)
    assert len(dag.edges) == 1
    assert dag.nodes[n2].state == EpistemicState.ESTIMATED

    # Transition state to VERIFIED
    dag.transition_node_state(n2, EpistemicState.VERIFIED)
    assert dag.nodes[n2].state == EpistemicState.VERIFIED

    # Test cycle detection UB error
    with pytest.raises(RuntimeError, match="Cycle detected"):
        dag.add_edge(EdgeType.SUPPORTS, n2, n1)


def test_cam_effects_algebra_ub_prevention() -> None:
    effects = EffectsAlgebra(
        is_pure=False,
        declared_effects={
            EffectType.KNOWLEDGE_WRITE,
            EffectType.LEDGER_APPEND,
        },
    )

    # Valid actual effects
    assert effects.verify_actual_effects(
        {EffectType.KNOWLEDGE_WRITE, EffectType.LEDGER_APPEND}
    ) is True

    # Undeclared actual effect triggers UB exception
    with pytest.raises(RuntimeError, match="Undeclared effects executed"):
        effects.verify_actual_effects(
            {EffectType.KNOWLEDGE_WRITE, EffectType.FILESYSTEM_WRITE}
        )


def test_cam_abstract_machine_verify_transition() -> None:
    machine = CAMAbstractMachine(profile="CAM Standard")
    machine.register_agent_capabilities("agent_01", {"Auditor", "Syscall_VERIFY"})

    ev_node = KGNode(
        node_type=NodeType.EVIDENCE,
        state=EpistemicState.MEASURED,
        epistemic_5d=Epistemic5D(truth=1.0, confidence=0.9, authority=0.8),
    )
    cl_node = KGNode(
        node_type=NodeType.CLAIM,
        state=EpistemicState.ESTIMATED,
        epistemic_5d=Epistemic5D(truth=1.0, confidence=0.7, authority=0.8),
    )

    ev_id = machine.state.graph.add_node(ev_node)
    cl_id = machine.state.graph.add_node(cl_node)

    declared_fx = EffectsAlgebra(
        is_pure=False,
        declared_effects={
            EffectType.KNOWLEDGE_WRITE,
            EffectType.LEDGER_APPEND,
        },
    )

    success = machine.execute_verify_transition(
        agent_id="agent_01",
        claim_id=cl_id,
        evidence_id=ev_id,
        declared_effects=declared_fx,
    )

    assert success is True
    assert machine.state.graph.nodes[cl_id].state == EpistemicState.VERIFIED
    assert len(machine.state.ledger) == 1
    assert "entry_hash" in machine.state.ledger[0]
