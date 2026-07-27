from dataclasses import dataclass, field
from typing import Dict, List, Set
from enum import Enum
from datetime import datetime

# ============================================================
# 1. ONTOLOGY (v0 — LOCKED)
# ============================================================

class EconomicEvent(Enum):
    PAYMENT_FIXED = "payment_fixed_amount"
    PAYMENT_VARIABLE = "payment_variable_amount"
    PAYMENT_RECURRING = "payment_recurring"
    PAYMENT_ONE_OFF = "payment_one_off"
    ACCESS_POST_PAYMENT = "access_granted_post_payment"
    ACCESS_PRE_PAYMENT = "access_granted_pre_payment"
    ACCESS_INDEPENDENT = "access_independent_of_payment"
    PRICE_MARKET_ALIGNED = "price_anchor_market_aligned"
    PRICE_ARBITRARY = "price_anchor_arbitrary"
    PRICE_HIDDEN = "price_hidden_or_suggested"
    HIGH_HOMOGENEITY = "high_user_homogeneity"
    HETEROGENEOUS_BASE = "heterogeneous_user_base"
    FREE_RIDER = "free_rider_presence"
    TIGHT_COUPLING = "tight_temporal_coupling"
    LOOSE_COUPLING = "loose_temporal_coupling"
    DELAYED_ACCESS = "delayed_access_pattern"

class JudicialInference(Enum):
    CONTRAPRESTACION_CORRELATION = "contraprestacion_inferred_from_correlation"
    CONTRAPRESTACION_AMBIGUITY = "contraprestacion_rejected_due_to_ambiguity"
    ECONOMIC_REALITY_OVER_FORM = "economic_reality_over_form_applied"
    FORMAL_STRUCTURE_UPHELD = "formal_structure_upheld"
    SIMULATION_DETECTED = "simulated_contract_detected"
    DONATION_INTENT_RECOGNIZED = "donation_intent_recognized"
    DONATION_INTENT_REJECTED = "donation_intent_rejected"
    BURDEN_SHIFT = "burden_shift_to_taxpayer"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence_for_reclassification"
    PRECEDENT_STRENGTHENED = "precedent_strengthened"
    PRECEDENT_NARROWED = "precedent_narrowed"
    PRECEDENT_DISTINGUISHED = "precedent_distinguished"

class SystemStateEvent(Enum):
    HIGH_CONFIDENCE_RECLASS = "high_confidence_reclassification_systemic"
    JURISPRUDENTIAL_SPLIT = "jurisprudential_split_detected"
    DOCTRINAL_DRIFT = "doctrinal_drift_accelerating"
    THRESHOLD_LOWER = "threshold_lowering_over_time"
    THRESHOLD_RAISE = "threshold_raising_over_time"
    INSTITUTIONAL_BIAS = "institutional_bias_amplification"
    NOISE_BECOMING_SIGNAL = "noise_becoming_signal"

# ============================================================
# 2. CASE NODE (input from corpus_seed)
# ============================================================

class Jurisdiction(Enum):
    AEAT = "AEAT"
    TEAC = "TEAC"
    TSJ_CAT = "TSJ-CAT"
    TSJ_MAD = "TSJ-MAD"
    TSJ_PV = "TSJ-PV"
    TS = "TS"
    TJUE = "TJUE"

@dataclass
class CaseNode:
    case_id: str
    jurisdiction: Jurisdiction
    date: datetime
    source_type: str  
    
    events_economic: List[EconomicEvent]
    events_inference: List[JudicialInference]
    events_system: List[SystemStateEvent]
    
    fragments_facts: List[str] = field(default_factory=list)
    fragments_law: List[str] = field(default_factory=list)
    fragments_decision: List[str] = field(default_factory=list)
    
    notes_why_important: str = ""
    notes_threshold_signal: str = ""
    notes_divergence_signal: str = ""

# ============================================================
# 3. REASONING GRAPH GENERATOR (Layer 2)
# ============================================================

