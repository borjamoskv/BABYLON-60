"""Regression tests for FL-016 journal recovery across broker restarts."""

import hashlib
import importlib.util
import multiprocessing
from pathlib import Path

import pytest


_SOURCE = Path(__file__).absolute().parents[1] / "scripts/guards/c5_fl016_boundary_escape.py"
_SPEC = importlib.util.spec_from_file_location("c5_fl016_boundary_escape", _SOURCE)
assert _SPEC is not None and _SPEC.loader is not None
fl016 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(fl016)


def _broker(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir(exist_ok=True)
    journal = tmp_path / "journal"
    return fl016.E5BrokerKernel(str(vault), str(journal)), vault, journal


def _process_racer(vault, journal, filename, ready, start, outcomes):
    broker = fl016.E5BrokerKernel(vault, journal)
    ready.put(True)
    if start.wait(10):
        outcomes.put(broker.execute_mediated_effect("shared", filename, b"payload"))


def test_uncommitted_overwrite_restores_original_after_restart(tmp_path):
    broker, vault, journal = _broker(tmp_path)
    assert broker.execute_mediated_effect("original", "target.txt", b"old")
    assert not broker.execute_mediated_effect("interrupted", "target.txt", b"new", inject_crash_after_effect=True)
    assert (vault / "target.txt").read_bytes() == b"new"

    broker = fl016.E5BrokerKernel(str(vault), str(journal))
    broker.recovery_protocol()

    assert (vault / "target.txt").read_bytes() == b"old"
    assert not (vault / ".bak_interrupted").exists()
    assert not broker.execute_mediated_effect("interrupted", "replay.txt", b"replay")
    assert broker.audit_journal_integrity()


def test_recovery_preserves_later_commit_on_same_target(tmp_path):
    broker, vault, journal = _broker(tmp_path)
    assert broker.execute_mediated_effect("original", "target.txt", b"old")
    assert not broker.execute_mediated_effect("interrupted", "target.txt", b"middle", inject_crash_after_effect=True)
    assert broker.execute_mediated_effect("later", "target.txt", b"final")

    broker = fl016.E5BrokerKernel(str(vault), str(journal))
    broker.recovery_protocol()

    assert (vault / "target.txt").read_bytes() == b"final"
    assert not (vault / ".bak_interrupted").exists()
    assert broker.audit_journal_integrity()


def test_missing_prepared_backup_fails_closed(tmp_path):
    broker, vault, journal = _broker(tmp_path)
    (vault / "target.txt").write_bytes(b"old")
    payload_hash = hashlib.sha256(b"new").hexdigest()
    broker.append_journal_block("BEGIN", "interrupted", payload_hash, "target.txt", "EXISTED")
    broker.append_journal_block("PREPARED", "interrupted", payload_hash, "target.txt")

    broker = fl016.E5BrokerKernel(str(vault), str(journal))
    with pytest.raises(fl016.BoundaryEscapeViolation, match="Respaldo ausente"):
        broker.recovery_protocol()
    assert (vault / "target.txt").read_bytes() == b"old"


def test_crash_before_prepared_keeps_original_and_cleans_backup(tmp_path):
    broker, vault, journal = _broker(tmp_path)
    (vault / "target.txt").write_bytes(b"old")
    payload_hash = hashlib.sha256(b"new").hexdigest()
    broker.append_journal_block("BEGIN", "interrupted", payload_hash, "target.txt", "EXISTED")
    (vault / ".bak_interrupted").hardlink_to(vault / "target.txt")

    broker = fl016.E5BrokerKernel(str(vault), str(journal))
    broker.recovery_protocol()

    assert (vault / "target.txt").read_bytes() == b"old"
    assert not (vault / ".bak_interrupted").exists()
    assert broker.audit_journal_integrity()


def test_two_existing_instances_reject_replayed_token(tmp_path):
    first, vault, journal = _broker(tmp_path)
    second = fl016.E5BrokerKernel(str(vault), str(journal))

    assert first.execute_mediated_effect("shared", "first.txt", b"first")
    assert not second.execute_mediated_effect("shared", "second.txt", b"second")
    assert (vault / "first.txt").read_bytes() == b"first"
    assert not (vault / "second.txt").exists()
    assert first.audit_journal_integrity()


def test_two_processes_share_one_token(tmp_path):
    _, vault, journal = _broker(tmp_path)
    context = multiprocessing.get_context("spawn")
    ready = context.Queue()
    start = context.Event()
    outcomes = context.Queue()
    processes = [
        context.Process(
            target=_process_racer,
            args=(str(vault), str(journal), f"process_{index}.txt", ready, start, outcomes),
        )
        for index in range(2)
    ]
    try:
        for process in processes:
            process.start()
        for _ in processes:
            assert ready.get(timeout=10)
        start.set()
        results = [outcomes.get(timeout=10) for _ in processes]
        for process in processes:
            process.join(timeout=10)
            assert process.exitcode == 0
    finally:
        for process in processes:
            if process.pid is not None:
                if process.is_alive():
                    process.terminate()
                process.join(timeout=10)
        ready.close()
        outcomes.close()

    assert sorted(results) == [False, True]
    assert len(list(vault.glob("process_*.txt"))) == 1
    assert fl016.E5BrokerKernel(str(vault), str(journal)).audit_journal_integrity()


def test_existing_instance_observes_another_instances_revocation(tmp_path):
    first, vault, journal = _broker(tmp_path)
    second = fl016.E5BrokerKernel(str(vault), str(journal))

    first.revoke_token("revoked")

    assert not second.execute_mediated_effect("revoked", "forbidden.txt", b"forbidden")
    assert not (vault / "forbidden.txt").exists()
    assert second.audit_journal_integrity()


def test_existing_instance_rejects_effect_after_journal_tampering(tmp_path):
    broker, vault, journal = _broker(tmp_path)
    assert broker.execute_mediated_effect("original", "target.txt", b"original")
    journal.write_text(journal.read_text().replace("COMMIT", "COMMIX"))

    with pytest.raises(fl016.BoundaryEscapeViolation, match="Journal corrupto"):
        broker.execute_mediated_effect("tampered", "forbidden.txt", b"forbidden")

    assert (vault / "target.txt").read_bytes() == b"original"
    assert not (vault / "forbidden.txt").exists()
    assert not broker.audit_journal_integrity()
