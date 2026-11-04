"""C0528/C0529: snapshots created only from a real, temporary SQLite source."""

import concurrent.futures
import importlib.util
import json
import os
import sqlite3
import stat
import threading
import uuid
from datetime import datetime, timezone, tzinfo
from pathlib import Path
from typing import Any

import pytest

SOURCE = Path(__file__).absolute().parents[1] / "scripts/c5_l1_ledger/ledger_snapshot_engine.py"


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz: tzinfo | None = None) -> "FixedDateTime":
        return cls(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)


def load_copy(tmp_path: Path) -> tuple[Any, Path]:
    repo = tmp_path / "fixture-repo"
    path = repo / "scripts/c5_l1_ledger/ledger_snapshot_engine.py"
    path.parent.mkdir(parents=True)
    path.write_bytes(SOURCE.read_bytes())
    spec = importlib.util.spec_from_file_location(f"snapshot_fixture_{uuid.uuid4().hex}", path)
    assert spec is not None and spec.loader is not None
    module: Any = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.get_latest_commit = lambda: "fixture-commit"
    return module, repo


def populate(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE payload (value TEXT NOT NULL)")
        conn.execute("INSERT INTO payload VALUES ('fixture-row')")


def inspect_pair(module: Any, manifest: Path) -> dict[str, Any]:
    data = json.loads(manifest.read_text())
    db = module.SNAPSHOT_DIR / data["snapshot_file"]
    assert db.is_file()
    assert module.compute_sha256(db) == data["sha256"]
    with sqlite3.connect(db) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert conn.execute("SELECT value FROM payload").fetchall() == [("fixture-row",)]
    return data


def test_c0528_default_root_uses_the_repository(tmp_path: Path) -> None:
    module, repo = load_copy(tmp_path)
    assert module.REPO_ROOT == repo
    assert module.DB_PATH == repo / "cortex.db"
    assert module.SNAPSHOT_DIR == repo / "audit/snapshots"


def test_c0528_default_root_preserves_a_logical_symlink(tmp_path: Path) -> None:
    _, repo = load_copy(tmp_path)
    logical = tmp_path / "logical-repo"
    logical.symlink_to(repo, target_is_directory=True)
    path = logical / "scripts/c5_l1_ledger/ledger_snapshot_engine.py"
    spec = importlib.util.spec_from_file_location(f"logical_snapshot_{uuid.uuid4().hex}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.REPO_ROOT == logical


def test_c0528_default_source_is_real_without_replacing_globals(tmp_path: Path) -> None:
    module, repo = load_copy(tmp_path)
    populate(repo / "cortex.db")
    manifest = module.create_snapshot()
    assert manifest.is_relative_to(repo)
    inspect_pair(module, manifest)
    assert not (repo.parent / "audit").exists()


def test_c0528_missing_source_preserves_absence_and_no_outputs(tmp_path: Path) -> None:
    module, _ = load_copy(tmp_path)
    with pytest.raises((FileNotFoundError, sqlite3.OperationalError)):
        module.create_snapshot()
    assert not module.DB_PATH.exists()
    assert not module.SNAPSHOT_DIR.exists()


def test_c0528_main_does_not_start_actor_after_missing_source(tmp_path: Path) -> None:
    module, _ = load_copy(tmp_path)
    actors = []

    def forbidden_actor(*args: Any, **kwargs: Any) -> None:
        actors.append(args)
        raise AssertionError("a missing source must never construct a ledger actor")

    module.BFTLedgerActor = forbidden_actor
    with pytest.raises((FileNotFoundError, sqlite3.OperationalError)):
        module.main()
    assert actors == []
    assert not module.SNAPSHOT_DIR.exists()


def test_c0529_fixed_clock_allocates_distinct_coherent_pairs(tmp_path: Path) -> None:
    module, repo = load_copy(tmp_path)
    source = repo / "cortex.db"
    populate(source)
    # This test isolates filename collisions independently of C0528's bad root.
    module.DB_PATH = source
    module.SNAPSHOT_DIR = repo / "audit/snapshots"
    module.datetime = FixedDateTime
    first = module.create_snapshot()
    first_bytes = first.read_bytes()
    second = module.create_snapshot()
    assert first != second
    assert first.read_bytes() == first_bytes
    assert inspect_pair(module, first)["snapshot_file"] != inspect_pair(module, second)["snapshot_file"]


def test_c0529_concurrent_fixed_clock_pairs_survive_warmup(tmp_path: Path) -> None:
    module, repo = load_copy(tmp_path)
    populate(repo / "cortex.db")
    module.DB_PATH = repo / "cortex.db"
    module.SNAPSHOT_DIR = repo / "audit/snapshots"
    module.datetime = FixedDateTime
    outputs: list[Path] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for _ in range(3 + 10):
            outputs.extend(pool.map(lambda _: module.create_snapshot(), range(4)))
    assert len(set(outputs)) == 52
    databases = {inspect_pair(module, p)["snapshot_file"] for p in outputs}
    assert len(databases) == 52


def test_snapshot_copies_committed_wal_and_ignores_open_transaction(tmp_path: Path) -> None:
    module, repo = load_copy(tmp_path)
    source = repo / "cortex.db"
    writer = sqlite3.connect(source)
    try:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("PRAGMA synchronous=FULL")
        writer.execute("CREATE TABLE payload (value TEXT NOT NULL)")
        writer.execute("INSERT INTO payload VALUES ('fixture-row')")
        writer.commit()
        writer.execute("INSERT INTO payload VALUES ('uncommitted-row')")
        assert source.with_name("cortex.db-wal").exists()
        inspect_pair(module, module.create_snapshot())
        assert writer.execute("SELECT count(*) FROM payload").fetchone() == (2,)
    finally:
        writer.rollback()
        writer.close()


def test_corrupt_source_produces_no_snapshot(tmp_path: Path) -> None:
    module, repo = load_copy(tmp_path)
    source = repo / "cortex.db"
    source.write_bytes(b"not a sqlite database")
    with pytest.raises(sqlite3.DatabaseError):
        module.create_snapshot()
    assert source.read_bytes() == b"not a sqlite database"
    assert not module.SNAPSHOT_DIR.exists()


def test_sqlite_uri_encodes_filename_without_creating_another_source(tmp_path: Path) -> None:
    module, repo = load_copy(tmp_path)
    source = repo / "fixture #with?query.db"
    populate(source)
    module.DB_PATH = source
    inspect_pair(module, module.create_snapshot())
    assert sorted(p.name for p in repo.glob("*.db")) == [source.name]


def test_c0529_preexisting_manifest_is_never_truncated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module, repo = load_copy(tmp_path)
    populate(repo / "cortex.db")
    module.datetime = FixedDateTime
    fixed_uuid = uuid.UUID(int=1)
    monkeypatch.setattr(module.uuid, "uuid4", lambda: fixed_uuid)
    module.SNAPSHOT_DIR.mkdir(parents=True)
    foreign = module.SNAPSHOT_DIR / f"manifest_20261030_120000_{fixed_uuid.hex}.json"
    foreign.write_bytes(b"preexisting-fixture-manifest")
    try:
        manifest = module.create_snapshot()
    except FileExistsError:
        pass
    else:
        assert manifest != foreign
        inspect_pair(module, manifest)
    assert foreign.read_bytes() == b"preexisting-fixture-manifest"


def test_snapshot_requires_durable_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module, repo = load_copy(tmp_path)
    populate(repo / "cortex.db")

    def fail_sync(fd: int) -> None:
        raise OSError("synthetic fsync failure")

    monkeypatch.setattr(os, "fsync", fail_sync)
    with pytest.raises(OSError, match="synthetic fsync failure"):
        module.create_snapshot()
    assert not list(module.SNAPSHOT_DIR.glob("manifest_*.json"))


def test_c0528_source_removed_before_connect_is_not_recreated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module, repo = load_copy(tmp_path)
    source = repo / "cortex.db"
    populate(source)
    original = sqlite3.connect
    removed = False

    def remove_before_open(database: Any, *args: Any, **kwargs: Any):
        nonlocal removed
        if not removed:
            removed = True
            source.unlink()
        return original(database, *args, **kwargs)

    monkeypatch.setattr(module.sqlite3, "connect", remove_before_open)
    with pytest.raises((FileNotFoundError, sqlite3.OperationalError)):
        module.create_snapshot()
    assert removed
    assert not source.exists()
    assert not module.SNAPSHOT_DIR.exists()


def test_c0529_published_manifest_is_complete_when_first_visible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module, repo = load_copy(tmp_path)
    populate(repo / "cortex.db")
    opened = threading.Event()
    release = threading.Event()
    original_sync = os.fsync

    def pause_write(fd: int) -> None:
        identity = os.fstat(fd)
        for path in module.SNAPSHOT_DIR.rglob("*.json"):
            if os.path.samestat(path.stat(), identity):
                opened.set()
                assert release.wait(5), "fixture timed out before releasing manifest writer"
                break
        original_sync(fd)

    monkeypatch.setattr(os, "fsync", pause_write)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(module.create_snapshot)
        try:
            assert opened.wait(5), "fixture timed out before opening manifest"
            assert list(module.SNAPSHOT_DIR.glob("manifest_*.json")) == []
        finally:
            release.set()
        inspect_pair(module, future.result(timeout=5))


def test_c0529_manifest_created_during_publication_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module, repo = load_copy(tmp_path)
    populate(repo / "cortex.db")
    module.datetime = FixedDateTime
    fixed_uuid = uuid.UUID(int=1)
    monkeypatch.setattr(module.uuid, "uuid4", lambda: fixed_uuid)
    foreign = module.SNAPSHOT_DIR / f"manifest_20261030_120000_{fixed_uuid.hex}.json"
    original_sync = os.fsync
    injected = False

    def inject_manifest(fd: int) -> None:
        nonlocal injected
        identity = os.fstat(fd)
        for path in module.SNAPSHOT_DIR.rglob("*.json"):
            if not injected and os.path.samestat(path.stat(), identity):
                foreign.write_bytes(b"concurrent-fixture-manifest")
                injected = True
                break
        original_sync(fd)

    monkeypatch.setattr(os, "fsync", inject_manifest)
    try:
        manifest = module.create_snapshot()
    except FileExistsError:
        pass
    else:
        assert manifest != foreign
    assert injected
    assert foreign.read_bytes() == b"concurrent-fixture-manifest"


def test_c0529_existing_zero_byte_database_is_not_reused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module, repo = load_copy(tmp_path)
    populate(repo / "cortex.db")
    module.datetime = FixedDateTime
    fixed_uuid = uuid.UUID(int=1)
    monkeypatch.setattr(module.uuid, "uuid4", lambda: fixed_uuid)
    module.SNAPSHOT_DIR.mkdir(parents=True)
    foreign = module.SNAPSHOT_DIR / f"cortex_snapshot_20261030_120000_{fixed_uuid.hex}.db"
    foreign.touch()
    identity = foreign.stat()
    with pytest.raises(FileExistsError):
        module.create_snapshot()
    assert foreign.read_bytes() == b""
    assert os.path.samestat(identity, foreign.stat())
    assert not list(module.SNAPSHOT_DIR.glob("manifest_*.json"))


def test_c0529_existing_staging_file_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module, repo = load_copy(tmp_path)
    populate(repo / "cortex.db")
    module.datetime = FixedDateTime
    fixed_uuid = uuid.UUID(int=1)
    monkeypatch.setattr(module.uuid, "uuid4", lambda: fixed_uuid)
    module.SNAPSHOT_DIR.mkdir(parents=True)
    foreign = module.SNAPSHOT_DIR / f".tmp_20261030_120000_{fixed_uuid.hex}.json"
    foreign.write_bytes(b"preexisting-staging-fixture")
    with pytest.raises(FileExistsError):
        module.create_snapshot()
    assert foreign.read_bytes() == b"preexisting-staging-fixture"
    assert sorted(module.SNAPSHOT_DIR.iterdir()) == [foreign]


def test_manifest_short_writes_are_completed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module, repo = load_copy(tmp_path)
    populate(repo / "cortex.db")
    original_write = os.write
    writes = 0

    def short_write(fd: int, data: bytes) -> int:
        nonlocal writes
        writes += 1
        return original_write(fd, data[:3])

    monkeypatch.setattr(os, "write", short_write)
    inspect_pair(module, module.create_snapshot())
    assert writes > 1


def test_manifest_zero_write_fails_and_cleans_owned_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module, repo = load_copy(tmp_path)
    populate(repo / "cortex.db")
    monkeypatch.setattr(os, "write", lambda *args: 0)
    with pytest.raises(OSError, match="made no progress"):
        module.create_snapshot()
    assert list(module.SNAPSHOT_DIR.iterdir()) == []


def test_directory_sync_failure_does_not_return_a_published_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module, repo = load_copy(tmp_path)
    populate(repo / "cortex.db")
    original_sync = os.fsync

    def fail_directory_sync(fd: int) -> None:
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("synthetic directory sync failure")
        original_sync(fd)

    monkeypatch.setattr(os, "fsync", fail_directory_sync)
    with pytest.raises(OSError, match="synthetic directory sync failure"):
        module.create_snapshot()
    assert list(module.SNAPSHOT_DIR.iterdir()) == []
    with sqlite3.connect(repo / "cortex.db") as conn:
        assert conn.execute("SELECT value FROM payload").fetchall() == [("fixture-row",)]


def test_cleanup_without_exception_notes_preserves_primary_error_and_continues(tmp_path, monkeypatch) -> None:
    module, repo = load_copy(tmp_path)
    populate(repo / "cortex.db")
    module.DB_PATH = repo / "cortex.db"
    module.SNAPSHOT_DIR = repo / "audit/snapshots"
    error = OSError("primary publication failure")
    monkeypatch.setattr(error, "add_note", None, raising=False)  # Python 3.10 has no exception notes.
    original_unlink = module._unlink_owned
    cleaned: list[Path] = []

    def fail_publication(*_args, **_kwargs):
        raise error

    def fail_database_cleanup(path, identity):
        cleaned.append(path)
        if path.suffix == ".db":
            raise OSError("secondary cleanup failure")
        original_unlink(path, identity)

    monkeypatch.setattr(module.os, "link", fail_publication)
    monkeypatch.setattr(module, "_unlink_owned", fail_database_cleanup)
    with pytest.raises(OSError) as caught:
        module.create_snapshot()
    assert caught.value is error
    assert len(cleaned) == 2
    assert not list(module.SNAPSHOT_DIR.glob(".tmp_*.json"))
    assert not list(module.SNAPSHOT_DIR.glob("manifest_*.json"))
