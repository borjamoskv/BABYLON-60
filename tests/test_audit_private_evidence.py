"""Privacy regressions use only synthetic inputs and temporary directories."""

import json
import logging
import os
from pathlib import Path
import stat
import uuid

import pytest

from scripts.c5_log_custody import c5_preserve_logs as custody
from scripts.c5_cli import moskv_native_host as host


def test_selection_required_without_creating_destination(tmp_path: Path) -> None:
    destination = tmp_path / "private"
    with pytest.raises(ValueError, match="explicitly"):
        custody.harvest_provider_logs("claude", destination=destination)
    assert not destination.exists()


def test_receipt_has_no_messages_paths_or_reasoning(tmp_path: Path) -> None:
    source = tmp_path / "session.jsonl"
    source.write_text(json.dumps({"prompt": "private synthetic prompt", "thinking": "private reasoning"}))
    destination = tmp_path / "private"
    names = custody.harvest_provider_logs("claude", [source], destination=destination)
    stored = json.loads((destination / names[0]).read_text())
    assert set(stored) == {"provider", "bytes", "sha256"}
    assert stored["bytes"] == source.stat().st_size
    assert stat.S_IMODE(destination.stat().st_mode) == 0o700
    assert stat.S_IMODE((destination / names[0]).stat().st_mode) == 0o600


def test_custody_rejects_repo_destination_and_symlink_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.write_text("synthetic")
    with pytest.raises(ValueError, match="outside"):
        custody.harvest_provider_logs("agent", [source], destination=custody.REPO_ROOT / "new-evidence")
    link = tmp_path / "link"
    link.symlink_to(source)
    with pytest.raises(OSError):
        custody.harvest_provider_logs("agent", [link], destination=tmp_path / "private")


def test_receipt_retention_only_removes_owned_namespace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    destination = tmp_path / "private"
    destination.mkdir(mode=0o700)
    old = destination / f"receipt-{uuid.uuid4()}.json"
    old.write_text("{}")
    other = destination / "unrelated.json"
    other.write_text("keep")
    os.utime(old, (1, 1))
    source = tmp_path / "source"
    source.write_text("synthetic")
    monkeypatch.setattr(custody, "MAX_RECEIPTS", 2)
    for _ in range(3):
        custody.harvest_provider_logs("agent", [source], destination=destination)
    assert not old.exists()
    assert other.read_text() == "keep"
    assert len(list(destination.glob("receipt-*.json"))) == 2


def test_private_log_rejects_symlinks_and_hardlinks(tmp_path: Path) -> None:
    directory = tmp_path / "logs"
    directory.mkdir(mode=0o700)
    victim = tmp_path / "victim"
    victim.write_text("unchanged")
    path = directory / "events.log"
    path.symlink_to(victim)
    with pytest.raises(OSError):
        host.PrivateRotatingHandler(path)
    path.unlink()
    os.link(victim, path)
    with pytest.raises(PermissionError):
        host.PrivateRotatingHandler(path)
    assert victim.read_text() == "unchanged"


def test_private_log_rejects_parent_symlink(tmp_path: Path) -> None:
    directory = tmp_path / "private"
    directory.mkdir(mode=0o700)
    link = tmp_path / "alias"
    link.symlink_to(directory)
    with pytest.raises(OSError):
        host.PrivateRotatingHandler(link / "events.log")


def test_private_log_rotation_is_bounded(tmp_path: Path) -> None:
    path = tmp_path / "logs" / "events.log"
    handler = host.PrivateRotatingHandler(path, max_bytes=256, backups=2)
    try:
        for _ in range(30):
            handler.emit(logging.LogRecord("test", logging.INFO, "", 0, "x" * 100, (), None))
    finally:
        handler.close()
    files = list(path.parent.iterdir())
    assert len(files) == 3
    assert all(file.stat().st_size <= 256 for file in files)
    assert all(stat.S_IMODE(file.stat().st_mode) == 0o600 for file in files)


def test_generate_prompt_is_transmitted_but_not_logged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    private_prompt = "synthetic private prompt"
    monkeypatch.setattr(host, "get_next_prompt", lambda: private_prompt)
    sent = []
    monkeypatch.setattr(host, "send_message_frame", lambda payload: sent.append(payload))
    path = tmp_path / "logs" / "events.log"
    handler = host.PrivateRotatingHandler(path)
    logger = logging.Logger("isolated")
    logger.addHandler(handler)
    try:
        host.process_extension_event({"status": "READY"}, logger)
        host.process_extension_event(
            {"status": private_prompt, "cmd": private_prompt, "prompt": private_prompt}, logger
        )
        host.process_extension_event({"status": "FATAL_ENTROPY", "error": private_prompt}, logger)
    finally:
        handler.close()
    assert sent[0]["prompt"] == private_prompt
    assert private_prompt not in path.read_text()
