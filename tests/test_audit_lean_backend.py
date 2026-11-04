"""Regression coverage for fail-closed Lean IR translation (H07)."""

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

BACKEND = Path(__file__).absolute().parents[1] / "00_ABZU_KERNEL/crates/babylon60-compiler/lean_backend.py"
spec = importlib.util.spec_from_file_location("audit_lean_backend", BACKEND)
assert spec is not None and spec.loader is not None
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)


@pytest.mark.parametrize(
    "instruction",
    [
        "(UNKNOWN_DANGEROUS_OP 1 2)",
        "(HappensBefore sorry 2)",
        "(HappensBefore admit 2)",
        "(Event 1)",
        "(Event 1 2 extra)",
        "()",
        "(Event 1 2",
        "Event 1 2)",
        "((Event 1 2))",
    ],
)
def test_invalid_instruction_rejects_entire_translation(instruction):
    with pytest.raises(ValueError, match="IR line 2:"):
        backend.translate_to_lean(["(Event 1 0)", instruction])


def test_legitimate_ir_preserves_every_instruction():
    output = backend.translate_to_lean(
        [
            "",
            "(Event 1 0)",
            "Event 2 1",
            "(HappensBefore 1 2)",
            "(Assign reg 4 a)",
            "(Add reg 5 b)",
            "(Sub reg -1 c)",
            "(Spawn worker d)",
            "(Block worker e)",
            "(Wait 3 f)",
            "(Emit done g)",
        ]
    )
    for declaration in [
        "ev_tick_1",
        "ev_tick_2",
        "causal_1_2",
        "assign_a",
        "add_b",
        "sub_c",
        "spawn_d",
        "await_e",
        "after_f",
        "emit_g",
    ]:
        assert declaration in output
    assert "#print axioms causal_1_2" in output
    assert "TAINT_UNPROVEN" not in output


def test_legitimate_ir_typechecks_with_the_pinned_lean_kernel(tmp_path):
    if shutil.which("elan") is None:
        if os.environ.get("BABYLON60_REQUIRE_LEAN_ENVELOPES") == "1":
            pytest.fail("The required Lean backend verification needs elan")
        pytest.skip("Pinned Lean toolchain unavailable")
    source = tmp_path / "generated.lean"
    source.write_text(
        backend.translate_to_lean(
            [
                "(Event 1 0)",
                "(Event 2 1)",
                "(HappensBefore 1 2)",
                "(Assign reg 4 a)",
                "(Add reg 5 b)",
                "(Sub reg -1 c)",
                "(Spawn worker d)",
                "(Block worker e)",
                "(Wait 3 f)",
                "(Emit done g)",
            ]
        )
    )
    pin = (BACKEND.parents[3] / "proof/lean/lean-toolchain").read_text().strip()
    result = subprocess.run(
        ["elan", "run", pin, "lean", str(source)], capture_output=True, text=True, check=False, timeout=60
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("existing", [False, True])
def test_cli_rejection_does_not_publish_or_overwrite_output(tmp_path, existing):
    source = tmp_path / "invalid.ir"
    target = tmp_path / "proof.lean"
    source.write_text("(Event 1 0)\n(Unknown 1 2)\n")
    if existing:
        target.write_text("existing proof")
    result = subprocess.run(
        [sys.executable, str(BACKEND), str(source), "--out", str(target)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 1
    assert "Invalid IR" in result.stderr
    assert "PASSED" not in result.stdout
    assert target.read_text() == "existing proof" if existing else not target.exists()
