"""Real SQLite and OS-lock regressions, isolated from operator databases."""

from pathlib import Path
import sqlite3

import pytest

from babylon60.bft.consensus_committer import BFT_Committer
from babylon60.bft.consensus_ledger import BFT_Ledger, StateMutation
from babylon60.core.crypto_utils import Ed25519Signer

fcntl = pytest.importorskip("fcntl", reason="These regressions exercise real POSIX advisory locks")


@pytest.mark.parametrize("target_exists", [False, True])
def test_lock_symlink_is_rejected_without_touching_its_target(tmp_path, target_exists):
    target = tmp_path / "sentinel"
    if target_exists:
        target.write_bytes(b"PRESERVE")
    path = tmp_path / "ledger.db"
    Path(f"{path}.lock").symlink_to(target)
    with pytest.raises(SystemExit, match="CRITICAL"):
        committer = BFT_Committer(str(path))
        committer.close()
    assert target.exists() is target_exists
    if target_exists:
        assert target.read_bytes() == b"PRESERVE"
    assert not path.exists()


def test_existing_lock_file_is_not_truncated(tmp_path):
    path = tmp_path / "ledger.db"
    lock = Path(f"{path}.lock")
    lock.write_bytes(b"PRESERVE")
    committer = BFT_Committer(str(path))
    try:
        assert lock.read_bytes() == b"PRESERVE"
    finally:
        committer.close()


def test_lock_contention_and_reacquisition_after_repeated_failures(tmp_path):
    path = str(tmp_path / "ledger.db")
    BFT_Committer(path).close()  # Warmup: schema, lock creation and release.
    owner = BFT_Committer(path)
    try:
        for _ in range(8):
            with pytest.raises(SystemExit, match="CRITICAL"):
                unexpected = BFT_Committer(path)
                unexpected.close()
        owner.conn.execute("CREATE TABLE owner_still_active(value)")
    finally:
        owner.close()
    BFT_Committer(path).close()


def test_schema_initialization_failure_releases_lock_before_exception_is_discarded(tmp_path):
    path = tmp_path / "ledger.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE VIEW state_log AS SELECT 1 AS id")
    # Keep the traceback alive: cleanup must not depend on Python's GC timing.
    with pytest.raises(sqlite3.OperationalError) as error:
        BFT_Committer(str(path))
    assert error.traceback is not None
    with open(f"{path}.lock", "rb") as probe:
        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(probe, fcntl.LOCK_UN)
    with sqlite3.connect(path) as conn:
        conn.execute("DROP VIEW state_log")
    reopened = BFT_Committer(str(path))
    reopened.close()


@pytest.mark.parametrize("second_path", ["another_cwd", "absolute"])
def test_all_names_of_resolved_database_share_one_lock(tmp_path, monkeypatch, second_path):
    home = tmp_path / "operator-state"
    monkeypatch.setenv("BABYLON_HOME", str(home))
    first_cwd, second_cwd = tmp_path / "one", tmp_path / "two"
    first_cwd.mkdir()
    second_cwd.mkdir()
    monkeypatch.chdir(first_cwd)
    first = BFT_Committer("shared.db")
    try:
        monkeypatch.chdir(second_cwd)
        path = "shared.db" if second_path == "another_cwd" else str(home / "dbs" / "shared.db")
        with pytest.raises(SystemExit, match="CRITICAL"):
            second = BFT_Committer(path)
            second.close()
    finally:
        first.close()
    reopened = BFT_Committer(str(home / "dbs" / "shared.db"))
    reopened.close()


@pytest.fixture
def ledger(tmp_path):
    signer = Ed25519Signer()
    instance = BFT_Ledger(str(tmp_path / "ledger.db"), {"node": signer.public_key_hex})
    mutation = StateMutation("operator", {"value": 1}, 0.0, "", "test")
    instance.invoke_subagent(mutation, 0, {"node": signer.sign(mutation.signing_hash(0))})
    try:
        yield instance, signer
    finally:
        instance.close()


@pytest.mark.parametrize("operation", ["audit", "checkpoint", "commit"])
def test_ledger_operations_preserve_callers_active_transaction(ledger, operation):
    instance, signer = ledger
    instance.conn.execute("CREATE TABLE caller_work(value)")
    instance.conn.execute("BEGIN")
    instance.conn.execute("INSERT INTO caller_work VALUES (1)")
    with pytest.raises(sqlite3.ProgrammingError, match="transaction"):
        if operation == "audit":
            instance.audit_integrity()
        elif operation == "checkpoint":
            instance.get_checkpoint()
        else:
            mutation = StateMutation("operator", {"value": 2}, 0.0, "", "test")
            instance.invoke_subagent(mutation, 0, {"node": signer.sign(mutation.signing_hash(0))})
    assert instance.conn.in_transaction
    assert instance.conn.execute("SELECT COUNT(*) FROM caller_work").fetchone()[0] == 1
    assert instance.conn.execute("SELECT COUNT(*) FROM state_log").fetchone()[0] == 1
    instance.conn.rollback()
    assert instance.audit_integrity()


@pytest.mark.parametrize("column", ["payload", "quorum_votes"])
@pytest.mark.parametrize("encoding", ["trailing_item", "indefinite_map"])
def test_audit_rejects_modified_cbor_encoding_even_with_same_decoded_value(ledger, column, encoding):
    instance, _ = ledger
    encoded = instance.conn.execute(f"SELECT {column} FROM state_log").fetchone()[0]
    assert encoded[0] == 0xA1  # Both test objects have one member.
    modified = encoded + b"\x00" if encoding == "trailing_item" else b"\xbf" + encoded[1:] + b"\xff"
    instance.conn.execute(f"UPDATE state_log SET {column}=?", (modified,))
    assert not instance.audit_integrity()
    with pytest.raises(ValueError, match="unauthenticated"):
        instance.get_checkpoint()