@dataclass
class ReasoningStep:
    type: str  
    content: str
    strength: float  
    source: str  

@dataclass
class InferenceLink:
    from_step: str
    to_step: str
    link_type: str  

@dataclass
class ReasoningGraph:
    steps: List[ReasoningStep] = field(default_factory=list)
    links: List[InferenceLink] = field(default_factory=list)

class ReasoningGraphGenerator:
    INFERENCE_RULES = {
        JudicialInference.CONTRAPRESTACION_CORRELATION: {
            "type": "inference",
            "template": "contraprestación implícita detectada por correlación sistémica",
            "strength_base": 0.75,
            "boosters": [
                EconomicEvent.PAYMENT_FIXED,
                EconomicEvent.TIGHT_COUPLING,
                EconomicEvent.HIGH_HOMOGENEITY
            ]
        },
        JudicialInference.CONTRAPRESTACION_AMBIGUITY: {
            "type": "inference", 
            "template": "ausencia de contraprestación por ambigüedad estructural",
            "strength_base": 0.65,
            "boosters": [
                EconomicEvent.FREE_RIDER,
                EconomicEvent.LOOSE_COUPLING,
                EconomicEvent.HETEROGENEOUS_BASE
            ]
        },
        JudicialInference.SIMULATION_DETECTED: {
            "type": "presumption",
            "template": "dolo de simulación infierido desde resultado fiscal anómalo",
            "strength_base": 0.80,
            "boosters": [
                EconomicEvent.PAYMENT_RECURRING,
                EconomicEvent.PRICE_HIDDEN
            ]
        },
        JudicialInference.DONATION_INTENT_RECOGNIZED: {
            "type": "inference",
            "template": "animus donandi preservado (ausencia de señal de onerosidad)",
            "strength_base": 0.70,
            "boosters": [
                EconomicEvent.PAYMENT_ONE_OFF,
                EconomicEvent.ACCESS_INDEPENDENT
            ]
        },
        JudicialInference.DONATION_INTENT_REJECTED: {
            "type": "inference",
            "template": "donación formal destruida por onerosidad real",
            "strength_base": 0.78,
            "boosters": [
                EconomicEvent.PRICE_MARKET_ALIGNED,
                EconomicEvent.PAYMENT_FIXED
            ]
        },
        JudicialInference.BURDEN_SHIFT: {
            "type": "presumption",
            "template": "carga de prueba invertida hacia el contribuyente",
            "strength_base": 0.85,
            "boosters": [
                SystemStateEvent.INSTITUTIONAL_BIAS
            ]
        },
        JudicialInference.PRECEDENT_STRENGTHENED: {
            "type": "legal_rule",
            "template": "precedent vinculante reforzado",
            "strength_base": 0.90,
            "boosters": []
        },
        JudicialInference.PRECEDENT_NARROWED: {
            "type": "legal_rule",
            "template": "precedent limitado ( excepciones añadidas)",
            "strength_base": 0.72,
            "boosters": []
        },
        JudicialInference.PRECEDENT_DISTINGUISHED: {
            "type": "legal_rule", 
            "template": "precedent distingué (caso diferente)",
            "strength_base": 0.68,
            "boosters": []
        }
    }
    
    def generate(self, case: CaseNode) -> ReasoningGraph:
        graph = ReasoningGraph()
        
        for event in case.events_economic:
            step = ReasoningStep(
                type="observation",
                content=event.value,
                strength=1.0,
                source="facts"
            )
            graph.steps.append(step)
        
        for inference in case.events_inference:
            rule = self.INFERENCE_RULES.get(inference)
            if not rule:
                continue
            
            strength = rule["strength_base"]
            for booster in rule["boosters"]:
                if booster in case.events_economic:
                    strength += 0.05
            
            step = ReasoningStep(
                type=rule["type"],
                content=rule["template"],
                strength=min(1.0, strength),
                source="precedent" if rule["type"] == "legal_rule" else "doctrine"
            )
            graph.steps.append(step)
        
        observations = [s for s in graph.steps if s.type == "observation"]
        inferences = [s for s in graph.steps if s.type in ["inference", "presumption"]]
        
        for inf in inferences:
            for obs in observations[:3]:  
                link = InferenceLink(
                    from_step=obs.content,
                    to_step=inf.content,
                    link_type="supports"
                )
                graph.links.append(link)
        
        return graph

