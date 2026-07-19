"""Tests C5-REAL para mcts_vnode_compiler.py (O2)."""

import hashlib
import pytest
from cortex.mcts_vnode_compiler import (
    ASTTheorem,
    calculate_shannon_entropy,
    EphemeralVNodePhysical,
    L3InferenceEnginePhysical,
    _mcts_expansion_worker,
)


class TestCalculateShannonEntropy:
    def test_empty_bytes_returns_zero(self) -> None:
        assert calculate_shannon_entropy(b"") == 0.0

    def test_uniform_bytes_max_entropy(self) -> None:
        # 256 unique bytes → max entropy ~8.0 bits
        data = bytes(range(256))
        entropy = calculate_shannon_entropy(data)
        assert entropy > 7.9

    def test_single_byte_zero_entropy(self) -> None:
        # All identical bytes → entropy 0
        data = b"\xAA" * 100
        entropy = calculate_shannon_entropy(data)
        assert entropy == 0.0

    def test_code_string_reasonable_entropy(self) -> None:
        code = b"def foo():\n    return 42 ** 2\n"
        entropy = calculate_shannon_entropy(code)
        assert 3.0 < entropy < 8.0


class TestEphemeralVNodePhysical:
    def test_valid_python_code_passes(self) -> None:
        vnode = EphemeralVNodePhysical("vnode-test-01")
        payload = "def synthesized_theorem_1():\n    # Intention: test\n    return 1 ** 2"
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
        # "aaa" has near-zero entropy and <3 AST nodes
        is_valid, entropy, nodes = vnode.execute_physical_test("aaa")
        # entropy of "aaa" is 0 → should fail
        assert is_valid is False

    def test_node_id_stored(self) -> None:
        vnode = EphemeralVNodePhysical("vnode-sentinel-99")
        assert vnode.node_id == "vnode-sentinel-99"


class TestMCTSExpansionWorker:
    def test_worker_returns_ast_theorem_for_valid_step(self) -> None:
        result = _mcts_expansion_worker(("maximize_exergy", 42))
        assert result is not None
        assert isinstance(result, ASTTheorem)
        assert result.proven is True
        assert len(result.code_hash) == 64  # SHA3-256 → exactly 64 hex chars
        assert result.shannon_entropy > 3.5
        assert result.ast_nodes > 2

    def test_ast_theorem_is_frozen(self) -> None:
        result = _mcts_expansion_worker(("test_immutability", 7))
        assert result is not None
        with pytest.raises(Exception):  # frozen dataclass  # noqa: B017
            result.proven = False  # type: ignore[misc]

    def test_code_hash_is_sha3_256(self) -> None:
        result = _mcts_expansion_worker(("hash_check", 1))
        assert result is not None
        payload = f"def synthesized_theorem_1():\n    # Intention: hash_check\n    return 1 ** 2"
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

    def test_compiled_theorem_payload_is_python(self) -> None:
        import ast as ast_module
        engine = L3InferenceEnginePhysical(target_trajectories=50)
        theorem = engine.compile_theorem("test_syntax_valid")
        # Should parse without SyntaxError
        tree = ast_module.parse(theorem.payload)
        assert tree is not None

    def test_vnode_field_is_set(self) -> None:
        engine = L3InferenceEnginePhysical(target_trajectories=50)
        theorem = engine.compile_theorem("test_vnode_field")
        assert theorem.ephemeral_vnode.startswith("vnode-")
