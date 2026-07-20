"""
compiled_theorem.py — Robinson-Anergy Transducer
=================================================
The compiled form of the Robinson Refutation applied to LLM thermodynamics.

Robinson (1965): If resolution saturates to the empty clause [],
    the original clause set is UNSATISFIABLE.

Isomorphism: If A(n) → threshold for n → ∞ without BFT ledger,
    the "intelligence" claim of the system is REFUTABLE.

This module provides the core metric computation as an importable library.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AnergyMeasurement:
    """Immutable measurement record — C5-REAL payload."""

    model_steps: int
    exergy_steps: int
    anergy_steps: int
    anergy_ratio: float
    exergy_ratio: float
    loop_count: int

    @property
    def is_refutable(self) -> bool:
        """Robinson criterion: A(n) > 0.85 ∧ n > 200 → refutable."""
        return self.anergy_ratio > 0.85 and self.model_steps > 200

    @property
    def robinson_clause(self) -> str:
        """Maps to resolution status."""
        if self.is_refutable:
            return "EMPTY_CLAUSE"  # Contradiction derived
        if self.anergy_ratio > 0.70:
            return "NEAR_SATURATION"
        return "SATISFIABLE"


def compute_anergy(
    model_steps: int,
    exergy_steps: int,
    loop_count: int = 0,
) -> AnergyMeasurement:
    """Pure function: compute anergy measurement from step counts."""
    anergy_steps = model_steps - exergy_steps
    ratio = 1.0 - (exergy_steps / model_steps) if model_steps > 0 else 0.0
    return AnergyMeasurement(
        model_steps=model_steps,
        exergy_steps=exergy_steps,
        anergy_steps=anergy_steps,
        anergy_ratio=round(ratio, 4),
        exergy_ratio=round(1.0 - ratio, 4),
        loop_count=loop_count,
    )


# Empirical data points — C5-REAL measurements from local transcripts
EMPIRICAL_LEDGER: list[dict[str, Any]] = [
    {"id": "f99a858c", "n": 507, "A": 0.8462, "clause": "NEAR_SATURATION"},
    {"id": "4e4c6b49", "n": 658, "A": 0.6505, "clause": "SATISFIABLE"},
    {"id": "f211008c", "n": 379, "A": 0.6939, "clause": "SATISFIABLE"},
    {"id": "d1a22586", "n": 166, "A": 0.7048, "clause": "NEAR_SATURATION"},
    {"id": "091f6802", "n": 117, "A": 0.8034, "clause": "NEAR_SATURATION"},
    {"id": "08bba3ea", "n": 50,  "A": 0.7000, "clause": "SATISFIABLE"},
    {"id": "34795b51", "n": 20,  "A": 1.0000, "clause": "EMPTY_CLAUSE"},
]
