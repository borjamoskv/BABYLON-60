#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.2.0 Sovereign Hardened — LEAN 4 KERNEL SOUNDNESS TEST SUITE
# ============================================================================
"""
Oráculo de Falsación y Atestación de Solidez para el Kernel Formal en Lean 4.
Verifica:
1. Ausencia del token literal 'sorry'.
2. Erradicación del backdoor 'goal.admit' en BabylonOracle.lean.
3. Ausencia de axiomas no acotados (ax_tz_1, ax_pl_hot_memory_bounded).
4. Presencia y validez de TransductionTensor60.
5. Compilación determinista de Lake con salida código 0.
"""

import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LEAN_DIR = os.path.join(REPO_ROOT, "proof", "lean")
BABYLON_LEAN = os.path.join(LEAN_DIR, "Babylon.lean")
ORACLE_LEAN = os.path.join(LEAN_DIR, "BabylonOracle.lean")


def _strip_lean_comments(source: str) -> str:
    """Elimina comentarios de bloque `/- ... -/` (anidables) y de línea `--`."""
    out: list[str] = []
    depth = 0
    i = 0
    n = len(source)
    while i < n:
        two = source[i : i + 2]
        if two == "/-":
            depth += 1
            i += 2
        elif two == "-/" and depth > 0:
            depth -= 1
            i += 2
        elif depth > 0:
            i += 1
        elif two == "--":
            newline = source.find("\n", i)
            i = n if newline == -1 else newline
        else:
            out.append(source[i])
            i += 1
    return "".join(out)


def test_strip_lean_comments_keeps_code_tokens() -> None:
    """El filtro de comentarios no debe ocultar un `sorry` de código."""
    src = "-- 0 sorry\n/- sorry /- nested sorry -/ -/\ntheorem t : True := by sorry\n"
    assert re.findall(r"\bsorry\b", _strip_lean_comments(src)) == ["sorry"]


