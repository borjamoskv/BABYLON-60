# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
tonnetz_monitor.py — Production Primitive for Tonnetz Harmonic Oversight Monitor

Implements the bi-modal audio oversight engine mapping Shannon Entropy H(T | C)
and Exergy Consumption Delta_Ex to Tonnetz Torus transformations under Art. 14 EU AI Act.
"""

import math
from typing import List, NamedTuple

PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


class TonnetzTelemetry(NamedTuple):
    state: str
    triad_notes: List[str]
    is_major: bool
    microtonal_cents_offset: float
    harmonic_tension: float
    eu_ai_act_status: str


def compute_shannon_entropy(probabilities: List[float]) -> float:
    """Compute Shannon entropy H(T | C) for a given discrete probability vector."""
    total = sum(probabilities)
    if total <= 0:
        return 0.0
    norm_probs = [p / total for p in probabilities if p > 0]
    return -sum(p * math.log2(p) for p in norm_probs)


def evaluate_tonnetz_oversight(entropy: float, exergy_consumption: float) -> TonnetzTelemetry:
    """
    Evaluate the Tonnetz oversight state given systemic entropy and exergy consumption.
    Enforces AX-TZ-1 (Homeostatic Triadic Compliance) and AX-TZ-2 (Dissonance Alert).
    """
    is_homeostatic = (entropy < 0.1) and (exergy_consumption < 0.1)

    if is_homeostatic:
        state = "HOMEOSTATIC_PURE"
        triad_notes = ["C", "E", "G"]
        is_major = True
        cents_offset = 0.0
        tension = 0.0
        status = "OVERSIGHT_ACTIVE_STABLE"
    else:
        state = "ANERGY_ALERT_DISSONANT" if (entropy > 1.0 or exergy_consumption > 1.0) else "DEGRADED_TRANSITION"
        # Shift triad Neo-Riemannian under tension
        triad_notes = ["D#", "F", "C"] if exergy_consumption > 1.0 else ["C", "D#", "G"]
        is_major = False
        cents_offset = min(100.0, entropy * 25.0 + exergy_consumption * 15.0)
        tension = min(1.0, (entropy + exergy_consumption) / 3.0)
        status = "OVERSIGHT_ALERT_TRIGGERED"

    return TonnetzTelemetry(
        state=state,
        triad_notes=triad_notes,
        is_major=is_major,
        microtonal_cents_offset=cents_offset,
        harmonic_tension=tension,
        eu_ai_act_status=status,
    )
