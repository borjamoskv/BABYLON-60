#!/usr/bin/env python3
"""
FAS v12 — Jurisdictional Multi-Agent Court System (Path Dependency Engine)
Reality level: C5-REAL (Deterministic analytical tool executing on local hardware)
Aesthetics: Industrial Noir 2026

Simulates the manufacturing of a legal sentence across a hierarchical court system.
Models path dependency: the verdict of layer N becomes the factual anchor for layer N+1.
Actors:
- Red Team (AEAT Inspector): Initial prosecutor.
- Blue Team (Defense): Reasonable doubt engineer.
- TEAC (Administrative Tribunal): High AEAT alignment, checks formal thresholds.
- TS (Tribunal Supremo): Doctrinal filter, lowers AEAT bias, requires high structural integrity.
- TJUE (Tribunal Europeo): Pure legal principle filter, anti-bias, evaluates proportionality.
"""

import json
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class DualCourtConfig:
    inspector_bias: float = 0.35
    defense_burden_of_proof_discount: float = 0.25

@dataclass
class CourtNodeConfig:
    name: str
    institutional_bias: float           # Baseline affinity with State/AEAT (0.0 to 1.0)
    standard_of_proof: float          # Minimum effective strength to uphold the State's case
    anchoring_vulnerability: float      # How much previous instance's ruling anchors them
    doctrinal_rigidity: float           # How much they penalize noise in the State's case

class FeatureExtractor:
    @staticmethod
    def extract(data: Dict[str, Any]) -> Dict[str, float]:
        payments, accesses = data.get("payments", []), data.get("accesses", [])
        time_deltas = data.get("time_deltas", [])
        prices = data.get("prices", [])
        market_price = data.get("market_price", 237.0)

        coupling = min(1.0, len(accesses) / len(payments)) if payments else 0.0
        
        avg_time = sum(time_deltas) / len(time_deltas) if time_deltas else 30.0
        clustering = max(0.0, min(1.0, 1.0 - avg_time / 30.0))

        deviation = sum(abs(p - market_price) for p in prices) / len(prices) if prices else market_price
        homogeneity = max(0.0, min(1.0, 1.0 - deviation / market_price))
        
        ambiguity = data.get("noise_ratio", 0.0)

        return {
            "access_coupling": coupling,
            "temporal_clustering": clustering,
            "price_homogeneity": homogeneity,
            "ambiguity": ambiguity
        }

class BaseAgent:
    def __init__(self, config: DualCourtConfig):
        self.config = config

class InspectorAgent(BaseAgent):
    def infer(self, features: Dict[str, float]) -> float:
        base_risk = (features["access_coupling"] * 0.4 + features["temporal_clustering"] * 0.4 + features["price_homogeneity"] * 0.2)
        return min(1.0, base_risk * (1.0 + self.config.inspector_bias))

class DefenseAgent(BaseAgent):
    def infer(self, features: Dict[str, float]) -> float:
        base_defense = ((1.0 - features["access_coupling"]) * 0.4 + features["ambiguity"] * 0.4 + (1.0 - features["price_homogeneity"]) * 0.2)
        return min(1.0, base_defense + self.config.defense_burden_of_proof_discount)

class CourtNode:
    """A generic court layer in the jurisdictional hierarchy."""
    def __init__(self, config: CourtNodeConfig):
        self.config = config

    def adjudicate(self, 
                   previous_state_strength: float, 
                   defense_doubt: float, 
                   features: Dict[str, float],
                   prior_verdict_was_state: bool) -> Dict[str, Any]:
        
        # Path Dependency: The previous court's ruling modifies the baseline strength
        # If the state won previously, their anchor is stronger. If they lost, they are fighting uphill.
        anchor_multiplier = 1.0 + (self.config.anchoring_vulnerability if prior_verdict_was_state else -self.config.anchoring_vulnerability)
        
        anchored_state_case = previous_state_strength * anchor_multiplier
        
        # Doctrinal Rigidity: Higher courts penalize the State if the evidence has ambiguity
        state_doctrinal_penalty = features["ambiguity"] * self.config.doctrinal_rigidity
        
        # The State's case is bolstered by the court's institutional bias, but damaged by doctrinal flaws
        institutional_state_strength = (anchored_state_case * (1.0 + self.config.institutional_bias)) - state_doctrinal_penalty
        
        # Weaponized doubt from defense
        weaponized_doubt = defense_doubt * features["ambiguity"]
        
        # Effective strength must clear the Court's Standard of Proof
        effective_strength = max(0.0, institutional_state_strength - weaponized_doubt)
        state_wins = effective_strength >= self.config.standard_of_proof

        return {
            "court": self.config.name,
            "mechanics": {
                "anchored_state_case": round(anchored_state_case, 4),
                "state_doctrinal_penalty": round(state_doctrinal_penalty, 4),
                "institutional_state_strength": round(institutional_state_strength, 4),
                "weaponized_defense_doubt": round(weaponized_doubt, 4),
                "effective_strength": round(effective_strength, 4),
                "threshold_required": self.config.standard_of_proof
            },
            "state_wins": state_wins,
            "verdict": "STATE_WINS (Reclassification Upheld)" if state_wins else "DEFENSE_WINS (Reclassification Annulled)"
        }

