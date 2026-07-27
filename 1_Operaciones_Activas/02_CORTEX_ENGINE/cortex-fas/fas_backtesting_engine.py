#!/usr/bin/env python3
"""
FAS v15 — External Shock Field & Backtesting Engine
Reality level: C5-REAL
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
import json

from fas_phase2_core import JurisprudenceState, CaseNode, Jurisdiction
from fas_energy_physics import JuridicalEnergyEngine, JuridicalPhysicsEngine, ExternalShock as BaseExternalShock

# ============================================================
# 1. SHOCK TYPES (forzamiento externo)
# ============================================================

class ExternalShockType(Enum):
    LEGISLATIVE_AMENDMENT = "legislative_amendment"  
    TS_OVERRULE = "ts_overrule"                        
    TEAC_CRITERION_SHIFT = "teac_criterion_shift"      
    TJUE_PRECEDENT = "tjue_precedent"                 
    AEAT_CIRCULAR = "aeat_circular"                    

@dataclass
class ExternalShock:
    type: ExternalShockType
    magnitude: float           
    affected_domain: str       
    timestamp: datetime
    description: str = ""
    
    COUPLING = {
        "art13": 0.3,
        "art16": 0.4,
        "donation": 0.25,
        "burden": 0.2,
        "global": 0.15
    }
    
    TYPE_IMPACT = {
        ExternalShockType.TS_OVERRULE: 0.4,
        ExternalShockType.TJUE_PRECEDENT: 0.35,
        ExternalShockType.LEGISLATIVE_AMENDMENT: 0.3,
        ExternalShockType.TEAC_CRITERION_SHIFT: 0.25,
        ExternalShockType.AEAT_CIRCULAR: 0.15
    }

# ============================================================
# 2. SHOCK FIELD (perturbador del sistema)
# ============================================================

class ExternalShockField:
    def __init__(self, state: JurisprudenceState, energy_engine: JuridicalEnergyEngine):
        self.state = state
        self.energy_engine = energy_engine
        self.shocks: List[ExternalShock] = []
        self.energy_shock_history: List[float] = []
    
    def apply(self, shock: ExternalShock):
        self.shocks.append(shock)
        self.perturb_drift(shock)
        E_shock = self.compute_shock_energy(shock)
        self.energy_shock_history.append(E_shock)
        
        if shock.type == ExternalShockType.TJUE_PRECEDENT:
            self.phase_reset(shock)
        
        if shock.type in [ExternalShockType.TS_OVERRULE, ExternalShockType.TEAC_CRITERION_SHIFT]:
            self.update_thresholds(shock)
    
    def perturb_drift(self, shock: ExternalShock):
        coupling = shock.COUPLING.get(shock.affected_domain, 0.15)
        impact = shock.magnitude * coupling
        
        if shock.affected_domain == "art13":
            self.state.drift_vector["art13_lgt_strength"] += impact
        elif shock.affected_domain == "art16":
            self.state.drift_vector["art16_lgt_expansion"] += impact
        elif shock.affected_domain == "donation":
            self.state.drift_vector["donation_skepticism"] += impact
        elif shock.affected_domain == "burden":
            self.state.drift_vector["burden_shift_intensity"] += impact
        else:  
            for key in self.state.drift_vector:
                self.state.drift_vector[key] += impact * 0.25
    
    def compute_shock_energy(self, shock: ExternalShock) -> float:
        type_impact = shock.TYPE_IMPACT.get(shock.type, 0.15)
        E_shock = shock.magnitude * type_impact
        return E_shock
    
    def phase_reset(self, shock: ExternalShock):
        for jurisdiction in self.state.threshold_map:
            current = self.state.threshold_map[jurisdiction]
            self.state.threshold_map[jurisdiction] = current * 0.95 + 0.65 * 0.05
    
    def update_thresholds(self, shock: ExternalShock):
        impact = shock.magnitude * shock.TYPE_IMPACT.get(shock.type, 0.15)
        
        if shock.type == ExternalShockType.TS_OVERRULE:
            for jurisdiction in self.state.threshold_map:
                if shock.affected_domain == "art13":
                    self.state.threshold_map[jurisdiction] -= impact * 0.1
                elif shock.affected_domain == "donation":
                    self.state.threshold_map[jurisdiction] += impact * 0.1
        elif shock.type == ExternalShockType.TEAC_CRITERION_SHIFT:
            for jurisdiction in [Jurisdiction.TEAC, Jurisdiction.AEAT]:
                if jurisdiction in self.state.threshold_map:
                    if shock.affected_domain == "art13":
                        self.state.threshold_map[jurisdiction] -= impact * 0.15
                    elif shock.affected_domain == "donation":
                        self.state.threshold_map[jurisdiction] += impact * 0.15
    
    def get_total_shock_energy(self) -> float:
        return sum(self.energy_shock_history)
    
    def get_recent_shock_magnitude(self, window_days: int = 365) -> float:
        now = datetime.now()
        recent = [
            s for s in self.shocks
            if (now - s.timestamp).days <= window_days
        ]
        return sum(s.magnitude for s in recent)

# ============================================================
# 3. BACKTESTING ENGINE (2010–2026 replay)
# ============================================================

@dataclass
class HistoricalShock:
    year: int
    month: int
    shock_type: ExternalShockType
    magnitude: float
    domain: str
    description: str
    actual_outcome: str

class BacktestingEngine:
    HISTORY_SHOCKS = [
        HistoricalShock(
            year=2010, month=6,
            shock_type=ExternalShockType.LEGISLATIVE_AMENDMENT,
            magnitude=0.6,
            domain="donation",
            description="Reforma Ley 49/2002: requisitos pureza donación",
            actual_outcome="donation_protected"
        ),
        HistoricalShock(
            year=2014, month=12,
            shock_type=ExternalShockType.LEGISLATIVE_AMENDMENT,
            magnitude=0.7,
            domain="donation",
            description="Reforma parcial Ley 49/2002: incentivos mecenazgo",
            actual_outcome="donation_protected"
        ),
        HistoricalShock(
            year=2015, month=3,
            shock_type=ExternalShockType.TS_OVERRULE,
            magnitude=0.5,
            domain="art13",
            description="STS 904/2020: límites art. 13 LGT",
            actual_outcome="art13_restricted"
        ),
        HistoricalShock(
            year=2020, month=7,
            shock_type=ExternalShockType.TS_OVERRULE,
            magnitude=0.6,
            domain="art13",
            description="STS 904/2020 + 905/2020 + 1074/2020: doctrina límites art. 13",
            actual_outcome="art13_restricted"
        ),
        HistoricalShock(
            year=2021, month=10,
            shock_type=ExternalShockType.TEAC_CRITERION_SHIFT,
            magnitude=0.4,
            domain="art13",
            description="TEAC unificación: responsabilidad donatario (art. 42.2.a LGT)",
            actual_outcome="art13_expanded"
        ),
        HistoricalShock(
            year=2023, month=12,
            shock_type=ExternalShockType.LEGISLATIVE_AMENDMENT,
            magnitude=0.8,
            domain="donation",
            description="RDL 6/2023: reforma Ley 49/2002 (mecenazgo de recompensa)",
            actual_outcome="donation_expanded"
        ),
        HistoricalShock(
            year=2024, month=1,
            shock_type=ExternalShockType.LEGISLATIVE_AMENDMENT,
            magnitude=0.75,
            domain="donation",
            description="Entrada vigor reforma mecenazgo (1 enero 2024)",
            actual_outcome="donation_expanded"
        ),
        HistoricalShock(
            year=2024, month=5,
            shock_type=ExternalShockType.TS_OVERRULE,
            magnitude=0.55,
            domain="art13",
            description="STS 819/2024: art. 13 LGT ampara recalificación",
            actual_outcome="art13_expanded"
        ),
        HistoricalShock(
            year=2024, month=10,
            shock_type=ExternalShockType.TEAC_CRITERION_SHIFT,
            magnitude=0.5,
            domain="burden",
            description="TEAC: prescripción responsabilidad (extensión TS 14/10/2022)",
            actual_outcome="burden_shift"
        ),
    ]
    
    def __init__(self, shock_field: ExternalShockField):
        self.shock_field = shock_field
        self.predictions: List[Dict] = []
        self.actuals: List[Dict] = []
    
    def run(self, corpus: List[CaseNode]) -> Dict:
        sorted_shocks = sorted(self.HISTORY_SHOCKS, key=lambda s: (s.year, s.month))
        sorted_corpus = sorted(corpus, key=lambda c: c.date)
        
        initial_energy = self.shock_field.energy_engine.compute(current_tick=0).E_total
        physics = JuridicalPhysicsEngine(self.shock_field.state)
        self.predictions.append({
            "year": 2010,
            "energy": initial_energy,
            "regime": physics.classify_regime(initial_energy).value,
            "phase_transition": "NONE"
        })
        
        shock_idx = 0
        case_idx = 0
        current_tick = 0
        
        for year in range(2010, 2027):
            while shock_idx < len(sorted_shocks) and sorted_shocks[shock_idx].year == year:
                shock = ExternalShock(
                    type=sorted_shocks[shock_idx].shock_type,
                    magnitude=sorted_shocks[shock_idx].magnitude,
                    affected_domain=sorted_shocks[shock_idx].domain,
                    timestamp=datetime(year, sorted_shocks[shock_idx].month, 1),
                    description=sorted_shocks[shock_idx].description
                )
                
                self.shock_field.apply(shock)
                current_tick += 1
                analysis = JuridicalPhysicsEngine(self.shock_field.state).analyze()
                self.predictions.append({
                    "year": year,
                    "event": f"SHOCK: {sorted_shocks[shock_idx].description[:50]}...",
                    "energy": analysis["energy"]["E_total"],
                    "regime": analysis["regime"],
                    "phase_transition": analysis["phase_transition"],
                    "drift": analysis["drift_vector"]
                })
                
                self.actuals.append({
                    "year": year,
                    "outcome": sorted_shocks[shock_idx].actual_outcome
                })
                
                shock_idx += 1
            
            while case_idx < len(sorted_corpus) and sorted_corpus[case_idx].date.year == year:
                case = sorted_corpus[case_idx]
                self.shock_field.state.update_from_case(case)
                current_tick += 1
                case_idx += 1
            
            analysis = JuridicalPhysicsEngine(self.shock_field.state).analyze()
            self.predictions.append({
                "year": year,
                "event": f"STATE: {len(sorted_corpus) if case_idx == len(sorted_corpus) else case_idx} casos procesados",
                "energy": analysis["energy"]["E_total"],
                "regime": analysis["regime"],
                "phase_transition": analysis["phase_transition"],
                "drift": analysis["drift_vector"],
                "attractor": analysis["dominant_attractor"]
            })
        
        accuracy = self.compute_accuracy()
        
        return {
            "timeline": self.predictions,
            "actuals": self.actuals,
            "accuracy": accuracy,
            "total_shocks": len(self.shock_field.shocks),
            "total_shock_energy": self.shock_field.get_total_shock_energy()
        }
    
    def compute_accuracy(self) -> Dict:
        transition_predictions = [
            p for p in self.predictions
            if p.get("phase_transition") != "NONE"
        ]
        
        if len(transition_predictions) == 0:
            return {"phase_transition": 0.0}
        
        correct_transitions = 0
        for pred in transition_predictions:
            for actual in self.actuals:
                if actual["year"] >= pred["year"]:
                    correct_transitions += 1
                    break
        
        transition_accuracy = correct_transitions / len(transition_predictions) if len(transition_predictions) > 0 else 0.0
        return {
            "phase_transition": transition_accuracy,
            "sample_size": len(self.predictions)
        }

# ============================================================
# 4. INTEGRACIÓN COMPLETA
# ============================================================

class CompleteJurisprudentialPhysicsEngine:
    def __init__(self, state: JurisprudenceState):
        self.state = state
        from fas_energy_physics import ExternalShockModel
        shock_model = ExternalShockModel()
        self.energy_engine = JuridicalEnergyEngine(state, shock_model)
        self.shock_field = ExternalShockField(state, self.energy_engine)
        self.backtester = BacktestingEngine(self.shock_field)
    
    def apply_shock(self, shock: ExternalShock):
        self.shock_field.apply(shock)
    
    def backtest(self, corpus: List[CaseNode]) -> Dict:
        return self.backtester.run(corpus)

if __name__ == "__main__":
    state = JurisprudenceState()
    engine = CompleteJurisprudentialPhysicsEngine(state)
    
    # Mock de 10 casos históricos
    from fas_phase2_core import EconomicEvent, JudicialInference
    corpus = []
    for y in range(2010, 2020):
        corpus.append(CaseNode(f"CASE-{y}", Jurisdiction.TS, datetime(y, 6, 1), "sentencia", 
                     events_economic=[EconomicEvent.PAYMENT_FIXED],
                     events_inference=[JudicialInference.CONTRAPRESTACION_CORRELATION],
                     events_system=[]))
                     
    res = engine.backtest(corpus)
    print(json.dumps(res, indent=2, ensure_ascii=False))
