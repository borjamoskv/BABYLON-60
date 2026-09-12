# =============================================================================
# BABYLON-60 C5-REAL: TEST SUITE FOR B60 NATIVE C-ABI / FFI BRIDGE
# =============================================================================

import pytest
from babylon60.bft.b60_native import B60NativeBridge


def test_native_dylib_loaded():
    assert B60NativeBridge.is_available() is True
    ver = B60NativeBridge.version()
    assert ver == "1.0.0-omega"


def test_native_sexa_add():
    # 10s + 6,480,000 u  (10.5 s) + 5s + 6,480,000 u (5.5 s) = 16s + 0 u
    s, f = B60NativeBridge.sexa_add(10, 6480000, 5, 6480000)
    assert s == 16
    assert f == 0


def test_native_fisher_distance():
    p = [0.5, 0.5]
    q = [0.5, 0.5]
    dist_same = B60NativeBridge.fisher_distance(p, q)
    assert dist_same == pytest.approx(0.0, abs=1e-9)

    p_ortho = [1.0, 0.0]
    q_ortho = [0.0, 1.0]
    dist_ortho = B60NativeBridge.fisher_distance(p_ortho, q_ortho)
    assert dist_ortho == pytest.approx(3.141592653589793, abs=1e-5)


def test_native_kullback_leibler():
    p = [0.7, 0.3]
    q = [0.7, 0.3]
    kl_zero = B60NativeBridge.kullback_leibler(p, q)
    assert kl_zero == pytest.approx(0.0, abs=1e-9)

    p2 = [0.8, 0.2]
    q2 = [0.5, 0.5]
    kl_val = B60NativeBridge.kullback_leibler(p2, q2)
    assert kl_val > 0.0


def test_native_eval_agent_intent_admitted():
    verdict, root = B60NativeBridge.eval_agent_intent(
        agent_id="ULTRATHINK-APEX",
        tool_name="commit_proof",
        reasoning_len=200,
        payload_len=100,
        budget=1000,
    )
    assert verdict == 0
    assert len(root) == 64


def test_native_eval_agent_intent_cheap_talk_rejected():
    verdict, root = B60NativeBridge.eval_agent_intent(
        agent_id="HALLUCINATING-BOT",
        tool_name="noop",
        reasoning_len=4000,
        payload_len=10,
        budget=1000,
    )
    assert verdict == 2
    assert root == ""


def test_native_eval_agent_intent_budget_overflow():
    verdict, root = B60NativeBridge.eval_agent_intent(
        agent_id="GREEDY-BOT",
        tool_name="infinite",
        reasoning_len=50,
        payload_len=50,
        budget=99999,
    )
    assert verdict == 3
    assert root == ""


def test_native_validate_causal_dag():
    nodes = [(1, 10), (2, 20), (3, 20), (4, 30)]
    edges = [(1, 2), (1, 3), (2, 4), (3, 4)]
    res, stages = B60NativeBridge.validate_causal_dag(nodes, edges)
    assert res == 0
    assert stages == 3  # Onda 0: [1], Onda 1: [2, 3], Onda 2: [4]


def test_native_validate_causal_dag_temporal_inversion():
    nodes = [(1, 50), (2, 20)]
    edges = [(1, 2)]  # Inversión: Lamport(1)=50 > Lamport(2)=20
    res, stages = B60NativeBridge.validate_causal_dag(nodes, edges)
    assert res == 2  # Temporal inversion detected!

