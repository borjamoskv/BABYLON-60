"""Regression tests for FL-016 journal recovery across broker restarts."""

import hashlib
import importlib.util
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
