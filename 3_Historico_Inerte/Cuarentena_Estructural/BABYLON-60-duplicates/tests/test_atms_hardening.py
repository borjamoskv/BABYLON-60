# C5-REAL EXERGY CERTIFIED
# C5-REAL: TEST_ATMS_HARDENING
# [CORTEX-TAINT:borjamoskv:test_atms_hardening:2026-07-18T05:00:00Z]

import pytest

try:
    from strike_rs import CortexKernel  # type: ignore[attr-defined]
except ImportError:
    # El núcleo Rust (PyO3) es opcional por diseño: solo existe si se compiló
    # e instaló strike_rs en el entorno. En CI limpio no está -> skip honesto.
    pytest.skip(
        "strike_rs (núcleo PyO3 nativo) no compilado en este entorno",
        allow_module_level=True,
    )


def test_python_cortex_kernel_atms_hardening_and_replay(tmp_path):
    """
    Test suite verifying that CortexKernel exposed via PyO3 to Python correctly:
    1. Asserts empirical knowledge and checks ATMS fixpoint beliefs.
    2. Asserts nogood contradictions and triggers DDB label pruning.
    3. Persists statements and nogoods to SQLite WAL on disk.
    4. Accurately reconstructs historical ATMS beliefs across independent Python instances.
    """
    db_file = str(tmp_path / "cortex_atms_hardening.db")

    # Instance 1: Assert knowledge and contradiction
    kernel1 = CortexKernel(db_file)

    id1 = kernel1.assert_knowledge("Water is H2O", "sensor_py", "env_py")
    assert id1 and "-" in id1, f"Expected UUID for assertion, got {id1}"

    assert kernel1.is_believed("Water is H2O") is True
    assert kernel1.contradiction_free("Water is H2O") is True

    # Inject contradiction against a conjecture hypothesis
    taint_nogood = kernel1.contradict_knowledge("Alien hypothesis Y", "env_py")
    assert "TAINT:C5_REAL_RUST:NOGOOD:" in taint_nogood

    assert kernel1.is_believed("Water is H2O") is True
    assert kernel1.is_believed("Alien hypothesis Y") is False
    assert kernel1.contradiction_free("Alien hypothesis Y") is False

    # Instance 2: Reopen from disk without any prior RAM state
    kernel2 = CortexKernel(db_file)
    assert kernel2.is_believed("Water is H2O") is True, "Replayed premise must be believed in new kernel instance"
    assert kernel2.contradiction_free("Water is H2O") is True
    assert kernel2.is_believed("Alien hypothesis Y") is False, "Replayed nogood must preserve pruned belief state"
    assert kernel2.contradiction_free("Alien hypothesis Y") is False
