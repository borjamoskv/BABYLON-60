#!/usr/bin/env python3
"""
FAS v13 — Jurisprudence Drift Engine (Phase 2)
Reality level: C5-REAL
Aesthetics: Industrial Noir 2026

Ingests Case Seeds and computes the non-linear Jurisdictional Drift.
Detects institutional anomalies (like TEAC being more aggressive than AEAT)
and computes the momentum of legal reclassification.
"""

import json
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class JurisprudenceState:
    threshold_map: Dict[str, float]
    drift_vector: Dict[str, float]

class ReasoningGraphGenerator:
    """Builds the causal graph from observed events in case seeds."""
    def __init__(self):
        self.nodes = set()
        self.edges = []

    def ingest(self, case: Dict[str, Any]):
        jurisdiction = case["jurisdiction"]
        self.nodes.add(jurisdiction)
        
        # Link economic events to inference events
        for eco_event in case.get("events_economic", []):
            self.nodes.add(eco_event)
            for inf_event in case.get("events_inference", []):
                self.nodes.add(inf_event)
                # Weighted edge based on jurisdiction
                self.edges.append((eco_event, inf_event, jurisdiction))

class JurisprudenceStateEngine:
    """Computes the threshold drift and institutional bias from the graph."""
    
    def __init__(self):
        self.base_thresholds = {
            "AEAT": 0.70,
            "TEAC": 0.70,
            "TSJ-MAD": 0.75,
            "TSJ-PV": 0.75,
            "TS": 0.80,
            "TJUE": 0.85
        }

    def compute_state(self, cases: List[Dict[str, Any]]) -> JurisprudenceState:
        thresholds = self.base_thresholds.copy()
        drift = {
            "art13_lgt_strength": 0.0,
            "art16_lgt_expansion": 0.0,
            "donation_skepticism": 0.0,
            "burden_shift_intensity": 0.0
        }

        for case in cases:
            jur = case["jurisdiction"]
            sys_events = case.get("events_system", [])
            inf_events = case.get("events_inference", [])

            # Dynamic Threshold Mutation
            if "threshold_lowering_over_time" in sys_events:
                thresholds[jur] = max(0.50, thresholds.get(jur, 0.70) - 0.05)
            if "threshold_raising_over_time" in sys_events:
                thresholds[jur] = min(0.95, thresholds.get(jur, 0.70) + 0.05)
            if "institutional_bias_amplification" in sys_events:
                # TEAC specific anomaly: Bias amplification lowers their threshold of proof
                thresholds[jur] = max(0.40, thresholds.get(jur, 0.70) - 0.08)

            # Drift Vector Calculation
            if "economic_reality_over_form_applied" in inf_events:
                drift["art13_lgt_strength"] += 0.02
            if "simulated_contract_detected" in inf_events:
                drift["art16_lgt_expansion"] += 0.05
            if "donation_intent_rejected" in inf_events:
                drift["donation_skepticism"] += 0.04
            if "burden_shift_to_taxpayer" in inf_events:
                drift["burden_shift_intensity"] += 0.06
            if "insufficient_evidence_for_reclassification" in inf_events:
                drift["burden_shift_intensity"] -= 0.03
                drift["art13_lgt_strength"] -= 0.02

        # Round values
        for k, v in thresholds.items():
            thresholds[k] = round(v, 4)
        for k, v in drift.items():
            drift[k] = round(v, 4)

        return JurisprudenceState(threshold_map=thresholds, drift_vector=drift)

def run_phase2_demo():
    # Injecting the 5 known cases from Corpus Seed v1 (Cases 6-10)
    # In a real environment, this loads the full 10-case JSON.
    cases = [
        {
            "case_id": "TSJ-MAD-2024-11267", "jurisdiction": "TSJ-MAD",
            "events_inference": ["simulated_contract_detected", "economic_reality_over_form_applied", "burden_shift_to_taxpayer"],
            "events_system": ["jurisprudential_split_detected", "institutional_bias_amplification"]
        },
        {
            "case_id": "TEAC-2024-2023", "jurisdiction": "TEAC",
            "events_inference": ["donation_intent_rejected", "economic_reality_over_form_applied", "burden_shift_to_taxpayer"],
            "events_system": ["threshold_lowering_over_time", "institutional_bias_amplification"]
        },
        {
            "case_id": "TS-2024-DISCAPACIDAD", "jurisdiction": "TS",
            "events_inference": ["donation_intent_recognized", "insufficient_evidence_for_reclassification"],
            "events_system": ["threshold_raising_over_time"]
        },
        {
            "case_id": "TSJ-PV-2024-DONACION", "jurisdiction": "TSJ-PV",
            "events_inference": ["donation_intent_recognized", "insufficient_evidence_for_reclassification"],
            "events_system": ["threshold_raising_over_time"]
        },
        {
            "case_id": "TEAC-2024-03063", "jurisdiction": "TEAC",
            "events_inference": ["donation_intent_recognized", "burden_shift_to_taxpayer"],
            "events_system": ["institutional_bias_amplification"]
        }
    ]

    engine = JurisprudenceStateEngine()
    state = engine.compute_state(cases)

    print("=========================================================================")
    print("  FAS v13 : JURISPRUDENCE DRIFT ENGINE (PHASE 2)                         ")
    print("=========================================================================\n")
    print(">>> [JURISDICTIONAL THRESHOLD MAP] (Lower = Easier for AEAT to win)")
    print(json.dumps(state.threshold_map, indent=2))
    
    print("\n>>> [DOCTRINAL DRIFT VECTOR] (Momentum of State's inference powers)")
    print(json.dumps(state.drift_vector, indent=2))
    print("\n=========================================================================")

if __name__ == "__main__":
    run_phase2_demo()
