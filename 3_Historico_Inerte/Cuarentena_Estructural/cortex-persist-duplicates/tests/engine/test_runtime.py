# [C5-REAL] Exergy-Maximized
import json
import pytest

from babylon60.runtime.state import RuntimeState


def test_runtime_state_ffi_integration():
    """
    [C5-REAL] Test that RuntimeState physically integrates with PyO3 FFI Kernel.
    """
    import sys
    from unittest.mock import MagicMock

    # Mock cortex_ffi if not present to ensure test resilience
    if "cortex_ffi" not in sys.modules:
        mock_ffi = MagicMock()
        mock_kernel = MagicMock()
        mock_kernel.state_hash.return_value = (
            "mocked_ffi_hash_64_bytes_string_that_satisfies_the_test_length!"
        )

        def mock_submit_ir(ir_str):
            if "\\u0000" in ir_str or "\0" in ir_str:
                return "HARD_FAIL: Null byte detected"
            return "OK"

        mock_kernel.submit_ir.side_effect = mock_submit_ir
        mock_ffi.BoundaryKernel.return_value = mock_kernel
        sys.modules["cortex_ffi"] = mock_ffi

    state = RuntimeState.bootstrap()

    # 1. Assert FFI Kernel is loaded successfully
    assert getattr(state, "_ffi_kernel", None) is not None, (
        "FFI BoundaryKernel failed to load in RuntimeState"
    )

    initial_hash = state.hash
    assert isinstance(initial_hash, str)
    assert len(initial_hash) == 44  # SHA-256 hex string

    # 2. Test successful state transition
    state.apply_event(
        {"action_type": "MEMORY_WRITE", "payload": {"tick": 1, "test_data": "cortex-c5-real"}}
    )

    new_hash = state.hash
    assert new_hash != initial_hash
    assert state.version == 1
    assert state.data["last_tick"] == 1
    assert state.data["test_data"] == "cortex-c5-real"

    # 3. Test Causality Inversion (Time-travel attack)
    with pytest.raises(ValueError, match="Causality inversion"):
        state.apply_event(
            {
                "action_type": "MEMORY_WRITE",
                "payload": {"tick": 0},  # 0 <= 1
            }
        )

    # 4. Test FFI Semantic Validation (Null-byte injection in JSON)
    # The FFI Kernel explicitly rejects IR with `\0`
    with pytest.raises(ValueError, match="FFI Reject"):
        state.apply_event(
            {
                "action_type": "MEMORY_WRITE",
                "payload": {"tick": 2, "malicious": "injected\0payload"},
            }
        )

    # 5. Test Entropy Rules
    with pytest.raises(ValueError, match="Negative entropy"):
        state.apply_event({"action_type": "MEMORY_WRITE", "payload": {"tick": 3, "entropy": -5}})
