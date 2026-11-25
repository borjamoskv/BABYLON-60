"""Conformance must authenticate its control, preserve failed exits and not repeat the suite."""

import subprocess
import sys

import pytest

from scripts.c5_verifiers import conformance_test


def test_replay_control_uses_real_quorum_before_detecting_corruption() -> None:
    conformance_test.test_replay_corruption()


def test_failed_command_is_not_retried_in_a_different_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fail(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 7, "", "first command failed")

    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(SystemExit) as exc:
        conformance_test.run_cmd([sys.executable, "-c", "raise SystemExit(7)"])
    assert exc.value.code == 7
    assert calls == [[sys.executable, "-c", "raise SystemExit(7)"]]


def test_main_runs_its_own_checks_and_leaves_the_suite_to_python_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    order: list[str] = []
    for name in ("check_wheel_contents", "create_crypto_vectors", "test_replay_corruption"):
        monkeypatch.setattr(conformance_test, name, lambda name=name: order.append(name))

    def no_subprocess(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise AssertionError(f"conformance main must not run {command}")

    monkeypatch.setattr(subprocess, "run", no_subprocess)
    conformance_test.main()
    assert order == ["check_wheel_contents", "create_crypto_vectors", "test_replay_corruption"]
