"""verify_claims treats a test runner that reports no passed test as empty evidence."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.c5_quality_gates.verify_claims import count_executed_tests, is_test_runner_step, run_command

CARGO_OK = "running 3 tests\ntest result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out"
CARGO_ALL_IGNORED = "running 3 tests\ntest result: ok. 0 passed; 0 failed; 3 ignored; 0 measured; 0 filtered out"
PYTEST_OK = "============================== 4 passed, 1 skipped in 0.12s =============================="
PYTEST_ALL_SKIPPED = "============================== 2 skipped in 0.03s =============================="
PYTEST_ALL_DESELECTED = "============================ 7 deselected in 0.02s ============================="


def test_counts_passed_tests_not_declared_tests() -> None:
    assert count_executed_tests(CARGO_OK) == 3
    assert count_executed_tests(PYTEST_OK) == 4
    assert count_executed_tests(CARGO_OK + "\n" + PYTEST_OK) == 7


@pytest.mark.parametrize("output", [CARGO_ALL_IGNORED, PYTEST_ALL_SKIPPED, PYTEST_ALL_DESELECTED, "2 skipped in 0.03s"])
def test_runs_without_a_passed_test_count_as_zero_or_unrecognised(output: str) -> None:
    assert not count_executed_tests(output)


def test_an_empty_block_is_not_hidden_by_a_passing_one() -> None:
    assert count_executed_tests(CARGO_OK + "\n" + CARGO_ALL_IGNORED) == 0
    assert count_executed_tests(PYTEST_OK + "\n" + PYTEST_ALL_SKIPPED) == 0


def test_output_without_test_results_is_unrecognised() -> None:
    assert count_executed_tests("Finished `dev` profile in 0.31s") is None


def test_test_runner_steps_are_identified() -> None:
    assert is_test_runner_step(["cargo", "test", "--locked"])
    assert is_test_runner_step(["cargo", "+nightly", "test"])
    assert is_test_runner_step(["pytest", "tests/"])
    assert is_test_runner_step(["python3", "-m", "pytest", "-q"])
    assert not is_test_runner_step(["cargo", "run", "--locked"])
    assert not is_test_runner_step(["lean", "proof/lean/BabylonTrace.lean"])
    assert not is_test_runner_step([])


def _fake_runner(monkeypatch: pytest.MonkeyPatch, *stdouts: str) -> None:
    """Stubs subprocess.run; successive steps receive successive outputs (the last one repeats)."""
    pending = list(stdouts)

    def fake_run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        stdout = pending.pop(0) if len(pending) > 1 else pending[0]
        return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)


@pytest.mark.parametrize("stdout", ["2 skipped in 0.03s", "Finished `test` profile in 0.31s", ""])
def test_test_runner_exiting_zero_without_passed_tests_is_vacuous(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, stdout: str
) -> None:
    _fake_runner(monkeypatch, stdout)
    for command in (
        "pytest -q tests/test_probe.py",
        "cargo test --locked --test probe",
        "uv run --locked pytest tests/test_probe.py -q",
    ):
        ok, output, _ = run_command(command, tmp_path)
        assert not ok
        assert output.startswith("VACUOUS_EVIDENCE")


def test_non_test_command_without_test_output_is_accepted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _fake_runner(monkeypatch, "Finished `dev` profile in 0.31s")
    ok, output, _ = run_command("cargo run --locked --bin probe", tmp_path)
    assert ok, output


def test_passing_test_run_is_accepted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _fake_runner(monkeypatch, PYTEST_OK)
    for command in ("pytest tests/test_probe.py", "uv run --locked pytest tests/test_probe.py -q"):
        ok, output, _ = run_command(command, tmp_path)
        assert ok, output


@pytest.mark.parametrize("empty", ["2 skipped in 0.01s", ""])
@pytest.mark.parametrize("empty_first", [False, True])
def test_a_passing_step_does_not_hide_an_empty_chained_step(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, empty: str, empty_first: bool
) -> None:
    outputs = (empty, "1 passed in 0.01s") if empty_first else ("1 passed in 0.01s", empty)
    _fake_runner(monkeypatch, *outputs)
    ok, output, _ = run_command("pytest -q tests/a.py && pytest -q tests/b.py", tmp_path)
    assert not ok
    assert output.startswith("VACUOUS_EVIDENCE")


def test_non_test_step_chained_with_a_passing_test_step_is_accepted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _fake_runner(monkeypatch, "Finished `dev` profile in 0.31s", CARGO_OK)
    ok, output, _ = run_command("cargo build --locked && cargo test --locked --lib probe", tmp_path)
    assert ok, output


def test_announced_cargo_tests_without_a_result_do_not_count() -> None:
    # The harness exited 0 mid-run (e.g. a test calling std::process::exit(0)).
    assert count_executed_tests("running 1 test") == 0
    assert count_executed_tests(CARGO_OK + "\nrunning 2 tests") == 0


def test_uv_run_wrapper_is_unwrapped_before_classifying() -> None:
    assert is_test_runner_step(["uv", "run", "--locked", "pytest", "tests/a.py", "-q"])
    assert is_test_runner_step(["uv", "run", "--no-sync", "--extra", "dev", "cargo", "test", "--workspace"])
    assert is_test_runner_step(["uv", "run", "--", "python", "-m", "pytest"])
    assert not is_test_runner_step(["uv", "run", "--locked", "ruff", "check", "tests"])
    assert not is_test_runner_step(["uv", "run", "--locked"])
    assert not is_test_runner_step(["uv", "sync", "--locked"])
