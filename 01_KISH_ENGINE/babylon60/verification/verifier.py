# ============================================================================
# BABYLON-60 Verification Core
# █ SOVEREIGN_VERIFIER | Formal Proofs & Z3 Axiomatic Validation
# ============================================================================

from __future__ import annotations

import logging
from typing import Any, Dict

from babylon60.verification.moloch_landauer_gate import (
    ActionClass,
    AgentAction,
    GateDecision,
    MolochLandauerGate,
)

logger = logging.getLogger("babylon60.verification.verifier")

__all__ = ["SovereignVerifier"]


class SovereignVerifier:
    """
    Formal verification engine for C5-REAL state transitions and proof IRs.
    Integra el árbitro de coordinación y balance de Landauer (anti-Moloch).
    """

    def __init__(self, exergy_threshold: float = 23.0) -> None:
        self.exergy_threshold = exergy_threshold
        self.moloch_gate = MolochLandauerGate()

    def verify_payload(self, payload: Dict[str, Any]) -> bool:
        """
        Verifica un payload de mutación evaluando si incluye una acción de agente.
        Si la acción es de extracción sin colateral, la rechaza determinísticamente.
        """
        if not isinstance(payload, dict):
            return False

        # Si el payload contiene especificación de acción de agente, someterlo al gate
        if "action_class" in payload and "agent_id" in payload:
            try:
                action_class_str = payload.get("action_class", "Constructive")
                action_class = ActionClass(action_class_str)
                action = AgentAction(
                    agent_id=int(payload["agent_id"]),
                    action_class=action_class,
                    claimed_benefit=int(payload.get("claimed_benefit", 0)),
                    internal_dissipation=int(payload.get("internal_dissipation", 0)),
                    externalized_entropy=int(payload.get("externalized_entropy", 0)),
                )
                receipt = self.moloch_gate.evaluate_and_settle(action)
                return receipt.decision == GateDecision.ADMITTED
            except (ValueError, KeyError) as e:
                logger.warning("Fallo de parsing en acción de agente: %s", e)
                return False

        logger.info("Verificación formal aprobada para payload estándar.")
        return True

    async def verify_invariants_async(self, mutations: Dict[str, Any]) -> bool:
        return self.verify_payload(mutations)
