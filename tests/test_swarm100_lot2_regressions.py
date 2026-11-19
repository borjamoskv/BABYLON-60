"""Lot2 helpers only: temporary SQLite/files, no global purge or operator data."""

import importlib.util
import os
import py_compile
import shutil
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue
from types import SimpleNamespace

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


@pytest.fixture(params=SKILLS, ids=["primary", "bundled"])
def skill(request, monkeypatch, tmp_path):
    return load_source(request.param, "lot2_skill_fixture", monkeypatch)


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


def bound_find(root):
    """Interpret only the legacy helper's exact commands, restricted to fixture root."""

    def run(cmd, **kwargs):
        assert Path.cwd() == root and cmd[:2] == ["find", "."]
        if cmd[2:4] in [["-name", "*.db-wal"], ["-name", "*.db-shm"]]:
            assert cmd[-1] == "-delete"
            for path in root.rglob(cmd[3]):
                path.unlink()
        else:
            assert cmd == ["find", ".", "-name", "__pycache__", "-type", "d", "-exec", "rm", "-rf", "{}", "+"]
            for path in root.rglob("__pycache__"):
                if path.is_dir() and not path.is_symlink():
                    shutil.rmtree(path)
        return SimpleNamespace(returncode=0)

    return SimpleNamespace(run=run, SubprocessError=subprocess.SubprocessError)


@pytest.mark.parametrize("location", ["data.db", "__pycache__/data.db"])
def test_itera_preserves_live_sqlite_and_cleans_only_bytecode(tmp_path, monkeypatch, wal_factory, location):
    module = load_source("01_KISH_ENGINE/babylon60/commands/itera.py", "lot2_itera", monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "subprocess", bound_find(tmp_path), raising=False)
    path = tmp_path / location
    writer = wal_factory(path)
    pyc = cache_file(tmp_path / "__pycache__" / "fixture.pyc")
    module.run_auto_purge()
    assert_preserved(path, writer)
    assert not pyc.exists()


@pytest.mark.parametrize("location", ["data.db", "__pycache__/data.db", "__pycache__/database.pyc"])
async def test_cohort_one_preserves_live_sqlite(tmp_path, monkeypatch, wal_factory, location):
    module = load_source("scripts/repatriated/c5_sharur_100_anergy_purge.py", "lot2_cohort", monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "WORKSPACE", tmp_path)
    monkeypatch.setattr(module, "CORTEX_DIR", tmp_path / "empty-cortex")
    path = tmp_path / location
    writer = wal_factory(path)
    pyc = cache_file(tmp_path / "__pycache__" / "fixture.pyc")
    report = module.CohortReport(1, "fixture", [0])
    await module.run_cohort_1(report)
    assert_preserved(path, writer)
    assert not pyc.exists()
    assert "eliminados: 0" not in " ".join(report.details)


async def test_cohort_one_does_not_clean_other_projects(tmp_path, monkeypatch):
    module = load_source("scripts/repatriated/c5_sharur_100_anergy_purge.py", "lot2_cohort_scope", monkeypatch)
    selected, other = tmp_path / "selected", tmp_path / "other"
    selected.mkdir()
    other.mkdir()
    own = cache_file(selected / "__pycache__" / "own.pyc")
    foreign = cache_file(other / "__pycache__" / "foreign.pyc")
    monkeypatch.chdir(selected)
    monkeypatch.setattr(module, "WORKSPACE", tmp_path)
    monkeypatch.setattr(module, "CORTEX_DIR", other)
    report = module.CohortReport(1, "fixture", [0])
    await module.run_cohort_1(report)
    assert foreign.exists()
    assert not own.exists()


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


async def test_consolidation_refusal_preserves_exact_journal_rows(tmp_path, monkeypatch):
    module = load_source("scripts/c5_cortex/autoconsolidate.py", "lot2_consolidate", monkeypatch)
    path = tmp_path / "journal.db"
    rows = [("one", 1, '{"payload":"alpha"}'), ("two", 2, '{"payload":"beta"}'), ("three", 3, '{"payload":"gamma"}')]
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE journal(id TEXT PRIMARY KEY,lamport_t INTEGER,payload TEXT)")
        conn.executemany("INSERT INTO journal VALUES(?,?,?)", rows)
    with pytest.raises(RuntimeError, match="CONSOLIDATION_UNSUPPORTED"):
        await module.autoconsolidate(batch_size=2, db_path=str(path))
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT * FROM journal ORDER BY lamport_t").fetchall() == rows
        conn.execute("INSERT INTO journal VALUES('other-writer',4,'unaffected')")
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM journal").fetchone()[0] == 4


async def test_consolidation_rejects_before_open_or_creation(tmp_path, monkeypatch):
    module = load_source("scripts/c5_cortex/autoconsolidate.py", "lot2_consolidate_no_open", monkeypatch)

    async def forbidden(*args, **kwargs):
        pytest.fail("Consolidation must reject before connecting")

    monkeypatch.setattr(module, "connect", forbidden, raising=False)
    path = tmp_path / "absent.db"
    with pytest.raises(RuntimeError, match="CONSOLIDATION_UNSUPPORTED"):
        await module.autoconsolidate(db_path=str(path))
    assert not path.exists()


@pytest.mark.parametrize("size", [0, -1, True, "2"])
async def test_invalid_batch_size_rejects_without_creating_database(tmp_path, monkeypatch, size):
    module = load_source("scripts/c5_cortex/autoconsolidate.py", "lot2_consolidate_args", monkeypatch)
    path = tmp_path / "absent.db"
    with pytest.raises(ValueError):
        await module.autoconsolidate(batch_size=size, db_path=str(path))
    assert not path.exists()


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


@pytest.mark.parametrize("method", ["load", "merge", "save"])
async def test_legacy_journal_helpers_refuse_instead_of_claiming_persistence(tmp_path, monkeypatch, method):
    module = load_source("scripts/c5_cortex/autoconsolidate.py", "lot2_journal_api", monkeypatch)
    entry = module.JournalEntry("one", {"payload": "must survive"})
    with pytest.raises(RuntimeError, match="CONSOLIDATION_UNSUPPORTED"):
        if method == "load":
            await module.JournalEntry.load("one")
        elif method == "merge":
            module.JournalEntry.merge([entry])
        else:
            await entry.save()
    assert entry.payload == {"payload": "must survive"}


def test_consolidation_cli_refuses_without_creating_default_database(tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/c5_cortex/autoconsolidate.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=5,
        env={**os.environ, "BABYLON_HOME": str(tmp_path / "virtual-babylon")},
    )
    assert result.returncode == 2
    assert "CONSOLIDATION_UNSUPPORTED" in result.stderr
    assert not (tmp_path / "journal.db").exists()
    assert not (tmp_path / "virtual-babylon").exists()
