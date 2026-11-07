# ============================================================================
# BABYLON-60 Verification Core
# █ MOLOCH_LANDAUER_GATE | Runtime Coordination Arbiter & Landauer Balance
# ============================================================================
"""
Implementación ejecutable del contrato formal Lean 4 `Babylon.MolochLandauer`.
Detecta computable e invariablemente acciones extractivas de Moloch (asimetría
entrópica) e internaliza la degradación del pool compartido mediante gravámenes
de balance de Landauer en aritmética de números enteros no negativos.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Dict, Set

__all__ = [
    "ActionClass",
    "AgentAction",
    "GateDecision",
    "SettlementReceipt",
    "MolochLandauerGate",
    "is_moloch_extraction",
    "landauer_penalty",
    "net_exergy_payoff",
    "is_admissible",
]


class ActionClass(enum.Enum):
    CONSTRUCTIVE = "Constructive"
    NEUTRAL = "Neutral"
    EXTRACT = "Extract"
    APOPTOSIS = "Apoptosis"


@dataclass(frozen=True)
class AgentAction:
    agent_id: int
    action_class: ActionClass
    claimed_benefit: int
    internal_dissipation: int
    externalized_entropy: int

    def __post_init__(self) -> None:
        if self.claimed_benefit < 0:
            raise ValueError("claimed_benefit debe ser no negativo (ℕ)")
        if self.internal_dissipation < 0:
            raise ValueError("internal_dissipation debe ser no negativo (ℕ)")
        if self.externalized_entropy < 0:
            raise ValueError("externalized_entropy debe ser no negativo (ℕ)")


def is_moloch_extraction(a: AgentAction) -> bool:
    """
    Predicado computable isomorfo al teorema Lean 4:
    is_moloch_extraction a := match a.action_class with
      | .Extract => (a.claimed_benefit > 0) && (a.externalized_entropy > a.internal_dissipation)
      | _ => false
    """
    if a.action_class == ActionClass.EXTRACT:
        return (a.claimed_benefit > 0) and (a.externalized_entropy > a.internal_dissipation)
    return False


def landauer_penalty(a: AgentAction) -> int:
    """
    Gravamen de Landauer:
    if is_moloch_extraction a then a.externalized_entropy + a.claimed_benefit else a.externalized_entropy
    """
    if is_moloch_extraction(a):
        return a.externalized_entropy + a.claimed_benefit
    return a.externalized_entropy


def net_exergy_payoff(a: AgentAction) -> int:
    """
    Payoff neto en ℕ truncado:
    a.claimed_benefit - (a.internal_dissipation + landauer_penalty a)
    """
    deductions = a.internal_dissipation + landauer_penalty(a)
    return max(0, a.claimed_benefit - deductions)


def is_admissible(a: AgentAction, collateral: int) -> bool:
    """
    Regla de admisión:
    collateral >= landauer_penalty a
    """
    return collateral >= landauer_penalty(a)


class GateDecision(enum.Enum):
    ADMITTED = "ADMITTED"
    REJECTED_INSUFFICIENT_COLLATERAL = "REJECTED_INSUFFICIENT_COLLATERAL"
    FAIL_STOP_APOPTOSIS = "FAIL_STOP_APOPTOSIS"


@dataclass(frozen=True)
class SettlementReceipt:
    agent_id: int
    decision: GateDecision
    is_moloch: bool
    penalty_deducted: int
    net_payoff_awarded: int
    remaining_collateral: int
    collective_entropy_absorbed: int


class MolochLandauerGate:
    """
    Árbitro de coordinación multi-agente en runtime.
    Garantiza que ningún agente obtenga ventaja neta mediante estrategias extractivas.
    """

    def __init__(self, max_infractions_before_apoptosis: int = 2) -> None:
        self.max_infractions = max_infractions_before_apoptosis
        self._collateral_balances: Dict[int, int] = {}
        self._infraction_counts: Dict[int, int] = {}
        self._poisoned_agents: Set[int] = set()
        self._collective_entropy_pool: int = 0

    def register_agent(self, agent_id: int, initial_collateral: int) -> None:
        if initial_collateral < 0:
            raise ValueError("Colateral inicial debe ser no negativo")
        self._collateral_balances[agent_id] = initial_collateral
        self._infraction_counts[agent_id] = 0

    def get_collateral(self, agent_id: int) -> int:
        return self._collateral_balances.get(agent_id, 0)

    def is_poisoned(self, agent_id: int) -> bool:
        return agent_id in self._poisoned_agents

    def evaluate_and_settle(self, action: AgentAction) -> SettlementReceipt:
        agent_id = action.agent_id

        if self.is_poisoned(agent_id):
            return SettlementReceipt(
                agent_id=agent_id,
                decision=GateDecision.FAIL_STOP_APOPTOSIS,
                is_moloch=is_moloch_extraction(action),
                penalty_deducted=0,
                net_payoff_awarded=0,
                remaining_collateral=0,
                collective_entropy_absorbed=0,
            )

        moloch_flag = is_moloch_extraction(action)
        penalty = landauer_penalty(action)
        current_collateral = self._collateral_balances.get(agent_id, 0)

        if not is_admissible(action, current_collateral):
            # Infracción por intento de extracción no colateralizada
            infractions = self._infraction_counts.get(agent_id, 0) + 1
            self._infraction_counts[agent_id] = infractions

            if infractions >= self.max_infractions:
                self._poisoned_agents.add(agent_id)
                self._collateral_balances[agent_id] = 0
                return SettlementReceipt(
                    agent_id=agent_id,
                    decision=GateDecision.FAIL_STOP_APOPTOSIS,
                    is_moloch=moloch_flag,
                    penalty_deducted=0,
                    net_payoff_awarded=0,
                    remaining_collateral=0,
                    collective_entropy_absorbed=0,
                )

            return SettlementReceipt(
                agent_id=agent_id,
                decision=GateDecision.REJECTED_INSUFFICIENT_COLLATERAL,
                is_moloch=moloch_flag,
                penalty_deducted=0,
                net_payoff_awarded=0,
                remaining_collateral=current_collateral,
                collective_entropy_absorbed=0,
            )

        # Acción admitida: liquidación del balance de Landauer
        new_collateral = current_collateral - penalty
        self._collateral_balances[agent_id] = new_collateral
        payoff = net_exergy_payoff(action)
        self._collective_entropy_pool += action.externalized_entropy

        # Si era un intento de Moloch admitido, el payoff es exactamente 0 (Teorema Lean 4)
        if moloch_flag:
            assert payoff == 0, "Violación del teorema moloch_payoff_is_zero"

        return SettlementReceipt(
            agent_id=agent_id,
            decision=GateDecision.ADMITTED,
            is_moloch=moloch_flag,
            penalty_deducted=penalty,
            net_payoff_awarded=payoff,
            remaining_collateral=new_collateral,
            collective_entropy_absorbed=action.externalized_entropy,
        )
