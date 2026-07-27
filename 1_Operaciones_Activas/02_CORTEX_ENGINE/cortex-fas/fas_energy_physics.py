#!/usr/bin/env python3
"""
FAS v14 — Juridical Energy Engine (JEF v1) + Shock Dynamics
Reality level: C5-REAL
Aesthetics: Industrial Noir 2026

Computes the physical energy of the legal system:
E(system) = E_corr + E_thresh + E_entropy + E_conflict + E_shock

Added Option A: External Shock Model & Stability Duration.
"""

import numpy as np
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from fas_phase2_core import (
    JurisprudenceState, JudicialInference, EconomicEvent, ReasoningGraphGenerator,
    CaseNode, Jurisdiction, SystemStateEvent
)

# ============================================================
# 1. ENERGY COMPONENTS (definición física)
# ============================================================

@dataclass
class EnergyComponents:
    E_correlation: float
    E_threshold: float
    E_entropy: float
    E_conflict: float
    E_shock: float            # Nueva componente: External Shock
    E_total: float

class Regime(Enum):
    STABLE_FORMALISM = "STABLE_FORMALISM"           # E < 0.3
    INTERPRETATIVE_DRIFT = "INTERPRETATIVE_DRIFT"   # 0.3 < E < 0.6
    DOCTRINAL_TENSION = "DOCTRINAL_TENSION"         # 0.6 < E < 0.8
    PHASE_TRANSITION = "PHASE_TRANSITION"           # E > 0.8

class PhaseTransition(Enum):
    NONE = "NONE"
    WARNING = "PHASE_TRANSITION_WARNING"
    CRITICAL = "PHASE_TRANSITION_CRITICAL"
    SHIFT = "DOCTRINAL_SHIFT_DETECTED"

def clamp(x: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, x))

# ============================================================
# 2. EXTERNAL SHOCK MODEL (Option A Extension)
# ============================================================

class ShockType(Enum):
    LEGISLATIVE_OVERRIDE = "LEGISLATIVE_OVERRIDE"
    TJUE_PREJUDICIAL = "TJUE_PREJUDICIAL"
    TS_UNIFICATION = "TS_UNIFICATION"

@dataclass
class ExternalShock:
    type: ShockType
    magnitude: float  # 0.0 to 1.0
    target_jurisdictions: List[Jurisdiction]
    timestamp: int # case index

class ExternalShockModel:
    """Modela impactos exógenos que rompen la inercia del sistema."""
    def __init__(self):
        self.active_shocks: List[ExternalShock] = []
        
    def inject_shock(self, shock: ExternalShock):
        self.active_shocks.append(shock)
        
    def get_current_shock_energy(self, current_tick: int) -> float:
        """Decay exponencial del shock a lo largo del tiempo (casos)."""
        total_shock = 0.0
        for shock in self.active_shocks:
            time_since = current_tick - shock.timestamp
            if time_since >= 0:
                decay = math.exp(-0.2 * time_since) # Decay rate
                total_shock += shock.magnitude * decay
        return clamp(total_shock, 0.0, 1.0)

# ============================================================
# 3. JURIDICAL ENERGY ENGINE
# ============================================================

