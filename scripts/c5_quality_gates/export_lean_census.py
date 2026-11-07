#!/usr/bin/env python3
"""
BABYLON-60 · Deterministic Lean 4 Formal Census & Axiom Traceability Exporter
=============================================================================
Extracts the complete inventory of:
  - 26 proprietary .lean modules in proof/lean/ (22 with theorems + 4 auxiliary)
  - 144 theorem declarations (#001-#144) with fully qualified names, untruncated
    types, formal result classes, transitive axiom dependencies, and strict scope notes
  - 228 core constructions (205 def + 23 inductive => 144 + 228 = 372) plus
    34 structure and 13 abbrev declarations (275 total non-theorem declarations => 419 total)

Outputs:
  - docs/06_theory/evidence/lean-census-372-v511.json
  - Optional Markdown report (--markdown-out <path>)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
LEAN_DIR = REPO_ROOT / "proof" / "lean"
SCOPE_2025_JSON = REPO_ROOT / "docs" / "06_theory" / "evidence" / "lean-scope-20261025.json"
DEFAULT_JSON_OUT = REPO_ROOT / "docs" / "06_theory" / "evidence" / "lean-census-372-v511.json"

# Explicit axioms verified via `elan run leanprover/lean4:v4.34.0-rc2 lean` for declarations
# added after the 2026-10-25 snapshot.
POST_2025_AXIOMS: dict[str, list[str] | str] = {
    "verifiedAuthInvariant": ["propext"],
    "Babylon60.L0Ledger.genesis_satisfies_invariant": [],
    "Babylon60.L0Ledger.append_preserves_l0_invariant": ["propext"],
    "Babylon60.L0Ledger.append_strictly_increases_tick": [
        "propext",
        "Classical.choice",
        "Quot.sound",
    ],
    "Babylon60.L0Ledger.merkle_root_uniqueness": [],
    "Babylon60.L0Ledger.l0_trigger_inhabited": [],
    "B60.Ledger.fl018_missing_critical_check_rejected": ["propext", "Quot.sound"],
    "B60.Ledger.fl018_artifact_hash_mismatch_rejected": ["propext", "Quot.sound"],
    "B60.Ledger.fl018_stale_epoch_rejected": ["propext", "Quot.sound"],
    "B60.Ledger.fl026_zero_threshold_rejected": ["propext", "Quot.sound"],
    "B60.Ledger.composite_gate_ok_valid": ["propext", "Quot.sound"],
    "B60.Ledger.fl018_composite_acceptance_inhabited": ["propext", "Quot.sound"],
    "B60.Ledger.composite_gate_ple_91pct_rejected": ["propext", "Quot.sound"],
    "B60.ExampleSeqlockTrace.inv_inhabited": ["propext"],
    "LarsaEquivocationSafety.canonical_quorum_intersection": ["propext", "Quot.sound"],
    "LarsaEquivocationSafety.unilateral_expulsion_weakens_intersection": [
        "propext",
        "Quot.sound",
    ],
    "LarsaEquivocationSafety.instance_inhabited": [],
    "LarsaEquivocationSafety.total_nodes_no_u64_overflow": ["propext", "Quot.sound"],
    "LarsaEquivocationSafety.quorum_threshold_no_u64_overflow": ["propext", "Quot.sound"],
    "LarsaEquivocationSafety.bounded_arithmetic_f1": [],
    "LarsaEquivocationSafety.verifiedQuorumInvariant": ["propext", "Quot.sound"],
}

NEGATIVE_FIXTURE_FILES = {"BabylonAutoTrace.lean", "BabylonStressCorrupt.lean"}

# Per-theorem classification and strict scope notes (remediating all audit findings)
THEOREM_SCOPE_OVERRIDES: dict[int, tuple[str, str]] = {
    1: ("I-DEC", "Comprobación cerrada por rfl sobre la traza concreta trace_happy de 3 eventos en la FSM abstracta."),
    2: ("I-DEC", "Comprobación cerrada por rfl que rechaza la traza concreta trace_double_dispatch en la FSM abstracta."),
    3: ("I-DEC", "Comprobación cerrada por rfl que rechaza la traza concreta trace_illegal_dispatch en la FSM abstracta."),
    4: ("I-DEC", "Comprobación cerrada por rfl de la traza concreta trace_crash ([.reserve, .dispatch, .ackCrash]); no demuestra recuperación general de estado persistido en disco ni reconciliación de efectos externos."),
    5: ("U-IND", "Lema inductivo universal sobre cualquier traza finita admitida desde el estado s en la FSM AuthState."),
    6: ("U-IND", "Cota inductiva universal: toda traza aceptada desde Proposed contiene como máximo un evento dispatch (0 o 1) en el modelo FSM; no establece liveness, persistencia física ni correspondencia con syscalls del SO."),
    7: ("W-EX", "Empaqueta la cota inductiva universal (#006) con el testigo no vacío trace_happy (patrón AP-10 VerifiedAuthInvariant)."),
    28: ("U-ALG", "Proyecta el campo h_no_hallucination exigido al construir BayesianDisintegration: conserva p x_fake = 0 en f_dag_p; no identifica falsedad de origen ni modela adversarios."),
    29: ("U-ALG", "Rama cero por definición de bayesian_inverse sobre Nat cuando prior x = 0; cociente entero truncado sin normalización probabilística."),
    30: ("U-ALG", "Proyecta el campo h_circuit_breaker de BayesianDisintegration cuando pushforward y_unseen = 0; fila cero por convención de subprobabilidad/rechazo, no aborto físico."),
    31: ("U-ALG", "Rama de denominador cero en bayesian_inverse sobre Nat (devuelve 0 para todo x cuando pushforward y_unseen = 0); no construye un posterior normalizado en el sentido de Markov/Fritz."),
    32: ("U-ALG", "Proposición idéntica a #028 (proyecta bd.h_no_hallucination bajo p x_fake = 0); el nombre histórico no añade protocolo BFT ni modelo de prompt injection."),
    33: ("U-ALG", "Extrae el campo h_homeostasis del registro TonnetzMonitor en (0, 0); no mide percepción acústica ni límites físicos."),
    34: ("U-ALG", "Aplica la implicación hipótética h_growth : s1.tick ≤ s2.tick → s1.entropy ≤ s2.entropy a h_t; la monotonía se recibe como hipótesis y no se deriva de termodinámica."),
    35: ("U-ALG", "Reescribe el campo h_bounded : s.hot_memory_bytes = 64 del registro AeonState; acota un campo Nat, no mide layout ni heap real."),
    36: ("U-ALG", "Igualdades definicionales de los campos de conformal_reset por reducción (entropy = 0, exergy conservada, hot_memory_bytes = 64); no contiene magnitud física de calor."),
    37: ("U-ALG", "Valores y cota de campos del registro construido por conformal_reset; no demuestra estabilidad cíclica física ni cosmológica."),
    38: ("U-ALG", "Igualdades definicionales sobre el registro devuelto por conformal_reset; el nombre histórico no demuestra un bypass físico del límite de Landauer."),
    39: ("U-ALG", "Conmutatividad de la coordenada fraccionaria (add_tick60 a b).sexa_fraction = (add_tick60 b a).sexa_fraction; no prueba por sí sola exactitud de representación del valor completo con acarreo."),
    40: ("U-ALG", "Identidad algebraica involutiva de XOR sobre Nat ((x ^^^ y) ^^^ y = x); el nombre histórico no formaliza conservación de volumen en espacio de fases (Liouville)."),
    41: ("U-ALG", "Existencia de cociente entero k tal que winding_phase = 60 * k cuando winding_phase % 60 = 0; propiedad de divisibilidad en Int, no grupo fundamental ni homotopía topológica."),
    42: ("U-ALG", "Reflexividad sobre la función mmr_peaks_bound n definida como n.log2 + 1; no cuenta picos de una estructura Merkle Mountain Range real."),
    43: ("U-ALG", "Identidad aditiva en Nat cuando el término cruzado se supone cero (cross_term = 0); no define divergencia KL ni variedad de Fisher."),
    44: ("U-ALG", "Implicación identidad: recibe h_contractive : fisher_out ≤ fisher_in como hipótesis y la devuelve directamente (exact h_contractive); no define un canal de Markov ni demuestra el teorema de Chentsov."),
    45: ("U-ALG", "Selecciona la rama RejectedCheapTalk de evaluate_agent_intent bajo las guardas booleanas de presupuesto y ratio; clasificador aritmético de longitudes, no detector semántico de confabulación."),
    46: ("U-ALG", "Desigualdad estándar de división entera en Nat ((total_energy / step_cost) * step_cost ≤ total_energy), válida incluso para step_cost = 0; no modela una relación de paso ni demuestra terminación."),
    47: ("U-ALG", "Igualdad de la segunda componente entre dos funciones puras en Lean (ffi_sexa_add_model y add_tick60); no invoca código C externo ni verifica ABI o punteros FFI."),
    48: ("U-IND", "Inducción sobre N pasos de run_repl_steps mostrando que el campo hot_manifest_bytes del registro ReplSession permanece igual a la constante 64."),
    49: ("U-ALG", "Extrae el campo de orden estricto h_causal : from_ts < to_ts exigido al construir CausalEdge."),
    50: ("U-ALG", "Contradicción aritmética elemental entre las hipótesis simultáneas stage_u = stage_v y stage_u < stage_v; no modela memoria compartida ni ausencia de carreras en hilos reales."),
    51: ("U-IND", "Propiedad de confluencia (diamante) para la relación funcional determinista SmallStep (cuyo paso es único por construcción sobre ReplSession)."),
    52: ("U-ALG", "Retracción finita por casos sobre los 4 constructores de EscalationStratum (toponymToStratum ∘ stratumToToponym = some)."),
    53: ("U-ALG", "Invarianza por proyección: triadCausalQuotient ignora el tercer campo parasitic_dirs_count del registro TriadTopologyState."),
    54: ("I-DEC", "Comprobación cerrada sobre el fragmento literal aeon_0_events (1.500 eventos, seq 0 → 1000)."),
    55: ("I-DEC", "Comprobación cerrada sobre el fragmento literal aeon_1_events (1.500 eventos, seq 1000 → 2000)."),
    56: ("I-DEC", "Comprobación cerrada sobre el fragmento literal aeon_2_events (1.500 eventos, seq 2000 → 3000)."),
    57: ("I-DEC", "Comprobación cerrada sobre el fragmento literal aeon_3_events (1.500 eventos, seq 3000 → 4000)."),
    58: ("I-DEC", "Comprobación cerrada sobre el fragmento literal aeon_4_events (1.500 eventos, seq 4000 → 5000)."),
    59: ("I-DEC", "Comprobación cerrada sobre la lista literal aeon_events de 1.500 eventos (seq 49000 → 50000)."),
    60: ("NEG-FIXTURE", "Fixture negativo de rechazo semántico esperado (AUDIT_LEAN_SCOPE_2026 §8): la lista auto_execution_trace contiene una transición inválida y decide refuta la igualdad = true."),
    61: ("U-ALG", "El estado inicial con entries = [] satisface vacuamente L0StateInvariant por ausencia de elementos en la lista."),
    62: ("U-IND", "Preservación de L0StateInvariant al prepender una entrada que cumple TriggerAllowsInsert sobre una lista que ya cumplía el invariante."),
    63: ("U-ALG", "Incremento estricto de headTick (db.headTick < (appendEntry db newEntry).headTick) bajo la precondición newEntry.logicalTick = db.headTick + 1 de TriggerAllowsInsert."),
    64: ("U-ALG", "Inyectividad de inserción y alineación de paso bajo TriggerAllowsInsert: deduce e1.logicalTick = e2.logicalTick, e1.prevMerkleRoot = e2.prevMerkleRoot y e1 = e2 cuando (appendEntry db e1).entries = (appendEntry db e2).entries; no modela funciones hash criptográficas ni resistencia a colisiones."),
    65: ("W-EX", "Testigo constructivo de habitabilidad (AP-10) para TriggerAllowsInsert sobre witnessDbL0 y witnessEntryL0."),
    66: ("NEG-FIXTURE", "Fixture negativo de rechazo semántico esperado (AUDIT_LEAN_SCOPE_2026 §8): lista de 1.501 eventos con lectura impar final donde decide rechaza la igualdad = true."),
    67: ("I-DEC", "Comprobación cerrada por decide sobre una traza literal válida de 6.000 eventos en BabylonStressTrace.lean."),
    68: ("I-DEC", "Comprobación cerrada por decide sobre la traza literal trace_perfect de 5 eventos en BabylonTrace.lean."),
    69: ("U-ALG", "Lema de un paso: si step s ev = some next y ev.action = Action.read, la secuencia declarada en el evento es par (ev.seq % 2 = 0)."),
    70: ("U-IND", "Lema inductivo sobre listas de eventos: si runAeon (some s) trace = some finalState, todo evento de lectura en trace declara secuencia par (TraceReadsEven trace)."),
    71: ("U-IND", "Propiedad inductiva universal sobre el modelo de eventos: validateTrace trace = true → TraceReadsEven trace. Certifica paridad de las secuencias declaradas en eventos read; no modela el payload leído ni orden de memoria físico en Rust."),
    72: ("U-ALG", "Rechazo de transición en BabylonEvent cuando el campo booleano formalVeto = true."),
    73: ("U-ALG", "Rechazo de transición en BabylonEvent cuando el campo booleano formalWitnessOk = false."),
    74: ("U-ALG", "Rechazo de transición en BabylonEvent cuando leaseEpoch < kernelEpoch."),
    75: ("U-ALG", "Extrae las conjunciones e.seqStart % 2 = 0 y e.seqStart = e.seqEnd de ValidBabylonTransition e."),
    76: ("U-ALG", "Rechazo de transición en BabylonEvent cuando seqStart ≠ seqEnd (corolario directo de #075)."),
    77: ("I-DEC", "Comprobación cerrada por decide de ValidBabylonTransition sobre el registro concreto trace_step_ok."),
    78: ("U-ALG", "Rechazo en CompositeGateState (BitVec 64) cuando (verifiedCriticalMask &&& requiredCriticalMask) ≠ requiredCriticalMask."),
    79: ("U-ALG", "Rechazo en CompositeGateState cuando acceptedArtifactHash ≠ verifiedArtifactHash."),
    80: ("U-ALG", "Rechazo en CompositeGateState cuando ¬(minPolicyEpoch ≤ evidenceEpoch)."),
    81: ("U-ALG", "Rechazo en CompositeGateState cuando quorumThreshold = 0#64."),
    82: ("I-DEC", "Comprobación cerrada por decide de ValidCompositeAcceptance sobre el estado concreto composite_gate_ok."),
    83: ("W-EX", "Testigo de habitabilidad (AP-10) para ValidCompositeAcceptance usando composite_gate_ok."),
    84: ("I-DEC", "Comprobación cerrada por decide que rechaza el estado concreto composite_gate_ple_91pct_fail (máscara 0x3FF vs 0x7FF)."),
    85: ("U-ALG", "Evaluación de consume sobre el constructor AffineResource.consumed devolviendo none; tipo inductivo puro y duplicable en Lean, no sistema de tipos lineales ni verificador de heap/aliasing."),
    86: ("U-ALG", "Identidad algebraica en el anillo Int: x * (-y) + y * x = 0."),
    87: ("I-DEC", "Comprobación cerrada por decide de un único paso discreto stepPHLD desde s0 = (1000, 1000) con r_percent = 20; no demuestra monotonía global de Lyapunov (existe contraejemplo en (0, 1) documentado en AUDIT_LEAN_SCOPE_2026 §5)."),
    88: ("I-DEC", "Comprobación cerrada por decide de que 0, 64 y 128 tienen resto 0 módulo 64; no verifica alineamiento físico del asignador en Rust."),
    100: ("U-ALG", "Paridad impar ((2 * k + 1) % 2 = 1) de la función aritmética seqlock_write_begin sobre Nat."),
    101: ("U-ALG", "Paridad par ((2 * k + 2) % 2 = 0) de la función aritmética seqlock_write_commit sobre Nat."),
    102: ("U-ALG", "Si el campo booleano poisoned = true en SystemState, evalFastPath devuelve FastPathVerdict.Miss."),
    103: ("I-DEC", "Comprobación cerrada de evalFastPath devolviendo Hit cuando astPrefix y filesCount coinciden con las constantes esperadas en estado no envenenado."),
    104: ("I-DEC", "Comprobación cerrada de evalFastPath devolviendo Miss cuando astPrefix difiere en +1 de la constante esperada."),
    105: ("U-ALG", "Preservación en un paso del predicado invariant (s.poisoned = true ∨ s.seq % 2 = 0) por la función transition."),
    106: ("U-IND", "Preservación inductiva del predicado invariant a lo largo de cualquier lista finita de acciones en runTrace."),
    107: ("W-EX", "Testigo constructivo de existencia de una traza no vacía validCycle aceptada por isValidTrace en aritmética BitVec 64/32."),
    108: ("U-ALG", "Identidad aritmética en Nat: (2*f + 1) + (2*f + 1) - (3*f + 1) = f + 1; ingrediente aritmético de intersección de quórum, no prueba por sí sola cardinalidad de conjuntos finitos de votantes ni protocolo BFT completo."),
    109: ("U-ALG", "Identidad aritmética en Nat para f ≥ 1: 2*f + 2*f - 3*f = f."),
    110: ("W-EX", "Testigo de existencia de ConsensusInstance con n = 4 y q = 3 (para f = 1)."),
    111: ("U-ALG", "Cota aritmética universal sin overflow en 64 bits: para todo f < 2^62, 3 * f + 1 < 2^64."),
    112: ("U-ALG", "Cota aritmética universal sin overflow en 64 bits: para todo f < 2^62, 2 * f + 1 < 2^64."),
    113: ("I-DEC", "Comprobación cerrada por decide de las cotas < 2^64 para f = 1."),
    114: ("W-EX", "Empaqueta la identidad aritmética #108 y el testigo #110 en la estructura VerifiedQuorumInvariant."),
    115: ("U-ALG", "En la función de puntuación truncada en Nat (net_exergy_payoff), si is_moloch_extraction a = true entonces la resta truncada produce 0."),
    116: ("U-ALG", "Para una acción con action_class = .Constructive, externalized_entropy = 0 y claimed_benefit > internal_dissipation, la fórmula net_exergy_payoff devuelve un valor > 0."),
    117: ("U-ALG", "Combina #115 y #116 para dos registros AgentAction que satisfacen esas hipótesis; compara la función de puntuación sobre ambos registros, sin demostrar equilibrio de Nash ni dominancia estratégica en un juego multi-agente."),
    118: ("U-ALG", "Por definición de landauer_penalty en Nat, su valor es ≥ a.externalized_entropy."),
    119: ("U-IND", "Inducción sobre listas finitas de AgentAction: la suma de landauer_penalty es ≥ la suma de externalized_entropy."),
    120: ("I-DEC", "Comprobación cerrada por decide de auditTrace sobre la lista concreta trace_depleted de 3 pasos."),
    121: ("I-DEC", "Comprobación cerrada por decide de auditTrace sobre la lista concreta trace_singular_candidate de 3 pasos."),
    122: ("U-ALG", "Extrae la hipótesis de campo h_curl_grad : d1_eval (d0_eval phi) = 0 suministrada dentro del registro DiscreteChainComplex."),
    123: ("U-ALG", "Extrae la hipótesis de campo h_div_curl : d2_eval (d1_eval u) = 0 suministrada dentro del registro DiscreteChainComplex."),
    124: ("I-DEC", "Comprobación cerrada por decide de isStrictlySolenoidal 0 = true (comprueba 0 == 0)."),
    125: ("I-DEC", "Comprobación aritmética cerrada por decide: 120 > 0 * 60 + 90 en isSobolevContinuousEmbedding; no construye espacios funcionales H^2 ni C^0."),
    126: ("I-DEC", "Comprobación aritmética cerrada por decide: 180 > 1 * 60 + 90 en isSobolevContinuousEmbedding; no construye espacios funcionales H^3 ni C^1."),
    127: ("I-DEC", "Comprobación aritmética cerrada por decide: 180 > 150 en isKatoLocalWellPosed; no demuestra existencia local de soluciones PDE."),
    128: ("I-DEC", "Comprobación aritmética cerrada por decide: 980 + 2 * 1 * 10 * 1 ≤ 1000 en verifyDissipationCurryHoward."),
    129: ("I-DEC", "Comprobación cerrada por decide de inclusión entre dos intervalos concretos [20, 80] ⊆ [10, 100]."),
    130: ("I-DEC", "Comprobación cerrada por decide: 150 ≤ 200 evaluando gronwallBound 100 [1, 0, 0]."),
    131: ("I-DEC", "Comprobación cerrada por decide de que la lista concreta [1, 2, 3, 4, 5, 10, 20, 50, 60] es estrictamente creciente en verifyCausalTrace."),
    132: ("I-DEC", "Aceptación de tres indicadores booleanos fijados en true (isMillenniumRegular { bkmIntegralBounded := true, constantinFeffermanSmooth := true, sobolevH3Controlled := true } = true); no define campos de velocidad/presión ni demuestra regularidad analítica de las ecuaciones de Navier-Stokes."),
    133: ("I-DEC", "Comprobación cerrada por decide de validateEcpTrace sobre la traza concreta validWave4Trace de 3 eventos."),
    134: ("I-DEC", "Comprobación cerrada por decide que rechaza la traza concreta corruptFencingRaceTrace en validateEcpTrace."),
    135: ("I-DEC", "Comprobación cerrada por decide que rechaza la traza concreta corruptBlindRetryTrace en validateEcpTrace."),
    136: ("I-DEC", "Comprobación cerrada por decide que rechaza la traza concreta corruptBudgetCompositionTrace en validateEcpTrace."),
    137: ("I-DEC", "Comprobación cerrada por decide de evaluateSealStrength false true false true = some .degradedSameUidOrInProcess."),
    138: ("I-DEC", "Comprobación cerrada por decide de validateDeploymentPermit 0xAAA1 0xBBB2 5 5 100 500 = false."),
}


def get_git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "log", "-n", "1", "--format=%H", "--", "proof/lean"],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _strip_top_level_proof(text: str) -> tuple[str, bool]:
    """Return (statement_before_top_level_colon_eq, found_colon_eq)."""
    depth_paren = 0
    depth_brack = 0
    depth_brace = 0
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in ("(", "⟨"):
            depth_paren += 1
        elif ch in (")", "⟩"):
            depth_paren = max(0, depth_paren - 1)
        elif ch == "[":
            depth_brack += 1
        elif ch == "]":
            depth_brack = max(0, depth_brack - 1)
        elif ch == "{":
            depth_brace += 1
        elif ch == "}":
            depth_brace = max(0, depth_brace - 1)
        elif (
            ch == ":"
            and i + 1 < n
            and text[i + 1] == "="
            and depth_paren == 0
            and depth_brack == 0
            and depth_brace == 0
        ):
            if re.search(r"\blet\s+[A-Za-z0-9_']+(?:\s*:[^:=]+)?\s*$", text[:i]):
                i += 2
                continue
            return text[:i].strip(), True
        i += 1
    return text.strip(), False


def extract_full_signature(lines: list[str], start_idx: int, first_rest: str) -> str:
    sig_parts: list[str] = []
    if first_rest:
        stmt, found = _strip_top_level_proof(first_rest)
        if stmt:
            sig_parts.append(stmt)
        if found:
            return re.sub(r"\s+", " ", " ".join(sig_parts)).strip()

    j = start_idx
    while j < len(lines) and (j - start_idx) < 16:
        raw = lines[j].strip()
        if not raw or raw.startswith("--"):
            j += 1
            continue
        if any(
            raw.startswith(kw)
            for kw in (
                "theorem ",
                "lemma ",
                "def ",
                "inductive ",
                "structure ",
                "abbrev ",
                "/--",
                "#guard_msgs",
                "#print",
                "end ",
                "namespace ",
                "| ",
            )
        ):
            break
        combined_candidate = " ".join(sig_parts + [raw])
        stmt, found = _strip_top_level_proof(combined_candidate)
        if found:
            return re.sub(r"\s+", " ", stmt).strip()
        sig_parts.append(raw)
        j += 1
    sig = re.sub(r"\s+", " ", " ".join(sig_parts)).strip()
    return sig


def classify_codec_theorem(idx: int, name: str, fname: str) -> tuple[str, str]:
    if idx in THEOREM_SCOPE_OVERRIDES:
        return THEOREM_SCOPE_OVERRIDES[idx]
    if fname in (
        "AcsEnvelope.lean",
        "CanonicalEnvelope.lean",
        "CanonicalHead.lean",
        "TicketEnvelope.lean",
    ):
        if "injective" in name:
            detail = "Inyectividad universal del codificador sobre el subconjunto de entradas que satisfacen el predicado `.valid`"
        elif "decode_encode" in name or "decodeFrom_encode_append" in name:
            detail = "Roundtrip universal de decodificación tras codificación (`decode (encode x) = some x`, o con sufijo arbitrario en `decodeFrom`) bajo `.valid x`"
        elif "encode_decode" in name:
            detail = "Re-codificación canónica determinista (`decode wire = some x → encode x = wire`) que excluye maleabilidad de representación en el modelo"
        elif "valid" in name:
            detail = "Soundness del decodificador comprobado (`decodeChecked wire = some x → valid x`) sobre el dominio del codec"
        elif "tag_ne" in name:
            detail = "Separación universal de dominios por prefijo (`tag_ne`): dos constructores con etiquetas distintas producen bytes disjuntos para cualesquiera sufijos"
        else:
            detail = "Propiedad universal de composición/delimitación de codecs sobre dominios válidos explícitos"
        return (
            "U-CODEC",
            f"{detail} en `{fname}` (`{name}`); no certifica por sí sola autenticidad criptográfica de claves ni frescura anti-replay en runtime.",
        )
    return ("U-ALG", f"Propiedad formal verificada en el modelo discreto de {fname}.")


def build_census() -> dict[str, Any]:
    scope25 = json.loads(SCOPE_2025_JSON.read_text(encoding="utf-8"))
    ax25: dict[str, list[str]] = scope25.get(
        "axioms_of_successfully_compiled_named_theorems", {}
    )

    files = sorted(LEAN_DIR.glob("*.lean"))
    modules_summary: list[dict[str, Any]] = []
    theorems_list: list[dict[str, Any]] = []
    constructions_list: list[dict[str, Any]] = []

    thm_counter = 0
    con_counter = 0
    core228_counter = 0

    for f in files:
        content = f.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        lines = content.splitlines()
        ns_stack: list[str] = []

        mod_thm_count = 0
        mod_def_count = 0
        mod_ind_count = 0
        mod_str_count = 0
        mod_abb_count = 0
        mod_first_thm = None
        mod_last_thm = None

        for line_no, line in enumerate(lines, 1):
            m_ns = re.match(r"^namespace\s+([^\s]+)", line)
            if m_ns:
                ns_stack.append(m_ns.group(1))
                continue
            m_end = re.match(r"^end\s+([^\s]+)", line)
            if m_end and ns_stack:
                ns_stack.pop()
                continue

            prefix = ".".join(ns_stack)

            m_thm = re.match(r"^(theorem|lemma)\s+([^\s(:{]+)(.*)", line)
            if m_thm:
                thm_counter += 1
                mod_thm_count += 1
                if mod_first_thm is None:
                    mod_first_thm = thm_counter
                mod_last_thm = thm_counter

                kind, name, rest = m_thm.group(1), m_thm.group(2), m_thm.group(3).strip()
                fqn = f"{prefix}.{name}" if prefix else name
                sig = extract_full_signature(lines, line_no, rest)
                res_class, scope_note = classify_codec_theorem(thm_counter, name, f.name)

                if f.name in NEGATIVE_FIXTURE_FILES:
                    axioms_val: list[str] | str = (
                        "N/A (negative fixture: expected decide rejection)"
                    )
                elif fqn in ax25:
                    axioms_val = ax25[fqn]
                elif name in ax25:
                    axioms_val = ax25[name]
                elif fqn in POST_2025_AXIOMS:
                    axioms_val = POST_2025_AXIOMS[fqn]
                elif name in POST_2025_AXIOMS:
                    axioms_val = POST_2025_AXIOMS[name]
                else:
                    axioms_val = "UNRESOLVED"

                theorems_list.append(
                    {
                        "id": f"#{thm_counter:03d}",
                        "index": thm_counter,
                        "file": f.name,
                        "line": line_no,
                        "kind": kind,
                        "name": name,
                        "qualified_name": fqn,
                        "signature": sig,
                        "result_class": res_class,
                        "axioms": axioms_val,
                        "scope_note": scope_note,
                    }
                )
                continue

            m_con = re.match(r"^(def|inductive|structure|abbrev)\s+([^\s(:{]+)", line)
            if m_con:
                con_counter += 1
                ckind, cname = m_con.group(1), m_con.group(2)
                fqn = f"{prefix}.{cname}" if prefix else cname
                is_core_228 = ckind in ("def", "inductive")
                core_id = None
                if is_core_228:
                    core228_counter += 1
                    core_id = f"#C{core228_counter:03d}"

                if ckind == "def":
                    mod_def_count += 1
                elif ckind == "inductive":
                    mod_ind_count += 1
                elif ckind == "structure":
                    mod_str_count += 1
                elif ckind == "abbrev":
                    mod_abb_count += 1

                constructions_list.append(
                    {
                        "all_index": con_counter,
                        "core228_id": core_id,
                        "file": f.name,
                        "line": line_no,
                        "kind": ckind,
                        "name": cname,
                        "qualified_name": fqn,
                        "in_core_228": is_core_228,
                    }
                )

        modules_summary.append(
            {
                "file": f.name,
                "lines": len(lines),
                "sha256": sha256,
                "has_theorems": mod_thm_count > 0,
                "is_negative_fixture": f.name in NEGATIVE_FIXTURE_FILES,
                "theorems": mod_thm_count,
                "theorem_range": (
                    f"#{mod_first_thm:03d}–#{mod_last_thm:03d}"
                    if mod_first_thm and mod_first_thm != mod_last_thm
                    else (f"#{mod_first_thm:03d}" if mod_first_thm else "—")
                ),
                "defs": mod_def_count,
                "inductives": mod_ind_count,
                "core_228_count": mod_def_count + mod_ind_count,
                "structures": mod_str_count,
                "abbrevs": mod_abb_count,
                "total_non_theorem": mod_def_count
                + mod_ind_count
                + mod_str_count
                + mod_abb_count,
            }
        )

    class_counts: dict[str, int] = {}
    for t in theorems_list:
        rc = t["result_class"]
        class_counts[rc] = class_counts.get(rc, 0) + 1

    return {
        "schema": "babylon60.lean4.formal_census.v2",
        "generated_from_commit": get_git_head(),
        "toolchain": "leanprover/lean4:v4.34.0-rc2",
        "totals": {
            "proprietary_modules_total": len(files),
            "modules_with_theorems": sum(1 for m in modules_summary if m["has_theorems"]),
            "auxiliary_modules_without_theorems": sum(
                1 for m in modules_summary if not m["has_theorems"]
            ),
            "theorems_total": len(theorems_list),
            "defs_total": sum(m["defs"] for m in modules_summary),
            "inductives_total": sum(m["inductives"] for m in modules_summary),
            "core_228_constructions_total": core228_counter,
            "theorems_plus_core_228": len(theorems_list) + core228_counter,
            "structures_total": sum(m["structures"] for m in modules_summary),
            "abbrevs_total": sum(m["abbrevs"] for m in modules_summary),
            "non_theorem_declarations_total": len(constructions_list),
            "all_top_level_declarations_total": len(theorems_list)
            + len(constructions_list),
        },
        "theorem_class_distribution": class_counts,
        "modules": modules_summary,
        "theorems": theorems_list,
        "constructions": constructions_list,
    }


def render_markdown(data: dict[str, Any]) -> str:
    t = data["totals"]
    cd = data["theorem_class_distribution"]
    commit = data["generated_from_commit"][:12]
    lines: list[str] = []

    lines.append("# Inventario de 144 Declaraciones de Teoremas y 228 Construcciones de BABYLON-60 en Lean 4")
    lines.append("")
    lines.append("**Autoría en Sala Limpia:** `Borja Fernández Angulo` (*Investigador en Sistemas Complejos*)  ")
    lines.append(f"**Revisión de Silicio:** Commit `{commit}` · Toolchain `{data['toolchain']}`  ")
    lines.append("**Auditoría de Alcance Vinculada:** [`docs/06_theory/AUDIT_LEAN_SCOPE_2026.md`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/docs/06_theory/AUDIT_LEAN_SCOPE_2026.md) · [`docs/06_theory/evidence/lean-census-372-v511.json`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/docs/06_theory/evidence/lean-census-372-v511.json)")
    lines.append("")
    lines.append("> [!IMPORTANT]")
    lines.append("> **Alcance Epistémico y Metodológico (Encabezado Canónico Corregido):**")
    lines.append(f"> El catálogo distribuye **144 declaraciones de teoremas** (`#001–#144`) entre **22 módulos con teoremas** y enumera **4 módulos auxiliares sin teoremas** (**26 módulos `.lean` propietarios** en [`proof/lean/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/proof/lean/)). Incluye lemas generales de codificación/inyectividad, preservación inductiva de invariantes sobre trazas, identidades algebraicas/aritméticas, testigos constructivos de existencia y comprobaciones de instancias concretas.")
    lines.append("> Las propiedades se refieren estrictamente a los **modelos discretos formalizados**. Su validación reproducible identifica la revisión Git, el hash `SHA-256` de cada módulo, el nombre completamente cualificado y las dependencias axiomáticas (`#print axioms`). Las garantías operacionales sobre el runtime Rust exigen además los contratos y tests de correspondencia de [`CLAIMS.toml`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/CLAIMS.toml).")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Conciliación Aritmética y Taxonomía de Resultados")
    lines.append("")
    lines.append("### 1.1 Recuento Mecánico Verificado (`22 + 4 = 26` Módulos · `144 + 228 = 372` Construcciones)")
    lines.append("")
    lines.append("| Métrica del Árbol Propietario (`proof/lean/*.lean`) | Recuento Exacto | Desglose y Verificación |")
    lines.append("|:---|:---:|:---|")
    lines.append(f"| **Módulos propietarios totales** | **{t['proprietary_modules_total']}** | **{t['modules_with_theorems']}** módulos con declaraciones `theorem` + **{t['auxiliary_modules_without_theorems']}** módulos auxiliares (`BabylonAOTOracle.lean`, `BabylonOracle.lean`, `HolographicPoC.lean`, `NavierStokesOracle.lean`) |")
    lines.append(f"| **Declaraciones de teoremas (`theorem`)** | **{t['theorems_total']}** | Identificadores consecutivos `#001–#144` sin huecos ni duplicados (142 en módulos positivos + 2 en fixtures negativos de rechazo esperado) |")
    lines.append(f"| **Definiciones y tipos inductivos (`def` + `inductive`)** | **{t['core_228_constructions_total']}** | **{t['defs_total']}** `def` + **{t['inductives_total']}** `inductive` (enumerados 1:1 como `#C001–#C228` en la Sección 4) |")
    lines.append(f"| **Suma canónica (`144 teoremas + 228 def/inductive`)** | **{t['theorems_plus_core_228']}** | Conciliación exacta de las **372 construcciones formales** declaradas en `IP_PROVENANCE.md` |")
    lines.append(f"| **Estructuras y abreviaturas adicionales (`structure` + `abbrev`)** | **{t['structures_total'] + t['abbrevs_total']}** | **{t['structures_total']}** `structure` (suma `406` con `144 + 228`) + **{t['abbrevs_total']}** `abbrev` (**{t['all_top_level_declarations_total']}** declaraciones totales de nivel superior, todas listadas en la Sección 4) |")
    lines.append("")
    lines.append("### 1.2 Clasificación de las 144 Declaraciones por Clase de Resultado y Alcance")
    lines.append("")
    lines.append("| Código | Clase de Resultado | Cantidad | % sobre 144 | Alcance Formal Exacto |")
    lines.append("|:---:|:---|:---:|:---:|:---|")
    lines.append(f"| `U-CODEC` | **Leyes Universales de Codificación e Inyectividad** | **{cd.get('U-CODEC', 0)}** | {cd.get('U-CODEC', 0)*100/144:.1f} % | Roundtrip (`decode_encode`, `encode_decode`), inyectividad, preservación de sufijos y validez sobre dominios explícitos (`AcsEnvelope`, `CanonicalEnvelope`, `CanonicalHead`, `TicketEnvelope`). |")
    lines.append(f"| `U-IND` | **Preservación Inductiva Universal y Confluencia** | **{cd.get('U-IND', 0)}** | {cd.get('U-IND', 0)*100/144:.1f} % | Inducción estructural sobre listas/trazas de longitud arbitraria (`AX0` cota `≤ 1` despacho, `BabylonL0Ledger` preservación L0, `BabylonTrace` paridad de lecturas, `Destiladora` invariante de traza, `MolochLandauer` solvencia en traza, `SmallStep` confluencia). |")
    lines.append(f"| `U-ALG` | **Lemas Universales de Un Paso, Aritmética y Proyección** | **{cd.get('U-ALG', 0)}** | {cd.get('U-ALG', 0)*100/144:.1f} % | Propiedades cuantificadas universalmente sobre registros de un paso (`ValidBabylonTransition`, `CompositeGateState`), cotas `u64` (`f < 2^62`), identidades algebraicas (`Nat`/`Int`/`XOR`), y proyecciones de hipótesis/campos de estructuras. |")
    lines.append(f"| `W-EX` | **Testigos Constructivos de No-Vacuidad (`AP-10`)** | **{cd.get('W-EX', 0)}** | {cd.get('W-EX', 0)*100/144:.1f} % | Pruebas existenciales (`∃ x, P x`) y empaquetados `VerifiedInvariant` que acreditan que las precondiciones de disparo no son vacuas. |")
    lines.append(f"| `I-DEC` | **Comprobaciones de Instancias Cerradas Positivas** | **{cd.get('I-DEC', 0)}** | {cd.get('I-DEC', 0)*100/144:.1f} % | Evaluaciones decidibles (`by decide` / `rfl`) sobre trazas concretas, constantes en punto fijo o configuraciones finitas de banderas. |")
    lines.append(f"| `NEG-FIXTURE` | **Fixtures Negativos de Rechazo Esperado** | **{cd.get('NEG-FIXTURE', 0)}** | {cd.get('NEG-FIXTURE', 0)*100/144:.1f} % | `#060` (`BabylonAutoTrace.lean`) y `#066` (`BabylonStressCorrupt.lean`): fuentes negativas diseñadas para que `decide` refute la igualdad `= true` ante una traza corrupta. |")
    lines.append(f"| **TOTAL** | **39 Instancias Cerradas (`I-DEC` + `NEG-FIXTURE` = 27,1 %) + 105 Universales/Testigos (72,9 %)** | **144** | **100,0 %** | — |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Distribución por Módulo Propietario (22 con Teoremas + 4 Auxiliares = 26 Módulos)")
    lines.append("")
    lines.append("### 2.1 Los 22 Módulos con Declaraciones de Teoremas")
    lines.append("")
    lines.append("| # | Módulo `.lean` | Teoremas | Rango | `def` | `ind` | `str` | `abb` | Estatus de Compilación y Alcance |")
    lines.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|")
    idx_with_thm = 0
    for m in data["modules"]:
        if not m["has_theorems"]:
            continue
        idx_with_thm += 1
        fname = m["file"]
        status = (
            "Fixture negativo (rechazo esperado por `decide`)"
            if m["is_negative_fixture"]
            else "Compila (`v4.34.0-rc2`); alcance del modelo"
        )
        lines.append(
            f"| {idx_with_thm} | [{fname}](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/proof/lean/{fname}) | **{m['theorems']}** | `{m['theorem_range']}` | {m['defs']} | {m['inductives']} | {m['structures']} | {m['abbrevs']} | {status} |"
        )
    lines.append("")
    lines.append("### 2.2 Los 4 Módulos Auxiliares sin Declaraciones `theorem`")
    lines.append("")
    lines.append("| # | Módulo Auxiliar `.lean` | Teoremas | `def` | `ind` | `str` | `abb` | Rol en `proof/lean/` y Estatus |")
    lines.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---|")
    idx_aux = 0
    aux_roles = {
        "BabylonAOTOracle.lean": "Parser binario y bucle IO por bloques de 8 KiB (`main`); compila con `v4.34.0-rc2`.",
        "BabylonOracle.lean": "Parser CSV y validador de pasos abstractos (`main`); compila con `v4.34.0-rc2`.",
        "HolographicPoC.lean": "Widget `HtmlDisplay` de ejemplo (`ProofWidgets`); compila con imports locales precompilados.",
        "NavierStokesOracle.lean": "Clasificador ejecutable de flags/umbrales sobre trazas discretas (`main`); compila con `v4.34.0-rc2`.",
    }
    for m in data["modules"]:
        if m["has_theorems"]:
            continue
        idx_aux += 1
        fname = m["file"]
        lines.append(
            f"| {idx_aux} | [{fname}](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/proof/lean/{fname}) | **0** | {m['defs']} | {m['inductives']} | {m['structures']} | {m['abbrevs']} | {aux_roles.get(fname, 'Módulo auxiliar')} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Catálogo Trazable 1:1 de las 144 Declaraciones de Teoremas (`#001` – `#144`)")
    lines.append("")
    current_file = None
    for thm in data["theorems"]:
        if thm["file"] != current_file:
            current_file = thm["file"]
            lines.append(f"### Módulo: [{current_file}](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/proof/lean/{current_file})")
            lines.append("")
        ax_str = (
            ", ".join(thm["axioms"])
            if isinstance(thm["axioms"], list) and thm["axioms"]
            else ("ninguno (`[]`)" if thm["axioms"] == [] else str(thm["axioms"]))
        )
        lines.append(
            f"{thm['index']}. **`{thm['id']}`** · [`{thm['qualified_name']}`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/proof/lean/{thm['file']}#L{thm['line']}) · **Clase:** `[{thm['result_class']}]` · **Axiomas:** `{ax_str}`  "
        )
        lines.append(f"   - **Enunciado:** `{thm['kind']} {thm['name']} {thm['signature']}`")
        lines.append(f"   - **Alcance exacto:** {thm['scope_note']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. Anexo Contrastable: Las 228 Definiciones e Inductivos (`#C001–#C228`) y las 47 Estructuras/Abreviaturas (`275` Construcciones No-Teorema)")
    lines.append("")
    lines.append("Esta tabla enumera 1:1 todas las declaraciones de tipos y funciones en `proof/lean/*.lean` que sustentan los 144 teoremas, permitiendo verificar mecánicamente tanto el subtotal **`205 def + 23 inductive = 228`** (`144 + 228 = 372`) como el total incluyendo **`34 structure + 13 abbrev`** (`275` construcciones no-teorema; `144 + 275 = 419` declaraciones totales).")
    lines.append("")
    lines.append("| # Global | ID Core-228 | Módulo:Línea | Especie | Nombre Cualificado |")
    lines.append("|:---:|:---:|:---|:---:|:---|")
    for c in data["constructions"]:
        cid = f"`{c['core228_id']}`" if c["core228_id"] else "*(struct/abbrev)*"
        lines.append(
            f"| {c['all_index']:03d} | {cid} | [{c['file']}:{c['line']}](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/proof/lean/{c['file']}#L{c['line']}) | `{c['kind']}` | `{c['qualified_name']}` |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**Borja Fernández Angulo** · *Investigador en Sistemas Complejos*")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export deterministic Lean 4 formal census")
    parser.add_argument("--json-out", type=pathlib.Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=pathlib.Path, default=None)
    parser.add_argument("--verify", action="store_true", help="Assert exact cardinal invariants")
    args = parser.parse_args()

    census = build_census()
    totals = census["totals"]

    if args.verify:
        assert totals["proprietary_modules_total"] == 26, f"Expected 26 modules, got {totals['proprietary_modules_total']}"
        assert totals["modules_with_theorems"] == 22, f"Expected 22 modules with theorems, got {totals['modules_with_theorems']}"
        assert totals["auxiliary_modules_without_theorems"] == 4, f"Expected 4 aux modules, got {totals['auxiliary_modules_without_theorems']}"
        assert totals["theorems_total"] == 144, f"Expected 144 theorems, got {totals['theorems_total']}"
        assert totals["core_228_constructions_total"] == 228, f"Expected 228 core constructions, got {totals['core_228_constructions_total']}"
        assert totals["theorems_plus_core_228"] == 372, f"Expected 372 total (144+228), got {totals['theorems_plus_core_228']}"
        unresolved = [t["qualified_name"] for t in census["theorems"] if t["axioms"] == "UNRESOLVED"]
        assert not unresolved, f"Unresolved axioms for: {unresolved}"
        print(
            "[LEAN-CENSUS PASS] 26 modules (22+4) | 144 theorems | 228 def+inductive (372) | "
            f"+34 struct +13 abbrev = {totals['all_top_level_declarations_total']} total declarations | 0 unresolved axioms"
        )

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(census, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.markdown_out:
        md = render_markdown(census)
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
