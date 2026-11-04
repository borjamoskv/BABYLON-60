# ============================================================================
# BABYLON-60 Verification Core — MOLOCH LANDAUER GATE TEST SUITE
# ============================================================================
"""
Suite de pruebas de falsación empírica para el MolochLandauerGate.
Verifica:
1. Isomorfismo estricto con los teoremas formales en Lean 4 (MolochLandauer.lean).
2. Detección unívoca de acciones extractivas (Moloch).
3. Neutralización de payoff extractivo a exactamente 0.
4. Dominancia de Pareto de la cooperación constructiva.
5. Liquidación de colateral bajo penalización de Landauer.
6. Fail-stop y transición a apoptosis ante insolvencia reincidente.
"""

import pytest

from babylon60.verification.moloch_landauer_gate import (
    ActionClass,
    AgentAction,
    GateDecision,
    MolochLandauerGate,
    is_moloch_extraction,
    landauer_penalty,
    net_exergy_payoff,
    is_admissible,
)


def test_agent_action_validation() -> None:
    """Verifica que las cantidades negativas en AgentAction sean rechazadas de inmediato."""
    with pytest.raises(ValueError, match="claimed_benefit"):
        AgentAction(agent_id=1, action_class=ActionClass.EXTRACT, claimed_benefit=-5, internal_dissipation=10, externalized_entropy=20)

    with pytest.raises(ValueError, match="internal_dissipation"):
        AgentAction(agent_id=1, action_class=ActionClass.EXTRACT, claimed_benefit=5, internal_dissipation=-10, externalized_entropy=20)

    with pytest.raises(ValueError, match="externalized_entropy"):
        AgentAction(agent_id=1, action_class=ActionClass.EXTRACT, claimed_benefit=5, internal_dissipation=10, externalized_entropy=-20)


def test_is_moloch_extraction_detection() -> None:
    """Verifica el predicado de detección de Moloch."""
    # Caso 1: Extracción neta (claimed_benefit > 0 y externalized_entropy > internal_dissipation)
    moloch_act = AgentAction(
        agent_id=101,
        action_class=ActionClass.EXTRACT,
        claimed_benefit=100,
        internal_dissipation=10,
        externalized_entropy=50,
    )
    assert is_moloch_extraction(moloch_act) is True

    # Caso 2: Acción constructiva no es Moloch aunque tenga entropía interna
    constructive_act = AgentAction(
        agent_id=102,
        action_class=ActionClass.CONSTRUCTIVE,
        claimed_benefit=100,
        internal_dissipation=20,
        externalized_entropy=0,
    )
    assert is_moloch_extraction(constructive_act) is False

    # Caso 3: Acción extract sin beneficio positivo
    zero_benefit = AgentAction(
        agent_id=103,
        action_class=ActionClass.EXTRACT,
        claimed_benefit=0,
        internal_dissipation=10,
        externalized_entropy=50,
    )
    assert is_moloch_extraction(zero_benefit) is False

    # Caso 4: Acción extract donde la disipación interna supera la externa (no es asimetría extractiva externa)
    self_contained = AgentAction(
        agent_id=104,
        action_class=ActionClass.EXTRACT,
        claimed_benefit=10,
        internal_dissipation=50,
        externalized_entropy=10,
    )
    assert is_moloch_extraction(self_contained) is False


def test_theorem_1_isomorphism_moloch_payoff_is_zero() -> None:
    """
    Verifica el Teorema 1 de Lean 4:
    Para toda acción de Moloch, net_exergy_payoff(a) == 0.
    """
    moloch_act = AgentAction(
        agent_id=1,
        action_class=ActionClass.EXTRACT,
        claimed_benefit=500,
        internal_dissipation=50,
        externalized_entropy=200,
    )
    assert is_moloch_extraction(moloch_act) is True
    # penalty = externalized_entropy + claimed_benefit = 200 + 500 = 700
    # deductions = internal_dissipation + penalty = 50 + 700 = 750
    # net_payoff = max(0, 500 - 750) = 0
    assert landauer_penalty(moloch_act) == 700
    assert net_exergy_payoff(moloch_act) == 0


def test_theorem_2_isomorphism_constructive_positive_payoff() -> None:
    """
    Verifica el Teorema 2 de Lean 4:
    Una acción constructiva con externalidad nula y claimed_benefit > internal_dissipation
    conserva net_exergy_payoff > 0.
    """
    coop_act = AgentAction(
        agent_id=2,
        action_class=ActionClass.CONSTRUCTIVE,
        claimed_benefit=100,
        internal_dissipation=20,
        externalized_entropy=0,
    )
    assert is_moloch_extraction(coop_act) is False
    assert landauer_penalty(coop_act) == 0
    # net_payoff = 100 - (20 + 0) = 80 > 0
    assert net_exergy_payoff(coop_act) == 80


def test_theorem_3_cooperation_dominates_moloch() -> None:
    """
    Verifica el Teorema 3 de Lean 4:
    net_exergy_payoff(coop) > net_exergy_payoff(moloch).
    """
    coop_act = AgentAction(
        agent_id=2,
        action_class=ActionClass.CONSTRUCTIVE,
        claimed_benefit=100,
        internal_dissipation=20,
        externalized_entropy=0,
    )
    moloch_act = AgentAction(
        agent_id=1,
        action_class=ActionClass.EXTRACT,
        claimed_benefit=5000,
        internal_dissipation=10,
        externalized_entropy=1000,
    )
    assert net_exergy_payoff(coop_act) > net_exergy_payoff(moloch_act)


