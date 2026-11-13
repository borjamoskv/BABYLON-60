"""Lot2 helpers only: temporary SQLite/files, no global purge or operator data."""

import importlib.util
import os
import py_compile
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).absolute().parents[1]


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
