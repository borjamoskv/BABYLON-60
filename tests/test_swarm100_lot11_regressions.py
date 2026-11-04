"""JSON persistence tests confined to an owned synthetic HOME."""

import builtins
from datetime import datetime, timezone
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import sys
import threading
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).absolute().parents[1]
SOURCE = ROOT / "01_KISH_ENGINE/babylon60/core/cortex_persist.py"


@pytest.fixture
def memory(tmp_path, monkeypatch):
    home = tmp_path / "home"
    base = home / ".agent/memory"
    projects = base / "projects"
    projects.mkdir(parents=True)
    (base / "snapshots").mkdir()
    for project in ["alpha", "beta"]:
        (projects / (project + ".json")).write_text(json.dumps({"meta": {}, "recent_changes": [], "decisions": []}))
    (base / "ghosts.json").write_text("{}")
    (base / "system.json").write_text(json.dumps({"meta": {}, "sessions_log": []}))
    monkeypatch.setenv("HOME", str(home))

    def forbidden(*args, **kwargs):
        raise AssertionError("network forbidden in memory fixture")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    kills = []
    real_kill = os.kill
    monkeypatch.setattr(os, "kill", lambda *args: kills.append(args))  # Original fail-fast made inert before imports.
    copied = tmp_path / "fixture_cortex_persist.py"
    shutil.copyfile(SOURCE, copied)
    spec = importlib.util.spec_from_file_location("lot11_memory_fixture", copied)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    ledger = module.CortexOntologyLedger("alpha")

    def delta(label):
        return module.SessionDelta(
            task_desc="fixture " + label,
            last_file="fixture.py",
            conversation_id=label,
            changes=["change " + label],
            decisions=["decision " + label],
            duration="fixture",
        )

    def read(relative):
        return json.loads((base / relative).read_text())

    return SimpleNamespace(
        module=module,
        ledger=ledger,
        base=base,
        home=home,
        tmp=tmp_path,
        kills=kills,
        real_kill=real_kill,
        delta=delta,
        read=read,
    )


def test_c0167_failed_partial_write_keeps_previous_bytes_and_inode(memory, monkeypatch):
    target = memory.base / "projects/alpha.json"
    before = (target.stat().st_ino, target.read_bytes())
    real_open = builtins.open
    real_write = os.write

    class BrokenWriter:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.stream.close()

        def write(self, value):
            self.stream.write(value[:5])
            self.stream.flush()
            raise OSError("fixture partial write")

    def opening(file, mode="r", *args, **kwargs):
        stream = real_open(file, mode, *args, **kwargs)
        return BrokenWriter(stream) if os.fspath(file) == str(target) and "w" in mode else stream

    def writing(descriptor, data):
        real_write(descriptor, data[:5])
        raise OSError("fixture partial write")

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "open", opening)
        patch.setattr(os, "write", writing)
        with pytest.raises((RuntimeError, OSError)):
            memory.ledger._write_json(str(target), {"fixture": "new content"})
    assert (target.stat().st_ino, target.read_bytes()) == before


def test_c0167_file_and_parent_sync_precede_success(memory, monkeypatch):
    target = memory.base / "projects/alpha.json"
    real_sync = os.fsync
    calls = []

    def syncing(descriptor):
        calls.append("directory" if stat.S_ISDIR(os.fstat(descriptor).st_mode) else "file")
        return real_sync(descriptor)

    monkeypatch.setattr(os, "fsync", syncing)
    memory.ledger._write_json(str(target), {"fixture": "new content"})
    assert calls == ["file", "directory"]
    assert memory.read("projects/alpha.json") == {"fixture": "new content"}


