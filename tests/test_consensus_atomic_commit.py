"""Acceptance must match a durable signed row, including under hostile SQL triggers."""

from concurrent.futures import ThreadPoolExecutor
import sqlite3

import pytest

from babylon60.bft.consensus_committer import BFT_Committer, StateMutation
from babylon60.bft.consensus_ledger import BFT_Ledger
from babylon60.core.crypto_utils import Ed25519Signer

pytest.importorskip("fcntl", reason="The consensus committer uses real POSIX locks")


@pytest.fixture
def ledger(tmp_path):
    path = str(tmp_path / "ledger.db")
    signer = Ed25519Signer()
    instance = BFT_Ledger(path, {"node": signer.public_key_hex})
    first = StateMutation("operator", {"value": 0}, 0.0, "", "fixture")
    assert instance.invoke_subagent(first, 0, {"node": signer.sign(first.signing_hash(0))})
    try:
        yield instance, signer, path
    finally:
        instance.close()


@pytest.mark.parametrize(
    "trigger",
    [
        "BEFORE INSERT ON state_log BEGIN SELECT RAISE(IGNORE); END",
        "AFTER INSERT ON state_log BEGIN DELETE FROM state_log WHERE id=NEW.id; END",
        "AFTER INSERT ON state_log BEGIN UPDATE state_log SET payload=x'a1617801' WHERE id=NEW.id; END",
        "AFTER INSERT ON state_log BEGIN UPDATE state_log SET agent_id='forged' WHERE id=NEW.id; END",
        "AFTER INSERT ON state_log BEGIN UPDATE state_log SET fault_budget=1 WHERE id=NEW.id; END",
        "AFTER INSERT ON state_log BEGIN UPDATE state_log SET quorum_votes=x'00' WHERE id=NEW.id; END",
        "AFTER INSERT ON state_log BEGIN UPDATE state_log SET id=NEW.id+10 WHERE id=NEW.id; END",
    ],
)
def test_ignored_or_modified_insert_is_rejected_and_rolled_back(ledger, trigger):
    instance, signer, path = ledger
    checkpoint = instance.get_checkpoint()
    instance.conn.execute("CREATE TRIGGER attack " + trigger)
    mutation = StateMutation("operator", {"value": 1}, 0.0, "", "fixture")
    with pytest.raises(ValueError, match="persist"):
        instance.invoke_subagent(mutation, 0, {"node": signer.sign(mutation.signing_hash(0))})
    assert not instance.conn.in_transaction
    assert instance.audit_integrity(expected_checkpoint=checkpoint)
    with sqlite3.connect(path) as outside:
        assert outside.execute("SELECT COUNT(*) FROM state_log").fetchone()[0] == 1
        assert outside.execute("SELECT seq FROM sqlite_sequence WHERE name='state_log'").fetchone()[0] == 1
    instance.conn.execute("DROP TRIGGER attack")
    assert instance.invoke_subagent(mutation, 0, {"node": signer.sign(mutation.signing_hash(0))})
    assert instance.get_checkpoint().entries == 2


def test_trigger_failure_cannot_commit_partial_changes_or_be_treated_as_idempotency(ledger):
    instance, signer, _ = ledger
    checkpoint = instance.get_checkpoint()
    instance.conn.execute(
        "CREATE TRIGGER attack AFTER INSERT ON state_log BEGIN "
        "UPDATE state_log SET agent_id='forged' WHERE id=1; "
        "SELECT RAISE(FAIL, 'injected failure'); END"
    )
    mutation = StateMutation("operator", {"value": 1}, 0.0, "", "fixture")
    with pytest.raises(sqlite3.IntegrityError, match="injected failure"):
        instance.invoke_subagent(mutation, 0, {"node": signer.sign(mutation.signing_hash(0))})
    assert not instance.conn.in_transaction
    assert instance.audit_integrity(expected_checkpoint=checkpoint)


def test_repeated_rejections_leave_connection_and_sequence_usable(ledger):
    instance, signer, _ = ledger  # Fixture performs one successful warmup commit.
    for value in range(1, 17):
        mutation = StateMutation("operator", {"value": value}, 0.0, "", "fixture")
        votes = {"node": signer.sign(mutation.signing_hash(0))}
        checkpoint = instance.get_checkpoint()
        instance.conn.execute("CREATE TRIGGER attack BEFORE INSERT ON state_log BEGIN SELECT RAISE(IGNORE); END")
        with pytest.raises(ValueError, match="persist"):
            instance.invoke_subagent(mutation, 0, votes)
        assert instance.audit_integrity(expected_checkpoint=checkpoint)
        instance.conn.execute("DROP TRIGGER attack")
        assert instance.invoke_subagent(mutation, 0, votes)
        assert instance.invoke_subagent(mutation, 0, votes)
        assert instance.get_checkpoint().entries == value + 1


def test_failed_close_from_another_thread_keeps_the_lock_and_owner_usable(ledger):
    instance, signer, path = ledger
    with ThreadPoolExecutor(max_workers=1) as pool:
        with pytest.raises(sqlite3.ProgrammingError):
            pool.submit(instance.close).result(timeout=5)
    with pytest.raises(SystemExit, match="CRITICAL"):
        unexpected = BFT_Committer(path)
        unexpected.close()
    mutation = StateMutation("operator", {"value": 1}, 0.0, "", "fixture")
    assert instance.invoke_subagent(mutation, 0, {"node": signer.sign(mutation.signing_hash(0))})
    instance.close()
    BFT_Committer(path).close()


@pytest.mark.parametrize("timestamp", [2**53 + 1, -(2**53 + 1), 10**400])
def test_integer_timestamp_cannot_be_silently_rounded_or_overflow(timestamp):
    with pytest.raises(ValueError, match="timestamp"):
        StateMutation("operator", {}, timestamp, "").signing_hash(0)


@pytest.mark.parametrize("timestamp", [0, -0.0, 1700000000, 2**53, 2**53 + 2])
def test_exactly_representable_timestamp_is_preserved(ledger, timestamp):
    instance, signer, _ = ledger
    mutation = StateMutation("operator", {"timestamp_case": timestamp}, timestamp, "", "fixture")
    assert instance.invoke_subagent(mutation, 0, {"node": signer.sign(mutation.signing_hash(0))})
    assert instance.audit_integrity()
