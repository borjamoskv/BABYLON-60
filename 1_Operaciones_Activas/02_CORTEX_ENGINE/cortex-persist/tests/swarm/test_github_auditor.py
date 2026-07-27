# [C5-REAL] Exergy-Maximized
"""Tests for GitHubAuditorDaemon."""

import asyncio
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from babylon60.extensions.swarm.github_auditor import GitHubAuditorDaemon


@pytest.fixture
def auditor():
    return GitHubAuditorDaemon(owner="borjamoskv", repo="BABYLON-60", poll_interval_s=1)


@pytest.mark.asyncio
async def test_fetch_codeql_alerts_success(auditor):
    """Prueba que el daemon parsea correctamente un JSON devuelto por GH CLI."""
    mock_gh_output = b'[{"number": 123, "rule": {"name": "test_rule"}}]\n'

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (mock_gh_output, b"")
    mock_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
        alerts = await auditor._fetch_codeql_alerts()

        assert len(alerts) == 1
        assert alerts[0]["number"] == 123
        mock_exec.assert_called_once_with(
            "gh",
            "api",
            "/repos/borjamoskv/BABYLON-60/code-scanning/alerts?state=open",
            "--paginate",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )


@pytest.mark.asyncio
async def test_mitigate_codeql_alert_skip_invalid(auditor):
    """Prueba que alertas sin path o línea son ignoradas termodinámicamente."""
    alert = {
        "number": 999,
        "rule": {"name": "sql-injection"},
        "most_recent_instance": {
            "location": {
                # Falta path y start_line
            }
        },
    }

    with patch("babylon60.extensions.mejoralo.swarm.MejoraloSwarm.refactor_file") as mock_refactor:
        await auditor._mitigate_codeql_alert(alert)
        mock_refactor.assert_not_called()


@pytest.mark.asyncio
async def test_mitigate_codeql_alert_success(auditor, tmp_path):
    """Prueba el ciclo de mitigación exitoso y cristalización."""
    target_file = tmp_path / "vulnerable.py"
    target_file.write_text("eval(user_input)")

    alert = {
        "number": 404,
        "rule": {"name": "eval-used"},
        "most_recent_instance": {"location": {"path": str(target_file), "start_line": 1}},
    }

    mock_swarm_instance = AsyncMock()
    mock_swarm_instance.refactor_file.return_value = "safe_eval(user_input)"

    with (
        patch(
            "babylon60.extensions.swarm.github_auditor.MejoraloSwarm",
            return_value=mock_swarm_instance,
        ),
        patch.object(auditor, "_git_commit", new_callable=AsyncMock) as mock_git,
    ):
        await auditor._mitigate_codeql_alert(alert)

        assert 404 in auditor._in_flight_alerts
        mock_swarm_instance.refactor_file.assert_called_once_with(
            file_path=target_file, findings=[f"{str(target_file)}:1 -> eval-used"]
        )
        assert target_file.read_text() == "safe_eval(user_input)"
        mock_git.assert_called_once_with(
            target_file, "[bridge] fix(security): resolve CodeQL alert #404"
        )
