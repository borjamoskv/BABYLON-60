#!/usr/bin/env python3
"""
FAS v18 — Digital Twin Jurisprudential Engine
Reality level: C5-REAL
Aesthetics: Industrial Noir 2026

Integration of JEF + Shocks + Attractors + Lyapunov Proxy.
"""

import copy
import numpy as np
import warnings
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

from fas_phase2_core import (
    JurisprudenceState, CaseNode, EconomicEvent, JudicialInference, Jurisdiction, SystemStateEvent
)
from fas_energy_physics import JuridicalEnergyEngine, PhaseTransitionDetector, AttractorMapping, ExternalShockModel
from fas_backtesting_engine import ExternalShockField, BacktestingEngine

# ============================================================
# 1. LYAPUNOV CLASSIFICATION
# ============================================================

class LyapunovRegime(Enum):
    RIGID_DOGMA = "RIGID_DOGMA"          
    STRUCTURAL_STABILITY = "STRUCTURAL_STABILITY"  
    INTERPRETATIVE_DRIFT = "INTERPRETATIVE_DRIFT"  
    CHAOTIC_DOCTRINAL = "CHAOTIC_DOCTRINAL"  
    NON_IDENTITY = "NON_IDENTITY"  

@dataclass
class LyapunovResult:
    lambda_value: float
    regime: LyapunovRegime
    interpretation: str
    risk_level: str
    flip_probability: float
    dominant_sensitivity: str

# ============================================================
# 2. LYAPUNOV PROXY ENGINE
# ============================================================

