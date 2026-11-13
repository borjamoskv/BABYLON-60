"""CLI wording distinguishes logical cleanup and report verification failures."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from babylon60.cli.main_dispatcher import cmd_mcp_bomb
from babylon60.kernel import mcp_lifecycle_manager


@pytest.mark.parametrize("cleaned", [True, False])
def test_ephemeral_cli_reports_only_logical_cleanup(
    cleaned: bool, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    receipt = {
        "status": "SUCCESS", "server_name": "fixture", "tool_name": "fixture.run",
        "code_hash": "ab" * 32, "self_destruct_verified": cleaned, "latency_ms": 1.0, "tool_output": 2,
    }
    monkeypatch.setattr(
        mcp_lifecycle_manager, "McpLifecycleManager",
        lambda: SimpleNamespace(synthesize_and_detonate_bomb=lambda **arguments: dict(receipt)),
    )
    args = argparse.Namespace(domain="fixture", code="unused fixture", args="{}", json=False)
    assert cmd_mcp_bomb(args) == 0
    output = capsys.readouterr().out
    assert "Limpieza lógica (ruta/registro):" in output
    assert ("COMPROBADA" if cleaned else "INCOMPLETA") in output
    assert "CERO HUELLA" not in output
    assert "Autodestrucción (Disk)" not in output


def test_legacy_cleanup_boolean_is_preserved_in_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    receipt = {"status": "SUCCESS", "self_destruct_verified": True}
    monkeypatch.setattr(
        mcp_lifecycle_manager, "McpLifecycleManager",
        lambda: SimpleNamespace(synthesize_and_detonate_bomb=lambda **arguments: dict(receipt)),
    )
    args = argparse.Namespace(domain="fixture", code="unused fixture", args="{}", json=True)
    assert cmd_mcp_bomb(args) == 0
    assert json.loads(capsys.readouterr().out) == receipt


def test_missing_compliance_bundle_fails_before_report_generation(tmp_path: Path) -> None:
    root = Path(__file__).absolute().parents[1]
    output = tmp_path / "report.html"
    environment = dict(
        os.environ,
        PYTHONPATH=str(root / "01_KISH_ENGINE"),
        BABYLON_HOME=str(tmp_path / "state"),
        BABYLON_CAUSAL_GATE_DB=str(tmp_path / "gate.db"),
    )
    result = subprocess.run(
        [sys.executable, "-m", "babylon60.cli.main_dispatcher", "compliance",
         "--bundle", str(tmp_path / "missing-bundle"), "--format", "html", "--output", str(output)],
        cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 1
    assert "FileNotFoundError" in result.stderr
    assert not output.exists()
    assert not (tmp_path / "state").exists()
