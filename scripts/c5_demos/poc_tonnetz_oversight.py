#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
r"""
poc_tonnetz_oversight.py — Proof of Concept: Tonnetz Harmonic Oversight & Audio Engine

Demonstrates the Neo-Riemannian Tonnetz mapping for EU AI Act (Art. 14) Human Oversight:
1. Shannon Entropy H(T | C) & Exergy Consumption Delta_Ex telemetry computation.
2. Homeostatic Triadic Mapping (AX-TZ-1): Pure major triads under zero-anergy conditions.
3. Thermodynamic Degradation & Microtonal Dissonance (AX-TZ-2): Neo-Riemannian L, P, R 
   transformations and microtonal cent detuning under systemic instability.
"""

import math
import sys
from typing import Dict, List, Tuple

# Pitch names in 12-TET
PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Neo-Riemannian Transformations on 12-TET pitch class sets
def apply_p(triad: Tuple[int, int, int], is_major: bool) -> Tuple[Tuple[int, int, int], bool]:
    """Parallel transformation (P): C Major (0, 4, 7) <-> C Minor (0, 3, 7)."""
    root, third, fifth = triad
    if is_major:
        return (root, (third - 1) % 12, fifth), False
    else:
        return (root, (third + 1) % 12, fifth), True

def apply_l(triad: Tuple[int, int, int], is_major: bool) -> Tuple[Tuple[int, int, int], bool]:
    """Leittonwechsel transformation (L): C Major (0, 4, 7) <-> E Minor (4, 7, 11)."""
    root, third, fifth = triad
    if is_major:
        return (third, fifth, (root - 1) % 12), False
    else:
        return ((fifth + 1) % 12, root, third), True

def apply_r(triad: Tuple[int, int, int], is_major: bool) -> Tuple[Tuple[int, int, int], bool]:
    """Relative transformation (R): C Major (0, 4, 7) <-> A Minor (9, 0, 4)."""
    root, third, fifth = triad
    if is_major:
        return (fifth, (fifth + 2) % 12, third), False
    else:
        return (third, (root - 2) % 12, fifth), True


class TonnetzOversightEngine:
    """Bi-Modal Audio Oversight Engine mapping Shannon Entropy & Exergy to Tonnetz Space."""

    def __init__(self):
        # Base state: C Major Triad (0, 4, 7)
        self.current_triad = (0, 4, 7)
        self.is_major = True

    def calculate_shannon_entropy(self, execution_trace: List[float]) -> float:
        """Calculate Shannon entropy H(T | C) over discrete execution probability distribution."""
        total = sum(execution_trace)
        if total <= 0:
            return 0.0
        probs = [p / total for p in execution_trace if p > 0]
        return -sum(p * math.log2(p) for p in probs)

    def map_telemetry_to_tonnetz(
        self, entropy: float, exergy_consumption: float
    ) -> Dict[str, object]:
        """
        Map (entropy, exergy_consumption) to Tonnetz state & microtonal detuning.
        AX-TZ-1: Zero anergy -> Pure C Major Triad, 0 cents detuning.
        AX-TZ-2: High anergy -> Neo-Riemannian transformation & microtonal detuning (cents).
        """
        is_homeostatic = (entropy < 0.1) and (exergy_consumption < 0.1)
        
        if is_homeostatic:
            triad = (0, 4, 7)
            is_major = True
            microtonal_cents = 0.0
            tension = 0.0
            state = "HOMEOSTATIC_PURE"
        else:
            # Determine Neo-Riemannian path based on exergy level
            triad = self.current_triad
            is_major = self.is_major
            
            if exergy_consumption > 0.5:
                triad, is_major = apply_p(triad, is_major)
            if entropy > 1.0:
                triad, is_major = apply_l(triad, is_major)
            if exergy_consumption > 1.5:
                triad, is_major = apply_r(triad, is_major)
                
            # Microtonal detuning directly proportional to entropy divergence
            microtonal_cents = min(100.0, entropy * 25.0 + exergy_consumption * 15.0)
            tension = min(1.0, (entropy + exergy_consumption) / 3.0)
            state = "ANERGY_ALERT_DISSONANT" if tension > 0.4 else "DEGRADED_TRANSITION"

        notes = [PITCH_CLASSES[n] for n in triad]
        return {
            "state": state,
            "triad_pitch_classes": triad,
            "triad_notes": notes,
            "is_major": is_major,
            "microtonal_cents_offset": microtonal_cents,
            "harmonic_tension": tension,
            "eu_ai_act_art14_status": "OVERSIGHT_ACTIVE_STABLE" if is_homeostatic else "OVERSIGHT_ALERT_TRIGGERED"
        }


def run_proof_of_concept():
    print("============================================================================")
    print("BABYLON-60 v4.0 Sovereign Hardened — Tonnetz Audio Oversight PoC")
    print("============================================================================")

    engine = TonnetzOversightEngine()

    # Test Case 1: Ideal Homeostatic State (AX-TZ-1)
    trace_homeostatic = [1.0, 0.0, 0.0, 0.0]
    H_1 = engine.calculate_shannon_entropy(trace_homeostatic)
    Ex_1 = 0.02
    res_1 = engine.map_telemetry_to_tonnetz(H_1, Ex_1)

    print("\n--- [TEST 1: AX-TZ-1 Homeostatic Triadic Compliance] ---")
    print(f"Shannon Entropy H(T|C): {H_1:.4f} bits")
    print(f"Exergy Consumption Delta_Ex: {Ex_1:.4f}")
    print(f"Tonnetz State: {res_1['state']}")
    print(f"Triad Notes: {res_1['triad_notes']} (Major: {res_1['is_major']})")
    print(f"Microtonal Cent Offset: {res_1['microtonal_cents_offset']:.2f} cents")
    print(f"EU AI Act Art. 14 Status: {res_1['eu_ai_act_art14_status']}")
    
    assert res_1['state'] == "HOMEOSTATIC_PURE", "AX-TZ-1 Failure: State must be HOMEOSTATIC_PURE"
    assert res_1['microtonal_cents_offset'] == 0.0, "AX-TZ-1 Failure: Microtonal detuning must be 0"

    # Test Case 2: High Anergy & Entropic Degradation (AX-TZ-2)
    trace_degraded = [0.25, 0.25, 0.25, 0.25]
    H_2 = engine.calculate_shannon_entropy(trace_degraded)
    Ex_2 = 1.85
    res_2 = engine.map_telemetry_to_tonnetz(H_2, Ex_2)

    print("\n--- [TEST 2: AX-TZ-2 Thermodynamic Degradation & Disonance] ---")
    print(f"Shannon Entropy H(T|C): {H_2:.4f} bits")
    print(f"Exergy Consumption Delta_Ex: {Ex_2:.4f}")
    print(f"Tonnetz State: {res_2['state']}")
    print(f"Triad Notes: {res_2['triad_notes']} (Major: {res_2['is_major']})")
    print(f"Microtonal Cent Offset: {res_2['microtonal_cents_offset']:.2f} cents")
    print(f"EU AI Act Art. 14 Status: {res_2['eu_ai_act_art14_status']}")

    assert res_2['microtonal_cents_offset'] > 0.0, "AX-TZ-2 Failure: Microtonal detuning must trigger"
    assert res_2['eu_ai_act_art14_status'] == "OVERSIGHT_ALERT_TRIGGERED", "AX-TZ-2 Failure: Alert status required"

    print("\n[SUCCESS] Tonnetz Oversight Audio Engine PoC verified under AX-TZ-1 & AX-TZ-2!")
    print("============================================================================")


if __name__ == "__main__":
    run_proof_of_concept()