# ============================================================
# 4. JURISPRUDENCE STATE ENGINE (drift + threshold)
# ============================================================

def clamp(x, min_val, max_val):
    return max(min_val, min(max_val, x))

@dataclass
class JurisprudenceState:
    threshold_map: Dict[Jurisdiction, float] = field(default_factory=lambda: {
        Jurisdiction.AEAT: 0.72,
        Jurisdiction.TEAC: 0.78,
        Jurisdiction.TSJ_CAT: 0.65,
        Jurisdiction.TSJ_MAD: 0.65,
        Jurisdiction.TSJ_PV: 0.55,
        Jurisdiction.TS: 0.60,
        Jurisdiction.TJUE: 0.50
    })
    
    drift_vector: Dict[str, float] = field(default_factory=lambda: {
        "art13_lgt_strength": 0.0,
        "art16_lgt_expansion": 0.0,
        "donation_skepticism": 0.0,
        "burden_shift_intensity": 0.0
    })
    
    precedent_lock: Dict[str, float] = field(default_factory=dict)  
    case_history: List[CaseNode] = field(default_factory=list)
    
    def update_from_case(self, case: CaseNode):
        self.case_history.append(case)
        
        for system_event in case.events_system:
            if system_event == SystemStateEvent.THRESHOLD_LOWER:
                self.drift_vector["art13_lgt_strength"] += 0.01
            elif system_event == SystemStateEvent.THRESHOLD_RAISE:
                self.drift_vector["art13_lgt_strength"] -= 0.01
            elif system_event == SystemStateEvent.DOCTRINAL_DRIFT:
                self.drift_vector["art16_lgt_expansion"] += 0.02
            elif system_event == SystemStateEvent.INSTITUTIONAL_BIAS:
                self.drift_vector["burden_shift_intensity"] += 0.02
            elif system_event == SystemStateEvent.HIGH_CONFIDENCE_RECLASS:
                self.drift_vector["donation_skepticism"] += 0.02
        
        if case.jurisdiction in [Jurisdiction.TEAC, Jurisdiction.TS]:
            impact = 0.003
        elif case.jurisdiction in [Jurisdiction.TSJ_MAD, Jurisdiction.TSJ_PV]:
            impact = 0.001
        else:
            impact = 0.0005
        
        protective_inferences = [
            JudicialInference.PRECEDENT_NARROWED,
            JudicialInference.INSUFFICIENT_EVIDENCE,
            JudicialInference.CONTRAPRESTACION_AMBIGUITY
        ]
        if any(inv in protective_inferences for inv in case.events_inference):
            self.threshold_map[case.jurisdiction] += impact
        else:
            self.threshold_map[case.jurisdiction] -= impact
        
        if case.jurisdiction in [Jurisdiction.TEAC, Jurisdiction.TS]:
            strength = len([i for i in case.events_inference if i in [
                JudicialInference.PRECEDENT_STRENGTHENED,
                JudicialInference.BURDEN_SHIFT,
                JudicialInference.SIMULATION_DETECTED
            ]])
            self.precedent_lock[case.case_id] = strength * 0.15
    
    def get_effective_threshold(self, jurisdiction: Jurisdiction, inference_type: JudicialInference) -> float:
        base = self.threshold_map[jurisdiction]
        
        if inference_type == JudicialInference.CONTRAPRESTACION_CORRELATION:
            base += self.drift_vector["art13_lgt_strength"]
        elif inference_type == JudicialInference.SIMULATION_DETECTED:
            base += self.drift_vector["art16_lgt_expansion"]
        elif inference_type in [JudicialInference.DONATION_INTENT_RECOGNIZED,
                                JudicialInference.CONTRAPRESTACION_AMBIGUITY]:
            base += self.drift_vector["donation_skepticism"]
        
        if jurisdiction in [Jurisdiction.TEAC, Jurisdiction.TS]:
            for case_id, strength in self.precedent_lock.items():
                if case_id in [c.case_id for c in self.case_history]:
                    base -= strength * 0.02  
        
        return clamp(base, 0.4, 0.95)