@pytest.mark.parametrize("scope", ["project", "ghosts", "system"])
def test_c0168_cooperating_threads_do_not_lose_updates(memory, monkeypatch, scope):
    cls = memory.module.CortexOntologyLedger
    a = memory.ledger
    b = cls("alpha" if scope == "project" else "beta")
    pause_path = str(memory.base / ("projects/alpha.json" if scope == "project" else scope + ".json"))
    original_read = cls._read_json
    real_flock = fcntl.flock
    a_read = threading.Event()
    release = threading.Event()
    b_attempt = threading.Event()
    b_read = threading.Event()
    b_done = threading.Event()
    errors = []

    def read(self, path):
        value = original_read(self, path)
        if threading.current_thread().name == "lot11-A" and path == pause_path:
            a_read.set()
            assert release.wait(10), "fixture release timeout"
        elif threading.current_thread().name == "lot11-B":
            b_read.set()
            b_attempt.set()
        return value

    def flock(descriptor, operation):
        if threading.current_thread().name == "lot11-B" and operation & fcntl.LOCK_EX:
            b_attempt.set()
        return real_flock(descriptor, operation)

    def worker(ledger, label):
        try:
            ledger.crystallize_session(memory.delta(label))
        except BaseException as error:
            errors.append(error)
        finally:
            if label == "B":
                b_done.set()

    monkeypatch.setattr(cls, "_read_json", read)
    monkeypatch.setattr(fcntl, "flock", flock)
    first = threading.Thread(target=worker, args=(a, "A"), name="lot11-A")
    second = threading.Thread(target=worker, args=(b, "B"), name="lot11-B")
    first.start()
    try:
        assert a_read.wait(10)
        second.start()
        assert b_attempt.wait(10)
        if b_read.is_set():
            assert b_done.wait(10)  # Original: force B commit before A overwrites its snapshot.
    finally:
        release.set()
        first.join(10)
        if second.ident is not None:
            second.join(10)
    assert not first.is_alive() and not second.is_alive() and not errors, errors
    if scope == "project":
        assert {row["desc"] for row in memory.read("projects/alpha.json")["recent_changes"]} == {"change A", "change B"}
    elif scope == "ghosts":
        assert set(memory.read("ghosts.json")) == {"alpha", "beta"}
    else:
        assert {row["conversation_id"] for row in memory.read("system.json")["sessions_log"]} == {"A", "B"}


@pytest.mark.parametrize(
    "instant",
    [datetime(2026, 1, 15, 12, 34, 56, tzinfo=timezone.utc), datetime(2026, 7, 15, 12, 34, 56, tzinfo=timezone.utc)],
)
def test_c0169_timestamp_preserves_utc_instant(memory, monkeypatch, instant):
    class Frozen(datetime):
        @classmethod
        def now(cls, tz=None):
            assert tz is timezone.utc
            return instant

    monkeypatch.setattr(memory.module, "datetime", Frozen)
    actual = datetime.fromisoformat(memory.ledger._get_iso_now())
    assert actual == instant


def test_c0167_nonfinite_json_is_rejected_before_destination_write(memory):
    target = memory.base / "projects/alpha.json"
    before = target.read_bytes()
    with pytest.raises((RuntimeError, ValueError)):
        memory.ledger._write_json(str(target), {"number": float("nan")})
    assert target.read_bytes() == before


def test_successful_session_preserves_schema_and_historical_timestamps(memory, monkeypatch):
    historical = "2020-01-01T10:00:00+02:00"
    project = memory.read("projects/alpha.json")
    project["meta"]["historical"] = historical
    project["recent_changes"] = [{"ts": historical, "desc": "historical"}]
    (memory.base / "projects/alpha.json").write_text(json.dumps(project))
    monkeypatch.setattr(memory.ledger, "_get_iso_now", lambda: "2026-10-29T12:00:00+00:00")
    memory.ledger.crystallize_session(memory.delta("A"))
    stored = memory.read("projects/alpha.json")
    assert stored["meta"]["historical"] == historical
    assert stored["recent_changes"][1] == {"ts": historical, "desc": "historical"}
    assert stored["ghost"]["timestamp"] == "2026-10-29T12:00:00+00:00"
    assert memory.read("ghosts.json")["alpha"]["last_conversation"] == "A"
    assert memory.read("system.json")["sessions_log"][0]["conversation_id"] == "A"
    assert memory.kills == []


def test_atomic_success_changes_inode_preserves_mode_and_utf8(memory):
    path = memory.base / "projects/alpha.json"
    path.chmod(0o640)
    inode = path.stat().st_ino
    value = {"message": "Información Ω", "values": [True, None, 42]}
    memory.ledger._write_json(str(path), value)
    assert path.stat().st_ino != inode and stat.S_IMODE(path.stat().st_mode) == 0o640
    assert memory.read("projects/alpha.json") == value
    assert list(path.parent.glob(".cortex-persist-*.tmp")) == []


def test_short_writes_are_completed(memory, monkeypatch):
    path = memory.base / "projects/alpha.json"
    real = os.write
    calls = []

    def short(descriptor, value):
        calls.append(len(value))
        return real(descriptor, value[:7])

    monkeypatch.setattr(os, "write", short)
    value = {"message": "x" * 200}
    memory.ledger._write_json(str(path), value)
    assert len(calls) > 1 and memory.read("projects/alpha.json") == value