def test_theorem_4_landauer_compensates_entropy() -> None:
    """
    Verifica el Teorema 4 de Lean 4:
    landauer_penalty(a) >= a.externalized_entropy.
    """
    for act in [
        AgentAction(1, ActionClass.CONSTRUCTIVE, 100, 10, 0),
        AgentAction(2, ActionClass.NEUTRAL, 0, 5, 5),
        AgentAction(3, ActionClass.EXTRACT, 200, 10, 50),
    ]:
        assert landauer_penalty(act) >= act.externalized_entropy


def test_theorem_5_trace_entropy_solvency_universal() -> None:
    """
    Verifica el Teorema 5 de Lean 4:
    Para toda traza finita de acciones, la penalización total acumulada de Landauer
    es mayor o igual a la entropía total externalizada.
    """
    trace = [
        AgentAction(1, ActionClass.CONSTRUCTIVE, 100, 10, 0),
        AgentAction(2, ActionClass.NEUTRAL, 0, 5, 20),
        AgentAction(3, ActionClass.EXTRACT, 200, 10, 50),
        AgentAction(4, ActionClass.EXTRACT, 500, 20, 150),
    ]
    total_entropy = sum(a.externalized_entropy for a in trace)
    total_penalty = sum(landauer_penalty(a) for a in trace)
    assert total_penalty >= total_entropy


def test_is_admissible_predicate() -> None:
    """Verifica la función pura de admisibilidad basada en colateral."""
    act = AgentAction(1, ActionClass.CONSTRUCTIVE, 100, 10, 50)
    assert is_admissible(act, collateral=100) is True
    assert is_admissible(act, collateral=50) is True
    assert is_admissible(act, collateral=49) is False


def test_moloch_gate_lifecycle_and_settlement() -> None:
    """Verifica el ciclo de vida completo del gatekeeper en runtime."""
    gate = MolochLandauerGate(max_infractions_before_apoptosis=2)
    gate.register_agent(agent_id=42, initial_collateral=1000)

    # Paso 1: Acción constructiva legítima
    coop_act = AgentAction(
        agent_id=42,
        action_class=ActionClass.CONSTRUCTIVE,
        claimed_benefit=80,
        internal_dissipation=10,
        externalized_entropy=5,
    )
    # penalty = 5, admitted
    rec1 = gate.evaluate_and_settle(coop_act)
    assert rec1.decision == GateDecision.ADMITTED
    assert rec1.is_moloch is False
    assert rec1.penalty_deducted == 5
    assert rec1.net_payoff_awarded == (80 - (10 + 5))  # 65
    assert rec1.remaining_collateral == 995
    assert gate.get_collateral(42) == 995

    # Paso 2: Acción extractiva con colateral suficiente
    # claimed=100, ext=200, int=10 -> moloch. penalty = 200 + 100 = 300 <= 995
    moloch_act = AgentAction(
        agent_id=42,
        action_class=ActionClass.EXTRACT,
        claimed_benefit=100,
        internal_dissipation=10,
        externalized_entropy=200,
    )
    rec2 = gate.evaluate_and_settle(moloch_act)
    assert rec2.decision == GateDecision.ADMITTED
    assert rec2.is_moloch is True
    assert rec2.penalty_deducted == 300
    assert rec2.net_payoff_awarded == 0  # Extinción de beneficio
    assert rec2.remaining_collateral == 695

    # Paso 3: Intento de extracción masiva que supera el colateral restante
    # claimed=500, ext=500 -> moloch. penalty = 1000 > 695
    massive_act = AgentAction(
        agent_id=42,
        action_class=ActionClass.EXTRACT,
        claimed_benefit=500,
        internal_dissipation=10,
        externalized_entropy=500,
    )
    rec3 = gate.evaluate_and_settle(massive_act)
    assert rec3.decision == GateDecision.REJECTED_INSUFFICIENT_COLLATERAL
    assert rec3.remaining_collateral == 695

    # Paso 4: Segunda infracción consecutiva -> Disparo de FAIL_STOP_APOPTOSIS
    rec4 = gate.evaluate_and_settle(massive_act)
    assert rec4.decision == GateDecision.FAIL_STOP_APOPTOSIS
    assert rec4.remaining_collateral == 0
    assert gate.is_poisoned(42) is True

    # Paso 5: Todo intento subsecuente de un agente envenenado colapsa en FAIL_STOP
    rec5 = gate.evaluate_and_settle(coop_act)
    assert rec5.decision == GateDecision.FAIL_STOP_APOPTOSIS


def test_sovereign_verifier_end_to_end() -> None:
    """Verifica que SovereignVerifier rechaza payloads con acciones de Moloch no autorizadas."""
    from babylon60.verification.verifier import SovereignVerifier

    verifier = SovereignVerifier()

    # Payload estándar no-acción es admitido
    assert verifier.verify_payload({"type": "ping", "data": "ok"}) is True

    # Payload inválido no-dict es rechazado
    assert verifier.verify_payload("not_a_dict") is False  # type: ignore

    # Acción de Moloch sin registrar/sin colateral es rechazada
    moloch_payload = {
        "agent_id": 999,
        "action_class": "Extract",
        "claimed_benefit": 100,
        "internal_dissipation": 10,
        "externalized_entropy": 50,
    }
    assert verifier.verify_payload(moloch_payload) is False

    # Acción constructiva sin externalidad es admitida
    coop_payload = {
        "agent_id": 999,
        "action_class": "Constructive",
        "claimed_benefit": 50,
        "internal_dissipation": 10,
        "externalized_entropy": 0,
    }
    assert verifier.verify_payload(coop_payload) is True
