"""The historical entrypoint must retain the maintained dashboard boundary."""

import io
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from babylon60.dashboard import server
from scripts.c5_thermo import exergy_dashboard_server as legacy


def test_legacy_entrypoint_uses_the_maintained_implementation() -> None:
    assert legacy.main is server.main
    assert legacy.ExergyDashboardHandler is server.ExergyDashboardHandler


def test_legacy_entrypoint_rejects_all_interface_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    constructor = Mock(side_effect=AssertionError("No listener may be opened"))
    monkeypatch.setattr(server, "HTTPServer", constructor)
    monkeypatch.setenv("BABYLON_DASHBOARD_HOST", "0.0.0.0")
    with pytest.raises(ValueError, match="literal IPv4 loopback"):
        legacy.main()
    constructor.assert_not_called()


@pytest.mark.parametrize("valid_schema", [True, False])
def test_legacy_metrics_restrict_columns_and_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_schema: bool
) -> None:
    db_path = tmp_path / "private-ledger.sqlite"
    with sqlite3.connect(db_path) as db:
        if valid_schema:
            db.execute("CREATE TABLE ledger(timestamp REAL, commit_hash TEXT, exergy_score REAL, verdict_yaml TEXT)")
            db.execute("INSERT INTO ledger VALUES (1, 'public-commit', 0.5, 'private-verdict-canary')")
    monkeypatch.setattr(server, "_get_db_path", lambda: db_path)
    handler = object.__new__(legacy.ExergyDashboardHandler)
    handler.wfile = io.BytesIO()
    response = Mock()
    monkeypatch.setattr(handler, "send_response", response)
    monkeypatch.setattr(handler, "send_header", Mock())
    monkeypatch.setattr(handler, "end_headers", Mock())
    handler.serve_metrics()
    body = handler.wfile.getvalue()
    assert b"private-verdict-canary" not in body
    assert str(db_path).encode() not in body
    if valid_schema:
        response.assert_called_once_with(200)
        assert json.loads(body) == [{"timestamp": 1.0, "commit_hash": "public-commit", "exergy_score": 0.5}]
    else:
        response.assert_called_once_with(500)
        assert json.loads(body) == {"error": "Telemetry query failed", "code": 500}


def test_direct_legacy_script_works_outside_repository(tmp_path: Path) -> None:
    script = Path(legacy.__file__).absolute()
    environment = {**os.environ, "BABYLON_DASHBOARD_HOST": "0.0.0.0"}
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(script)], cwd=tmp_path, env=environment,
        capture_output=True, text=True, timeout=10, check=False,
    )
    assert result.returncode != 0
    assert "Dashboard host must be a literal IPv4 loopback address" in result.stderr
    assert "ModuleNotFoundError" not in result.stderr
