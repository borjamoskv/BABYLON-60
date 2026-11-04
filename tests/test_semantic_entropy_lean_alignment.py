"""Check Rust constants and the typed solver contract in the Lean summary model.

This checks finite thresholds/codes, not Rust matrix-validation refinement or truth.
"""

import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

ROOT = Path(__file__).absolute().parents[1]
RUST = ROOT / "00_ABZU_KERNEL/crates/babylon60-kernel/src/semantic_entropy.rs"
LEAN = ROOT / "scripts/c5_demos/SemanticEntropyApoptosis.lean"


def rust_constant(name: str) -> int:
    match = re.search(rf"pub const {name}: u32 = (0x[0-9A-Fa-f_]+|[0-9_]+);", RUST.read_text())
    assert match is not None, f"Missing numeric Rust contract constant: {name}"
    return int(match.group(1).replace("_", ""), 0)


def test_lean_summary_thresholds_and_codes_match_rust(tmp_path: Path) -> None:
    lean = shutil.which("lean")
    if lean is None:
        if os.environ.get("BABYLON_REQUIRE_LEAN") == "1":
            pytest.fail("Lean is required for this explicit model-alignment check")
        pytest.skip("Lean unavailable; set BABYLON_REQUIRE_LEAN=1 to require the check")

    tau = rust_constant("TAU_SEM_Q16")
    high_code = rust_constant("ERR_CONFABULATION")
    low_code = rust_constant("ERR_INCORRECT_BELIEF")
    cases = {
        f"audit_{name}_threshold": f"{name}.tauSem = {tau}"
        for name in ("claim_genuine", "claim_confabulation", "claim_incorrect_belief", "claim_polysemy")
    }
    for name, entropy, external, expected in [
        ("at_threshold", tau, ".Unsat", f"CausalStatus.Apoptosis {low_code}"),
        ("above_threshold", tau + 1, ".Unsat", f"CausalStatus.Apoptosis {high_code}"),
        ("accepted", 0, ".Sat", "CausalStatus.Verified"),
    ]:
        claim = (
            f"{{ claimId := 99, hSemScaled := {entropy}, tauSem := {tau}, "
            f"solverOutcome := {external} }}"
        )
        cases[f"audit_{name}"] = f"evaluateCausalGate {claim} = {expected}"

    # Both sides of the threshold and the representable entropy endpoints.
    for entropy in (0, tau, tau + 1, 196608):
        claim = f"{{ claimId := 99, hSemScaled := {entropy}, tauSem := {tau}, solverOutcome := .Unknown }}"
        cases[f"audit_unknown_{entropy}"] = f"evaluateCausalGate {claim} = CausalStatus.SolverUnknown"
        for reason in ("Timeout", "Transport", "Protocol", "Execution"):
            claim = (
                f"{{ claimId := 99, hSemScaled := {entropy}, tauSem := {tau}, "
                f"solverOutcome := .Error .{reason} }}"
            )
            cases[f"audit_error_{reason}_{entropy}"] = (
                f"evaluateCausalGate {claim} = CausalStatus.SolverFailure .{reason}"
            )

    source_theorems = [
        "genuine_knowledge_is_verified",
        "confabulation_triggers_0x6060",
        "incorrect_belief_triggers_0x6061",
        "polysemy_is_verified",
        "falsity_never_reaches_ring1_commit",
        "verified_requires_solver_sat",
        "solver_sat_is_verified",
        "verified_iff_solver_sat",
        "unknown_never_reaches_verified",
        "solver_error_never_reaches_verified",
    ]
    lines = [LEAN.read_text(), "namespace Babylon60.Epistemology", "set_option warningAsError true"]
    for name, proposition in cases.items():
        lines.append(f"theorem {name} : {proposition} := by decide")
    for name in [*cases, *source_theorems]:
        lines.extend([
            f"/-- info: 'Babylon60.Epistemology.{name}' does not depend on any axioms -/",
            "#guard_msgs in",
            f"#print axioms {name}",
        ])
    lines.append("end Babylon60.Epistemology")
    fixture = tmp_path / "SemanticEntropyAlignment.lean"
    fixture.write_text("\n".join(lines) + "\n")
    env = os.environ.copy()
    env["ELAN_TOOLCHAIN"] = (ROOT / "proof/lean/lean-toolchain").read_text().strip()
    result = subprocess.run(
        [lean, str(fixture)], cwd=ROOT / "proof/lean", env=env,
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not result.stdout.strip() and not result.stderr.strip(), "Unexpected Lean diagnostics"