class LyapunovProxyEngine:
    DOMAIN_SENSITIVITY = {
        "art13": 1.2,  
        "art16": 1.4,  
        "donation": 0.9,  
        "burden": 1.1,  
        "global": 1.0
    }
    
    def __init__(self, base_state: JurisprudenceState):
        self.base_state = base_state
        self.shock_model = ExternalShockModel()
    
    def perturb_case(self, state: JurisprudenceState, epsilon_case: CaseNode) -> JurisprudenceState:
        state.case_history.append(epsilon_case)
        state.update_from_case(epsilon_case)
        return state
    
    def run_dynamics(self, state: JurisprudenceState) -> float:
        engine = JuridicalEnergyEngine(state, self.shock_model)
        return engine.compute(current_tick=len(state.case_history)).E_total
    
    def create_epsilon_case(self, perturbation_type: str = "correlation", intensity: float = 0.05) -> CaseNode:
        from datetime import datetime
        if perturbation_type == "correlation":
            events_economic = [EconomicEvent.PAYMENT_FIXED, EconomicEvent.TIGHT_COUPLING, EconomicEvent.HIGH_HOMOGENEITY]
            events_inference = [JudicialInference.CONTRAPRESTACION_CORRELATION, JudicialInference.BURDEN_SHIFT]
            events_system = [SystemStateEvent.THRESHOLD_LOWER, SystemStateEvent.INSTITUTIONAL_BIAS]
        elif perturbation_type == "simulation":
            events_economic = [EconomicEvent.PAYMENT_RECURRING, EconomicEvent.PRICE_HIDDEN]
            events_inference = [JudicialInference.SIMULATION_DETECTED, JudicialInference.ECONOMIC_REALITY_OVER_FORM]
            events_system = [SystemStateEvent.DOCTRINAL_DRIFT, SystemStateEvent.HIGH_CONFIDENCE_RECLASS]
        elif perturbation_type == "donation":
            events_economic = [EconomicEvent.PAYMENT_ONE_OFF, EconomicEvent.ACCESS_INDEPENDENT]
            events_inference = [JudicialInference.DONATION_INTENT_RECOGNIZED, JudicialInference.INSUFFICIENT_EVIDENCE]
            events_system = [SystemStateEvent.THRESHOLD_RAISE]
        else:  
            events_economic = [EconomicEvent.PAYMENT_FIXED, EconomicEvent.LOOSE_COUPLING]
            events_inference = [JudicialInference.BURDEN_SHIFT, JudicialInference.PRECEDENT_STRENGTHENED]
            events_system = [SystemStateEvent.INSTITUTIONAL_BIAS]
        
        return CaseNode(
            case_id=f"EPSILON-{perturbation_type}-{intensity}",
            jurisdiction=Jurisdiction.TS,  
            date=datetime.now(),
            source_type="sintético",
            events_economic=events_economic,
            events_inference=events_inference,
            events_system=events_system,
            fragments_facts=[],
            fragments_law=[],
            fragments_decision=[],
            notes_why_important=f"Caso sintético: {perturbation_type} intensity={intensity}",
            notes_threshold_signal="",
            notes_divergence_signal=""
        )
    
    def compute_lyapunov(self, epsilon_cases: List[CaseNode] = None, steps: int = 10, epsilon_intensity: float = 0.05) -> LyapunovResult:
        if epsilon_cases is None:
            epsilon_cases = [
                self.create_epsilon_case("correlation", epsilon_intensity),
                self.create_epsilon_case("simulation", epsilon_intensity),
                self.create_epsilon_case("donation", epsilon_intensity),
                self.create_epsilon_case("burden", epsilon_intensity)
            ]
        
        divergences = []
        sensitivity_by_domain = {}
        
        for eps_case in epsilon_cases:
            perturbation_type = eps_case.notes_why_important.split(":")[1].split()[0].strip()
            
            state_0 = copy.deepcopy(self.base_state)
            E0_initial = self.run_dynamics(state_0)
            
            state_1 = copy.deepcopy(self.base_state)
            state_1 = self.perturb_case(state_1, eps_case)
            E1_initial = self.run_dynamics(state_1)
            
            delta_0 = abs(E1_initial - E0_initial)
            
            if delta_0 == 0:
                continue
            
            trajectory_divergence = []
            
            for t in range(1, steps + 1):
                state_0.drift_vector["art16_lgt_expansion"] *= 1.01
                state_0.drift_vector["art13_lgt_strength"] *= 1.005
                state_0.drift_vector["donation_skepticism"] *= 1.008
                
                state_1.drift_vector["art16_lgt_expansion"] *= 1.01
                state_1.drift_vector["art13_lgt_strength"] *= 1.005
                state_1.drift_vector["donation_skepticism"] *= 1.008
                
                sensitivity = self.DOMAIN_SENSITIVITY.get(perturbation_type, 1.0)
                if perturbation_type == "correlation":
                    state_1.drift_vector["art13_lgt_strength"] *= (1.002 * sensitivity)
                elif perturbation_type == "simulation":
                    state_1.drift_vector["art16_lgt_expansion"] *= (1.003 * sensitivity)
                elif perturbation_type == "donation":
                    state_1.drift_vector["donation_skepticism"] *= (1.001 * sensitivity)
                
                E0_t = self.run_dynamics(state_0)
                E1_t = self.run_dynamics(state_1)
                
                delta_t = abs(E1_t - E0_t)
                trajectory_divergence.append(delta_t)
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                log_ratios = [np.log(max(d, 1e-9) / delta_0) for d in trajectory_divergence]
            
            growth = np.mean(log_ratios) / steps
            divergences.append(growth)
            sensitivity_by_domain[perturbation_type] = growth
        
        lambda_value = float(np.mean(divergences)) if divergences else 0.0
        regime = self.classify_regime(lambda_value)
        interpretation = self.get_interpretation(lambda_value, regime)
        risk_level = self.get_risk_level(lambda_value, regime)
        flip_probability = self.compute_flip_probability(lambda_value, regime)
        dominant_sensitivity = max(sensitivity_by_domain.keys(), key=lambda k: sensitivity_by_domain.get(k, 0.0)) if sensitivity_by_domain else "unknown"
        
        return LyapunovResult(lambda_value, regime, interpretation, risk_level, flip_probability, dominant_sensitivity)
    
    def classify_regime(self, lambda_value: float) -> LyapunovRegime:
        if lambda_value < -0.1: return LyapunovRegime.RIGID_DOGMA
        elif lambda_value < 0.1: return LyapunovRegime.STRUCTURAL_STABILITY
        elif lambda_value < 0.5: return LyapunovRegime.INTERPRETATIVE_DRIFT
        elif lambda_value < 1.0: return LyapunovRegime.CHAOTIC_DOCTRINAL
        else: return LyapunovRegime.NON_IDENTITY
    
    def get_interpretation(self, lambda_value: float, regime: LyapunovRegime) -> str:
        interpretations = {
            LyapunovRegime.RIGID_DOGMA: "Derecho codificado (baja interpretación, dogma rígido)",
            LyapunovRegime.STRUCTURAL_STABILITY: "Sistema estable (jurisprudencia consistente, predecible)",
            LyapunovRegime.INTERPRETATIVE_DRIFT: "Drift interpretativo (pequeños cambios se amplifican lentamente)",
            LyapunovRegime.CHAOTIC_DOCTRINAL: "Caos doctrinal (sistema no predictible, micro-decisiones cambian futuro)",
            LyapunovRegime.NON_IDENTITY: "Derecho no-identitario (mutación constante, significado inestable)"
        }
        return interpretations.get(regime, "Unknown")
    
    def get_risk_level(self, lambda_value: float, regime: LyapunovRegime) -> str:
        if regime in [LyapunovRegime.RIGID_DOGMA, LyapunovRegime.STRUCTURAL_STABILITY]: return "LOW"
        elif regime == LyapunovRegime.INTERPRETATIVE_DRIFT: return "MODERATE"
        elif regime == LyapunovRegime.CHAOTIC_DOCTRINAL: return "HIGH_NONLINEARITY"
        else: return "CRITICAL_UNPREDICTABLE"
    
    def compute_flip_probability(self, lambda_value: float, regime: LyapunovRegime) -> float:
        if regime == LyapunovRegime.RIGID_DOGMA: return 0.02
        elif regime == LyapunovRegime.STRUCTURAL_STABILITY: return 0.08
        elif regime == LyapunovRegime.INTERPRETATIVE_DRIFT: return 0.35 + (lambda_value - 0.1) * 0.5
        elif regime == LyapunovRegime.CHAOTIC_DOCTRINAL: return 0.65 + (lambda_value - 0.5) * 0.5
        else: return 0.90

