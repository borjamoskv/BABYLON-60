# =============================================================================
# BABYLON-60 C5-REAL: TEST SUITE FOR B60 NATIVE C-ABI / FFI BRIDGE
# =============================================================================

import pytest
from babylon60.bft.b60_native import B60NativeBridge

pytestmark = pytest.mark.skipif(
    not B60NativeBridge.is_available(),
    reason="libb60_lang no compilada en target/ (requiere cargo build previo)"
)


def test_native_dylib_loaded() -> None:
    assert B60NativeBridge.is_available() is True
    ver = B60NativeBridge.version()
    assert ver == "4.3.0"


def test_native_sexa_add() -> None:
    # 10s + 6,480,000 u  (10.5 s) + 5s + 6,480,000 u (5.5 s) = 16s + 0 u
    s, f = B60NativeBridge.sexa_add(10, 6480000, 5, 6480000)
    assert s == 16
    assert f == 0


def test_native_fisher_distance() -> None:
    p = [0.5, 0.5]
    q = [0.5, 0.5]
    dist_same = B60NativeBridge.fisher_distance(p, q)
    assert dist_same == pytest.approx(0.0, abs=1e-9)

    p_ortho = [1.0, 0.0]
    q_ortho = [0.0, 1.0]
    dist_ortho = B60NativeBridge.fisher_distance(p_ortho, q_ortho)
    assert dist_ortho == pytest.approx(3.141592653589793, abs=1e-5)


def test_native_kullback_leibler() -> None:
    p = [0.7, 0.3]
    q = [0.7, 0.3]
    kl_zero = B60NativeBridge.kullback_leibler(p, q)
    assert kl_zero == pytest.approx(0.0, abs=1e-9)

    p2 = [0.8, 0.2]
    q2 = [0.5, 0.5]
    kl_val = B60NativeBridge.kullback_leibler(p2, q2)
    assert kl_val > 0.0


def test_native_eval_agent_intent_admitted() -> None:
    verdict, root = B60NativeBridge.eval_agent_intent(
        agent_id="ULTRATHINK-APEX",
        tool_name="commit_proof",
        reasoning_len=200,
        payload_len=100,
        budget=1000,
    )
    assert verdict == 0
    assert len(root) == 64


def test_native_eval_agent_intent_cheap_talk_rejected() -> None:
    verdict, root = B60NativeBridge.eval_agent_intent(
        agent_id="HALLUCINATING-BOT",
        tool_name="noop",
        reasoning_len=4000,
        payload_len=10,
        budget=1000,
    )
    assert verdict == 2
    assert root == ""


def test_native_eval_agent_intent_budget_overflow() -> None:
    verdict, root = B60NativeBridge.eval_agent_intent(
        agent_id="GREEDY-BOT",
        tool_name="infinite",
        reasoning_len=50,
        payload_len=50,
        budget=99999,
    )
    assert verdict == 3
    assert root == ""


def test_native_validate_causal_dag() -> None:
    nodes = [(1, 10), (2, 20), (3, 20), (4, 30)]
    edges = [(1, 2), (1, 3), (2, 4), (3, 4)]
    res, stages = B60NativeBridge.validate_causal_dag(nodes, edges)
    assert res == 0
    assert stages == 3  # Onda 0: [1], Onda 1: [2, 3], Onda 2: [4]


def test_native_validate_causal_dag_temporal_inversion() -> None:
    nodes = [(1, 50), (2, 20)]
    edges = [(1, 2)]  # Inversión: Lamport(1)=50 > Lamport(2)=20
    res, stages = B60NativeBridge.validate_causal_dag(nodes, edges)
    assert res == 2  # Temporal inversion detected!


def test_native_validate_causal_dag_cyclic_paradox() -> None:
    nodes = [(1, 10), (2, 20), (3, 30)]
    edges = [(1, 2), (2, 3), (3, 1)]  # Ciclo cerrado 1 -> 2 -> 3 -> 1
    res, stages = B60NativeBridge.validate_causal_dag(nodes, edges)
    assert res == 1  # Cyclic paradox detected via Kahn's algorithm!

def pack_event(thread_id: int, seq: int, action: int) -> bytes:
    # [ seq (32) | thread_id (24) | action (8) ]
    packed = (action & 0xFF) | ((thread_id & 0xFFFFFF) << 8) | ((seq & 0xFFFFFFFF) << 32)
    return packed.to_bytes(8, byteorder='little')

def test_native_bft_eval_trace_aot() -> None:
    # 1. Crear traza válida
    valid_bytes = b""
    valid_bytes += pack_event(1, 1, 0) # WriteBegin
    valid_bytes += pack_event(1, 2, 1) # WriteEnd
    valid_bytes += pack_event(1, 3, 0) # WriteBegin
    valid_bytes += pack_event(1, 4, 1) # WriteEnd
    
    res_valid = B60NativeBridge.eval_trace_aot(valid_bytes)
    assert res_valid == 1  # 1 = RUNNING
    
    # 2. Crear traza corrupta
    bad_bytes = b""
    bad_bytes += pack_event(1, 1, 0) # WriteBegin
    bad_bytes += pack_event(1, 2, 0) # WriteBegin de nuevo (Paradoja)
    
    res_bad = B60NativeBridge.eval_trace_aot(bad_bytes)
    assert res_bad == 1 # Aún RUNNING (Quorum 2/3) 

    # 3. Crear traza corrupta temporalmente (Inversión Lamport)
    bad_time_bytes = b""
    bad_time_bytes += pack_event(1, 5, 0) # WriteBegin
    bad_time_bytes += pack_event(1, 2, 1) # WriteEnd con seq menor (Paradoja SMT)
    
    res_bad_time = B60NativeBridge.eval_trace_aot(bad_time_bytes)
    assert res_bad_time == 0xDEAD6060 # Colapsa Gamma. Quorum = 1 (Alpha vivo). BFT POISONED!
