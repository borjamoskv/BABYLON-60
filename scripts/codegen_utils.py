"""
codegen_utils.py — Shared primitives for YAML-to-code generation pipeline.
Extracted from generate_*.py scripts (C5-REAL DRY enforcement).
DO NOT duplicate parse_yaml, write_output, or get_ledger_hash in individual generators.
"""

from __future__ import annotations

import hashlib
import os
import re
from typing import Any, Dict


def parse_yaml(yaml_path: str) -> tuple[dict[int, str], dict[int, str], dict[int, str]]:
    """Parse a 1000-primitive YAML taxonomy into (domains, primitives, modifiers)."""
    with open(yaml_path, encoding="utf-8") as f:
        content = f.read()

    domains: dict[int, str] = {}
    primitives: dict[int, str] = {}
    modifiers: dict[int, str] = {}
    current_section: str | None = None

    for line in content.splitlines():
        line = line.strip()
        if (
            not line
            or line.startswith("#")
            or line.startswith("Claim:")
            or line.startswith("Proof:")
            or line.startswith("Formula:")
        ):
            continue
        if line.startswith("Domains_Context:"):
            current_section = "domains"
            continue
        elif line.startswith("Primitives_Action:"):
            current_section = "primitives"
            continue
        elif line.startswith("Modifiers_Constraint:"):
            current_section = "modifiers"
            continue

        match = re.match(r"(\d+):\s*\"([^\"]+)\"", line)
        if match:
            idx = int(match.group(1))
            val = match.group(2)
            if current_section == "domains":
                domains[idx] = val
            elif current_section == "primitives":
                primitives[idx] = val
            elif current_section == "modifiers":
                modifiers[idx] = val

    assert len(domains) == 10, f"Expected 10 domains, got {len(domains)}"
    assert len(primitives) == 10, f"Expected 10 primitives, got {len(primitives)}"
    assert len(modifiers) == 10, f"Expected 10 modifiers, got {len(modifiers)}"

    return domains, primitives, modifiers


def write_output(path: str, lines: list[Any]) -> None:
    """Atomically write generated source lines to *path*, creating parent dirs (Ω41)."""
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write("\n".join(str(ln) for ln in lines))
        os.replace(tmp_path, path)
    except Exception as e:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise e
    print(f"Generated: {path}")