# ============================================================
# 3. INTEGRACIÓN COMPLETA (DIGITAL TWIN)
# ============================================================

class DigitalTwinJurisprudentialEngine:
    def __init__(self, state: JurisprudenceState):
        self.state = state
        self.shock_model = ExternalShockModel()
        self.energy_engine = JuridicalEnergyEngine(state, self.shock_model)
        self.transition_detector = PhaseTransitionDetector(self.energy_engine)
        self.attractor_mapper = AttractorMapping()
        self.shock_field = ExternalShockField(state, self.energy_engine)
        self.lyapunov_engine = LyapunovProxyEngine(state)
        self.backtester = BacktestingEngine(self.shock_field)
    
    def analyze_full(self) -> Dict:
        from fas_energy_physics import JuridicalPhysicsEngine
        physics = JuridicalPhysicsEngine(self.state)
        energy_analysis = physics.analyze()
        
        lyapunov_result = self.lyapunov_engine.compute_lyapunov()
        
        full_analysis = {
            "energy": energy_analysis["energy"],
            "regime": energy_analysis["regime"],
            "phase_transition": energy_analysis["phase_transition"],
            "attractor": energy_analysis["dominant_attractor"],
            "attractor_strength": energy_analysis["attractor_strength"],
            "lyapunov": {
                "lambda": round(lyapunov_result.lambda_value, 4),
                "chaos_regime": lyapunov_result.regime.value,
                "interpretation": lyapunov_result.interpretation,
                "risk_level": lyapunov_result.risk_level,
                "flip_probability": round(lyapunov_result.flip_probability, 4),
                "dominant_sensitivity": lyapunov_result.dominant_sensitivity
            },
            "drift_vector": energy_analysis["drift_vector"],
            "threshold_map": energy_analysis["threshold_map"],
            "case_count": energy_analysis["case_count"]
        }
        
        return full_analysis

if __name__ == "__main__":
    import json
    
    state = JurisprudenceState()
    engine = DigitalTwinJurisprudentialEngine(state)
    analysis = engine.analyze_full()
    
    print("[CORTEX] DIGITAL TWIN INITIALIZED.")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
