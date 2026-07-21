"""Tests C5-REAL para mcts_vnode_compiler.py (v3.0 - OMEGATRON APEX).

Enforces:
1. Vectorized & C-accelerated Shannon Entropy calculations.
2. Property-Based Testing via Hypothesis.
3. MCTSNode UCT tree calculations and invariants.
4. Custom Typed Exception handling and edge cases.
5. Rich Diagnostics & CORTEX Causal Taint assertion (Ω113).
"""

import hashlib
import math
import pytest
try:
    from hypothesis import given, strategies as st
except ImportError:
    from typing import Callable, Any
    def given(*args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:  # type: ignore[no-redef]
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func
        return decorator
    class st:  # type: ignore[no-redef]
        @staticmethod
        def binary() -> Any:
            class SimpleStrategy:
                def example(self) -> bytes:
                    return b""
            return SimpleStrategy()
from cortex.mcts_vnode_compiler import (
    ASTTheorem,
    calculate_shannon_entropy,
    EphemeralVNodePhysical,
    L3InferenceEnginePhysical,
    MCTSCompilerError,
    MCTSNode,
    MCTSTreeSearchError,
    _fast_log2,
    _generate_cortex_taint,
    _mcts_expansion_worker,
)


class TestCalculateShannonEntropy:
    def test_empty_bytes_returns_zero(self) -> None:
        assert calculate_shannon_entropy(b"") == 0.0

    def test_uniform_bytes_max_entropy(self) -> None:
        # 256 unique bytes -> max entropy = 8.0 bits
        data = bytes(range(256))
        entropy = calculate_shannon_entropy(data)
        assert abs(entropy - 8.0) < 1e-5

    def test_single_byte_zero_entropy(self) -> None:
        # All identical bytes -> entropy 0
        data = b"\xaa" * 100
        entropy = calculate_shannon_entropy(data)
        assert entropy == 0.0

    def test_code_string_reasonable_entropy(self) -> None:
        code = b"def foo():\n    return 42 ** 2\n"
        entropy = calculate_shannon_entropy(code)
        assert 3.0 < entropy < 8.0

    @given(st.binary())
    def test_hypothesis_entropy_bounds(self, data: bytes) -> None:
        """Property-based test: Shannon entropy MUST strictly lie within [0.0, 8.0]."""
        entropy = calculate_shannon_entropy(data)
        assert 0.0 <= entropy <= 8.0

    def test_fast_log2_accuracy(self) -> None:
        for x in [1, 2, 10, 256, 1000, 65535, 100000]:
            assert abs(_fast_log2(x) - math.log2(x)) < 1e-9


class TestEphemeralVNodePhysical:
    def test_valid_python_code_passes(self) -> None:
        vnode = EphemeralVNodePhysical("vnode-test-01")
        payload = (
            "def synthesized_theorem_1():\n    # Intention: test\n    return 1 ** 2"
        )
        is_valid, entropy, nodes = vnode.execute_physical_test(payload)
        assert is_valid is True
        assert entropy > 3.0
        assert nodes > 2

    def test_invalid_syntax_returns_false(self) -> None:
        vnode = EphemeralVNodePhysical("vnode-test-02")
        is_valid, entropy, nodes = vnode.execute_physical_test("def broken(:\n    pass")
        assert is_valid is False
        assert nodes == 0

    def test_low_entropy_code_fails_threshold(self) -> None:
        vnode = EphemeralVNodePhysical("vnode-test-03")
        is_valid, entropy, nodes = vnode.execute_physical_test("aaa")
        assert is_valid is False

    def test_empty_node_id_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="node_id cannot be empty"):
            EphemeralVNodePhysical("")

    def test_empty_payload_returns_false(self) -> None:
        vnode = EphemeralVNodePhysical("vnode-test-empty")
        is_valid, entropy, nodes = vnode.execute_physical_test("")
        assert is_valid is False
        assert entropy == 0.0
        assert nodes == 0


