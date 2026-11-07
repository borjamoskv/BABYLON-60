"""Acceptance of the isolated Babylon Work workspace and its HTTP boundary."""

import json
import threading
from contextlib import closing, contextmanager
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

import pytest

from tools.babylon_work import workspace as module
from tools.babylon_work.server import WorkServer
from tools.babylon_work.workspace import Workspace, WorkspaceError, read_source


@pytest.fixture
def workspace(tmp_path):
    return Workspace(tmp_path / "work.sqlite")


def task(workspace):
    return workspace.create(
        {"title": "Guía de instalación", "prompt": "Documentar la instalación de Babylon.", "kind": "document"}
    )


def change(workspace, current, action, **fields):
    return workspace.update(current["id"], {"revision": current["revision"], "action": action, **fields})


def test_recovers_document_decisions_and_history_after_reopen(workspace):
    current = task(workspace)
    current = change(workspace, current, "prepare")
    assert "README.md" in current["document"]
    assert "no se ha invocado un modelo de IA" in current["document"]
    assert current["sources"][0]["digest"] == read_source("overview")["digest"]
    current = change(workspace, current, "save", document="# Revisión humana\n\nDocumento propio.")
    current = change(workspace, current, "decision", decision="Mantener la CLI actual.")
    current = change(workspace, current, "pause")
    reopened = Workspace(workspace.path).get(current["id"])
    assert reopened["document"] == "# Revisión humana\n\nDocumento propio."
    assert reopened["decisions"] == ["Mantener la CLI actual."]
    assert reopened["status"] == "paused"
    resumed = change(workspace, reopened, "resume")
    assert resumed["status"] == "active"
    assert len(resumed["events"]) == 6
    with closing(workspace.connect()) as db:
        assert db.execute("PRAGMA synchronous").fetchone()[0] == 2
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_stale_revision_cannot_overwrite_document(workspace):
    initial = task(workspace)
    saved = change(workspace, initial, "save", document="Primer editor")
    with pytest.raises(WorkspaceError, match="otra ventana") as caught:
        change(workspace, initial, "save", document="Texto atrasado")
    assert caught.value.status == 409
    assert workspace.get(initial["id"])["document"] == saved["document"]


def test_failed_prepare_rolls_back_revision_and_event(workspace, monkeypatch):
    current = task(workspace)
    monkeypatch.setattr(module, "read_source", lambda _: (_ for _ in ()).throw(WorkspaceError("Fuente ausente")))
    with pytest.raises(WorkspaceError, match="Fuente ausente"):
        change(workspace, current, "prepare")
    recovered = workspace.get(current["id"])
    assert recovered["revision"] == 1
    assert recovered["document"] == ""
    assert len(recovered["events"]) == 1


def test_existing_draft_is_not_overwritten_by_prepare(workspace):
    current = change(workspace, task(workspace), "save", document="Trabajo manual")
    with pytest.raises(WorkspaceError, match="Ya existe un borrador"):
        change(workspace, current, "prepare")
    assert workspace.get(current["id"])["document"] == "Trabajo manual"


def test_completion_requires_saved_document_and_human_review(workspace):
    current = task(workspace)
    with pytest.raises(WorkspaceError):
        change(workspace, current, "complete", reviewed=True)
    current = change(workspace, current, "save", document="Documento revisado")
    with pytest.raises(WorkspaceError):
        change(workspace, current, "complete", reviewed=False)
    current = change(workspace, current, "complete", reviewed=True)
    with pytest.raises(WorkspaceError, match="Reabre"):
        change(workspace, current, "save", document="Otro texto")
    assert change(workspace, current, "reopen")["status"] == "review"


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "", "prompt": "Objetivo"},
        {"title": "A", "prompt": " "},
        {"title": "A", "prompt": "B", "kind": "shell"},
        {"title": "A", "prompt": "B", "kind": []},
        {"title": "A" * 161, "prompt": "B"},
    ],
)
def test_invalid_task_is_rejected(workspace, payload):
    with pytest.raises(WorkspaceError):
        workspace.create(payload)
    assert workspace.list() == []


@pytest.mark.parametrize("component", ["file", "directory"])
def test_symlink_source_is_rejected(tmp_path, monkeypatch, component):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "source.md").write_text("Private content")
    if component == "directory":
        (root / "docs").symlink_to(outside, target_is_directory=True)
    else:
        (root / "docs").mkdir()
        (root / "docs" / "source.md").symlink_to(outside / "source.md")
    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setitem(module.SOURCES, "fixture", ("Fixture", "docs/source.md"))
    with pytest.raises(WorkspaceError, match="alcance actual"):
        read_source("fixture")


@pytest.mark.parametrize("source", ["../../.env", "overview/../../.env", "missing"])
def test_arbitrary_source_paths_are_rejected(source):
    with pytest.raises(WorkspaceError):
        read_source(source)


@pytest.mark.parametrize("source_id", module.SOURCES)
def test_catalog_sources_are_readable_and_identified(source_id):
    source = read_source(source_id)
    assert source["content"].strip()
    assert len(source["digest"]) == 64
    assert source["bytes"] == len(source["content"].encode())


@contextmanager
def server_for(workspace):
    # HTTP workspace tests never contact live model providers.
    with patch("tools.babylon_work.providers.ModelClient.discover", return_value=[]):
        server = WorkServer(0, workspace)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


def request(server, path, body=None, *, authorized=True, headers=None):
    request_headers = {"Content-Type": "application/json"}
    if authorized:
        request_headers["Authorization"] = "Bearer " + server.token
    request_headers.update(headers or {})
    req = Request(
        server.origin + path, data=None if body is None else json.dumps(body).encode(), headers=request_headers
    )
    return urlopen(req, timeout=3)


def test_http_authentication_origin_scope_and_csp(workspace):
    with server_for(workspace) as server:
        for headers, authorized, code in [
            ({}, False, 401),
            ({"Origin": "https://untrusted.example"}, True, 403),
            ({"Host": "untrusted.example"}, True, 403),
        ]:
            with pytest.raises(HTTPError) as caught:
                request(server, "/api/workspace", authorized=authorized, headers=headers)
            assert caught.value.code == code
        with request(server, "/", authorized=False) as response:
            assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
            assert b"Babylon Work" in response.read()
        with request(server, "/api/tasks", {"title": "HTTP", "prompt": "Persistir por HTTP"}) as response:
            current = json.load(response)
        with request(
            server, "/api/tasks/" + current["id"], {"action": "prepare", "revision": current["revision"]}
        ) as response:
            prepared = json.load(response)
        assert prepared["status"] == "review"
        assert prepared["document"]
        with pytest.raises(HTTPError) as caught:
            request(server, "/api/tasks/" + current["id"], {"action": "execute", "revision": 2})
        assert caught.value.code == 400
        with pytest.raises(HTTPError) as caught:
            request(server, "/api/sources/../../.env")
        assert caught.value.code == 404
    with server_for(Workspace(workspace.path)) as restarted:
        with request(restarted, "/api/tasks/" + current["id"]) as response:
            assert json.load(response)["document"] == prepared["document"]
