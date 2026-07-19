"""Tests C5-REAL para github_webhook_daemon.py (O1)."""

import hmac
import hashlib
import os
import sqlite3
from io import BytesIO
from unittest.mock import patch, MagicMock

import pytest

# Patching DB path before importing module
os.environ.setdefault("CORTEX_GITHUB_SECRET", "test-secret-key")


class FakeHeaders(dict):
    def get(self, key: str, default: str | None = None) -> str | None:  # type: ignore[override]
        return super().get(key, default)


def make_sig(payload: bytes, secret: str = "test-secret-key") -> str:
    mac = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={mac}"


class TestInitPerceptionLedger:
    def test_creates_db_and_table(self, tmp_path: "pytest.TempPathFactory") -> None:
        with patch(
            "cortex.github_webhook_daemon.CORTEX_DB_PATH", str(tmp_path / "test.db")
        ):
            with patch(
                "cortex.github_webhook_daemon.os.path.exists", return_value=True
            ):
                from cortex.github_webhook_daemon import init_perception_ledger

                init_perception_ledger()
                conn = sqlite3.connect(str(tmp_path / "test.db"))
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='github_events'"
                )
                assert cursor.fetchone() is not None
                conn.close()


class TestLogEvent:
    def test_log_event_new_payload(self, tmp_path: "pytest.TempPathFactory") -> None:
        db_path = str(tmp_path / "events.db")
        with patch("cortex.github_webhook_daemon.CORTEX_DB_PATH", db_path):
            from cortex.github_webhook_daemon import init_perception_ledger, log_event

            init_perception_ledger()
            result = log_event("push", b"unique-payload-abc")
            assert result is True

    def test_log_event_idempotency_lock(
        self, tmp_path: "pytest.TempPathFactory"
    ) -> None:
        db_path = str(tmp_path / "events.db")
        with patch("cortex.github_webhook_daemon.CORTEX_DB_PATH", db_path):
            from cortex.github_webhook_daemon import init_perception_ledger, log_event

            init_perception_ledger()
            log_event("push", b"duplicate-payload")
            result = log_event("push", b"duplicate-payload")
            assert result is False  # Idempotency Lock Ω15

    def test_lamport_clock_increments(self, tmp_path: "pytest.TempPathFactory") -> None:
        db_path = str(tmp_path / "events.db")
        with patch("cortex.github_webhook_daemon.CORTEX_DB_PATH", db_path):
            from cortex.github_webhook_daemon import init_perception_ledger, log_event

            init_perception_ledger()
            log_event("push", b"payload-a")
            log_event("pull_request", b"payload-b")
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT MAX(lamport_t) FROM github_events")
            max_t = cur.fetchone()[0]
            conn.close()
            assert max_t == 2


class TestGitHubWebhookHandler:
    def _make_handler(
        self,
        method: str,
        payload: bytes,
        secret: str = "test-secret-key",
        event_type: str = "push",
        include_sig: bool = True,
        valid_sig: bool = True,
        include_content_length: bool = True,
    ) -> MagicMock:
        from cortex.github_webhook_daemon import GitHubWebhookHandler

        handler = MagicMock(spec=GitHubWebhookHandler)
        handler.rfile = BytesIO(payload)
        headers: dict[str, str] = {}
        if include_content_length:
            headers["Content-Length"] = str(len(payload))
        if include_sig:
            sig = make_sig(payload, secret) if valid_sig else "sha256=invalidsig"
            headers["X-Hub-Signature-256"] = sig
        headers["X-GitHub-Event"] = event_type
        handler.headers = FakeHeaders(headers)
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.wfile = BytesIO()
        return handler

    def test_missing_content_length_returns_411(self) -> None:
        from cortex.github_webhook_daemon import GitHubWebhookHandler

        handler = MagicMock(spec=GitHubWebhookHandler)
        handler.headers = FakeHeaders({})
        handler.send_response = MagicMock()
        handler.end_headers = MagicMock()
        GitHubWebhookHandler.do_POST(handler)  # type: ignore[arg-type]
        handler.send_response.assert_called_once_with(411)

    def test_missing_signature_returns_401(self) -> None:
        from cortex.github_webhook_daemon import GitHubWebhookHandler

        handler = MagicMock(spec=GitHubWebhookHandler)
        handler.headers = FakeHeaders({"Content-Length": "5"})
        handler.rfile = BytesIO(b"hello")
        handler.send_response = MagicMock()
        handler.end_headers = MagicMock()
        GitHubWebhookHandler.do_POST(handler)  # type: ignore[arg-type]
        handler.send_response.assert_called_once_with(401)

    def test_invalid_signature_returns_403(
        self, tmp_path: "pytest.TempPathFactory"
    ) -> None:
        from cortex.github_webhook_daemon import GitHubWebhookHandler

        payload = b'{"ref": "main"}'
        handler = MagicMock(spec=GitHubWebhookHandler)
        handler.headers = FakeHeaders(
            {
                "Content-Length": str(len(payload)),
                "X-Hub-Signature-256": "sha256=wrongsig",
                "X-GitHub-Event": "push",
            }
        )
        handler.rfile = BytesIO(payload)
        handler.send_response = MagicMock()
        handler.end_headers = MagicMock()
        with patch("cortex.github_webhook_daemon.SECRET_KEY", "test-secret-key"):
            GitHubWebhookHandler.do_POST(handler)  # type: ignore[arg-type]
        handler.send_response.assert_called_once_with(403)

    def test_valid_new_event_returns_202(
        self, tmp_path: "pytest.TempPathFactory"
    ) -> None:
        from cortex.github_webhook_daemon import GitHubWebhookHandler

        payload = b'{"ref": "unique-main-branch"}'
        sig = make_sig(payload)
        handler = MagicMock(spec=GitHubWebhookHandler)
        handler.headers = FakeHeaders(
            {
                "Content-Length": str(len(payload)),
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "push",
            }
        )
        handler.rfile = BytesIO(payload)
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.wfile = BytesIO()
        db_path = str(tmp_path / "webhook.db")
        trigger_path = str(tmp_path / ".trigger_swarm")
        with (
            patch("cortex.github_webhook_daemon.SECRET_KEY", "test-secret-key"),
            patch("cortex.github_webhook_daemon.CORTEX_DB_PATH", db_path),
            patch("cortex.github_webhook_daemon.TRIGGER_PATH", trigger_path),
            patch("cortex.github_webhook_daemon.init_perception_ledger"),
            patch("cortex.github_webhook_daemon.log_event", return_value=True),
        ):
            GitHubWebhookHandler.do_POST(handler)  # type: ignore[arg-type]
        handler.send_response.assert_called_once_with(202)

    def test_duplicate_event_returns_200_idempotency(
        self, tmp_path: "pytest.TempPathFactory"
    ) -> None:
        from cortex.github_webhook_daemon import GitHubWebhookHandler

        payload = b'{"ref": "duplicate-ref"}'
        sig = make_sig(payload)
        handler = MagicMock(spec=GitHubWebhookHandler)
        handler.headers = FakeHeaders(
            {
                "Content-Length": str(len(payload)),
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "push",
            }
        )
        handler.rfile = BytesIO(payload)
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.wfile = BytesIO()
        with (
            patch("cortex.github_webhook_daemon.SECRET_KEY", "test-secret-key"),
            patch("cortex.github_webhook_daemon.log_event", return_value=False),
        ):
            GitHubWebhookHandler.do_POST(handler)  # type: ignore[arg-type]
        handler.send_response.assert_called_once_with(200)
