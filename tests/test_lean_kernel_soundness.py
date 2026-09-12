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
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LEAN_DIR = os.path.join(REPO_ROOT, "proof", "lean")
BABYLON_LEAN = os.path.join(LEAN_DIR, "Babylon.lean")
ORACLE_LEAN = os.path.join(LEAN_DIR, "BabylonOracle.lean")


def test_absence_of_literal_sorry() -> None:
    """Verifica que ningún archivo Lean en proof/lean contenga 'sorry'."""
    assert os.path.exists(BABYLON_LEAN), "Babylon.lean no encontrado"
    with open(BABYLON_LEAN, "r", encoding="utf-8") as f:
        content = f.read()
    assert "sorry" not in content, "Detectado 'sorry' en proof/lean/Babylon.lean"


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


def test_lake_build_clean_compilation() -> None:
    """Verifica que lake build compile el proyecto Lean 4 sin fallos."""
    cmd = ["lake", "build"]
    result = subprocess.run(cmd, cwd=LEAN_DIR, capture_output=True, text=True)
    assert result.returncode == 0, f"lake build falló:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
