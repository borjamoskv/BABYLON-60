"""C27: isolated descriptor confinement regressions; no user brain is accessed."""

import os

import pytest

from babylon60.adapters.codex import mcp_server as module


@pytest.fixture
def artifact_tree(tmp_path, monkeypatch):
    root = tmp_path.resolve() / "brain"
    root.mkdir(mode=0o700)
    conversation = root / "conversation"
    conversation.mkdir(mode=0o700)
    (conversation / "report.txt").write_text("inside")
    monkeypatch.setattr(module, "ANTIGRAVITY_BRAIN", root)
    server = object.__new__(module.AntigravityMcpServer)
    return server, root, conversation


def read(server, name="report.txt"):
    return server._tool_read_artifact({"artifact_name": name})


def test_regular_artifact_and_traversal(artifact_tree):
    server, _, _ = artifact_tree
    assert "inside" in read(server)["content"][0]["text"]
    for name in ("../report.txt", "/report.txt", "a\\b", "\x00"):
        assert read(server, name)["isError"]


def test_parent_replacement_cannot_redirect_open(artifact_tree, tmp_path, monkeypatch):
    server, root, conversation = artifact_tree
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "report.txt").write_text("outside-secret")
    original_open = os.open
    replaced = False

    def racing_open(path, flags, *args, **kwargs):
        nonlocal replaced
        if path == "report.txt" and not replaced:
            replaced = True
            conversation.rename(root / "moved")
            conversation.symlink_to(outside, target_is_directory=True)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", racing_open)
    result = read(server)
    assert replaced
    assert "inside" in result["content"][0]["text"]
    assert "outside-secret" not in str(result)


def test_symlink_fifo_oversized_and_writable_files_rejected(artifact_tree, tmp_path):
    server, _, conversation = artifact_tree
    artifact = conversation / "report.txt"
    artifact.unlink()
    outside = tmp_path / "secret"
    outside.write_text("secret")
    artifact.symlink_to(outside)
    assert read(server)["isError"]
    artifact.unlink()
    os.mkfifo(artifact)
    assert read(server)["isError"]
    artifact.unlink()
    artifact.write_bytes(b"x" * (module.MAX_ARTIFACT_BYTES + 1))
    assert read(server)["isError"]
    artifact.write_text("unsafe")
    artifact.chmod(0o666)
    assert read(server)["isError"]


def test_root_symlink_rejected(artifact_tree, tmp_path, monkeypatch):
    server, root, _ = artifact_tree
    link = tmp_path / "linked-brain"
    link.symlink_to(root, target_is_directory=True)
    monkeypatch.setattr(module, "ANTIGRAVITY_BRAIN", link)
    assert read(server)["isError"]


def test_file_growth_after_validation_is_bounded(artifact_tree, monkeypatch):
    server, _, conversation = artifact_tree
    original = server._find_artifact

    def growing(name):
        descriptor = original(name)
        (conversation / name).write_bytes(b"x" * (module.MAX_ARTIFACT_BYTES + 1))
        return descriptor

    monkeypatch.setattr(server, "_find_artifact", growing)
    assert read(server)["isError"]
