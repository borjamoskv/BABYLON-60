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
import shutil
import subprocess

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LEAN_DIR = os.path.join(REPO_ROOT, "proof", "lean")
BABYLON_LEAN = os.path.join(LEAN_DIR, "Babylon.lean")
ORACLE_LEAN = os.path.join(LEAN_DIR, "BabylonOracle.lean")


def test_absence_of_literal_sorry() -> None:
    """Verifica que ningún archivo Lean en proof/lean contenga 'sorry'."""
    assert os.path.exists(BABYLON_LEAN), "Babylon.lean no encontrado"
    for fname in os.listdir(LEAN_DIR):
        if fname.endswith(".lean") and not fname.startswith("."):
            fpath = os.path.join(LEAN_DIR, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            assert "sorry" not in content, f"Detectado 'sorry' en {fname}"


def test_erradication_of_goal_admit_backdoor() -> None:
    """Verifica la erradicación total del backdoor 'goal.admit' en BabylonOracle.lean."""
    assert os.path.exists(ORACLE_LEAN), "BabylonOracle.lean no encontrado"
    with open(ORACLE_LEAN, "r", encoding="utf-8") as f:
        content = f.read()
    assert "goal.admit" not in content, "VULNERABILIDAD: 'goal.admit' detectado en BabylonOracle.lean"
    assert "INV_C5_07 LOUD FAILURE" in content, "Falta mensaje formal de INV_C5_07 en BabylonOracle.lean"


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
    """Verifica la especificación y prueba de teoremas inductivos universales."""
    ax0_lean = os.path.join(LEAN_DIR, "AX0.lean")
    trace_lean = os.path.join(LEAN_DIR, "BabylonTrace.lean")
    assert os.path.exists(ax0_lean), "AX0.lean no encontrado"
    assert os.path.exists(trace_lean), "BabylonTrace.lean no encontrado"

    with open(ax0_lean, "r", encoding="utf-8") as f:
        ax0_content = f.read()
    assert "theorem auth_001_universal_inductive_safety" in ax0_content

    with open(trace_lean, "r", encoding="utf-8") as f:
        trace_content = f.read()
    assert "theorem no_torn_reads_universal" in trace_content


def test_lake_build_clean_compilation() -> None:
    """Verifica que lake build compile el proyecto Lean 4 sin fallos."""
    if shutil.which("lake") is None:
        pytest.skip("lake (Lean 4 build tool) not found in PATH — skipped in Python-only CI runners")
    cmd = ["lake", "build"]
    result = subprocess.run(cmd, cwd=LEAN_DIR, capture_output=True, text=True)
    assert result.returncode == 0, f"lake build falló:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