def test_zero_write_is_failure_without_truncation(memory, monkeypatch):
    path = memory.base / "projects/alpha.json"
    before = (path.stat().st_ino, path.read_bytes())
    monkeypatch.setattr(os, "write", lambda *args: 0)
    with pytest.raises(memory.module.PersistenceWriteError) as caught:
        memory.ledger._write_json(str(path), {"new": True})
    assert caught.value.replacement_state == "NOT_ATTEMPTED"
    assert (path.stat().st_ino, path.read_bytes()) == before
    assert not list(path.parent.glob(".cortex-persist-*.tmp"))


@pytest.mark.parametrize("stage", ["file-sync", "replace-before", "replace-after", "directory-sync", "replace-foreign"])
def test_write_error_reports_commit_boundary(memory, monkeypatch, stage):
    path = memory.base / "projects/alpha.json"
    before = (path.stat().st_ino, path.read_bytes())
    real_sync = os.fsync
    real_replace = os.replace
    value = {"new": "fixture payload"}

    def sync(descriptor):
        directory = stat.S_ISDIR(os.fstat(descriptor).st_mode)
        if stage == ("directory-sync" if directory else "file-sync"):
            raise OSError("fixture sync failure")
        return real_sync(descriptor)

    def replace(src, dst, **kwargs):
        if stage == "replace-before":
            raise OSError("fixture before replace")
        if stage == "replace-foreign":
            (path.parent / "actor.json").write_text('{"actor":true}')
            real_replace("actor.json", dst, src_dir_fd=kwargs["dst_dir_fd"], dst_dir_fd=kwargs["dst_dir_fd"])
            raise OSError("fixture foreign replacement")
        result = real_replace(src, dst, **kwargs)
        if stage == "replace-after":
            raise OSError("fixture after replace")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(os, "fsync", sync)
        patch.setattr(os, "replace", replace)
        with pytest.raises(memory.module.PersistenceWriteError) as caught:
            memory.ledger._write_json(str(path), value)
    expected = {
        "file-sync": "NOT_ATTEMPTED",
        "replace-before": "NOT_REPLACED",
        "replace-after": "REPLACED",
        "directory-sync": "REPLACED",
        "replace-foreign": "UNKNOWN",
    }[stage]
    assert caught.value.replacement_state == expected and caught.value.durability_confirmed is False
    if stage in ("file-sync", "replace-before"):
        assert (path.stat().st_ino, path.read_bytes()) == before
    elif stage == "replace-foreign":
        assert memory.read("projects/alpha.json") == {"actor": True}
    else:
        assert memory.read("projects/alpha.json") == value
    assert not list(path.parent.glob(".cortex-persist-*.tmp"))


@pytest.mark.parametrize("failed_index", [0, 1, 2])
def test_consolidation_failure_exposes_partial_files(memory, monkeypatch, capsys, failed_index):
    paths = [
        str(memory.base / "projects/alpha.json"),
        str(memory.base / "ghosts.json"),
        str(memory.base / "system.json"),
    ]
    before = {path: Path(path).read_bytes() for path in paths}
    original = memory.ledger._write_json

    def write(path, data):
        if path == paths[failed_index]:
            raise memory.module.PersistenceWriteError(path, "NOT_ATTEMPTED")
        return original(path, data)

    monkeypatch.setattr(memory.ledger, "_write_json", write)
    with pytest.raises(memory.module.ConsolidationError) as caught:
        memory.ledger.crystallize_session(memory.delta("A"))
    assert caught.value.completed_files == tuple(paths[:failed_index])
    assert caught.value.current_file == paths[failed_index] and caught.value.replacement_state == "NOT_ATTEMPTED"
    for index, path in enumerate(paths):
        assert isinstance(json.loads(Path(path).read_text()), dict)
        assert (Path(path).read_bytes() == before[path]) == (index >= failed_index)
    assert "success" not in capsys.readouterr().out
    assert memory.kills == []


