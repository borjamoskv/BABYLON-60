"""Lot2 anergy-purge skill cases split from test_swarm100_lot2_regressions.py.

They load tools/skill_library sources, which the public projection excludes.
"""

import importlib.util
import os
import py_compile
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue

import pytest

ROOT = Path(__file__).absolute().parents[1]
SKILLS = [
    "tools/skill_library/global/anergy-purge-protocol/scripts/anergy_purge.py",
    "tools/skill_library/global/c5-cortex-swarm-orchestrator/references/modules/anergy-purge-protocol/scripts/anergy_purge.py",
]


def load_source(path, name, monkeypatch):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def confined_environment(monkeypatch, tmp_path):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def wal_factory():
    opened = []

    def create(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        opened.append(conn)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("PRAGMA wal_autocheckpoint=0")
        conn.execute("CREATE TABLE records(id INTEGER PRIMARY KEY, payload TEXT)")
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("INSERT INTO records VALUES(1,'committed-in-wal')")
        conn.commit()
        assert Path(str(path) + "-wal").stat().st_size > 0
        return conn

    yield create
    for conn in opened:
        try:
            conn.close()
        except sqlite3.Error:
            pass  # The negative pre-patch reproduction can unlink live WAL files.


def assert_preserved(path, writer):
    assert Path(str(path) + "-wal").is_file(), "Committed WAL was deleted"
    assert Path(str(path) + "-shm").is_file(), "Live shared-memory file was deleted"
    with sqlite3.connect(path) as reader:
        assert reader.execute("SELECT payload FROM records ORDER BY id").fetchall() == [("committed-in-wal",)]
    writer.execute("INSERT INTO records VALUES(2,'writer-still-active')")
    writer.commit()
    with sqlite3.connect(path) as reader:
        assert reader.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 2


def cache_file(path):
    source = path.parent / (path.stem + "_source.py")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("value = 1\n")
    py_compile.compile(str(source), cfile=str(path), doraise=True)
    return path


@pytest.fixture(params=SKILLS, ids=["primary", "bundled"])
def skill(request, monkeypatch, tmp_path):
    return load_source(request.param, "lot2_skill_fixture", monkeypatch)


@pytest.mark.parametrize(
    "location", ["data.db", "scratch_fixture/data.db", "out/data.db", "__pycache__/data.db", "database.tmp"]
)
@pytest.mark.parametrize("dry_run", [False, True])
def test_skill_preserves_sqlite_in_every_cleanup_category(skill, tmp_path, wal_factory, location, dry_run):
    workspace = tmp_path / "workspace"
    path = workspace / location
    writer = wal_factory(path)
    stats = skill.purge_anergy(workspace, dry_run=dry_run)
    assert_preserved(path, writer)
    assert stats["wal_orphans"] == 0
    assert stats["wal_bytes"] == 0


@pytest.mark.parametrize("dry_run", [False, True])
def test_skill_does_not_read_or_reset_global_sessions(skill, tmp_path, monkeypatch, dry_run):
    home = Path.home()
    global_db = home / ".gemini/antigravity/conversation_summaries.db"
    global_db.parent.mkdir(parents=True)
    connect = sqlite3.connect
    with connect(global_db) as conn:
        conn.execute("CREATE TABLE conversation_summaries(workspace TEXT,status TEXT,not_fully_idle INTEGER)")
        conn.executemany(
            "INSERT INTO conversation_summaries VALUES(?,?,1)",
            [("one", "CASCADE_RUN_STATUS_RUNNING"), ("two", "CASCADE_RUN_STATUS_RUNNING")],
        )
    accesses = []

    def observe(database, *args, **kwargs):
        assert Path(database).is_relative_to(tmp_path)
        if Path(database) == global_db:
            accesses.append(str(database))
        return connect(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", observe)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    stats = skill.purge_anergy(workspace, dry_run=dry_run)
    assert not accesses
    assert stats["ghost_listeners_reset"] == 0
    with connect(global_db) as conn:
        assert conn.execute("SELECT status,not_fully_idle FROM conversation_summaries").fetchall() == [
            ("CASCADE_RUN_STATUS_RUNNING", 1),
            ("CASCADE_RUN_STATUS_RUNNING", 1),
        ]


def test_skill_does_not_even_resolve_home(skill, tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: pytest.fail("No implicit global access")))
    skill.purge_anergy(workspace, dry_run=True)


def test_skill_dry_run_reports_zero_recovered_bytes(skill, tmp_path, capsys):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    candidate = workspace / "removable.tmp"
    candidate.write_text("owned temporary artifact")
    stats = skill.purge_anergy(workspace, dry_run=True)
    assert candidate.exists()
    assert stats["total_bytes_recovered"] == 0
    skill.print_brutalist_table(stats, workspace)
    output = capsys.readouterr().out
    assert "**PURGED**" not in output and "IDLE RESET" not in output


def test_skill_cleans_owned_artifacts_and_preserves_protected_content(skill, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    artifact = workspace / "removable.tmp"
    artifact.write_text("owned temporary artifact")
    protected = workspace / "out/artifact_bundle_v3/keep.tmp"
    protected.parent.mkdir(parents=True)
    protected.write_text("canonical evidence")
    cache_file(workspace / "__pycache__/fixture.pyc")
    stats = skill.purge_anergy(workspace)
    assert not artifact.exists()
    assert protected.read_text() == "canonical evidence"
    assert not (workspace / "__pycache__/fixture.pyc").exists()
    assert stats["total_bytes_recovered"] > 0


def test_skill_skips_symlinked_outside_directories(skill, tmp_path):
    workspace, outside = tmp_path / "workspace", tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    victim = outside / "keep.tmp"
    victim.write_text("outside selected workspace")
    (workspace / "out").symlink_to(outside, target_is_directory=True)
    skill.purge_anergy(workspace)
    assert victim.exists()


def test_skill_preserves_candidate_if_inspection_fails(skill, tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    candidate = workspace / "denied.tmp"
    candidate.write_text("must remain")
    original_open = os.open

    def guarded_open(path, *args, **kwargs):
        if Path(path).name == "denied.tmp":
            raise PermissionError("synthetic inspection refusal")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", guarded_open)
    stats = skill.purge_anergy(workspace)
    assert candidate.exists()
    assert stats["total_bytes_recovered"] == 0


@pytest.mark.parametrize(
    "header", [b"SQLite format 3\0", b"\x37\x7f\x06\x82", b"\x37\x7f\x06\x83", b"\xd9\xd5\x05\xf9\x20\xa1\x63\xd7"]
)
@pytest.mark.parametrize(
    "location", ["scratch_fixture/disguised.tmp", "out/disguised.bak", "__pycache__/disguised.pyc"]
)
def test_skill_preserves_sqlite_headers_under_artifact_names(skill, tmp_path, header, location):
    workspace = tmp_path / "workspace"
    candidate = workspace / location
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(header + b"synthetic protected header fixture")
    original = candidate.read_bytes()
    stats = skill.purge_anergy(workspace)
    assert candidate.read_bytes() == original
    assert stats["total_bytes_recovered"] == 0


def test_skill_preserves_sqlite_superjournal_names(skill, tmp_path):
    workspace = tmp_path / "workspace"
    candidate = workspace / "out/database-mj12345678"
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(b"synthetic superjournal filename fixture")
    skill.purge_anergy(workspace)
    assert candidate.exists()


def test_skill_rejects_symlink_workspace_root(skill, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    candidate = outside / "keep.tmp"
    candidate.write_text("outside")
    link = tmp_path / "workspace-link"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(OSError):
        skill.purge_anergy(link)
    assert candidate.exists()


def test_live_writer_interleavings_with_warmup(skill, tmp_path, monkeypatch, wal_factory):
    workspace = tmp_path / "workspace"
    path = workspace / "writer.db"
    wal_factory(path)
    requests: Queue[int | None] = Queue()
    replies: Queue[int] = Queue()

    def writer():
        conn = sqlite3.connect(path)
        try:
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("PRAGMA wal_autocheckpoint=0")
            while True:
                index = requests.get(timeout=3)
                if index is None:
                    return
                conn.execute("INSERT INTO records VALUES(?,?)", (index, f"concurrent-{index}"))
                conn.commit()
                replies.put(index)
        finally:
            conn.close()

    category = skill._category
    writes: list[int] = []

    def schedule_write(parts):
        if parts[-1] == "writer.db":
            index = len(writes) + 2
            requests.put(index)
            assert replies.get(timeout=3) == index
            writes.append(index)
        return category(parts)

    monkeypatch.setattr(skill, "_category", schedule_write)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(writer)
        try:
            for _ in range(3):
                skill.purge_anergy(workspace)
            for _ in range(20):
                skill.purge_anergy(workspace)
        finally:
            requests.put(None)
            future.result(timeout=3)
    assert len(writes) == 23
    assert Path(str(path) + "-wal").exists()
    with sqlite3.connect(path) as reader:
        assert reader.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 24
        assert reader.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
