"""Codex discovery and process failures must stay visible to callers."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from babylon60.adapters.codex import codex_driver


def test_driver_honors_explicit_cli_at_construction(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    executable = tmp_path / "custom-codex"
    monkeypatch.setenv("CODEX_CLI", str(executable))
    assert codex_driver.CodexDriver().cli_path == executable


@pytest.mark.parametrize("bundled", [True, False])
def test_driver_discovers_available_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bundled: bool) -> None:
    executable = tmp_path / "codex"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    monkeypatch.delenv("CODEX_CLI", raising=False)
    monkeypatch.setattr(codex_driver, "_CODEX_CLI_CANDIDATES", (executable if bundled else tmp_path / "absent",))
    monkeypatch.setattr(shutil, "which", lambda _name: None if bundled else str(executable))
    assert codex_driver.CodexDriver().cli_path == executable


@pytest.mark.parametrize("partial_text", ["", "Partial response before the failure"])
def test_nonzero_cli_exit_is_failure_even_after_partial_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, partial_text: str
) -> None:
    executable = tmp_path / "codex"
    executable.touch()
    events = [
        {"type": "item.completed", "item": {"type": "agent_message", "text": partial_text}},
        {"type": "error", "message": "The requested model is unavailable"},
    ]
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 1, "\n".join(json.dumps(event) for event in events), "diagnostic stderr"
        ),
    )
    result = codex_driver.CodexDriver(cli_path=executable).ask("test prompt")
    assert result["success"] is False
    assert result["returncode"] == 1
    assert result["error"] == "The requested model is unavailable"
