"""Prevent a green Seqlock CI gate when its tests are skipped or not selected."""

from fnmatch import fnmatchcase
from pathlib import Path

import pytest
import yaml

from scripts.c5_quality_gates.verify_seqlock_lean import TESTS, prepare_workspace, require_one_passed_test

ROOT = Path(__file__).absolute().parents[1]


def test_accepts_one_executed_test_with_expected_lean_rejection_diagnostics():
    require_one_passed_test(
        "error: Tactic `decide` proved that the proposition is false\n"
        "test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 48 filtered out; finished in 1.0s\n"
    )


@pytest.mark.parametrize(
    "summary",
    [
        "",
        "test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 49 filtered out;",
        "test result: ok. 0 passed; 0 failed; 1 ignored; 0 measured; 48 filtered out;",
        "test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 48 filtered out;",
        "test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 47 filtered out;",
        "test result: ok. 1 passed; 0 failed; 0 ignored; 1 measured; 48 filtered out;",
        "test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured;\n" * 2,
    ],
)
def test_zero_skipped_failed_or_ambiguous_results_fail_closed(summary):
    with pytest.raises(ValueError):
        require_one_passed_test(summary)


def test_workspace_copies_canonical_inputs_and_has_no_external_dependencies(tmp_path):
    workspace = tmp_path / "lean"
    pin = prepare_workspace(ROOT, workspace)
    assert pin == (ROOT / "proof/lean/lean-toolchain").read_text().strip()
    for name in ("BabylonTrace.lean", "lean-toolchain"):
        assert (workspace / name).read_bytes() == (ROOT / "proof/lean" / name).read_bytes()
    assert "require" not in (workspace / "lakefile.toml").read_text()
    assert not (workspace / ".lake").exists(), "must not inherit stale build artifacts"


@pytest.mark.parametrize("event", ["push", "pull_request"])
def test_workflow_triggers_for_every_seqlock_input_and_runs_an_unconditional_gate(event):
    workflow = yaml.load((ROOT / ".github/workflows/verify_lean.yml").read_text(), Loader=yaml.BaseLoader)
    paths = workflow["on"][event]["paths"]
    for path in (
        "crates/b60-lang/src/lean_emitter.rs",
        "crates/b60-lang/Cargo.toml",
        "proof/lean/BabylonTrace.lean",
        "proof/lean/lean-toolchain",
        "scripts/c5_quality_gates/verify_seqlock_lean.py",
        "tests/test_seqlock_lean_ci.py",
        "Cargo.toml",
        "Cargo.lock",
        ".cargo/config.toml",
        "rust-toolchain.toml",
        ".github/workflows/verify_lean.yml",
    ):
        assert any(fnmatchcase(path, pattern) for pattern in paths), path
    job = workflow["jobs"]["verify-seqlock"]
    assert not job.get("if") and not job.get("needs") and not job.get("continue-on-error")
    steps = job["steps"]
    gate = next(step for step in steps if "verify_seqlock_lean.py" in step.get("run", ""))
    assert not gate.get("if") and not gate.get("continue-on-error")
    assert "--output-dir" in gate["run"]
    assert any("rust-toolchain@" in step.get("uses", "") for step in steps[: steps.index(gate)])
    assert any("elan-init" in step.get("run", "") for step in steps[: steps.index(gate)])
    assert any("upload-artifact@" in step.get("uses", "") and step.get("if") == "always()" for step in steps)
    source = (ROOT / "crates/b60-lang/src/lean_emitter.rs").read_text()
    assert len(TESTS) == len(set(TESTS)) == 2, "both distinct Seqlock regressions are required"
    for name in TESTS:
        assert f"fn {name.rsplit('::', 1)[1]}()" in source
