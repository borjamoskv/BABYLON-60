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
            "PlanckScaleRatio        [64]float64",
            "GravitationalCoupling   [64]float64",
            "ElectromagneticShielding [64]float64",
            "QuantumEntropy          [64]float64",
            "SingularityDensity      [64]float64",
        ],
        "rust_fields": [
            "pub planck_scale_ratio: [f64; 64],",
            "pub gravitational_coupling: [f64; 64],",
            "pub electromagnetic_shielding: [f64; 64],",
            "pub quantum_entropy: [f64; 64],",
            "pub singularity_density: [f64; 64],",
        ],
        "rust_new": [
            "planck_scale_ratio: [1.616255e-35; 64],",
            "gravitational_coupling: [6.67430e-11; 64],",
            "electromagnetic_shielding: [1.602176634e-19; 64],",
            "quantum_entropy: [1.054571817e-34; 64],",
            "singularity_density: [0.0; 64],",
        ],
        "py_fields": [
            "self.planck_scale_ratio = [1.616255e-35] * 64",
            "self.gravitational_coupling = [6.67430e-11] * 64",
            "self.electromagnetic_shielding = [1.602176634e-19] * 64",
            "self.quantum_entropy = [1.054571817e-34] * 64",
            "self.singularity_density = [0.0] * 64",
        ],
        "go_sim": [
            "for i := 0; i < 64; i++ {",
            "\tvec.PlanckScaleRatio[i] = math.Abs(math.Sin(float64(id.Code)+float64(i))) * 1.616255e-35",
            "\tvec.GravitationalCoupling[i] = 6.67430e-11 * (1.0 + 0.01*math.Cos(float64(id.Code)+float64(i)))",
            "\tvec.ElectromagneticShielding[i] = 1.602176634e-19 * (float64(id.Code%10) + float64(i) + 1.0)",
            "\tvec.QuantumEntropy[i] = math.Max(0.0, vec.QuantumEntropy[i]*0.99 + 1.054571817e-34*(float64(id.Code)+float64(i)))",
            "\tvec.SingularityDensity[i] = vec.GravitationalCoupling[i] / math.Max(1e-100, vec.PlanckScaleRatio[i]*vec.PlanckScaleRatio[i])",
            "}",
        ],
        "rust_sim": [
            "for i in 0..64 {",
            "        vec.planck_scale_ratio[i] = (code as f64 + i as f64).sin().abs() * 1.616255e-35;",
            "        vec.gravitational_coupling[i] = 6.67430e-11 * (1.0 + 0.01 * (code as f64 + i as f64).cos());",
            "        vec.electromagnetic_shielding[i] = 1.602176634e-19 * ((code % 10) as f64 + i as f64 + 1.0);",
            "        vec.quantum_entropy[i] = f64::max(0.0, vec.quantum_entropy[i] * 0.99 + 1.054571817e-34 * (code as f64 + i as f64));",
            "        vec.singularity_density[i] = vec.gravitational_coupling[i] / f64::max(1e-100, vec.planck_scale_ratio[i] * vec.planck_scale_ratio[i]);",
            "    }",
        ],
        "py_sim": [
            "for i in range(64):",
            "    vec.planck_scale_ratio[i] = abs(math.sin(code + i)) * 1.616255e-35",
            "    vec.gravitational_coupling[i] = 6.67430e-11 * (1.0 + 0.01 * math.cos(code + i))",
            "    vec.electromagnetic_shielding[i] = 1.602176634e-19 * (float(code % 10) + i + 1.0)",
            "    vec.quantum_entropy[i] = max(0.0, vec.quantum_entropy[i] * 0.99 + 1.054571817e-34 * float(code + i))",
            "    vec.singularity_density[i] = vec.gravitational_coupling[i] / max(1e-100, vec.planck_scale_ratio[i] * vec.planck_scale_ratio[i])",
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
            "ActionVariation   [64]float64",
            "NoetherCurrentDiv [64]float64",
            "ConservedCharge   [64]float64",
            "QuantumAnomaly    [64]float64",
            "EntropyGeneration [64]float64",
        ],
        "rust_fields": [
            "pub action_variation: [f64; 64],",
            "pub noether_current_div: [f64; 64],",
            "pub conserved_charge: [f64; 64],",
            "pub quantum_anomaly: [f64; 64],",
            "pub entropy_generation: [f64; 64],",
        ],
        "rust_new": [
            "action_variation: [0.0; 64],",
            "noether_current_div: [0.0; 64],",
            "conserved_charge: [1.0; 64],",
            "quantum_anomaly: [0.0; 64],",
            "entropy_generation: [0.0; 64],",
        ],
        "py_fields": [
            "self.action_variation = [0.0] * 64",
            "self.noether_current_div = [0.0] * 64",
            "self.conserved_charge = [1.0] * 64",
            "self.quantum_anomaly = [0.0] * 64",
            "self.entropy_generation = [0.0] * 64",
        ],
        "go_sim": [
            "for i := 0; i < 64; i++ {",
            "\tvec.ActionVariation[i] = math.Sin(float64(id.Code)+float64(i)) * 0.01",
            "\tif id.Modifier == NoetherModifierAnomalous {",
            "\t\tvec.QuantumAnomaly[i] = 0.05 * math.Cos(float64(id.Code)+float64(i))",
            "\t} else {",
            "\t\tvec.QuantumAnomaly[i] = 0.0",
            "\t}",
            "\tvec.NoetherCurrentDiv[i] = vec.ActionVariation[i]*0.1 + vec.QuantumAnomaly[i]",
            "\tvec.ConservedCharge[i] = math.Max(0.0, vec.ConservedCharge[i]*0.99 + 0.1*math.Sin(float64(id.Code)+float64(i)))",
            "\tvec.EntropyGeneration[i] = vec.NoetherCurrentDiv[i] * vec.NoetherCurrentDiv[i]",
            "}",
        ],
        "rust_sim": [
            "for i in 0..64 {",
            "        vec.action_variation[i] = (code as f64 + i as f64).sin() * 0.01;",
            "        vec.quantum_anomaly[i] = if m == 8 { 0.05 * (code as f64 + i as f64).cos() } else { 0.0 };",
            "        vec.noether_current_div[i] = vec.action_variation[i] * 0.1 + vec.quantum_anomaly[i];",
            "        vec.conserved_charge[i] = (vec.conserved_charge[i] * 0.99 + 0.1 * (code as f64 + i as f64).sin()).max(0.0);",
            "        vec.entropy_generation[i] = vec.noether_current_div[i] * vec.noether_current_div[i];",
            "    }",
        ],
        "py_sim": [
            "for i in range(64):",
            "    vec.action_variation[i] = math.sin(code + i) * 0.01",
            "    vec.quantum_anomaly[i] = 0.05 * math.cos(code + i) if m == 8 else 0.0",
            "    vec.noether_current_div[i] = vec.action_variation[i] * 0.1 + vec.quantum_anomaly[i]",
            "    vec.conserved_charge[i] = max(0.0, vec.conserved_charge[i] * 0.99 + 0.1 * math.sin(code + i))",
            "    vec.entropy_generation[i] = vec.noether_current_div[i] * vec.noether_current_div[i]",
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
            "ThunkDepth    [64]float64",
            "MonadicDepth  [64]float64",
            "CategoryDepth [64]float64",
            "Concurrency   [64]float64",
            "CompileCost   [64]float64",
        ],
        "rust_fields": [
            "pub thunk_depth: [f64; 64],",
            "pub monadic_depth: [f64; 64],",
            "pub category_depth: [f64; 64],",
            "pub concurrency: [f64; 64],",
            "pub compile_cost: [f64; 64],",
        ],
        "rust_new": [
            "thunk_depth: [0.1; 64],",
            "monadic_depth: [0.0; 64],",
            "category_depth: [1.0; 64],",
            "concurrency: [1.0; 64],",
            "compile_cost: [0.0; 64],",
        ],
        "py_fields": [
            "self.thunk_depth = [0.1] * 64",
            "self.monadic_depth = [0.0] * 64",
            "self.category_depth = [1.0] * 64",
            "self.concurrency = [1.0] * 64",
            "self.compile_cost = [0.0] * 64",
        ],
        "go_sim": [
            "for i := 0; i < 64; i++ {",
            "\tvec.ThunkDepth[i] = math.Max(0.01, vec.ThunkDepth[i]*0.98 + 0.02*math.Cos(float64(id.Code)+float64(i)))",
            "\tvec.MonadicDepth[i] = math.Abs(math.Sin(float64(id.Code)+float64(i))*0.1 - vec.ThunkDepth[i]*0.05)",
            "\tvec.CategoryDepth[i] = 1.0 / (1.0 + vec.MonadicDepth[i])",
            "\tvec.Concurrency[i] = vec.CategoryDepth[i] * (float64((uint64(id.Code)+uint64(i))%10) + 1.0)",
            "\tvec.CompileCost[i] = math.Log2(1.0 + vec.Concurrency[i])",
            "}",
        ],
        "rust_sim": [
            "for i in 0..64 {",
            "        vec.thunk_depth[i] = f64::max(0.01, vec.thunk_depth[i] * 0.98 + 0.02 * (code as f64 + i as f64).cos());",
            "        vec.monadic_depth[i] = ((code as f64 + i as f64).sin() * 0.1 - vec.thunk_depth[i] * 0.05).abs();",
            "        vec.category_depth[i] = 1.0 / (1.0 + vec.monadic_depth[i]);",
            "        vec.concurrency[i] = vec.category_depth[i] * (((code + i as u64) % 10) as f64 + 1.0);",
            "        vec.compile_cost[i] = (1.0 + vec.concurrency[i]).log2();",
            "    }",
        ],
        "py_sim": [
            "for i in range(64):",
            "    vec.thunk_depth[i] = max(0.01, vec.thunk_depth[i] * 0.98 + 0.02 * math.cos(code + i))",
            "    vec.monadic_depth[i] = abs(math.sin(code + i) * 0.1 - vec.thunk_depth[i] * 0.05)",
            "    vec.category_depth[i] = 1.0 / (1.0 + vec.monadic_depth[i])",
            "    vec.concurrency[i] = vec.category_depth[i] * (float((code + i) % 10) + 1.0)",
            "    vec.compile_cost[i] = math.log2(1.0 + vec.concurrency[i])",
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
            "HomeostasisEnergy [64]float64",
            "PredictionError   [64]float64",
            "AttentionWeight   [64]float64",
            "ActionTorque      [64]float64",
            "LanguageEntropy   [64]float64",
        ],
        "rust_fields": [
            "pub homeostasis_energy: [f64; 64],",
            "pub prediction_error: [f64; 64],",
            "pub attention_weight: [f64; 64],",
            "pub action_torque: [f64; 64],",
            "pub language_entropy: [f64; 64],",
        ],
        "rust_new": [
            "homeostasis_energy: [1.0; 64],",
            "prediction_error: [0.0; 64],",
            "attention_weight: [1.0; 64],",
            "action_torque: [0.0; 64],",
            "language_entropy: [0.0; 64],",
        ],
        "py_fields": [
            "self.homeostasis_energy = [1.0] * 64",
            "self.prediction_error = [0.0] * 64",
            "self.attention_weight = [1.0] * 64",
            "self.action_torque = [0.0] * 64",
            "self.language_entropy = [0.0] * 64",
        ],
        "go_sim": [
            "for i := 0; i < 64; i++ {",
            "\tvec.HomeostasisEnergy[i] = math.Max(0.01, vec.HomeostasisEnergy[i]*0.98 + 0.02*math.Cos(float64(id.Code)+float64(i)))",
            "\tvec.PredictionError[i] = math.Abs(math.Sin(float64(id.Code)+float64(i))*0.1 - vec.HomeostasisEnergy[i]*0.05)",
            "\tvec.AttentionWeight[i] = 1.0 / (1.0 + vec.PredictionError[i])",
            "\tvec.ActionTorque[i] = vec.AttentionWeight[i] * (float64((uint64(id.Code)+uint64(i))%10) + 1.0)",
            "\tvec.LanguageEntropy[i] = math.Log2(1.0 + vec.ActionTorque[i])",
            "}",
        ],
        "rust_sim": [
            "for i in 0..64 {",
            "        vec.homeostasis_energy[i] = f64::max(0.01, vec.homeostasis_energy[i] * 0.98 + 0.02 * (code as f64 + i as f64).cos());",
            "        vec.prediction_error[i] = ((code as f64 + i as f64).sin() * 0.1 - vec.homeostasis_energy[i] * 0.05).abs();",
            "        vec.attention_weight[i] = 1.0 / (1.0 + vec.prediction_error[i]);",
            "        vec.action_torque[i] = vec.attention_weight[i] * (((code + i as u64) % 10) as f64 + 1.0);",
            "        vec.language_entropy[i] = (1.0 + vec.action_torque[i]).log2();",
            "    }",
        ],
        "py_sim": [
            "for i in range(64):",
            "    vec.homeostasis_energy[i] = max(0.01, vec.homeostasis_energy[i] * 0.98 + 0.02 * math.cos(code + i))",
            "    vec.prediction_error[i] = abs(math.sin(code + i) * 0.1 - vec.homeostasis_energy[i] * 0.05)",
            "    vec.attention_weight[i] = 1.0 / (1.0 + vec.prediction_error[i])",
            "    vec.action_torque[i] = vec.attention_weight[i] * (float((code + i) % 10) + 1.0)",
            "    vec.language_entropy[i] = math.log2(1.0 + vec.action_torque[i])",
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
            "MCTSBudgetTokens  [64]uint64",
            "LatentValue       [64]float64",
            "HarnessScore      [64]float64",
            "KVCacheEfficiency [64]float64",
            "PruningRate       [64]float64",
        ],
        "rust_fields": [
            "pub mcts_budget_tokens: [u64; 64],",
            "pub latent_value: [f64; 64],",
            "pub harness_score: [f64; 64],",
            "pub kv_cache_efficiency: [f64; 64],",
            "pub pruning_rate: [f64; 64],",
        ],
        "rust_new": [
            "mcts_budget_tokens: [0; 64],",
            "latent_value: [0.0; 64],",
            "harness_score: [0.0; 64],",
            "kv_cache_efficiency: [1.0; 64],",
            "pruning_rate: [0.0; 64],",
        ],
        "py_fields": [
            "self.mcts_budget_tokens = [0] * 64",
            "self.latent_value = [0.0] * 64",
            "self.harness_score = [0.0] * 64",
            "self.kv_cache_efficiency = [1.0] * 64",
            "self.pruning_rate = [0.0] * 64",
        ],
        "go_sim": [
            "for i := 0; i < 64; i++ {",
            "\tvec.MCTSBudgetTokens[i] += uint64((uint64(id.Code)+uint64(i))%50) + 10",
            "\tvec.LatentValue[i] = math.Tanh(float64(uint64(id.Code)+uint64(i)) * 0.001)",
            "\tvec.HarnessScore[i] = 0.5 + 0.5*math.Sin(float64(uint64(id.Code)+uint64(i)))",
            "\tvec.KVCacheEfficiency[i] = math.Min(1.0, 0.2 + float64((uint64(id.Code)+uint64(i))%10)*0.08)",
            "\tvec.PruningRate[i] = 1.0 - vec.KVCacheEfficiency[i]*0.5",
            "}",
        ],
        "rust_sim": [
            "for i in 0..64 {",
            "        vec.mcts_budget_tokens[i] += ((code + i as u64) % 50) as u64 + 10;",
            "        vec.latent_value[i] = ((code as f64 + i as f64) * 0.001).tanh();",
            "        vec.harness_score[i] = 0.5 + 0.5 * (code as f64 + i as f64).sin();",
            "        vec.kv_cache_efficiency[i] = f64::min(1.0, 0.2 + ((code + i as u64) % 10) as f64 * 0.08);",
            "        vec.pruning_rate[i] = 1.0 - vec.kv_cache_efficiency[i] * 0.5;",
            "    }",
        ],
        "py_sim": [
            "for i in range(64):",
            "    vec.mcts_budget_tokens[i] += ((code + i) % 50) + 10",
            "    vec.latent_value[i] = math.tanh((code + i) * 0.001)",
            "    vec.harness_score[i] = 0.5 + 0.5 * math.sin(code + i)",
            "    vec.kv_cache_efficiency[i] = min(1.0, 0.2 + ((code + i) % 10) * 0.08)",
            "    vec.pruning_rate[i] = 1.0 - vec.kv_cache_efficiency[i] * 0.5",
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
            "DaimonLatency      [64]float64",
            "TaintScore         [64]float64",
            "PromptSize         [64]float64",
            "CacheHits          [64]float64",
            "BftValidationCount [64]uint64",
        ],
        "rust_fields": [
            "pub daimon_latency: [f64; 64],",
            "pub taint_score: [f64; 64],",
            "pub prompt_size: [f64; 64],",
            "pub cache_hits: [f64; 64],",
            "pub bft_validation_count: [u64; 64],",
        ],
        "rust_new": [
            "daimon_latency: [0.0; 64],",
            "taint_score: [0.0; 64],",
            "prompt_size: [0.0; 64],",
            "cache_hits: [0.0; 64],",
            "bft_validation_count: [0; 64],",
        ],
        "py_fields": [
            "self.daimon_latency = [0.0] * 64",
            "self.taint_score = [0.0] * 64",
            "self.prompt_size = [0.0] * 64",
            "self.cache_hits = [0.0] * 64",
            "self.bft_validation_count = [0] * 64",
        ],
        "go_sim": [
            "for i := 0; i < 64; i++ {",
            "\tvec.DaimonLatency[i] = math.Max(0.001, vec.DaimonLatency[i]*0.95 + 0.05*math.Abs(math.Sin(float64(id.Code)+float64(i))))",
            "\tvec.TaintScore[i] = math.Max(0.0, math.Min(100.0, vec.TaintScore[i] + math.Cos(float64(id.Code)+float64(i))*5.0))",
            "\tvec.PromptSize[i] = math.Max(0.0, vec.PromptSize[i] + float64((uint64(id.Code)+uint64(i))%50) - 25.0)",
            "\tvec.CacheHits[i] = vec.CacheHits[i]*0.99 + 0.01*float64((uint64(id.Code)+uint64(i))%2)",
            "\tvec.BftValidationCount[i] += uint64((uint64(id.Code)+uint64(i))%5)",
            "}",
        ],
        "rust_sim": [
            "for i in 0..64 {",
            "        vec.daimon_latency[i] = f64::max(0.001, vec.daimon_latency[i] * 0.95 + 0.05 * (code as f64 + i as f64).sin().abs());",
            "        vec.taint_score[i] = f64::max(0.0, f64::min(100.0, vec.taint_score[i] + (code as f64 + i as f64).cos() * 5.0));",
            "        vec.prompt_size[i] = f64::max(0.0, vec.prompt_size[i] + ((code + i as u64) % 50) as f64 - 25.0);",
            "        vec.cache_hits[i] = vec.cache_hits[i] * 0.99 + 0.01 * ((code + i as u64) % 2) as f64;",
            "        vec.bft_validation_count[i] += ((code + i as u64) % 5) as u64;",
            "    }",
        ],
        "py_sim": [
            "for i in range(64):",
            "    vec.daimon_latency[i] = max(0.001, vec.daimon_latency[i] * 0.95 + 0.05 * abs(math.sin(code + i)))",
            "    vec.taint_score[i] = max(0.0, min(100.0, vec.taint_score[i] + math.cos(code + i) * 5.0))",
            "    vec.prompt_size[i] = max(0.0, vec.prompt_size[i] + ((code + i) % 50) - 25.0)",
            "    vec.cache_hits[i] = vec.cache_hits[i] * 0.99 + 0.01 * ((code + i) % 2)",
            "    vec.bft_validation_count[i] += ((code + i) % 5)",
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
            "BrowserActive     [64]bool",
            "PageCount         [64]uint64",
            "LastLoadTimeMS    [64]float64",
            "DomStabilityIndex [64]float64",
            "NetworkIdleState  [64]bool",
        ],
        "rust_fields": [
            "pub browser_active: [bool; 64],",
            "pub page_count: [u64; 64],",
            "pub last_load_time_ms: [f64; 64],",
            "pub dom_stability_index: [f64; 64],",
            "pub network_idle_state: [bool; 64],",
        ],
        "rust_new": [
            "browser_active: [false; 64],",
            "page_count: [0; 64],",
            "last_load_time_ms: [0.0; 64],",
            "dom_stability_index: [1.0; 64],",
            "network_idle_state: [true; 64],",
        ],
        "py_fields": [
            "self.browser_active = [False] * 64",
            "self.page_count = [0] * 64",
            "self.last_load_time_ms = [0.0] * 64",
            "self.dom_stability_index = [1.0] * 64",
            "self.network_idle_state = [True] * 64",
        ],
        "go_sim": [
            "for i := 0; i < 64; i++ {",
            "\tvec.BrowserActive[i] = id.Domain != PlaywrightDomainBrowsernav || id.Primitive != PlaywrightPrimitiveClose",
            "\tif id.Domain == PlaywrightDomainBrowsernav && id.Primitive == PlaywrightPrimitiveInit { vec.PageCount[i]++ }",
            "\tvec.LastLoadTimeMS[i] = math.Abs(math.Sin(float64(id.Code)+float64(i))) * 120.0",
            "\tvec.DomStabilityIndex[i] = math.Max(0.0, math.Min(1.0, vec.DomStabilityIndex[i] * 0.95 + 0.05 * math.Cos(float64(id.Code)+float64(i))))",
            "\tvec.NetworkIdleState[i] = id.Modifier == PlaywrightModifierWaitidle",
            "}",
        ],
        "rust_sim": [
            "for i in 0..64 {",
            "        vec.browser_active[i] = d != 0 || p != 9;",
            "        if d == 0 && p == 0 { vec.page_count[i] += 1; }",
            "        vec.last_load_time_ms[i] = (code as f64 + i as f64).sin().abs() * 120.0;",
            "        vec.dom_stability_index[i] = f64::max(0.0, f64::min(1.0, vec.dom_stability_index[i] * 0.95 + 0.05 * (code as f64 + i as f64).cos()));",
            "        vec.network_idle_state[i] = m == 3;",
            "    }",
        ],
        "py_sim": [
            "for i in range(64):",
            "    vec.browser_active[i] = d != 0 or p != 9",
            "    if d == 0 and p == 0:",
            "        vec.page_count[i] += 1",
            "    vec.last_load_time_ms[i] = abs(math.sin(code + i)) * 120.0",
            "    vec.dom_stability_index[i] = max(0.0, min(1.0, vec.dom_stability_index[i] * 0.95 + 0.05 * math.cos(code + i)))",
            "    vec.network_idle_state[i] = m == 3",
        ],
    },
}
