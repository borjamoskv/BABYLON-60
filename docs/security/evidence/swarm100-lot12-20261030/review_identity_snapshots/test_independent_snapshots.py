"""Independent snapshot effects; script defaults run only from owned copies."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import uuid

import pytest


ROOT = Path(__file__).absolute().parents[5]
SOURCE = ROOT / "scripts/c5_l1_ledger/ledger_snapshot_engine.py"


def fixture_module(tmp_path):
    repo = tmp_path / "owned-repo"
    path = repo / "scripts/c5_l1_ledger/ledger_snapshot_engine.py"
    path.parent.mkdir(parents=True)
    path.write_bytes(SOURCE.read_bytes())
    spec = importlib.util.spec_from_file_location(f"snapshot_review_{uuid.uuid4().hex}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.get_latest_commit = lambda: "controlled-fixture-commit"
    return module, repo


def create_source(module):
    with sqlite3.connect(module.DB_PATH) as conn:
        conn.execute("CREATE TABLE points (value INTEGER NOT NULL)")
        conn.execute("INSERT INTO points VALUES (73)")


class FrozenClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 10, 30, 14, 0, tzinfo=timezone.utc)


def test_empty_foreign_destination_is_not_reused(monkeypatch, tmp_path):
    module, repo = fixture_module(tmp_path)
    create_source(module)
    token = uuid.UUID(int=917)
    module.datetime = FrozenClock
    monkeypatch.setattr(module.uuid, "uuid4", lambda: token)
    module.SNAPSHOT_DIR.mkdir(parents=True)
    foreign = module.SNAPSHOT_DIR / f"cortex_snapshot_20261030_140000_{token.hex}.db"
    foreign.touch()
    inode = foreign.stat().st_ino
    with pytest.raises(FileExistsError):
        module.create_snapshot()
    assert foreign.stat().st_ino == inode
    assert foreign.read_bytes() == b""
    assert list(module.SNAPSHOT_DIR.iterdir()) == [foreign]


def test_foreign_staging_collision_is_preserved(monkeypatch, tmp_path):
    module, repo = fixture_module(tmp_path)
    create_source(module)
    token = uuid.UUID(int=918)
    module.datetime = FrozenClock
    monkeypatch.setattr(module.uuid, "uuid4", lambda: token)
    module.SNAPSHOT_DIR.mkdir(parents=True)
    foreign = module.SNAPSHOT_DIR / f".tmp_20261030_140000_{token.hex}.json"
    foreign.write_bytes(b"foreign-staging-content")
    inode = foreign.stat().st_ino
    with pytest.raises(FileExistsError):
        module.create_snapshot()
    assert foreign.stat().st_ino == inode
    assert foreign.read_bytes() == b"foreign-staging-content"
    assert list(module.SNAPSHOT_DIR.iterdir()) == [foreign]


def test_directory_sync_failure_does_not_emit_ledger_event(monkeypatch, tmp_path):
    module, repo = fixture_module(tmp_path)
    create_source(module)
    actors = []

    def forbidden_actor(*args, **kwargs):
        actors.append(args)
        raise AssertionError("the failed snapshot must not reach the ledger actor")

    def reject_directory_sync(path):
        raise OSError("fixture directory sync rejected")

    monkeypatch.setattr(module, "BFTLedgerActor", forbidden_actor)
    monkeypatch.setattr(module, "_sync_directory", reject_directory_sync)
    with pytest.raises(OSError, match="directory sync rejected"):
        module.main()
    assert actors == []
    assert list(module.SNAPSHOT_DIR.iterdir()) == []
    with sqlite3.connect(module.DB_PATH) as conn:
        assert conn.execute("SELECT value FROM points").fetchall() == [(73,)]


def test_database_sync_failure_preserves_source_and_publishes_nothing(monkeypatch, tmp_path):
    module, repo = fixture_module(tmp_path)
    create_source(module)
    before = module.DB_PATH.read_bytes()
    original = os.fsync

    def fail_database(fd):
        if not os.fstat(fd).st_mode & 0o040000:
            raise OSError("fixture database sync rejected")
        return original(fd)

    monkeypatch.setattr(module.os, "fsync", fail_database)
    with pytest.raises(OSError, match="database sync rejected"):
        module.create_snapshot()
    assert module.DB_PATH.read_bytes() == before
    assert list(module.SNAPSHOT_DIR.iterdir()) == []


def test_wal_pair_snapshots_see_only_complete_commits(tmp_path):
    module, repo = fixture_module(tmp_path)
    module.datetime = FrozenClock
    writer = sqlite3.connect(module.DB_PATH)
    try:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("PRAGMA synchronous=FULL")
        writer.execute("CREATE TABLE left_half (value INTEGER NOT NULL)")
        writer.execute("CREATE TABLE right_half (value INTEGER NOT NULL)")
        writer.execute("INSERT INTO left_half VALUES (0)")
        writer.execute("INSERT INTO right_half VALUES (0)")
        writer.commit()
        snapshots = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            for phase in range(4):
                writer.execute("BEGIN IMMEDIATE")
                writer.execute("UPDATE left_half SET value = ?", (phase + 1,))
                before_commit = list(pool.map(lambda _: module.create_snapshot(), range(4)))
                writer.execute("UPDATE right_half SET value = ?", (phase + 1,))
                writer.commit()
                after_commit = list(pool.map(lambda _: module.create_snapshot(), range(4)))
                snapshots.extend((path, phase) for path in before_commit)
                snapshots.extend((path, phase + 1) for path in after_commit)
        assert len({path for path, _ in snapshots}) == 32
        for path, expected in snapshots:
            manifest = json.loads(path.read_text())
            db = module.SNAPSHOT_DIR / manifest["snapshot_file"]
            assert module.compute_sha256(db) == manifest["sha256"]
            assert manifest["commit_sha"] == "controlled-fixture-commit"
            with sqlite3.connect(db) as conn:
                assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
                assert conn.execute("SELECT value FROM left_half").fetchone() == (expected,)
                assert conn.execute("SELECT value FROM right_half").fetchone() == (expected,)
    finally:
        writer.close()


@pytest.mark.parametrize("notes", [None, 42])
def test_cleanup_keeps_primary_error_without_callable_exception_notes(monkeypatch, tmp_path, notes):
    module, repo = fixture_module(tmp_path)
    create_source(module)
    primary = OSError("independent primary publication rejection")
    primary.add_note = notes
    original = module._unlink_owned
    cleanup_attempts = []

    def reject_publication(*args, **kwargs):
        raise primary

    def reject_db_cleanup(path, identity):
        cleanup_attempts.append(path)
        if path.suffix == ".db":
            raise OSError("independent secondary cleanup rejection")
        return original(path, identity)

    monkeypatch.setattr(module.os, "link", reject_publication)
    monkeypatch.setattr(module, "_unlink_owned", reject_db_cleanup)
    with pytest.raises(OSError) as observed:
        module.create_snapshot()
    assert observed.value is primary
    assert len(cleanup_attempts) == 2
    assert not list(module.SNAPSHOT_DIR.glob(".tmp_*.json"))
    assert not list(module.SNAPSHOT_DIR.glob("manifest_*.json"))
