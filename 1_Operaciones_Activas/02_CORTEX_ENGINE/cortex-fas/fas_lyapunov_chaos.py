#!/usr/bin/env python3
"""
FAS v17 — Lyapunov Proxy Layer (Doctrinal Chaos Engine)
Reality level: C5-REAL
Aesthetics: Industrial Noir 2026

Measures the sensitivity of the legal system to minimal perturbations (1 synthetic case).
λ > 0  → caos doctrinal (no predictible)
λ ≈ 0  → estabilidad estructural
λ < 0  → convergencia fuerte (dogma rígido)
"""

import copy
import numpy as np
from typing import List, Dict

from fas_phase2_core import JurisprudenceState, CaseNode, EconomicEvent, JudicialInference, Jurisdiction
from fas_energy_physics import JuridicalEnergyEngine, ExternalShockModel

class LyapunovProxyEngine:
    def __init__(self, base_state: JurisprudenceState):
        self.base_state = base_state
        self.shock_model = ExternalShockModel()
    
    def perturb_case(self, state: JurisprudenceState, epsilon_case: CaseNode) -> JurisprudenceState:
        """Injects minimal perturbation (1 synthetic case)."""
        state.case_history.append(epsilon_case)
        return state
    
    def run_dynamics(self, state: JurisprudenceState, tick: int = 1) -> float:
        """Runs the full system dynamics and returns E_total."""
        engine = JuridicalEnergyEngine(state, self.shock_model)
        return engine.compute(current_tick=tick).E_total
    
    def compute_lyapunov(self, epsilon_cases: List[CaseNode], steps: int = 10) -> float:
        """
        λ ≈ lim (t→∞) (1/t) log |ΔE(t)|
        """
        divergences = []
        
        for eps_case in epsilon_cases:
            # Base state
            state_0 = copy.deepcopy(self.base_state)
            E0 = self.run_dynamics(state_0, tick=1)
            
            # Perturbed state
            state_1 = copy.deepcopy(self.base_state)
            state_1 = self.perturb_case(state_1, eps_case)
            E1 = self.run_dynamics(state_1, tick=1)
            
            delta_0 = abs(E1 - E0)
            trajectory_divergence = []
            
            # Time evolution simulation
            for t in range(2, steps + 2):
                # Natural drift of the system
                state_0.drift_vector["art16_lgt_expansion"] *= 1.01
                state_1.drift_vector["art16_lgt_expansion"] *= 1.01
                
                E0_t = self.run_dynamics(state_0, tick=t)
                E1_t = self.run_dynamics(state_1, tick=t)
                
                delta_t = abs(E1_t - E0_t)
                trajectory_divergence.append(delta_t)
            
            # Lyapunov estimate
            if delta_0 == 0:
                continue
            
            growth = np.mean([
                np.log(max(d, 1e-9) / max(delta_0, 1e-9))
                for d in trajectory_divergence
            ])
            divergences.append(growth)
            
        return float(np.mean(divergences)) if divergences else 0.0

    def analyze_chaos(self, epsilon_cases: List[CaseNode]) -> Dict:
        lam = self.compute_lyapunov(epsilon_cases)
        
        if lam < 0:
            regime = "RIGID_DOGMA"
            risk = "LOW_DETERMINISTIC"
        elif lam <= 0.1:
            regime = "STRUCTURAL_STABILITY"
            risk = "LOW"
        elif lam <= 0.5:
            regime = "INTERPRETATIVE_DRIFT"
            risk = "MEDIUM_NONLINEARITY"
        elif lam <= 1.0:
            regime = "CHAOTIC_DOCTRINAL_SYSTEM"
            risk = "HIGH_NONLINEARITY"
        else:
            regime = "NON_IDENTITY_LAW"
            risk = "EXTREME_MUTATION"
            
        return {
            "lyapunov_lambda": round(lam, 4),
            "regime": regime,
            "interpretation": "small case changes amplify into regime shifts" if lam > 0.5 else "system absorbs perturbations",
            "risk_level": risk
        }

if __name__ == "__main__":
    import json
    from datetime import datetime
    
    # Mock Demo
    state = JurisprudenceState()
    # Baseline setup
    state.threshold_map = {Jurisdiction.AEAT: 0.71, Jurisdiction.TS: 0.59}
    
    # Synthetic perturbation case
    eps_case = CaseNode("EPS-1", Jurisdiction.TS, datetime.now(), "sentencia", 
                        events_economic=[EconomicEvent.PRICE_HIDDEN, EconomicEvent.PAYMENT_RECURRING],
                        events_inference=[JudicialInference.SIMULATION_DETECTED],
                        events_system=[])
                        
    lyapunov_engine = LyapunovProxyEngine(state)
    res = lyapunov_engine.analyze_chaos([eps_case])
    
    print("[CORTEX] DOCTRINAL CHAOS ENGINE (Lyapunov Proxy)")
    print(json.dumps(res, indent=2))
