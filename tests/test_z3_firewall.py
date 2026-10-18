"""
[AX-22] TOPOLOGY: Test Z3 SMT Firewall
Falsación Empírica de Apoptosis MUSHUSHU-0 ante anergía estocástica.
"""

import pytest
from babylon60.kernel.z3_firewall import Z3Firewall, MushushuApoptosisError


def test_z3_firewall_algebraic_falsification() -> None:
    firewall = Z3Firewall(timeout_ms=500)

    # 1. Validación exitosa
    assert firewall.falsify_algebraic_proposal(10, 5, 15) is True

    # 2. Falsación (Alucinación) -> Apoptosis
    with pytest.raises(MushushuApoptosisError) as exc_info:
        firewall.falsify_algebraic_proposal(10, 5, 999)
    assert "Apoptosis Triggered" in str(exc_info.value)
    assert "UNSAT" in str(exc_info.value)


def test_z3_firewall_mcp_contract_validation() -> None:
    firewall = Z3Firewall(timeout_ms=500)

    # 1. Contrato válido (5 parámetros, 0.70 exergy)
    assert firewall.validate_mcp_contract(parameters_count=5, estimated_exergy=0.70) is True

    # 2. Contrato inválido por exceso de complejidad (>10 params)
    with pytest.raises(MushushuApoptosisError) as exc_info:
        firewall.validate_mcp_contract(parameters_count=15, estimated_exergy=0.80)
    assert "Apoptosis Triggered" in str(exc_info.value)

    # 3. Contrato inválido por anergía térmica (<0.65 exergy)
    with pytest.raises(MushushuApoptosisError) as exc_info:
        firewall.validate_mcp_contract(parameters_count=2, estimated_exergy=0.50)
    assert "Apoptosis Triggered" in str(exc_info.value)


def test_z3_firewall_apoptosis_without_z3(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prueba que el sistema aplica apoptosis determinista (MUSHUSHU-0) si Z3 no está instalado."""
    import babylon60.kernel.z3_firewall as z3f

    monkeypatch.setattr(z3f, "z3", None)

    firewall = Z3Firewall()
    with pytest.raises(MushushuApoptosisError) as exc_info:
        firewall.falsify_algebraic_proposal(10, 5, 999)
    assert "MUSHUSHU-0" in str(exc_info.value)

    with pytest.raises(MushushuApoptosisError) as exc_info:
        firewall.validate_mcp_contract(15, 0.1)
    assert "MUSHUSHU-0" in str(exc_info.value)
