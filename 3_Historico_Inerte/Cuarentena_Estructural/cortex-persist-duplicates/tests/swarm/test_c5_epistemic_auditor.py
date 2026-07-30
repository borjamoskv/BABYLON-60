# [C5-REAL] Exergy-Maximized
"""
Test C5-REAL Epistemic Auditor P0 Invariants.
"""

import pytest

from babylon60.swarm.c5_epistemic_auditor import EpistemicSquadron
from babylon60.swarm.legion import SwarmSignal


@pytest.mark.asyncio
async def test_inv_one_mutation_and_landauer():
    """
    Verifica que el Squadron despliega y respeta INV_ONE_MUTATION.
    También valida que las señales pasen el Landauer Epistemic Filter.
    """
    # Usar un engine mock para evitar invocar el hardware local en tests unitarios
    class MockEngine:
        pass

    squadron = EpistemicSquadron(engine=MockEngine())

    # 1 Deploy
    report = await squadron.deploy(target_pattern="babylon60/swarm/c5_epistemic_auditor.py")

    # Assert
    assert "success" in report
    assert report["success"] > 0
    assert report["squadron"] == "EPISTEMIC_AUDIT"

    # Verificar entropía densa (LANDAUER_FILTER) - Los payloads deben tener "hash" y "proof_of_work"
    assert "raw" in report
    assert len(report["raw"]) > 0

    for signal_dict in report["raw"]:
        if signal_dict["status"] == "SUCCESS":
            payload = signal_dict["payload"]
            assert "hash" in payload
            assert "proof_of_work" in payload
            assert "C5-REAL-VERIFIED" in payload["proof_of_work"]


@pytest.mark.asyncio
async def test_byzantine_fault_handling():
    """
    Prueba el manejo de fallos bizantinos (falsos targets que generarían C4-SIM).
    Debe fallar el CausalClosureGuard por producir pura Anergía (solo errores sin invariantes).
    """
    squadron = EpistemicSquadron(engine=None)

    # Target inexistente -> genera status VOID (evasión C4-SIM)
    # Como es pura anergía, el Squadron aborta la SAGA.
    with pytest.raises(RuntimeError, match="AX-VIII Violation"):
        await squadron.deploy(target_pattern="babylon60/non_existent_file.py")