class JuridicalEnergyEngine:
    WEIGHTS = {
        "correlation": 0.25,
        "threshold": 0.20,
        "entropy": 0.15,
        "conflict": 0.20,
        "shock": 0.20  # Added shock weight
    }
    
    def __init__(self, state: JurisprudenceState, shock_model: ExternalShockModel):
        self.state = state
        self.shock_model = shock_model
    
    def compute(self, current_tick: int) -> EnergyComponents:
        E_corr = self.correlation_energy()
        E_thresh = self.threshold_variance()
        E_entropy = self.doctrinal_entropy()
        E_conflict = self.precedent_friction()
        E_shock = self.shock_model.get_current_shock_energy(current_tick)
        
        E_total = (
            self.WEIGHTS["correlation"] * E_corr +
            self.WEIGHTS["threshold"] * E_thresh +
            self.WEIGHTS["entropy"] * E_entropy +
            self.WEIGHTS["conflict"] * E_conflict +
            self.WEIGHTS["shock"] * E_shock
        )
        
        return EnergyComponents(
            E_correlation=round(E_corr, 4),
            E_threshold=round(E_thresh, 4),
            E_entropy=round(E_entropy, 4),
            E_conflict=round(E_conflict, 4),
            E_shock=round(E_shock, 4),
            E_total=round(E_total, 4)
        )
    
    def correlation_energy(self) -> float:
        if len(self.state.case_history) == 0: return 0.0
        total = 0.0
        correlation_inferences = [
            JudicialInference.CONTRAPRESTACION_CORRELATION,
            JudicialInference.SIMULATION_DETECTED,
            JudicialInference.DONATION_INTENT_REJECTED
        ]
        correlation_boosters = [
            EconomicEvent.PAYMENT_FIXED, EconomicEvent.PAYMENT_RECURRING,
            EconomicEvent.TIGHT_COUPLING, EconomicEvent.HIGH_HOMOGENEITY,
            EconomicEvent.PRICE_MARKET_ALIGNED
        ]
        
        for case in self.state.case_history:
            strength = 0.0
            for inference in case.events_inference:
                if inference in correlation_inferences:
                    rule = ReasoningGraphGenerator.INFERENCE_RULES.get(inference)
                    if rule: strength += rule["strength_base"] * 0.3
            for booster in correlation_boosters:
                if booster in case.events_economic: strength += 0.05
            total += strength
        
        E_corr = total / len(self.state.case_history)
        E_corr *= (1.0 + self.state.drift_vector.get("art13_lgt_strength", 0.0))
        return clamp(E_corr, 0.0, 1.0)
    
    def threshold_variance(self) -> float:
        thresholds = list(self.state.threshold_map.values())
        if len(thresholds) < 2: return 0.0
        variance = np.var(thresholds)
        max_variance = 0.06
        E_thresh = variance / max_variance
        return clamp(E_thresh, 0.0, 1.0)
    
    def doctrinal_entropy(self) -> float:
        if len(self.state.case_history) == 0: return 0.0
        inference_counts: Dict[JudicialInference, int] = {}
        for case in self.state.case_history:
            for inference in case.events_inference:
                inference_counts[inference] = inference_counts.get(inference, 0) + 1
        
        total_inferences = sum(inference_counts.values())
        if total_inferences == 0: return 0.0
        
        entropy = 0.0
        for count in inference_counts.values():
            p = count / total_inferences
            if p > 0: entropy -= p * math.log(p)
        
        max_entropy = math.log(len(JudicialInference.__members__))
        E_entropy = entropy / max_entropy if max_entropy > 0 else 0
        return clamp(E_entropy, 0.0, 1.0)
    
    def precedent_friction(self) -> float:
        if len(self.state.case_history) < 2: return 0.0
        conflict_points = 0.0
        narrowing_inferences = [JudicialInference.PRECEDENT_NARROWED, JudicialInference.PRECEDENT_DISTINGUISHED]
        
        for i, case in enumerate(self.state.case_history[1:], 1):
            prev_case = self.state.case_history[i - 1]
            if any(inv in narrowing_inferences for inv in case.events_inference):
                prev_main = self.get_main_inference(prev_case)
                curr_main = self.get_main_inference(case)
                conflict_points += 0.15 if prev_main != curr_main else 0.05
        
        E_conflict = conflict_points / len(self.state.case_history)
        E_conflict *= (1.0 + self.state.drift_vector.get("art16_lgt_expansion", 0.0))
        return clamp(E_conflict, 0.0, 1.0)
    
    def get_main_inference(self, case: CaseNode) -> JudicialInference:
        priority = [
            JudicialInference.CONTRAPRESTACION_CORRELATION, JudicialInference.SIMULATION_DETECTED,
            JudicialInference.DONATION_INTENT_RECOGNIZED, JudicialInference.DONATION_INTENT_REJECTED
        ]
        for inv in priority:
            if inv in case.events_inference: return inv
        return case.events_inference[0] if case.events_inference else JudicialInference.FORMAL_STRUCTURE_UPHELD

# ============================================================
# 4. PHASE TRANSITION DETECTOR
# ============================================================

class PhaseTransitionDetector:
    def __init__(self, energy_engine: JuridicalEnergyEngine):
        self.engine = energy_engine
        self.energy_history: List[float] = []
        self.regime_history: List[Regime] = []
        self.current_stability_duration = 0
    
    def update_stability(self, current_regime: Regime):
        if not self.regime_history:
            self.regime_history.append(current_regime)
            self.current_stability_duration = 1
        elif self.regime_history[-1] == current_regime:
            self.current_stability_duration += 1
        else:
            self.regime_history.append(current_regime)
            self.current_stability_duration = 1
            
    def detect(self, current_tick: int) -> PhaseTransition:
        E_total = self.engine.compute(current_tick).E_total
        self.energy_history.append(E_total)
        
        if len(self.energy_history) < 3:
            return PhaseTransition.NONE
        
        dE_dt = self.energy_history[-1] - self.energy_history[-3]
        
        if dE_dt > 0.15: return PhaseTransition.CRITICAL
        elif dE_dt > 0.08: return PhaseTransition.WARNING
        else: return PhaseTransition.NONE
    
    def predict_shift(self) -> Dict[str, float]:
        drift = self.engine.state.drift_vector
        likelihood = {
            "shift_to_correlation": max(0.0, drift.get("art13_lgt_strength", 0.0)),
            "shift_to_simulation": max(0.0, drift.get("art16_lgt_expansion", 0.0)),
            "shift_to_donation_protection": max(0.0, drift.get("donation_skepticism", 0.0) * -1)
        }
        total = sum(likelihood.values())
        return {k: round(v / total, 4) for k, v in likelihood.items()} if total > 0 else likelihood

class AttractorType(Enum):
    CORRELATION_REGIME = "correlation_regime"      
    SIMULATION_REGIME = "simulation_regime"        
    DONATION_PROTECTION = "donation_protection"    

