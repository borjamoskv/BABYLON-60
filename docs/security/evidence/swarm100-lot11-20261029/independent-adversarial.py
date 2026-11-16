"""Independent JSON-memory checks confined to synthetic HOME directories."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[4]
SOURCE = ROOT / "01_KISH_ENGINE/babylon60/core/cortex_persist.py"
TEST = ROOT / "tests/test_swarm100_lot11_regressions.py"
sys.dont_write_bytecode = True


def hashes():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (SOURCE, TEST)}


def snapshot(path):
    return (path.stat().st_ino, path.read_bytes())


def failed(callback, expected):
    try:
        callback()
    except expected as error:
        return error
    raise AssertionError("Expected persistence failure")


def populate(base):
    (base / "projects").mkdir(parents=True)
    (base / "snapshots").mkdir()
    for name in ("alpha", "beta"):
        (base / "projects" / (name + ".json")).write_text(json.dumps(dict(meta={}, recent_changes=[], decisions=[])))
    (base / "ghosts.json").write_text("{}")
    (base / "system.json").write_text(json.dumps(dict(meta={}, sessions_log=[])))


def main():
    before = hashes()
    original_env, original_cwd = dict(os.environ), Path.cwd()
    controls, prohibited_calls = [], []
    counter = [0]

    def forbidden(*args, **kwargs):
        prohibited_calls.append("forbidden kill/network/process")
        raise AssertionError("Protected operation forbidden")

    try:
        with tempfile.TemporaryDirectory(prefix="lot11-independent-") as temporary, \
                patch.object(os, "kill", forbidden), patch.object(socket.socket, "connect", forbidden), \
                patch.object(socket.socket, "connect_ex", forbidden), patch.object(socket, "getaddrinfo", forbidden), \
                patch.object(subprocess, "Popen", forbidden):
            boundary = Path(temporary).resolve()
            os.chdir(boundary)
            os.environ.clear()
            os.environ.update(PATH="/usr/bin:/bin", HOME=str(boundary), PYTHONDONTWRITEBYTECODE="1")

            class Fixture:
                def __init__(self):
                    counter[0] += 1
                    self.home = boundary / f"owned home {counter[0]}"
                    self.base = self.home / ".agent/memory"
                    populate(self.base)
                    os.environ["HOME"] = str(self.home)
                    copied = boundary / f"memory-{counter[0]}.py"
                    shutil.copyfile(SOURCE, copied)
                    spec = importlib.util.spec_from_file_location(f"independent_lot11_{counter[0]}", copied)
                    self.module = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = self.module
                    spec.loader.exec_module(self.module)
                    self.module.os = SimpleNamespace(**{name: getattr(os, name) for name in dir(os) if not name.startswith("__")})
                    self.module.fcntl = SimpleNamespace(flock=fcntl.flock, LOCK_EX=fcntl.LOCK_EX, LOCK_UN=fcntl.LOCK_UN)
                    self.ledger = self.module.CortexOntologyLedger("alpha")
                    self.target = self.base / "projects/alpha.json"

                def delta(self, label):
                    return self.module.SessionDelta(label, "fixture.py", label, ["change " + label], ["decision " + label], "fixture")

                def write(self, value=None):
                    self.ledger._write_json(str(self.target), {"fixture": "new value Ω"} if value is None else value)

                def read(self, relative):
                    return json.loads((self.base / relative).read_text())

                def tempfiles(self):
                    return list(self.base.rglob(".cortex-persist-*.tmp"))

            for phase in ("partial-write", "zero-write", "file-fsync", "replace-before"):
                f = Fixture()
                prior = snapshot(f.target)
                real_write, real_fsync = f.module.os.write, f.module.os.fsync

                def partial(fd, data):
                    real_write(fd, data[:4])
                    raise OSError("owned partial write")

                def sync_fail(fd):
                    if stat.S_ISREG(os.fstat(fd).st_mode):
                        raise OSError("owned file sync failure")
                    return real_fsync(fd)

                def replace_fail(*args, **kwargs):
                    raise OSError("owned pre-replace failure")

                if phase == "partial-write":
                    f.module.os.write = partial
                elif phase == "zero-write":
                    f.module.os.write = lambda *args: 0
                elif phase == "file-fsync":
                    f.module.os.fsync = sync_fail
                else:
                    f.module.os.replace = replace_fail
                error = failed(f.write, f.module.PersistenceWriteError)
                assert snapshot(f.target) == prior and not f.tempfiles()
                assert error.replacement_state == ("NOT_REPLACED" if phase == "replace-before" else "NOT_ATTEMPTED")
                assert error.durability_confirmed is False
            controls.append(dict(name="four_precommit_failures_preserve_prior_bytes_inode", passed=True, cases=4))

            f = Fixture()
            prior = snapshot(f.target)
            real_write, real_sync = f.module.os.write, f.module.os.fsync
            events = []

            def small_write(fd, data):
                return real_write(fd, data[:3])

            def sync_record(fd):
                kind = "directory" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file"
                if kind == "file":
                    assert snapshot(f.target) == prior
                events.append(kind)
                return real_sync(fd)

            f.module.os.write, f.module.os.fsync = small_write, sync_record
            f.write()
            assert f.read("projects/alpha.json") == {"fixture": "new value Ω"}
            assert f.target.stat().st_ino != prior[0] and events == ["file", "directory"] and not f.tempfiles()
            controls.append(dict(name="write_all_and_file_parent_sync_order", passed=True))

            for phase in ("directory-fsync", "replace-then-raise"):
                f = Fixture()
                real_sync, real_replace = f.module.os.fsync, f.module.os.replace

                def fail_directory(fd):
                    if stat.S_ISDIR(os.fstat(fd).st_mode):
                        raise OSError("owned directory sync failure")
                    return real_sync(fd)

                def replace_then_raise(*args, **kwargs):
                    real_replace(*args, **kwargs)
                    raise OSError("owned observed-after-replace failure")

                if phase == "directory-fsync":
                    f.module.os.fsync = fail_directory
                else:
                    f.module.os.replace = replace_then_raise
                error = failed(f.write, f.module.PersistenceWriteError)
                assert error.replacement_state == "REPLACED" and error.replaced and not error.durability_confirmed
                assert f.read("projects/alpha.json") == {"fixture": "new value Ω"} and not f.tempfiles()
            controls.append(dict(name="postreplace_failures_report_new_visible_json_without_rollback", passed=True, cases=2))

            f = Fixture()
            other = f.target.with_name("third-party.json")
            other.write_text('{"third_party":true}')
            real_replace = f.module.os.replace

            def replace_other(src, dst, **kwargs):
                real_replace(other.name, dst, src_dir_fd=kwargs["src_dir_fd"], dst_dir_fd=kwargs["dst_dir_fd"])
                raise OSError("owned third-party replacement")

            f.module.os.replace = replace_other
            error = failed(f.write, f.module.PersistenceWriteError)
            assert error.replacement_state == "UNKNOWN" and f.read("projects/alpha.json") == {"third_party": True}
            assert not f.tempfiles()
            controls.append(dict(name="ambiguous_replace_preserves_third_party_file_and_reports_unknown", passed=True))

            f = Fixture()
            prior = snapshot(f.target)
            colliding = f.target.with_name(".cortex-persist-" + "0" * 32 + ".tmp")
            colliding.write_bytes(b"foreign owned fixture temporary")
            f.module.secrets = SimpleNamespace(token_hex=lambda size: "0" * 32)
            failed(f.write, f.module.PersistenceWriteError)
            assert snapshot(f.target) == prior and colliding.read_bytes() == b"foreign owned fixture temporary"
            controls.append(dict(name="exclusive_temp_collision_does_not_remove_existing_file", passed=True))

            f = Fixture()
            original_ghost, original_system = snapshot(f.base / "ghosts.json"), snapshot(f.base / "system.json")
            real_replace = f.module.os.replace

            def fail_ghost(src, dst, **kwargs):
                if dst == "ghosts.json":
                    raise OSError("owned second-file failure")
                return real_replace(src, dst, **kwargs)

            f.module.os.replace = fail_ghost
            output = io.StringIO()
            with redirect_stdout(output):
                error = failed(lambda: f.ledger.crystallize_session(f.delta("partial")), f.module.ConsolidationError)
            assert error.completed_files == (str(f.target),)
            assert error.current_file == str(f.base / "ghosts.json") and error.replacement_state == "NOT_REPLACED"
            assert f.read("projects/alpha.json")["ghost"]["last_conversation"] == "partial"
            assert snapshot(f.base / "ghosts.json") == original_ghost and snapshot(f.base / "system.json") == original_system
            assert not output.getvalue() and not f.tempfiles()
            controls.append(dict(name="session_partial_progress_explicit_and_no_success_print", passed=True))

            f = Fixture()
            first_read, release, second_attempt, second_read = (threading.Event() for _ in range(4))
            original_read = f.module.CortexOntologyLedger._read_json
            real_flock = f.module.fcntl.flock
            errors = []
            a, b = f.ledger, f.module.CortexOntologyLedger("beta")

            def read_pause(self, path):
                value = original_read(self, path)
                if threading.current_thread().name == "independent-A" and path.endswith("alpha.json"):
                    first_read.set()
                    assert release.wait(5)
                elif threading.current_thread().name == "independent-B":
                    second_read.set()
                return value

            def lock_record(fd, operation):
                if threading.current_thread().name == "independent-B" and operation == fcntl.LOCK_EX:
                    second_attempt.set()
                return real_flock(fd, operation)

            def worker(ledger, name):
                try:
                    ledger.crystallize_session(f.delta(name))
                except BaseException as error:
                    errors.append(error)

            f.module.CortexOntologyLedger._read_json = read_pause
            f.module.fcntl.flock = lock_record
            thread_a = threading.Thread(target=worker, args=(a, "A"), name="independent-A", daemon=True)
            thread_b = threading.Thread(target=worker, args=(b, "B"), name="independent-B", daemon=True)
            with redirect_stdout(io.StringIO()):
                thread_a.start()
                try:
                    assert first_read.wait(5)
                    thread_b.start()
                    assert second_attempt.wait(5)
                    assert not second_read.wait(0.05)
                finally:
                    release.set()
                    thread_a.join(5)
                    if thread_b.ident is not None:
                        thread_b.join(5)
            assert not thread_a.is_alive() and not thread_b.is_alive() and not errors, errors
            assert set(f.read("ghosts.json")) == {"alpha", "beta"}
            assert {row["conversation_id"] for row in f.read("system.json")["sessions_log"]} == {"A", "B"}
            lock = f.base / ".cortex-persist.lock"
            lock_inode = lock.stat().st_ino
            f.module.CortexOntologyLedger._read_json = original_read
            f.module.fcntl.flock = real_flock
            with redirect_stdout(io.StringIO()), ThreadPoolExecutor(max_workers=4) as executor:
                list(executor.map(lambda n: a.crystallize_session(f.delta(f"parallel-{n}")), range(8)))
            assert len(f.read("system.json")["sessions_log"]) == 10 and lock.stat().st_ino == lock_inode
            controls.append(dict(name="common_lock_serializes_projects_and_shared_instance_threads", passed=True, additional_parallel_sessions=8))

            f = Fixture()
            original_read = f.ledger._read_json
            replaced = []
            archived = f.home / ".agent/old-memory"
            new_images = {}

            def read_and_replace(path):
                value = original_read(path)
                if not replaced:
                    f.base.rename(archived)
                    populate(f.base)
                    new_images.update({rel: snapshot(f.base / rel) for rel in ("projects/alpha.json", "ghosts.json", "system.json")})
                    replaced.append(True)
                return value

            f.ledger._read_json = read_and_replace
            with redirect_stdout(io.StringIO()):
                error = failed(lambda: f.ledger.crystallize_session(f.delta("replacement")), f.module.ConsolidationError)
            assert replaced and error.completed_files == ()
            assert all(snapshot(f.base / rel) == value for rel, value in new_images.items())
            assert json.loads((archived / "projects/alpha.json").read_text())["recent_changes"] == []
            controls.append(dict(name="replaced_memory_root_cannot_use_old_lock_for_new_files", passed=True))

            for instant in (datetime(2026, 1, 15, 12, 34, 56, tzinfo=timezone.utc), datetime(2026, 7, 15, 12, 34, 56, tzinfo=timezone.utc)):
                f = Fixture()
                historical = "2020-06-01T10:00:00+02:00"
                data = f.read("projects/alpha.json")
                data["historical"] = historical
                f.target.write_text(json.dumps(data))
                f.module.datetime = SimpleNamespace(now=lambda tz: instant)
                assert datetime.fromisoformat(f.ledger._get_iso_now()).timestamp() == instant.timestamp()
                with redirect_stdout(io.StringIO()):
                    f.ledger.crystallize_session(f.delta("clock"))
                assert f.read("projects/alpha.json")["historical"] == historical
                for timestamp in (f.read("projects/alpha.json")["meta"]["last_touched"], f.read("ghosts.json")["alpha"]["timestamp"], f.read("system.json")["last_updated"]):
                    assert timestamp.endswith("+00:00") and datetime.fromisoformat(timestamp) == instant
            controls.append(dict(name="winter_summer_utc_instant_and_historical_values_preserved", passed=True, cases=2))

            f = Fixture()
            prior = snapshot(f.target)
            for payload in ({"x": float("nan")}, [], {"x": float("inf")}):
                failed(lambda: f.write(payload), (ValueError, TypeError))
                assert snapshot(f.target) == prior
            for project in ("../escape", "a/b", "a\\b", "..", "", "x\0y"):
                failed(lambda: f.module.CortexOntologyLedger(project), ValueError)
            f.target.unlink()
            external = f.home / "owned-external.json"
            external.write_text('{"untouched":true}')
            f.target.symlink_to(external)
            failed(f.write, f.module.PersistenceWriteError)
            assert external.read_text() == '{"untouched":true}'
            controls.append(dict(name="invalid_payload_project_components_and_destination_symlink_rejected", passed=True))
            assert not prohibited_calls
    finally:
        os.chdir(original_cwd)
        os.environ.clear()
        os.environ.update(original_env)
    after = hashes()
    assert before[str(SOURCE.relative_to(ROOT))] == after[str(SOURCE.relative_to(ROOT))]
    print(json.dumps(dict(reviewer="03", status="PASS", checks=controls, check_count=len(controls), fixtures=counter[0], prohibited_calls=prohibited_calls,
                          source_sha256_before=before, source_sha256_after=after,
                          scope="Synthetic HOME/.agent/memory only; kill/network/subprocess blocked before import. Filesystem faults and cooperating threads, not real memory, hardware, power-cut or global three-file transaction certification."), indent=2))


if __name__ == "__main__":
    main()