def test_absence_of_literal_sorry() -> None:
    """Verifica que ningún archivo Lean en proof/lean use la táctica `sorry` en código."""
    assert os.path.exists(BABYLON_LEAN), "Babylon.lean no encontrado"
    for fname in os.listdir(LEAN_DIR):
        if fname.endswith(".lean") and not fname.startswith("."):
            fpath = os.path.join(LEAN_DIR, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            code = _strip_lean_comments(content)
            assert not re.search(r"\bsorry\b", code), f"Detectado 'sorry' en {fname}"


def test_erradication_of_goal_admit_backdoor() -> None:
    """Verifica la erradicación total del backdoor 'goal.admit' en BabylonOracle.lean."""
    assert os.path.exists(ORACLE_LEAN), "BabylonOracle.lean no encontrado"
    with open(ORACLE_LEAN, "r", encoding="utf-8") as f:
        content = f.read()
    assert "goal.admit" not in content, "VULNERABILIDAD: 'goal.admit' detectado en BabylonOracle.lean"
    # INV_C5_07: el rechazo debe ser ruidoso y fail-closed. Desde la auditoría de
    # alcance 2026-10-26 el mensaje describe solo el modelo y el bucle termina
    # con código de rechazo no nulo.
    assert "Registro rechazado por el modelo" in content, "Falta mensaje de rechazo INV_C5_07 en BabylonOracle.lean"
    assert re.search(r"Registro rechazado por el modelo[^\n]*\n\s*return 2\b", content), (
        "El rechazo INV_C5_07 debe terminar con código no nulo (return 2)"
    )


def test_absence_of_unsound_universal_axioms() -> None:
    """Verifica la eliminación de axiomas universales no acotados que permiten demostrar False."""
    with open(BABYLON_LEAN, "r", encoding="utf-8") as f:
        content = f.read()
    assert "axiom ax_tz_1" not in content, "Axioma ax_tz_1 (falsable) aún presente en Babylon.lean"
    assert "axiom ax_pl_hot_memory_bounded" not in content, "Axioma ax_pl_hot_memory_bounded (falsable) aún presente"


def test_transduction_tensor_defined() -> None:
    """Verifica la especificación formal del tensor de transducción sexagesimal."""
    with open(BABYLON_LEAN, "r", encoding="utf-8") as f:
        content = f.read()
    assert "structure TransductionTensor60" in content, "TransductionTensor60 ausente en Babylon.lean"


def test_universal_inductive_theorems_present() -> None:
    """Verifica la especificación, firma exacta y testigos anti-debilitamiento de teoremas universales."""
    ax0_lean = os.path.join(LEAN_DIR, "AX0.lean")
    trace_lean = os.path.join(LEAN_DIR, "BabylonTrace.lean")
    assert os.path.exists(ax0_lean), "AX0.lean no encontrado"
    assert os.path.exists(trace_lean), "BabylonTrace.lean no encontrado"

    with open(ax0_lean, "r", encoding="utf-8") as f:
        ax0_content = f.read()
    assert "theorem auth_001_universal_inductive_safety (trace : List AuthEvent) :" in ax0_content
    assert "validateTrace trace .Proposed = true → countDispatches trace ≤ 1" in ax0_content
    assert "example : Auth001SafetyProp := auth_001_universal_inductive_safety" in ax0_content
    assert "#check @auth_001_universal_inductive_safety" in ax0_content
    assert ": True := trivial" not in ax0_content

    with open(trace_lean, "r", encoding="utf-8") as f:
        trace_content = f.read()
    assert "theorem no_torn_reads_universal (trace : List Event) :" in trace_content
    assert "validateTrace trace = true → TraceReadsEven trace" in trace_content
    assert "example : NoTornReadsProp := no_torn_reads_universal" in trace_content
    assert "#check @no_torn_reads_universal" in trace_content
    assert ": True := trivial" not in trace_content


def test_moloch_landauer_kernel_theorems_present() -> None:
    """Verifica la formalización de detección de Moloch y balance de Landauer."""
    moloch_lean = os.path.join(LEAN_DIR, "MolochLandauer.lean")
    assert os.path.exists(moloch_lean), "MolochLandauer.lean no encontrado"

    with open(moloch_lean, "r", encoding="utf-8") as f:
        content = f.read()

    assert "def is_moloch_extraction (a : AgentAction) : Bool" in content
    assert "def landauer_penalty (a : AgentAction) : Nat" in content
    assert "theorem moloch_payoff_is_zero" in content
    assert "theorem constructive_action_positive_payoff" in content
    assert "theorem cooperation_dominates_moloch" in content
    assert "theorem landauer_compensates_entropy" in content
    assert "theorem trace_entropy_solvency_universal" in content
    assert ": True := trivial" not in content
    assert "sorry" not in content


def test_lean_mutation_m3_weakened_theorem_rejected(tmp_path: Path) -> None:
    """Verifica que la mutación m3 (debilitar auth_001_universal_inductive_safety a True := trivial) falla en Lean."""
    if shutil.which("lean") is None:
        pytest.skip("lean compiler not found in PATH")
    ax0_lean = os.path.join(LEAN_DIR, "AX0.lean")
    with open(ax0_lean, "r", encoding="utf-8") as f:
        original = f.read()

    target = (
        "theorem auth_001_universal_inductive_safety (trace : List AuthEvent) :\n"
        "  validateTrace trace .Proposed = true → countDispatches trace ≤ 1 := by\n"
        "  intro h\n"
        "  have h_max := max_dispatches_from_state trace .Proposed h\n"
        "  exact h_max"
    )
    assert target in original
    mutated = original.replace(
        target,
        "theorem auth_001_universal_inductive_safety : True := trivial",
        1,
    )
    mutated_file = tmp_path / "AX0_mutated.lean"
    mutated_file.write_text(mutated, encoding="utf-8")

    res = subprocess.run(
        ["lean", str(mutated_file)],
        cwd=LEAN_DIR,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert res.returncode != 0, "VULNERABILIDAD m3: El debilitamiento a True := trivial fue aceptado por Lean"


def test_lake_build_clean_compilation() -> None:
    """Verifica que lake build compile el proyecto Lean 4 sin fallos."""
    if shutil.which("lake") is None:
        pytest.skip("lake (Lean 4 build tool) not found in PATH — skipped in Python-only CI runners")
    cmd = ["lake", "build"]
    result = subprocess.run(cmd, cwd=LEAN_DIR, capture_output=True, text=True)
    assert result.returncode == 0, f"lake build falló:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