# ============================================================
# 5. JURISDICTIONAL AGENTS (v11 core)
# ============================================================

@dataclass
class AgentConfig:
    name: str
    jurisdiction: Jurisdiction
    bias_vector: Dict[str, float]
    review_standard: str  
    error_cost: Dict[str, float]  

class JurisdictionalAgent:
    def __init__(self, config: AgentConfig, jurisprudence_state: JurisprudenceState):
        self.config = config
        self.state = jurisprudence_state
        self.memory: List[CaseNode] = []
    
    def review(self, case: CaseNode) -> Dict[str, float]:
        self.memory.append(case)
        evidence_strength = self.compute_evidence_strength(case)
        key_inference = self.get_key_inference(case)
        threshold = self.state.get_effective_threshold(self.config.jurisdiction, key_inference)
        bias = self.compute_bias(case)
        
        if evidence_strength > threshold:
            if bias > 0.1:  
                p_aeat = 0.75 + bias
                p_defense = 0.25 - bias
            else:  
                p_defense = 0.70 - bias
                p_aeat = 0.30 + bias
        else:
            p_defense = 0.80
            p_aeat = 0.20
        
        if (p_aeat > 0.7 and self.config.error_cost.get("false_positive", 0) > 0.5):
            p_aeat -= 0.1
            p_defense += 0.1
        
        return {
            "p_aeat_win": clamp(p_aeat, 0.1, 0.95),
            "p_defense_win": clamp(p_defense, 0.05, 0.9),
            "confidence": clamp(abs(p_aeat - p_defense), 0.1, 0.95)
        }
    
    def compute_evidence_strength(self, case: CaseNode) -> float:
        strength = 0.0
        for inference in case.events_inference:
            rule = ReasoningGraphGenerator.INFERENCE_RULES.get(inference)
            if rule:
                strength += rule["strength_base"] * 0.2
        
        for inference in case.events_inference:
            rule = ReasoningGraphGenerator.INFERENCE_RULES.get(inference)
            if rule:
                for booster in rule.get("boosters", []):
                    if booster in case.events_economic:
                        strength += 0.05
        
        return clamp(strength, 0.3, 0.95)
    
    def get_key_inference(self, case: CaseNode) -> JudicialInference:
        priority = [
            JudicialInference.SIMULATION_DETECTED,
            JudicialInference.CONTRAPRESTACION_CORRELATION,
            JudicialInference.DONATION_INTENT_REJECTED,
            JudicialInference.BURDEN_SHIFT
        ]
        for inv in priority:
            if inv in case.events_inference:
                return inv
        return case.events_inference[0] if case.events_inference else JudicialInference.FORMAL_STRUCTURE_UPHELD
    
    def compute_bias(self, case: CaseNode) -> float:
        bias = self.config.bias_vector.get("default", 0.0)
        
        if any(inv in case.events_inference for inv in [
            JudicialInference.CONTRAPRESTACION_CORRELATION,
            JudicialInference.DONATION_INTENT_REJECTED,
            JudicialInference.SIMULATION_DETECTED
        ]):
            bias += self.config.bias_vector.get("AEAT_expansion", 0.05)
        
        if any(inv in case.events_inference for inv in [
            JudicialInference.DONATION_INTENT_RECOGNIZED,
            JudicialInference.CONTRAPRESTACION_AMBIGUITY,
            JudicialInference.INSUFFICIENT_EVIDENCE
        ]):
            bias -= self.config.bias_vector.get("defense_protection", 0.03)
        
        return clamp(bias, -0.15, 0.15)

