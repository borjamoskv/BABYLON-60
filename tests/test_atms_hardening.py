import pytest
try:
    from strike_rs import CortexKernel
except ImportError:
    pytest.skip('strike_rs (núcleo PyO3 nativo) no compilado en este entorno', allow_module_level=True)

def test_python_cortex_kernel_atms_hardening_and_replay(tmp_path) -> None:
    db_file = str(tmp_path / 'cortex_atms_hardening.db')
    kernel1 = CortexKernel(db_file)
    id1 = kernel1.assert_knowledge('Water is H2O', 'sensor_py', 'env_py')
    assert id1 and '-' in id1, f'Expected UUID for assertion, got {id1}'
    assert kernel1.is_believed('Water is H2O') is True
    assert kernel1.contradiction_free('Water is H2O') is True
    taint_nogood = kernel1.contradict_knowledge('Alien hypothesis Y', 'env_py')
    assert 'TAINT:C5_REAL_RUST:NOGOOD:' in taint_nogood
    assert kernel1.is_believed('Water is H2O') is True
    assert kernel1.is_believed('Alien hypothesis Y') is False
    assert kernel1.contradiction_free('Alien hypothesis Y') is False
    kernel2 = CortexKernel(db_file)
    assert kernel2.is_believed('Water is H2O') is True, 'Replayed premise must be believed in new kernel instance'
    assert kernel2.contradiction_free('Water is H2O') is True
    assert kernel2.is_believed('Alien hypothesis Y') is False, 'Replayed nogood must preserve pruned belief state'
    assert kernel2.contradiction_free('Alien hypothesis Y') is False