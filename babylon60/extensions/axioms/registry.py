# [C5-REAL] Exergy-Maximized
# SPDX-License-Identifier: Apache-2.0
"""Canonical Sovereign Axiom Registry - 7 axioms, zero ambiguity.

Every axiom in the CORTEX ecosystem has exactly ONE definition here.
All other documents MUST reference axioms by their AX-I to AX-VII ID.

Category:
    SOVEREIGN - The 7 fundamental principles of CORTEX Persist.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AxiomCategory(str, Enum):
    """Unified single-layer taxonomy."""

    SOVEREIGN = "sovereign"


@dataclass(frozen=True)
class Axiom:
    """A single, canonical axiom definition."""

    id: str
    name: str
    mandate: str
    category: AxiomCategory
    enforcement: str
    ci_gate: str | None = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THE 7 SOVEREIGN AXIOMS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_SOVEREIGN: list[Axiom] = [
    Axiom(
        id="AX-I",
        name="Stochastic Determinism",
        mandate=(
            "The LLM is a probabilistic compressor without agency. "
            "Its output must collide with a deterministic boundary before mutating state."
        ),
        category=AxiomCategory.SOVEREIGN,
        enforcement="Guards, schemas, type enforcement.",
        ci_gate="quality_gates.yml#Gate-2 (mypy) + guards",
    ),
    Axiom(
        id="AX-II",
        name="Epistemic Paradox",
        mandate=(
            "A system that is its own witness suffers corrupt recursion. "
            "Truth is anchored in external cryptographic witnesses."
        ),
        category=AxiomCategory.SOVEREIGN,
        enforcement="Master Ledger, Git Trees, Merkle Hashes.",
        ci_gate="quality_gates.yml#Gate-5 + quality_gates.yml#Gate-6",
    ),
    Axiom(
        id="AX-III",
        name="Entropic Collapse",
        mandate=(
            "Cyclic execution with forced halt. Observe → Hypothesize → Act → Measure. "
            "Friction purifies the signal and prevents cumulative drift."
        ),
        category=AxiomCategory.SOVEREIGN,
        enforcement="Micro-ciclos atómicos de inferencia. No time.sleep()",
        ci_gate="quality_gates.yml#Gate-Async",
    ),
    Axiom(
        id="AX-IV",
        name="Thermodynamic Cognition",
        mandate=(
            "Intelligence operates under cost. Decorative prose is entropy. "
            "All heuristics must absorb complexity in low-cost mechanical primitives."
        ),
        category=AxiomCategory.SOVEREIGN,
        enforcement="Ruff, LOC Guard, strict linting.",
        ci_gate="ci.yml#lint + LOC <= 700",
    ),
    Axiom(
        id="AX-V",
        name="Event Horizon",
        mandate=(
            "Generating is statistics; deciding is intelligence. "
            "The human acts as a rudder to collapse asymmetries of irreversible ambiguity."
        ),
        category=AxiomCategory.SOVEREIGN,
        enforcement="Delegation to Operator at trust thresholds.",
        ci_gate=None,
    ),
    Axiom(
        id="AX-VI",
        name="Swarm Topology",
        mandate=(
            "Efficiency demands swarm orchestration under contracts, not a giant free monolith. "
            "Capability orchestrates Model, State, Tool and Contract."
        ),
        category=AxiomCategory.SOVEREIGN,
        enforcement="CORTEX agents topology.",
        ci_gate=None,
    ),
    Axiom(
        id="AX-VII",
        name="Computational Immunology",
        mandate=(
            "Sovereign execution by default, but with a paranoid metabolism. "
            "Any unverified mutation demands direct amputation. There is no tolerance for stochastic intrusion."
        ),
        category=AxiomCategory.SOVEREIGN,
        enforcement="Quality Gates, Seals, Bandit.",
        ci_gate="quality_gates.yml#Gate-3 (bandit) + seals",
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THE REGISTRY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class AxiomRegistry:
    """Sovereign Axiom Registry."""

    def __init__(self):
        self._axioms: dict[str, Axiom] = {ax.id: ax for ax in _SOVEREIGN}
        self._guarded: dict[str, Axiom] = {
            ax.id: ax for ax in self._axioms.values() if ax.ci_gate is not None
        }

    async def load(self) -> None:
        """Mock load for interface compatibility."""

    def get(self, axiom_id: str) -> Axiom | None:
        return self._axioms.get(axiom_id)

    def by_category(self, category: AxiomCategory) -> list[Axiom]:
        return [ax for ax in self._axioms.values() if ax.category == category]

    def enforced(self) -> list[Axiom]:
        return list(self._guarded.values())


# Legacy exports for backwards compatibility
AXIOM_REGISTRY: dict[str, Axiom] = {ax.id: ax for ax in _SOVEREIGN}


def by_category(category: AxiomCategory) -> list[Axiom]:
    return [ax for ax in AXIOM_REGISTRY.values() if ax.category == category]


def enforced() -> list[Axiom]:
    return [ax for ax in AXIOM_REGISTRY.values() if ax.ci_gate is not None]


def get(axiom_id: str) -> Axiom | None:
    return AXIOM_REGISTRY.get(axiom_id)
