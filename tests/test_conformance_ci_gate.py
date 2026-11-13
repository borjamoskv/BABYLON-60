"""Conformance must authenticate its control and preserve failed test exits."""

import subprocess
import sys

import pytest

from scripts.c5_verifiers import conformance_test


def test_replay_control_uses_real_quorum_before_detecting_corruption() -> None:
    conformance_test.test_replay_corruption()


def test_failed_suite_is_not_retried_in_a_different_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fail_suite(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 7, "", "first suite failed")

    monkeypatch.setattr(subprocess, "run", fail_suite)
    with pytest.raises(SystemExit) as exc:
        conformance_test.run_ci_checks()
    assert exc.value.code == 7
    assert calls == [[sys.executable, "-m", "pytest", "tests/", "--maxfail=0"]]