def test_directory_sync_failure_during_ghosts_keeps_new_visible_data(memory, monkeypatch, capsys):
    real = os.fsync
    directories = []

    def sync(descriptor):
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            directories.append(descriptor)
            if len(directories) == 2:
                raise OSError("fixture ghosts directory sync")
        return real(descriptor)

    monkeypatch.setattr(os, "fsync", sync)
    with pytest.raises(memory.module.ConsolidationError) as caught:
        memory.ledger.crystallize_session(memory.delta("A"))
    assert caught.value.completed_files == (str(memory.base / "projects/alpha.json"),)
    assert (
        caught.value.current_file == str(memory.base / "ghosts.json") and caught.value.replacement_state == "REPLACED"
    )
    assert memory.read("projects/alpha.json")["ghost"]["last_conversation"] == "A"
    assert memory.read("ghosts.json")["alpha"]["last_conversation"] == "A"
    assert memory.read("system.json")["sessions_log"] == []
    assert "success" not in capsys.readouterr().out


def test_temporary_collision_does_not_remove_foreign_file(memory, monkeypatch):
    target = memory.base / "projects/alpha.json"
    collision = target.parent / ".cortex-persist-collision.tmp"
    collision.write_bytes(b"foreign fixture content")
    monkeypatch.setattr(memory.module.secrets, "token_hex", lambda n: "collision")
    before = target.read_bytes()
    with pytest.raises(memory.module.PersistenceWriteError):
        memory.ledger._write_json(str(target), {"new": True})
    assert target.read_bytes() == before and collision.read_bytes() == b"foreign fixture content"


def test_cleanup_failure_preserves_original_error_and_destination(memory, monkeypatch):
    target = memory.base / "projects/alpha.json"
    before = target.read_bytes()

    def write(*args):
        raise OSError("original fixture failure")

    def unlink(*args, **kwargs):
        raise PermissionError("fixture cleanup failure")

    with monkeypatch.context() as patch:
        patch.setattr(os, "write", write)
        patch.setattr(os, "unlink", unlink)
        with pytest.raises(memory.module.PersistenceWriteError) as caught:
            memory.ledger._write_json(str(target), {"new": True})
    assert target.read_bytes() == before
    assert str(caught.value.__cause__) == "original fixture failure"
    assert any("Temporary cleanup error" in note for note in caught.value.__cause__.__notes__)


@pytest.mark.parametrize(
    "project_id", ["", "..", ".", "../outside", "/absolute", "a/b", "a\\b", "a:b", "bad\x00id", "x" * 129]
)
def test_project_ids_cannot_escape_memory(memory, project_id):
    with pytest.raises(ValueError):
        memory.module.CortexOntologyLedger(project_id)
    assert memory.kills == []


@pytest.mark.parametrize("kind", ["outside", "other-project", "mutated-layout"])
def test_private_destination_allowlist_rejects_other_files(memory, monkeypatch, kind):
    outside = memory.tmp / "outside.json"
    outside.write_text('{"untouched":true}')
    path = str(outside if kind == "outside" else memory.base / "projects/beta.json")
    if kind == "mutated-layout":
        monkeypatch.setattr(memory.ledger, "base_dir", str(memory.tmp))
    with pytest.raises((ValueError, RuntimeError)):
        memory.ledger._write_json(path, {"changed": True})
    assert outside.read_text() == '{"untouched":true}' and memory.read("projects/beta.json")["recent_changes"] == []


@pytest.mark.parametrize(
    "kind", ["file-symlink", "project-directory-symlink", "memory-directory-symlink", "hardlink", "fifo", "read-only"]
)
def test_writer_rejects_unsafe_destination_types(memory, monkeypatch, kind):
    target = memory.base / "projects/alpha.json"
    outside = memory.tmp / "outside.json"
    outside.write_text('{"untouched":true}')
    if kind == "file-symlink":
        target.unlink()
        target.symlink_to(outside)
    elif kind == "project-directory-symlink":
        projects = memory.base / "projects"
        moved = memory.tmp / "owned-moved-projects"
        projects.rename(moved)
        projects.symlink_to(moved, target_is_directory=True)
    elif kind == "memory-directory-symlink":
        moved = memory.tmp / "owned-moved-memory"
        memory.base.rename(moved)
        memory.base.symlink_to(moved, target_is_directory=True)
    elif kind == "hardlink":
        os.link(target, memory.tmp / "alias.json")
    elif kind == "fifo":
        target.unlink()
        os.mkfifo(target)
    else:
        target.chmod(0o400)
    with pytest.raises((RuntimeError, OSError, ValueError)):
        memory.ledger._write_json(str(target), {"new": True})
    assert outside.read_text() == '{"untouched":true}' and memory.kills == []


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "directory"])
def test_invalid_operation_lock_is_rejected_without_writes(memory, kind, capsys):
    lock = memory.base / ".cortex-persist.lock"
    target = memory.tmp / "outside-lock"
    target.write_bytes(b"owned fixture")
    if kind == "symlink":
        lock.symlink_to(target)
    elif kind == "hardlink":
        os.link(target, lock)
    else:
        lock.mkdir()
    before = (memory.base / "projects/alpha.json").read_bytes()
    with pytest.raises(memory.module.ConsolidationError):
        memory.ledger.crystallize_session(memory.delta("A"))
    assert (memory.base / "projects/alpha.json").read_bytes() == before and target.read_bytes() == b"owned fixture"
    assert "success" not in capsys.readouterr().out