class TestMCTSNodeAndUCT:
    def test_unvisited_node_uct_score_is_inf(self) -> None:
        node = MCTSNode(state_id="unvisited")
        assert node.uct_score() == float("inf")

    def test_visited_node_uct_computation(self) -> None:
        parent = MCTSNode(state_id="parent")
        parent.update(1.0)
        parent.update(1.0)  # parent visits = 2

        child = parent.add_child("child")
        child.update(0.5)  # child visits = 1, value = 0.5, q = 0.5

        # uct = 0.5 + 1.414 * sqrt(ln(2) / 1)
        expected_uct = 0.5 + 1.414 * math.sqrt(math.log(2) / 1)
        assert abs(child.uct_score() - expected_uct) < 1e-4

    def test_add_child_idempotency(self) -> None:
        parent = MCTSNode(state_id="root")
        c1 = parent.add_child("node1")
        c2 = parent.add_child("node1")
        assert c1 is c2
        assert len(parent.children) == 1


class TestASTTheoremAndInvariants:
    def test_ast_theorem_valid_construction(self) -> None:
        payload = "x = 1"
        code_hash = hashlib.sha3_256(payload.encode("utf-8")).hexdigest()
        theorem = ASTTheorem(
            code_hash=code_hash,
            proven=True,
            shannon_entropy=4.5,
            ast_nodes=10,
            ephemeral_vnode="vnode-1",
            payload=payload,
            cortex_taint="CORTEX-TAINT:test",
        )
        assert theorem.code_hash == code_hash
        assert theorem.cortex_taint == "CORTEX-TAINT:test"

    def test_invalid_entropy_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Shannon entropy out of theoretical bounds"):
            ASTTheorem(
                code_hash="a" * 64,
                proven=True,
                shannon_entropy=9.5,
                ast_nodes=5,
                ephemeral_vnode="vnode-1",
                payload="x = 1",
            )

    def test_invalid_code_hash_length_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="code_hash must be 64-char hex"):
            ASTTheorem(
                code_hash="short_hash",
                proven=True,
                shannon_entropy=4.0,
                ast_nodes=5,
                ephemeral_vnode="vnode-1",
                payload="x = 1",
            )


class TestMCTSExpansionWorker:
    def test_worker_returns_ast_theorem_for_valid_step(self) -> None:
        result = _mcts_expansion_worker(("maximize_exergy", 42))
        assert result is not None
        assert isinstance(result, ASTTheorem)
        assert result.proven is True
        assert len(result.code_hash) == 64
        assert result.shannon_entropy > 3.5
        assert result.ast_nodes > 2
        assert result.cortex_taint.startswith("CORTEX-TAINT:borjamoskv:mcts:")

    def test_code_hash_is_sha3_256(self) -> None:
        result = _mcts_expansion_worker(("hash_check", 1))
        assert result is not None
        payload = (
            "def synthesized_theorem_1():\n    # Intention: hash_check\n    return 1**2\n"
        )
        expected = hashlib.sha3_256(payload.encode()).hexdigest()
        assert result.code_hash == expected


class TestL3InferenceEnginePhysical:
    def test_compile_theorem_returns_valid_theorem(self) -> None:
        engine = L3InferenceEnginePhysical(target_trajectories=50)
        theorem = engine.compile_theorem("test_compile_basic")
        assert theorem is not None
        assert theorem.proven is True
        assert theorem.shannon_entropy > 3.5
        assert len(theorem.code_hash) == 64
        assert "trajectories_evaluated" in engine.last_diagnostics
        assert engine.last_diagnostics["trajectories_evaluated"] > 0

    def test_invalid_target_trajectories_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="target_trajectories must be positive"):
            L3InferenceEnginePhysical(target_trajectories=0)

    def test_exhausted_trajectories_raises_mcts_error(self) -> None:
        engine = L3InferenceEnginePhysical(target_trajectories=1)
        # Monkeypatch worker to return None to test exhaustion exception
        import cortex.mcts_vnode_compiler as compiler_mod

        old_worker = compiler_mod._mcts_expansion_worker
        try:
            compiler_mod._mcts_expansion_worker = lambda args: None
            with pytest.raises(MCTSTreeSearchError, match="Imposible colapsar un teorema"):
                engine.compile_theorem("impossible_intention")
            assert engine.last_diagnostics["status"] == "EXHAUSTED"
        finally:
            compiler_mod._mcts_expansion_worker = old_worker

    def test_cortex_taint_generator_format(self) -> None:
        taint = _generate_cortex_taint("abc123hash")
        assert taint.startswith("CORTEX-TAINT:borjamoskv:mcts:")
        assert len(taint.split(":")) == 4
