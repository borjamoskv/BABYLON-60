"""Dashboard boundary regressions; no listening sockets are opened."""

import io
import json
import sqlite3
from pathlib import Path
from unittest.mock import Mock

import pytest

from babylon60.dashboard import server


@pytest.mark.parametrize(
    "host", ["0.0.0.0", "192.168.1.1", "8.8.8.8", "localhost", "::", "::1", "", "127.0.0.1.example"]
)
def test_non_loopback_bind_rejected_before_server_creation(monkeypatch: pytest.MonkeyPatch, host: str) -> None:
    constructor = Mock(side_effect=AssertionError("No listening socket may be opened"))
    monkeypatch.setattr(server, "HTTPServer", constructor)
    monkeypatch.setenv("BABYLON_DASHBOARD_HOST", host)
    with pytest.raises(ValueError, match="literal IPv4 loopback"):
        server.main()
    constructor.assert_not_called()


@pytest.mark.parametrize("host", ["127.0.0.1", "127.0.0.2"])
def test_loopback_bind_is_retained(monkeypatch: pytest.MonkeyPatch, host: str) -> None:
    httpd = Mock()
    httpd.serve_forever.side_effect = KeyboardInterrupt
    constructor = Mock(return_value=httpd)
    monkeypatch.setattr(server, "HTTPServer", constructor)
    monkeypatch.setenv("BABYLON_DASHBOARD_HOST", host)
    monkeypatch.setenv("BABYLON_DASHBOARD_PORT", "8080")
    server.main()
    constructor.assert_called_once_with((host, 8080), server.ExergyDashboardHandler)
    httpd.server_close.assert_called_once()


def test_dashboard_uses_only_text_sinks_and_external_script() -> None:
    assert "innerHTML" not in server.DASHBOARD_JS
    assert "outerHTML" not in server.DASHBOARD_JS
    assert "insertAdjacentHTML" not in server.DASHBOARD_JS
    assert server.DASHBOARD_JS.count(".textContent =") == 2
    assert '<pre id="events">' in server.DEFAULT_HTML
    assert '<script src="/dashboard.js" defer></script>' in server.DEFAULT_HTML
    assert "unsafe-inline" not in server.CONTENT_SECURITY_POLICY
    assert "script-src 'self'" in server.CONTENT_SECURITY_POLICY
    assert "default-src 'none'" in server.CONTENT_SECURITY_POLICY


def test_metrics_omit_private_columns_and_preserve_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "ledger.db"
    hostile_text = '<img src=x onerror="alert(1)">'
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE ledger (timestamp TEXT, commit_hash TEXT, exergy_score REAL, verdict_yaml TEXT)")
        conn.execute("INSERT INTO ledger VALUES (?, ?, ?, ?)", ("2026-10-23", hostile_text, 0.5, "private-details"))
    monkeypatch.setattr(server, "_get_db_path", lambda: db)
    handler = object.__new__(server.ExergyDashboardHandler)
    handler.wfile = io.BytesIO()
    response = Mock()
    monkeypatch.setattr(handler, "send_response", response)
    monkeypatch.setattr(handler, "send_header", Mock())
    monkeypatch.setattr(handler, "end_headers", Mock())
    handler.serve_metrics()
    response.assert_called_once_with(200)
    assert json.loads(handler.wfile.getvalue()) == [
        {"timestamp": "2026-10-23", "commit_hash": hostile_text, "exergy_score": 0.5}
    ]
    assert b"private-details" not in handler.wfile.getvalue()