def test_persistent_lock_is_not_deleted_or_truncated(memory):
    lock = memory.base / ".cortex-persist.lock"
    lock.write_bytes(b"old fixture metadata")
    os.utime(lock, (42, 42))
    inode = lock.stat().st_ino
    memory.ledger.crystallize_session(memory.delta("A"))
    memory.module.CortexOntologyLedger("beta").crystallize_session(memory.delta("B"))
    assert lock.stat().st_ino == inode and lock.read_bytes() == b"old fixture metadata"


def test_memory_directory_replacement_cannot_use_previous_lock(memory, monkeypatch, capsys):
    cls = memory.module.CortexOntologyLedger
    original = cls._read_json
    seen = []
    old = memory.home / ".agent/previous-memory"

    def read(self, path):
        value = original(self, path)
        if path == str(memory.base / "projects/alpha.json") and not seen:
            memory.base.rename(old)
            shutil.copytree(old, memory.base, ignore=shutil.ignore_patterns(".cortex-persist.lock"))
            seen.append(True)
        return value

    monkeypatch.setattr(cls, "_read_json", read)
    with pytest.raises(memory.module.ConsolidationError) as caught:
        memory.ledger.crystallize_session(memory.delta("A"))
    assert seen and caught.value.completed_files == ()
    assert memory.read("projects/alpha.json")["recent_changes"] == []
    assert json.loads((old / "projects/alpha.json").read_text())["recent_changes"] == []
    assert "success" not in capsys.readouterr().out
    cls("beta").crystallize_session(memory.delta("B"))
    assert memory.read("system.json")["sessions_log"][0]["conversation_id"] == "B"


def test_wrong_json_root_and_nonfinite_read_fail_without_process_kill(memory):
    path = memory.base / "projects/alpha.json"
    for value in ["[]", '{"value":NaN}', "not json"]:
        path.write_text(value)
        with pytest.raises(RuntimeError):
            memory.ledger._read_json(str(path))
    assert memory.kills == []


def test_retention_rules_are_preserved(memory):
    for index in range(32):
        memory.ledger.crystallize_session(memory.delta(str(index)))
    project = memory.read("projects/alpha.json")
    assert len(project["recent_changes"]) == 10 and project["recent_changes"][0]["desc"] == "change 31"
    assert len(project["decisions"]) == 32
    sessions = memory.read("system.json")["sessions_log"]
    assert len(sessions) == 30 and sessions[0]["conversation_id"] == "31"


def test_noncooperating_readers_observe_valid_old_or_new_file(memory):
    path = memory.base / "projects/alpha.json"
    memory.ledger._write_json(str(path), {"generation": 0})
    ready = threading.Event()
    stop = threading.Event()
    observations = []
    errors = []

    def reader():
        while not stop.is_set():
            try:
                observations.append(json.loads(path.read_text())["generation"])
            except BaseException as error:
                errors.append(error)
            ready.set()

    thread = threading.Thread(target=reader)
    thread.start()
    try:
        assert ready.wait(10)
        for index in range(1, 9):
            memory.ledger._write_json(str(path), {"generation": index})
    finally:
        stop.set()
        thread.join(10)
    assert not thread.is_alive() and not errors and observations
    assert set(observations) <= set(range(9))


CHILD_BOOTSTRAP = r"""
import importlib.util,os,socket,sys
from pathlib import Path

def forbidden(*args,**kwargs):raise AssertionError('network/kill forbidden in fixture child')
os.kill=forbidden
socket.socket.connect=forbidden
socket.socket.connect_ex=forbidden
socket.getaddrinfo=forbidden
spec=importlib.util.spec_from_file_location('child_memory_fixture',sys.argv[1])
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)
a=m.CortexOntologyLedger(sys.argv[2])
"""