class AttractorMapping:
    def identify(self, state: JurisprudenceState) -> Tuple[AttractorType, float]:
        counts = {AttractorType.CORRELATION_REGIME: 0, AttractorType.SIMULATION_REGIME: 0, AttractorType.DONATION_PROTECTION: 0}
        for case in state.case_history:
            for inference in case.events_inference:
                if inference == JudicialInference.CONTRAPRESTACION_CORRELATION: counts[AttractorType.CORRELATION_REGIME] += 1
                elif inference == JudicialInference.SIMULATION_DETECTED: counts[AttractorType.SIMULATION_REGIME] += 1
                elif inference in [JudicialInference.DONATION_INTENT_RECOGNIZED, JudicialInference.CONTRAPRESTACION_AMBIGUITY]: counts[AttractorType.DONATION_PROTECTION] += 1
        total = sum(counts.values())
        if total == 0: return (AttractorType.CORRELATION_REGIME, 0.5)
        dominant = max(counts.keys(), key=lambda k: counts[k])
        return (dominant, round(counts[dominant] / total, 4))

# ============================================================
# 5. API WRAPPER
# ============================================================

class JuridicalPhysicsEngine:
    def __init__(self, state: JurisprudenceState):
        self.state = state
        self.shock_model = ExternalShockModel()
        self.energy_engine = JuridicalEnergyEngine(state, self.shock_model)
        self.transition_detector = PhaseTransitionDetector(self.energy_engine)
        self.attractor_mapper = AttractorMapping()
        self.current_tick = 0
        
    def inject_shock(self, shock: ExternalShock):
        self.shock_model.inject_shock(shock)
    
    def analyze(self) -> Dict:
        self.current_tick += 1
        energy = self.energy_engine.compute(self.current_tick)
        regime = self.classify_regime(energy.E_total)
        self.transition_detector.update_stability(regime)
        transition = self.transition_detector.detect(self.current_tick)
        shift_likelihood = self.transition_detector.predict_shift()
        attractor, strength = self.attractor_mapper.identify(self.state)
        
        return {
            "energy": energy.__dict__,
            "regime": regime.value,
            "regime_stability_duration": self.transition_detector.current_stability_duration,
            "phase_transition": transition.value,
            "next_shift_likelihood": shift_likelihood,
            "dominant_attractor": attractor.value,
            "attractor_strength": strength,
            "threshold_map": {k.value: round(v, 4) for k, v in self.state.threshold_map.items()},
            "drift_vector": {k: round(v, 4) for k, v in self.state.drift_vector.items()},
            "case_count": len(self.state.case_history)
        }
    
    def classify_regime(self, E: float) -> Regime:
        if E < 0.3: return Regime.STABLE_FORMALISM
        elif E < 0.6: return Regime.INTERPRETATIVE_DRIFT
        elif E < 0.8: return Regime.DOCTRINAL_TENSION
        else: return Regime.PHASE_TRANSITION

# ============================================================
# DEMO EXECUTION
# ============================================================

if __name__ == "__main__":
    import json
    from datetime import datetime
    
    # Simulating the 10 cases injected previously (Mock objects to satisfy internal structure)
    state = JurisprudenceState()
    
    # Pre-populate state to simulate the outcome of the 10 real cases
    state.threshold_map = {
        Jurisdiction.AEAT: 0.71, Jurisdiction.TEAC: 0.77, Jurisdiction.TSJ_CAT: 0.65,
        Jurisdiction.TSJ_MAD: 0.65, Jurisdiction.TSJ_PV: 0.56, Jurisdiction.TS: 0.59,
        Jurisdiction.TJUE: 0.50
    }
    state.drift_vector = {
        "art13_lgt_strength": 0.08, "art16_lgt_expansion": 0.15,
        "donation_skepticism": 0.22, "burden_shift_intensity": 0.18
    }
    
    # Adding mock cases to satisfy the counts
    for i in range(10):
        c = CaseNode(f"CASE-{i}", Jurisdiction.TS, datetime.now(), "sentencia", 
                     events_economic=[EconomicEvent.PAYMENT_FIXED, EconomicEvent.HIGH_HOMOGENEITY],
                     events_inference=[JudicialInference.CONTRAPRESTACION_CORRELATION],
                     events_system=[])
        state.case_history.append(c)

    physics = JuridicalPhysicsEngine(state)
    
    print("=========================================================================")
    print("  FAS v14 : JURIDICAL ENERGY ENGINE (JEF v1) + EXTERNAL SHOCKS           ")
    print("=========================================================================\n")
    
    print(">>> TICK 10: BASE STATE (Interpretative Drift)")
    print(json.dumps(physics.analyze(), indent=2))
    
    print("\n" + "-"*73 + "\n")
    
    print(">>> TICK 11: SHOCK INJECTION (TJUE rules against AEAT systemic reclassifications)")
    shock = ExternalShock(ShockType.TJUE_PREJUDICIAL, magnitude=0.85, target_jurisdictions=[Jurisdiction.TS, Jurisdiction.TEAC], timestamp=physics.current_tick)
    physics.inject_shock(shock)
    
    print(json.dumps(physics.analyze(), indent=2))
    print("\n=========================================================================")