def get_ledger_hash(ledger_path: str = "mundo_f_ledger.yml") -> str | None:
    """AP-2: Canonical ledger hash function. Import this — DO NOT redefine.

    Returns SHA-256 hex digest of the ledger file, or None if not found.
    """
    try:
        with open(ledger_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except FileNotFoundError:
        return None


# METADATA CONFIGURATIONS FOR DRY PARALLEL GENERATOR (AP-R1)
CODEGEN_CONFIGS: Dict[str, Dict[str, Any]] = {
    "Constants": {
        "yaml": "cortex/ontology/fundamental_constants_1000_taxonomy.yaml",
        "prefix_upper": "CONST",
        "go_ident": "ConstantsIdentity",
        "go_state": "ConstantsStateVector",
        "go_handler": "ConstantsHandler",
        "go_table": "ConstantsTable",
        "go_metrics": "ConstantsMetrics",
        "go_init": "InitConstantsKernel",
        "go_dispatch": "DispatchConstants",
        "go_count": "GetConstantsExecutionCount",
        "rust_ident": "ConstantsIdentity",
        "rust_state": "ConstantsStateVector",
        "rust_dispatch": "dispatch_constants",
        "py_state": "ConstantsStateVector",
        "py_resolve": "resolve_constants_identity",
        "py_dispatch": "dispatch_constants",
        "py_key": "planck_scale_ratio",
        "go_fields": [
            "PlanckScaleRatio        float64",
            "GravitationalCoupling   float64",
            "ElectromagneticShielding float64",
            "QuantumEntropy          float64",
            "SingularityDensity      float64",
        ],
        "rust_fields": [
            "pub planck_scale_ratio: f64,",
            "pub gravitational_coupling: f64,",
            "pub electromagnetic_shielding: f64,",
            "pub quantum_entropy: f64,",
            "pub singularity_density: f64,",
        ],
        "rust_new": [
            "planck_scale_ratio: 1.616255e-35,",
            "gravitational_coupling: 6.67430e-11,",
            "electromagnetic_shielding: 1.602176634e-19,",
            "quantum_entropy: 1.054571817e-34,",
            "singularity_density: 0.0,",
        ],
        "py_fields": [
            "self.planck_scale_ratio = 1.616255e-35",
            "self.gravitational_coupling = 6.67430e-11",
            "self.electromagnetic_shielding = 1.602176634e-19",
            "self.quantum_entropy = 1.054571817e-34",
            "self.singularity_density = 0.0",
        ],
        "go_sim": [
            "vec.PlanckScaleRatio = math.Abs(math.Sin(float64(id.Code))) * 1.616255e-35",
            "vec.GravitationalCoupling = 6.67430e-11 * (1.0 + 0.01*math.Cos(float64(id.Code)))",
            "vec.ElectromagneticShielding = 1.602176634e-19 * (float64(id.Code%10) + 1.0)",
            "vec.QuantumEntropy = math.Max(0.0, vec.QuantumEntropy*0.99 + 1.054571817e-34*float64(id.Code))",
            "vec.SingularityDensity = vec.GravitationalCoupling / math.Max(1e-100, vec.PlanckScaleRatio*vec.PlanckScaleRatio)",
        ],
        "rust_sim": [
            "vec.planck_scale_ratio = (code as f64).sin().abs() * 1.616255e-35;",
            "vec.gravitational_coupling = 6.67430e-11 * (1.0 + 0.01 * (code as f64).cos());",
            "vec.electromagnetic_shielding = 1.602176634e-19 * ((code % 10) as f64 + 1.0);",
            "vec.quantum_entropy = f64::max(0.0, vec.quantum_entropy * 0.99 + 1.054571817e-34 * code as f64);",
            "vec.singularity_density = vec.gravitational_coupling / f64::max(1e-100, vec.planck_scale_ratio * vec.planck_scale_ratio);",
        ],
        "py_sim": [
            "vec.planck_scale_ratio = abs(math.sin(code)) * 1.616255e-35",
            "vec.gravitational_coupling = 6.67430e-11 * (1.0 + 0.01 * math.cos(code))",
            "vec.electromagnetic_shielding = 1.602176634e-19 * (float(code % 10) + 1.0)",
            "vec.quantum_entropy = max(0.0, vec.quantum_entropy * 0.99 + 1.054571817e-34 * float(code))",
            "vec.singularity_density = vec.gravitational_coupling / max(1e-100, vec.planck_scale_ratio * vec.planck_scale_ratio)",
        ],
    },
    "Noether": {
        "yaml": "cortex/ontology/noether_1000_taxonomy.yaml",
        "prefix_upper": "NOETHER",
        "go_ident": "NoetherIdentity",
        "go_state": "NoetherStateVector",
        "go_handler": "NoetherHandler",
        "go_table": "NoetherTable",
        "go_metrics": "NoetherMetrics",
        "go_init": "InitNoetherKernel",
        "go_dispatch": "DispatchNoether",
        "go_count": "GetNoetherExecutionCount",
        "rust_ident": "NoetherIdentity",
        "rust_state": "NoetherStateVector",
        "rust_dispatch": "dispatch_noether",
        "py_state": "NoetherStateVector",
        "py_resolve": "resolve_noether_identity",
        "py_dispatch": "dispatch_noether",
        "py_key": "conserved_charge",
        "go_fields": [
            "ActionVariation   float64",
            "NoetherCurrentDiv float64",
            "ConservedCharge   float64",
            "QuantumAnomaly    float64",
            "EntropyGeneration float64",
        ],
        "rust_fields": [
            "pub action_variation: f64,",
            "pub noether_current_div: f64,",
            "pub conserved_charge: f64,",
            "pub quantum_anomaly: f64,",
            "pub entropy_generation: f64,",
        ],
        "rust_new": [
            "action_variation: 0.0,",
            "noether_current_div: 0.0,",
            "conserved_charge: 1.0,",
            "quantum_anomaly: 0.0,",
            "entropy_generation: 0.0,",
        ],
        "py_fields": [
            "self.action_variation = 0.0",
            "self.noether_current_div = 0.0",
            "self.conserved_charge = 1.0",
            "self.quantum_anomaly = 0.0",
            "self.entropy_generation = 0.0",
        ],
        "go_sim": [
            "vec.ActionVariation = math.Sin(float64(id.Code)) * 0.01",
            "if id.Modifier == NoetherModifierAnomalous {",
            "\tvec.QuantumAnomaly = 0.05 * math.Cos(float64(id.Code))",
            "} else {",
            "\tvec.QuantumAnomaly = 0.0",
            "}",
            "vec.NoetherCurrentDiv = vec.ActionVariation*0.1 + vec.QuantumAnomaly",
            "vec.ConservedCharge = math.Max(0.0, vec.ConservedCharge*0.99 + 0.1*math.Sin(float64(id.Code)))",
            "vec.EntropyGeneration = vec.NoetherCurrentDiv * vec.NoetherCurrentDiv",
        ],
        "rust_sim": [
            "vec.action_variation = (code as f64).sin() * 0.01;",
            "vec.quantum_anomaly = if m == 8 { 0.05 * (code as f64).cos() } else { 0.0 };",
            "vec.noether_current_div = vec.action_variation * 0.1 + vec.quantum_anomaly;",
            "vec.conserved_charge = (vec.conserved_charge * 0.99 + 0.1 * (code as f64).sin()).max(0.0);",
            "vec.entropy_generation = vec.noether_current_div * vec.noether_current_div;",
        ],
        "py_sim": [
            "vec.action_variation = math.sin(code) * 0.01",
            "vec.quantum_anomaly = 0.05 * math.cos(code) if m == 8 else 0.0",
            "vec.noether_current_div = vec.action_variation * 0.1 + vec.quantum_anomaly",
            "vec.conserved_charge = max(0.0, vec.conserved_charge * 0.99 + 0.1 * math.sin(code))",
            "vec.entropy_generation = vec.noether_current_div * vec.noether_current_div",
        ],
    },
    "Observer": {
        "yaml": "cortex/ontology/state_observer_1000_taxonomy.yaml",
        "prefix_upper": "OBS",
        "go_ident": "StateObserverIdentity",
        "go_state": "StateVector",
        "go_handler": "StateObserverHandler",
        "go_table": "StateObserverTable",
        "go_metrics": "StateObserverMetrics",
        "go_init": "InitStateObserverKernel",
        "go_dispatch": "DispatchStateObserver",
        "go_count": "GetStateObserverExecutionCount",
        "rust_ident": "StateObserverIdentity",
        "rust_state": "StateVector",
        "rust_dispatch": "dispatch_state_observer",
        "py_state": "StateVector",
        "py_resolve": "resolve_observer_identity",
        "py_dispatch": "dispatch_state_observer",
        "py_key": "norm_error",
        "go_fields": [
            "States      [64]float64",
            "Covariance  [64][64]float64",
            "Innovation  [64]float64",
            "Gain        [64][64]float64",
            "NormError   float64",
        ],
        "rust_fields": [
            "pub states: [f64; 64],",
            "pub covariance: [[f64; 64]; 64],",
            "pub innovation: [f64; 64],",
            "pub gain: [[f64; 64]; 64],",
            "pub norm_error: f64,",
        ],
        "rust_new": [
            "states: [0.0; 64],",
            "covariance: [[0.0; 64]; 64],",
            "innovation: [0.0; 64],",
            "gain: [[0.0; 64]; 64],",
            "norm_error: 0.0,",
        ],
        "py_fields": [
            "self.states = [0.0] * 64",
            "self.covariance = [[1.0 if i==j else 0.0 for j in range(64)] for i in range(64)]",
            "self.innovation = [0.0] * 64",
            "self.norm_error = 0.0",
        ],
        "go_sim": [
            "for i := 0; i < 64; i++ {",
            "\tstate.States[i] += math.Sin(float64(id.Code)+float64(i))*0.01",
            "\tstate.Innovation[i] = (math.Cos(float64(id.Code)) - state.States[i]) * 0.1",
            "\tstate.Covariance[i][i] = math.Max(0.001, state.Covariance[i][i]*0.99 + 0.0001)",
            "}",
            "sumSq := 0.0",
            "for i := 0; i < 64; i++ { sumSq += state.Innovation[i]*state.Innovation[i] }",
            "state.NormError = math.Sqrt(sumSq)",
        ],
        "rust_sim": [
            "for i in 0..64 {",
            "        vec.states[i] += (code as f64 + i as f64).sin() * 0.01;",
            "        vec.innovation[i] = ((code as f64).cos() - vec.states[i]) * 0.1;",
            "        vec.covariance[i][i] = f64::max(0.001, vec.covariance[i][i] * 0.99 + 0.0001);",
            "    }",
            "    vec.norm_error = vec.innovation.iter().map(|x| x.powi(2)).sum::<f64>().sqrt();",
        ],
        "py_sim": [
            "for i in range(64):",
            "    state.states[i] += math.sin(code + i) * 0.01",
            "    state.innovation[i] = (math.cos(code) - state.states[i]) * 0.1",
            "state.norm_error = math.sqrt(sum(x**2 for x in state.innovation))",
        ],
    },
    "Haskell": {
        "yaml": "cortex/ontology/haskell_1000_taxonomy.yaml",
        "prefix_upper": "HS",
        "go_ident": "HaskellIdentity",
        "go_state": "HaskellStateVector",
        "go_handler": "HaskellHandler",
        "go_table": "HaskellTable",
        "go_metrics": "HaskellMetrics",
        "go_init": "InitHaskellKernel",
        "go_dispatch": "DispatchHaskell",
        "go_count": "GetHaskellExecutionCount",
        "rust_ident": "HaskellIdentity",
        "rust_state": "HaskellStateVector",
        "rust_dispatch": "dispatch_haskell",
        "py_state": "HaskellStateVector",
        "py_resolve": "resolve_haskell_identity",
        "py_dispatch": "dispatch_haskell",
        "py_key": "compile_cost",
        "go_fields": [
            "ThunkDepth    float64",
            "MonadicDepth  float64",
            "CategoryDepth float64",
            "Concurrency   float64",
            "CompileCost   float64",
        ],
        "rust_fields": [
            "pub thunk_depth: f64,",
            "pub monadic_depth: f64,",
            "pub category_depth: f64,",
            "pub concurrency: f64,",
            "pub compile_cost: f64,",
        ],
        "rust_new": [
            "thunk_depth: 0.1,",
            "monadic_depth: 0.0,",
            "category_depth: 1.0,",
            "concurrency: 1.0,",
            "compile_cost: 0.0,",
        ],
        "py_fields": [
            "self.thunk_depth = 0.1",
            "self.monadic_depth = 0.0",
            "self.category_depth = 1.0",
            "self.concurrency = 1.0",
            "self.compile_cost = 0.0",
        ],
        "go_sim": [
            "vec.ThunkDepth = math.Max(0.01, vec.ThunkDepth*0.98 + 0.02*math.Cos(float64(id.Code)))",
            "vec.MonadicDepth = math.Abs(math.Sin(float64(id.Code))*0.1 - vec.ThunkDepth*0.05)",
            "vec.CategoryDepth = 1.0 / (1.0 + vec.MonadicDepth)",
            "vec.Concurrency = vec.CategoryDepth * (float64(id.Code%10) + 1.0)",
            "vec.CompileCost = math.Log2(1.0 + vec.Concurrency)",
        ],
        "rust_sim": [
            "vec.thunk_depth = f64::max(0.01, vec.thunk_depth * 0.98 + 0.02 * (code as f64).cos());",
            "vec.monadic_depth = ((code as f64).sin() * 0.1 - vec.thunk_depth * 0.05).abs();",
            "vec.category_depth = 1.0 / (1.0 + vec.monadic_depth);",
            "vec.concurrency = vec.category_depth * ((code % 10) as f64 + 1.0);",
            "vec.compile_cost = (1.0 + vec.concurrency).log2();",
        ],
        "py_sim": [
            "vec.thunk_depth = max(0.01, vec.thunk_depth * 0.98 + 0.02 * math.cos(code))",
            "vec.monadic_depth = abs(math.sin(code) * 0.1 - vec.thunk_depth * 0.05)",
            "vec.category_depth = 1.0 / (1.0 + vec.monadic_depth)",
            "vec.concurrency = vec.category_depth * (float(code % 10) + 1.0)",
            "vec.compile_cost = math.log2(1.0 + vec.concurrency)",
        ],
        "has_haskell_native": True,
        "hs_module": "Primitives.Haskell1000",
        "hs_file": "primitives/Haskell1000.hs",
    },
    "Neuro": {
        "yaml": "cortex/ontology/neuro_chain_1000_taxonomy.yaml",
        "prefix_upper": "NEURO",
        "go_ident": "NeuroChainIdentity",
        "go_state": "CognitiveChainVector",
        "go_handler": "NeuroChainHandler",
        "go_table": "NeuroChainTable",
        "go_metrics": "NeuroChainMetrics",
        "go_init": "InitNeuroChainKernel",
        "go_dispatch": "DispatchNeuroChain",
        "go_count": "GetNeuroChainExecutionCount",
        "rust_ident": "NeuroChainIdentity",
        "rust_state": "CognitiveChainVector",
        "rust_dispatch": "dispatch_neuro_chain",
        "py_state": "CognitiveChainVector",
        "py_resolve": "resolve_neuro_identity",
        "py_dispatch": "dispatch_neuro_chain",
        "py_key": "language_entropy",
        "go_fields": [
            "HomeostasisEnergy float64",
            "PredictionError    float64",
            "AttentionWeight   float64",
            "ActionTorque      float64",
            "LanguageEntropy   float64",
        ],
        "rust_fields": [
            "pub homeostasis_energy: f64,",
            "pub prediction_error: f64,",
            "pub attention_weight: f64,",
            "pub action_torque: f64,",
            "pub language_entropy: f64,",
        ],
        "rust_new": [
            "homeostasis_energy: 1.0,",
            "prediction_error: 0.0,",
            "attention_weight: 1.0,",
            "action_torque: 0.0,",
            "language_entropy: 0.0,",
        ],
        "py_fields": [
            "self.homeostasis_energy = 1.0",
            "self.prediction_error = 0.0",
            "self.attention_weight = 1.0",
            "self.action_torque = 0.0",
            "self.language_entropy = 0.0",
        ],
        "go_sim": [
            "vec.HomeostasisEnergy = math.Max(0.01, vec.HomeostasisEnergy*0.98 + 0.02*math.Cos(float64(id.Code)))",
            "vec.PredictionError = math.Abs(math.Sin(float64(id.Code))*0.1 - vec.HomeostasisEnergy*0.05)",
            "vec.AttentionWeight = 1.0 / (1.0 + vec.PredictionError)",
            "vec.ActionTorque = vec.AttentionWeight * (float64(id.Code%10) + 1.0)",
            "vec.LanguageEntropy = math.Log2(1.0 + vec.ActionTorque)",
        ],
        "rust_sim": [
            "vec.homeostasis_energy = f64::max(0.01, vec.homeostasis_energy * 0.98 + 0.02 * (code as f64).cos());",
            "vec.prediction_error = ((code as f64).sin() * 0.1 - vec.homeostasis_energy * 0.05).abs();",
            "vec.attention_weight = 1.0 / (1.0 + vec.prediction_error);",
            "vec.action_torque = vec.attention_weight * ((code % 10) as f64 + 1.0);",
            "vec.language_entropy = (1.0 + vec.action_torque).log2();",
        ],
        "py_sim": [
            "vec.homeostasis_energy = max(0.01, vec.homeostasis_energy * 0.98 + 0.02 * math.cos(code))",
            "vec.prediction_error = abs(math.sin(code) * 0.1 - vec.homeostasis_energy * 0.05)",
            "vec.attention_weight = 1.0 / (1.0 + vec.prediction_error)",
            "vec.action_torque = vec.attention_weight * (float(code % 10) + 1.0)",
            "vec.language_entropy = math.log2(1.0 + vec.action_torque)",
        ],
    },
    "Tts": {
        "yaml": "cortex/ontology/tts_harness_1000_taxonomy.yaml",
        "prefix_upper": "TTS",
        "go_ident": "TTSHarnessIdentity",
        "go_state": "TTSHarnessState",
        "go_handler": "TTSHarnessHandler",
        "go_table": "TTSHarnessTable",
        "go_metrics": "TTSHarnessMetrics",
        "go_init": "InitTTSHarnessKernel",
        "go_dispatch": "DispatchTTSHarness",
        "go_count": "GetTTSHarnessExecutionCount",
        "rust_ident": "TTSHarnessIdentity",
        "rust_state": "TTSHarnessState",
        "rust_dispatch": "dispatch_tts_harness",
        "py_state": "TTSHarnessState",
        "py_resolve": "resolve_tts_identity",
        "py_dispatch": "dispatch_tts_harness",
        "py_key": "harness_score",
        "go_fields": [
            "MCTSBudgetTokens uint64",
            "LatentValue      float64",
            "HarnessScore     float64",
            "KVCacheEfficiency float64",
            "PruningRate      float64",
        ],
        "rust_fields": [
            "pub mcts_budget_tokens: u64,",
            "pub latent_value: f64,",
            "pub harness_score: f64,",
            "pub kv_cache_efficiency: f64,",
            "pub pruning_rate: f64,",
        ],
        "rust_new": [
            "mcts_budget_tokens: 0,",
            "latent_value: 0.0,",
            "harness_score: 0.0,",
            "kv_cache_efficiency: 1.0,",
            "pruning_rate: 0.0,",
        ],
        "py_fields": [
            "self.mcts_budget_tokens = 0",
            "self.latent_value = 0.0",
            "self.harness_score = 0.0",
            "self.kv_cache_efficiency = 1.0",
            "self.pruning_rate = 0.0",
        ],
        "go_sim": [
            "state.MCTSBudgetTokens += uint64(id.Code%50) + 10",
            "state.LatentValue = math.Tanh(float64(id.Code) * 0.001)",
            "state.HarnessScore = 0.5 + 0.5*math.Sin(float64(id.Code))",
            "state.KVCacheEfficiency = math.Min(1.0, 0.2 + float64(id.Code%10)*0.08)",
            "state.PruningRate = 1.0 - state.KVCacheEfficiency*0.5",
        ],
        "rust_sim": [
            "vec.mcts_budget_tokens += (code % 50) as u64 + 10;",
            "vec.latent_value = (code as f64 * 0.001).tanh();",
            "vec.harness_score = 0.5 + 0.5 * (code as f64).sin();",
            "vec.kv_cache_efficiency = f64::min(1.0, 0.2 + (code % 10) as f64 * 0.08);",
            "vec.pruning_rate = 1.0 - vec.kv_cache_efficiency * 0.5;",
        ],
        "py_sim": [
            "vec.mcts_budget_tokens += (code % 50) + 10",
            "vec.latent_value = math.tanh(code * 0.001)",
            "vec.harness_score = 0.5 + 0.5 * math.sin(code)",
            "vec.kv_cache_efficiency = min(1.0, 0.2 + (code % 10) * 0.08)",
            "vec.pruning_rate = 1.0 - vec.kv_cache_efficiency * 0.5",
        ],
    },
    "Kimi": {
        "yaml": "cortex/ontology/kimi_1000_taxonomy.yaml",
        "prefix_upper": "KIMI",
        "go_ident": "KimiIdentity",
        "go_state": "KimiStateVector",
        "go_handler": "KimiHandler",
        "go_table": "KimiTable",
        "go_metrics": "KimiMetrics",
        "go_init": "InitKimiKernel",
        "go_dispatch": "DispatchKimi",
        "go_count": "GetKimiExecutionCount",
        "rust_ident": "KimiIdentity",
        "rust_state": "KimiStateVector",
        "rust_dispatch": "dispatch_kimi",
        "py_state": "KimiStateVector",
        "py_resolve": "resolve_kimi_identity",
        "py_dispatch": "dispatch_kimi",
        "py_key": "daimon_latency",
        "go_fields": [
            "DaimonLatency       float64",
            "TaintScore           float64",
            "PromptSize           float64",
            "CacheHits            float64",
            "BftValidationCount   uint64",
        ],
        "rust_fields": [
            "pub daimon_latency: f64,",
            "pub taint_score: f64,",
            "pub prompt_size: f64,",
            "pub cache_hits: f64,",
            "pub bft_validation_count: u64,",
        ],
        "rust_new": [
            "daimon_latency: 0.0,",
            "taint_score: 0.0,",
            "prompt_size: 0.0,",
            "cache_hits: 0.0,",
            "bft_validation_count: 0,",
        ],
        "py_fields": [
            "self.daimon_latency = 0.0",
            "self.taint_score = 0.0",
            "self.prompt_size = 0.0",
            "self.cache_hits = 0.0",
            "self.bft_validation_count = 0",
        ],
        "go_sim": [
            "vec.DaimonLatency = math.Max(0.001, vec.DaimonLatency*0.95 + 0.05*math.Abs(math.Sin(float64(id.Code))))",
            "vec.TaintScore = math.Max(0.0, math.Min(100.0, vec.TaintScore + math.Cos(float64(id.Code))*5.0))",
            "vec.PromptSize = math.Max(0.0, vec.PromptSize + float64(id.Code%50) - 25.0)",
            "vec.CacheHits = vec.CacheHits*0.99 + 0.01*float64(id.Code%2)",
            "vec.BftValidationCount += uint64(id.Code%5)",
        ],
        "rust_sim": [
            "vec.daimon_latency = f64::max(0.001, vec.daimon_latency * 0.95 + 0.05 * (code as f64).sin().abs());",
            "vec.taint_score = f64::max(0.0, f64::min(100.0, vec.taint_score + (code as f64).cos() * 5.0));",
            "vec.prompt_size = f64::max(0.0, vec.prompt_size + (code % 50) as f64 - 25.0);",
            "vec.cache_hits = vec.cache_hits * 0.99 + 0.01 * (code % 2) as f64;",
            "vec.bft_validation_count += (code % 5) as u64;",
        ],
        "py_sim": [
            "vec.daimon_latency = max(0.001, vec.daimon_latency * 0.95 + 0.05 * abs(math.sin(code)))",
            "vec.taint_score = max(0.0, min(100.0, vec.taint_score + math.cos(code) * 5.0))",
            "vec.prompt_size = max(0.0, vec.prompt_size + (code % 50) - 25.0)",
            "vec.cache_hits = vec.cache_hits * 0.99 + 0.01 * (code % 2)",
            "vec.bft_validation_count += (code % 5)",
        ],
        "has_haskell_native": True,
        "hs_module": "Primitives.Kimi1000",
        "hs_file": "primitives/Kimi1000.hs",
    },
    "Playwright": {
        "yaml": "cortex/ontology/playwright_1000_taxonomy.yaml",
        "prefix_upper": "PW",
        "go_ident": "PlaywrightIdentity",
        "go_state": "PlaywrightStateVector",
        "go_handler": "PlaywrightHandler",
        "go_table": "PlaywrightTable",
        "go_metrics": "PlaywrightMetrics",
        "go_init": "InitPlaywrightKernel",
        "go_dispatch": "DispatchPlaywright",
        "go_count": "GetPlaywrightExecutionCount",
        "rust_ident": "PlaywrightIdentity",
        "rust_state": "PlaywrightStateVector",
        "rust_dispatch": "dispatch_playwright",
        "py_state": "PlaywrightStateVector",
        "py_resolve": "resolve_playwright_identity",
        "py_dispatch": "dispatch_playwright",
        "py_key": "dom_stability_index",
        "go_fields": [
            "BrowserActive     bool",
            "PageCount         uint64",
            "LastLoadTimeMS    float64",
            "DomStabilityIndex float64",
            "NetworkIdleState  bool",
        ],
        "rust_fields": [
            "pub browser_active: bool,",
            "pub page_count: u64,",
            "pub last_load_time_ms: f64,",
            "pub dom_stability_index: f64,",
            "pub network_idle_state: bool,",
        ],
        "rust_new": [
            "browser_active: false,",
            "page_count: 0,",
            "last_load_time_ms: 0.0,",
            "dom_stability_index: 1.0,",
            "network_idle_state: true,",
        ],
        "py_fields": [
            "self.browser_active = False",
            "self.page_count = 0",
            "self.last_load_time_ms = 0.0",
            "self.dom_stability_index = 1.0",
            "self.network_idle_state = True",
        ],
        "go_sim": [
            "vec.BrowserActive = id.Domain != PlaywrightDomainBrowsernav || id.Primitive != PlaywrightPrimitiveClose",
            "if id.Domain == PlaywrightDomainBrowsernav && id.Primitive == PlaywrightPrimitiveInit { vec.PageCount++ }",
            "vec.LastLoadTimeMS = math.Abs(math.Sin(float64(id.Code))) * 120.0",
            "vec.DomStabilityIndex = math.Max(0.0, math.Min(1.0, vec.DomStabilityIndex * 0.95 + 0.05 * math.Cos(float64(id.Code))))",
            "vec.NetworkIdleState = id.Modifier == PlaywrightModifierWaitidle",
        ],
        "rust_sim": [
            "vec.browser_active = d != 0 || p != 9;",
            "if d == 0 && p == 0 { vec.page_count += 1; }",
            "vec.last_load_time_ms = (code as f64).sin().abs() * 120.0;",
            "vec.dom_stability_index = f64::max(0.0, f64::min(1.0, vec.dom_stability_index * 0.95 + 0.05 * (code as f64).cos()));",
            "vec.network_idle_state = m == 3;",
        ],
        "py_sim": [
            "vec.browser_active = d != 0 or p != 9",
            "if d == 0 and p == 0:",
            "    vec.page_count += 1",
            "vec.last_load_time_ms = abs(math.sin(code)) * 120.0",
            "vec.dom_stability_index = max(0.0, min(1.0, vec.dom_stability_index * 0.95 + 0.05 * math.cos(code)))",
            "vec.network_idle_state = m == 3",
        ],
    },
}