class JurisdictionalEngine:
    def __init__(self):
        self.extractor = FeatureExtractor()
        self.inspector = InspectorAgent(DualCourtConfig())
        self.defense = DefenseAgent(DualCourtConfig())
        
        # The Hierarchical Pipeline
        self.courts = [
            CourtNode(CourtNodeConfig(
                name="1. TEAC (Tribunal Económico-Administrativo Central)",
                institutional_bias=0.25,        # High affinity with AEAT
                standard_of_proof=0.65,       # Low threshold to uphold
                anchoring_vulnerability=0.30,   # Highly anchored to Inspector's acta
                doctrinal_rigidity=0.10         # Ignores most ambiguity if formal facts match
            )),
            CourtNode(CourtNodeConfig(
                name="2. TS (Tribunal Supremo)",
                institutional_bias=0.05,        # Neutral/slight state bias
                standard_of_proof=0.75,       # Higher threshold (Cassation requires solid law)
                anchoring_vulnerability=0.15,   # Less anchored to TEAC
                doctrinal_rigidity=0.40         # Heavily penalizes ambiguous reconstructions
            )),
            CourtNode(CourtNodeConfig(
                name="3. TJUE (Tribunal de Justicia UE)",
                institutional_bias=-0.10,       # Slight anti-state bias (pro economic freedom)
                standard_of_proof=0.85,       # Draconian threshold for reclassifications
                anchoring_vulnerability=0.05,   # Almost ignores national path dependency
                doctrinal_rigidity=0.70         # Destroys any state narrative built on noise
            ))
        ]

    def litigate_pipeline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        features = self.extractor.extract(data)
        
        # Initial actors
        inspector_strength = self.inspector.infer(features)
        defense_doubt = self.defense.infer(features)
        
        trajectory = []
        current_state_strength = inspector_strength
        prior_verdict_was_state = True # The starting point is always the AEAT's Liquidation
        
        for court in self.courts:
            ruling = court.adjudicate(current_state_strength, defense_doubt, features, prior_verdict_was_state)
            trajectory.append(ruling)
            
            # The output strength of this court becomes the input for the next
            current_state_strength = ruling["mechanics"]["effective_strength"]
            prior_verdict_was_state = ruling["state_wins"]
            
            # If the State case is completely annihilated, it cannot be resurrected in appeal
            if current_state_strength <= 0.0:
                break

        final_winner = trajectory[-1]["verdict"]
        
        return {
            "0_evidence_embedding": {k: round(v, 4) for k, v in features.items()},
            "1_initial_narratives": {
                "inspector_base_strength": round(inspector_strength, 4),
                "defense_base_doubt": round(defense_doubt, 4)
            },
            "2_jurisdictional_trajectory": trajectory,
            "3_final_binding_resolution": final_winner
        }

def run_jurisdictional_demo():
    engine = JurisdictionalEngine()
    
    # CASE A: The Bulletproof Scheme (Zero Noise, Perfect Correlation)
    case_a = {
        "payments": [237.0]*100, "accesses": [1.0]*100, "time_deltas": [1.0]*100,
        "prices": [237.0]*100, "market_price": 237.0, "noise_ratio": 0.01
    }
    
    # CASE B: The Ergodic Hybrid (High Noise, Weak Structural Correlation)
    case_b = {
        "payments": [10.0, 50.0, 400.0, 150.0], "accesses": [1.0, 1.0, 1.0],
        "time_deltas": [28.0, 45.0, 12.0], "prices": [10.0, 50.0, 400.0, 150.0],
        "market_price": 237.0, "noise_ratio": 0.55
    }

    # CASE C: The "Spanish Trap" (TEAC confirms, TS/TJUE crushes due to doctrinal rigidity)
    case_c = {
        "payments": [237.0]*100, "accesses": [1.0]*100,
        "time_deltas": [5.0]*100, "prices": [237.0]*100,
        "market_price": 237.0, "noise_ratio": 0.30 # Just enough ambiguity to survive TEAC but die in TS
    }

    print("=========================================================================")
    print("  FAS v12 : JURISDICTIONAL MULTI-AGENT COURT SYSTEM                      ")
    print("=========================================================================\n")
    
    print(">>> [CASE A] BULLETPROOF SCHEME (State wins all layers)")
    print(json.dumps(engine.litigate_pipeline(case_a), indent=2, ensure_ascii=False))
    
    print("\n" + "-"*73 + "\n")
    
    print(">>> [CASE B] ERGODIC HYBRID (Defense kills AEAT at TEAC, appeal impossible)")
    print(json.dumps(engine.litigate_pipeline(case_b), indent=2, ensure_ascii=False))

    print("\n" + "-"*73 + "\n")

    print(">>> [CASE C] THE SPANISH TRAP (State wins TEAC, dies at Supremo/TJUE)")
    print(json.dumps(engine.litigate_pipeline(case_c), indent=2, ensure_ascii=False))
    print("\n=========================================================================")

if __name__ == "__main__":
    run_jurisdictional_demo()
