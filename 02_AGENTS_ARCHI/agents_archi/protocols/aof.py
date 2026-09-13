#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AOF PROTOCOL ENFORCER | DOMAIN: agents.archi | STATE: C5-REAL
# ============================================================================
"""
Agentic Operational Framework (AOF v2.0 / PSAFE v3.0) - Hume's Guillotine Enforcer.

Enforces:
  - Strict separation of epistemic (is) vs deontic (ought) propositions
  - Pre- and post-condition invariants for tool actions
  - Prevents hallucinated normative imperatives from ungrounded observations
"""

from typing import Dict, List, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class Modality(Enum):
    EPISTEMIC = "epistemic"  # Descriptive: "System CPU is at 90%"
    DEONTIC = "deontic"      # Normative: "You must throttle the swarm"


@dataclass
class Proposition:
    statement: str
    modality: Modality
    grounding_axioms: List[str] = field(default_factory=list)


class AOFValidator:
    """
    AOF / PSAFE Invariant Validator.
    Implements Hume's Guillotine: Deontic conclusions require at least one deontic premise.
    """

    @staticmethod
    def enforce_humes_guillotine(premises: List[Proposition], conclusion: Proposition) -> bool:
        """
        Validates whether a conclusion can logically follow from premises without Hume breach.
        If conclusion is DEONTIC, at least one premise MUST be DEONTIC.
        """
        if conclusion.modality == Modality.DEONTIC:
            has_deontic_premise = any(p.modality == Modality.DEONTIC for p in premises)
            if not has_deontic_premise:
                raise ValueError(
                    f"Hume's Guillotine Breach (INV_C5_HUME_GUILLOTINE): Cannot derive deontic conclusion "
                    f"'{conclusion.statement}' from purely epistemic premises."
                )
        return True

    @staticmethod
    def validate_tool_action(
        tool_name: str,
        arguments: Dict[str, Any],
        preconditions: List[Callable[[Dict[str, Any]], bool]] = None,
    ) -> bool:
        """
        Enforces tool execution preconditions before dispatch.
        """
        if preconditions:
            for i, check in enumerate(preconditions):
                if not check(arguments):
                    raise PermissionError(
                        f"AOF Precondition #{i} failed for tool '{tool_name}' with args {arguments}"
                    )
        return True