def test_process_writer_waits_on_common_lock_and_preserves_shared_updates(memory):
    import select
    import subprocess

    script = (
        CHILD_BOOTSTRAP
        + r"""
import fcntl
real=fcntl.flock
reported=False
def flock(fd,operation):
    global reported
    if operation & fcntl.LOCK_EX and not reported:
        reported=True
        try:real(fd,operation|fcntl.LOCK_NB)
        except BlockingIOError:
            print('BLOCKED',flush=True)
        else:
            print('ACQUIRED_EARLY',flush=True)
    return real(fd,operation)
fcntl.flock=flock
a.crystallize_session(m.SessionDelta('fixture B','fixture.py','B',['change B'],['decision B']))
"""
    )
    child = None
    try:
        with memory.ledger._exclusive_session():
            child = subprocess.Popen(
                [sys.executable, "-c", script, memory.module.__file__, "beta"],
                env={"HOME": str(memory.home), "PATH": "/usr/bin:/bin"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert select.select([child.stdout], [], [], 10)[0]
            assert child.stdout.readline() == b"BLOCKED\n"
            memory.ledger._crystallize_locked(memory.delta("A"), [])
        stdout, stderr = child.communicate(timeout=15)
        assert child.returncode == 0, (stdout, stderr)
    finally:
        if child is not None and child.poll() is None:
            import signal

            memory.real_kill(child.pid, signal.SIGTERM)  # Only our Popen fixture child, on failed assertions.
            child.communicate(timeout=10)
    assert {row["conversation_id"] for row in memory.read("system.json")["sessions_log"]} == {"A", "B"}
    assert set(memory.read("ghosts.json")) == {"alpha", "beta"}


def test_abrupt_fixture_child_exit_releases_lock_without_unlink(memory):
    import subprocess

    script = (
        CHILD_BOOTSTRAP
        + r"""
with a._exclusive_session():
    print('HELD',flush=True)
    os._exit(23)
"""
    )
    child = subprocess.run(
        [sys.executable, "-c", script, memory.module.__file__, "alpha"],
        env={"HOME": str(memory.home), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        timeout=15,
    )
    assert child.returncode == 23 and child.stdout == b"HELD\n", child.stderr
    lock = memory.base / ".cortex-persist.lock"
    inode = lock.stat().st_ino
    memory.ledger.crystallize_session(memory.delta("after-exit"))
    assert lock.stat().st_ino == inode


def test_abrupt_fixture_child_partial_write_leaves_old_valid_json(memory):
    import subprocess

    path = memory.base / "projects/alpha.json"
    before = (path.stat().st_ino, path.read_bytes())
    script = (
        CHILD_BOOTSTRAP
        + r"""
real=os.write
def write(fd,value):
    real(fd,value[:7])
    os._exit(24)
os.write=write
a._write_json(str(Path(a.projects_dir)/'alpha.json'),{'large':'x'*10000})
"""
    )
    child = subprocess.run(
        [sys.executable, "-c", script, memory.module.__file__, "alpha"],
        env={"HOME": str(memory.home), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        timeout=15,
    )
    assert child.returncode == 24, child.stderr
    assert (path.stat().st_ino, path.read_bytes()) == before
    leftovers = list(path.parent.glob(".cortex-persist-*.tmp"))
    assert len(leftovers) == 1  # No blind orphan deletion by name/age after a crash.
    memory.ledger.crystallize_session(memory.delta("reopened"))
    assert memory.read("projects/alpha.json")["ghost"]["last_conversation"] == "reopened"
    assert leftovers[0].exists()


@pytest.mark.parametrize("stage", ["ghosts-entry", "session-entry"])
def test_schema_method_errors_retain_partial_progress(memory, capsys, stage):
    if stage == "ghosts-entry":
        (memory.base / "ghosts.json").write_text('{"alpha":null}')
        expected = (str(memory.base / "projects/alpha.json"),)
    else:
        (memory.base / "system.json").write_text('{"meta":{},"sessions_log":[null]}')
        expected = (str(memory.base / "projects/alpha.json"), str(memory.base / "ghosts.json"))
    with pytest.raises(memory.module.ConsolidationError) as caught:
        memory.ledger.crystallize_session(memory.delta("schema-error"))
    assert caught.value.completed_files == expected
    assert isinstance(caught.value.__cause__, AttributeError)
    assert "success" not in capsys.readouterr().out
    for path in expected:
        assert isinstance(json.loads(Path(path).read_text()), dict)
