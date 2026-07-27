#!/usr/bin/env python3
"""
FAS v20 — Regulatory Stress Test Engine (iHelp Case Study)
Reality level: C5-REAL
Aesthetics: Industrial Noir 2026

Models the system's sensitivity to reclassification under extreme assumption sets.
This is a synthetic adversarial compliance simulation.
It DOES NOT assert factual wrongdoing. It calculates the theoretical phase transition
vector of fiscal interpretation based on hardcoded rules.
"""

import sys
import os
import json
from datetime import datetime

# Adjust path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fas_phase2_core import (
    JurisprudenceState, CaseNode, EconomicEvent, JudicialInference, Jurisdiction, SystemStateEvent
)
from fas_digital_twin import DigitalTwinJurisprudentialEngine

def simulate_stress_test():
    # 1. Initialize Baseline System State
    state = JurisprudenceState()
    
    # 2. Assumption Lattice Configuration
    # We set strict enforcement assumptions to observe the collapse mechanics.
    state.drift_vector["art13_lgt_strength"] = 0.65
    state.drift_vector["donation_skepticism"] = 0.80
    
    # 3. Define the Structural Node (Synthetic Case)
    ihelp_stress_case = CaseNode(
        case_id="STRESS_TEST_IHELP_001",
        jurisdiction=Jurisdiction.AEAT, 
        date=datetime.now(),
        source_type="stress_simulation",
        events_economic=[
            EconomicEvent.PAYMENT_ONE_OFF,        
            EconomicEvent.TIGHT_COUPLING,         
            EconomicEvent.PRICE_HIDDEN            
        ],
        events_inference=[
            JudicialInference.CONTRAPRESTACION_CORRELATION, 
            JudicialInference.ECONOMIC_REALITY_OVER_FORM,
            JudicialInference.SIMULATION_DETECTED 
        ],
        events_system=[
            SystemStateEvent.HIGH_CONFIDENCE_RECLASS
        ],
        fragments_facts=[
            "Donation structurally tied to 100% equivalent service discount."
        ],
        fragments_law=["Art. 13 LGT", "Art. 16 Ley 49/2002"],
        fragments_decision=[],
        notes_why_important="Models extreme correlation hypothesis",
        notes_threshold_signal="Testing threshold limit of 15% counter-prestation rule.",
        notes_divergence_signal=""
    )
    
    state.update_from_case(ihelp_stress_case)
    
    # 4. Engine Dynamics
    twin = DigitalTwinJurisprudentialEngine(state)
    analysis = twin.analyze_full()
    
    reclassification_likelihood = min((analysis["energy"]["E_total"] * 1.5) + (state.drift_vector["donation_skepticism"] * 0.5), 0.99)
    
    # 5. Output reframed as Physics of Law (not legal judgement)
    report = {
        "system": "CORTEX-FAS v6 (Digital Twin)",
        "mode": "adversarial stress simulation",
        "epistemic_status": "counterfactual_simulation_only",
        "case_topology": "iHelp-like donation + discount coupling",
        "assumption_lattice": [
            "100% contraprestation equivalence treated as linear correlation",
            "Art. 16 Ley 49/2002 strict threshold enforcement applied",
            "Zero de minimis tolerance modeled",
            "AEAT agent mapped as maximal correlation seeker"
        ],
        "simulation_output": {
            "regime_shift_model_score": round(reclassification_likelihood, 4),
            "system_energy_spike": analysis["energy"]["E_total"],
            "lyapunov_lambda_baseline": analysis["lyapunov"]["lambda"],
            "primary_sensitivity_axis": "DONORS (Declarantes IRPF)",
            "secondary_sensitivity_axis": "NETWORK_PROMOTER",
            "regime_signal": "Threshold overflow detected under strict assumptions.",
            "interpretation": "High sensitivity to reclassification rules detected under current state assumptions",
            "dominant_driver": "Art16_threshold_constraint",
            "note": "Result is conditional on rule strictness assumptions, NOT a legal prediction or assertion of factual wrongdoing."
        }
    }
    
    output_path = os.path.join(os.path.dirname(__file__), "ihelp_stress_test.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"[CORTEX] STRESS TEST COMPLETED. Report saved to {output_path}")
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    simulate_stress_test()