# ============================================================
# 6. AGENT CONFIGS (basado en corpus)
# ============================================================

AEAT_CONFIG = AgentConfig(
    name="AEAT Inspector",
    jurisdiction=Jurisdiction.AEAT,
    bias_vector={"default": 0.05, "AEAT_expansion": 0.08, "defense_protection": 0.02},
    review_standard="abuso",
    error_cost={"false_positive": 0.3, "false_negative": 0.7}
)

TEAC_CONFIG = AgentConfig(
    name="TEAC Unification",
    jurisdiction=Jurisdiction.TEAC,
    bias_vector={"default": 0.10, "AEAT_expansion": 0.12, "defense_protection": 0.01},
    review_standard="abuso",
    error_cost={"false_positive": 0.2, "false_negative": 0.8}
)

TS_CONFIG = AgentConfig(
    name="Tribunal Supremo",
    jurisdiction=Jurisdiction.TS,
    bias_vector={"default": 0.02, "AEAT_expansion": 0.05, "defense_protection": 0.05},
    review_standard="de_novo",
    error_cost={"false_positive": 0.5, "false_negative": 0.5}
)

TSJ_PV_CONFIG = AgentConfig(
    name="TSJ País Vasco",
    jurisdiction=Jurisdiction.TSJ_PV,
    bias_vector={"default": -0.05, "AEAT_expansion": 0.02, "defense_protection": 0.08},
    review_standard="proporcionalidad",
    error_cost={"false_positive": 0.6, "false_negative": 0.4}
)

# ============================================================
# 7. SIMULACIÓN (demo con corpus_seed)
# ============================================================

def run_simulation(corpus: List[CaseNode]):
    state = JurisprudenceState()
    
    agents = {
        "AEAT": JurisdictionalAgent(AEAT_CONFIG, state),
        "TEAC": JurisdictionalAgent(TEAC_CONFIG, state),
        "TS": JurisdictionalAgent(TS_CONFIG, state),
        "TSJ_PV": JurisdictionalAgent(TSJ_PV_CONFIG, state)
    }
    
    results = []
    
    for case in sorted(corpus, key=lambda c: c.date):
        state.update_from_case(case)
        agent_results = {}
        for name, agent in agents.items():
            result = agent.review(case)
            agent_results[name] = result
        
        results.append({
            "case_id": case.case_id,
            "date": case.date.isoformat(),
            "jurisdiction": case.jurisdiction.value,
            "outcome": [e.name for e in case.events_inference],
            "system_signals": [e.name for e in case.events_system],
            "agent_predictions": agent_results,
            "threshold_snapshot": {k.value: round(v, 4) for k, v in state.threshold_map.items()},
            "drift_snapshot": {k: round(v, 4) for k, v in state.drift_vector.items()}
        })
    
    return results

if __name__ == "__main__":
    import json
    
    case10 = CaseNode(
        case_id="TEAC-2024-03063-RESPONSABILIDAD-DONATARIO",
        jurisdiction=Jurisdiction.TEAC,
        date=datetime(2024, 10, 15),
        source_type="criterio",
        events_economic=[
            EconomicEvent.PAYMENT_ONE_OFF,
            EconomicEvent.PRICE_ARBITRARY,
            EconomicEvent.ACCESS_INDEPENDENT,
            EconomicEvent.HETEROGENEOUS_BASE
        ],
        events_inference=[
            JudicialInference.DONATION_INTENT_RECOGNIZED,
            JudicialInference.FORMAL_STRUCTURE_UPHELD,
            JudicialInference.BURDEN_SHIFT,
            JudicialInference.PRECEDENT_STRENGTHENED
        ],
        events_system=[
            SystemStateEvent.HIGH_CONFIDENCE_RECLASS,
            SystemStateEvent.INSTITUTIONAL_BIAS,
            SystemStateEvent.NOISE_BECOMING_SIGNAL
        ]
    )
    
    corpus = [case10]
    results = run_simulation(corpus)
    print(json.dumps(results[-1], indent=2, ensure_ascii=False))
