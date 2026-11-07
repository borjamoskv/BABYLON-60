"""Real SQLite, fork and process-death probes on disposable ledgers only."""

import json
import os
import selectors
import signal
import sqlite3
import subprocess
import sys
import textwrap

import pytest

from babylon60.bft.consensus_ledger import BFT_Ledger, StateMutation
from babylon60.core.crypto_utils import Ed25519Signer

pytest.importorskip("fcntl", reason="These tests exercise real POSIX locks and processes")


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


SECONDARY_EFFECTS = [
    "DELETE FROM state_log WHERE id=1",
    "UPDATE state_log SET agent_id='forged' WHERE id=1",
    "INSERT OR REPLACE INTO state_log "
    "SELECT id,mutation_hash,'forged',payload,ts,causal_taint,fault_budget,quorum_votes FROM state_log WHERE id=1",
    "UPDATE sqlite_sequence SET seq=99 WHERE name='state_log'",
    "INSERT INTO witness VALUES (1)",
    "INSERT INTO state_log(mutation_hash,agent_id,payload,ts) VALUES ('" + "f" * 64 + "','unsigned',x'a0',0)",
]


@pytest.mark.parametrize("effect", SECONDARY_EFFECTS)
def test_commit_rejects_secondary_trigger_changes_even_when_new_row_is_valid(ledger, effect):
    instance, signer, path = ledger
    checkpoint = instance.get_checkpoint()
    instance.conn.execute("CREATE TABLE witness(value)")
    instance.conn.execute("CREATE TRIGGER attack AFTER INSERT ON state_log BEGIN " + effect + "; END")
    mutation = StateMutation("operator", {"value": 1}, 0.0, "", "fixture")
    with pytest.raises(ValueError, match="persist"):
        instance.invoke_subagent(mutation, 0, {"node": signer.sign(mutation.signing_hash(0))})
    assert not instance.conn.in_transaction
    assert instance.audit_integrity(expected_checkpoint=checkpoint)
    with sqlite3.connect(path) as outside:
        assert outside.execute("SELECT COUNT(*) FROM witness").fetchone()[0] == 0
        assert outside.execute("SELECT seq FROM sqlite_sequence WHERE name='state_log'").fetchone()[0] == 1


def test_repeated_secondary_effect_rejections_do_not_poison_change_counter(ledger):
    instance, signer, _ = ledger  # One successful warmup commit already exists.
    instance.conn.execute("CREATE TABLE witness(value)")
    for value in range(1, 9):
        mutation = StateMutation("operator", {"value": value}, 0.0, "", "fixture")
        votes = {"node": signer.sign(mutation.signing_hash(0))}
        checkpoint = instance.get_checkpoint()
        instance.conn.execute(
            "CREATE TRIGGER attack AFTER INSERT ON state_log BEGIN INSERT INTO witness VALUES(1); END"
        )
        with pytest.raises(ValueError, match="persist"):
            instance.invoke_subagent(mutation, 0, votes)
        assert instance.audit_integrity(expected_checkpoint=checkpoint)
        assert instance.conn.execute("SELECT COUNT(*) FROM witness").fetchone()[0] == 0
        instance.conn.execute("DROP TRIGGER attack")
        assert instance.invoke_subagent(mutation, 0, votes)
        assert instance.get_checkpoint().entries == value + 1


@pytest.mark.parametrize("failure", ["trigger", "commit"])
def test_failed_rollback_closes_poisoned_connection_and_releases_lock(ledger, failure):
    instance, signer, path = ledger
    checkpoint = instance.get_checkpoint()
    if failure == "trigger":
        instance.conn.execute(
            "CREATE TRIGGER attack AFTER INSERT ON state_log BEGIN "
            "UPDATE state_log SET agent_id='forged' WHERE id=1; "
            "SELECT RAISE(FAIL,'injected failure'); END"
        )

    def authorize(action, operation, *unused):
        denied = {"ROLLBACK", "COMMIT"} if failure == "commit" else {"ROLLBACK"}
        return (
            sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_TRANSACTION and operation in denied else sqlite3.SQLITE_OK
        )

    instance.conn.set_authorizer(authorize)
    mutation = StateMutation("operator", {"value": 1}, 0.0, "", "fixture")
    try:
        with pytest.raises(sqlite3.DatabaseError) as error:
            instance.invoke_subagent(mutation, 0, {"node": signer.sign(mutation.signing_hash(0))})
        assert error.value.__cause__ is not None
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            instance.conn.execute("SELECT 1")
        reopened = BFT_Ledger(path, {"node": signer.public_key_hex})
        try:
            assert reopened.audit_integrity(expected_checkpoint=checkpoint)
        finally:
            reopened.close()
    finally:
        try:
            instance.conn.set_authorizer(None)
            instance.conn.rollback()
        except sqlite3.ProgrammingError:
            pass


@pytest.mark.skipif(not hasattr(os, "fork"), reason="Requires POSIX fork in an isolated interpreter")
def test_fork_child_cannot_use_connection_or_unlock_its_parent(tmp_path):
    # Fork a fresh interpreter, never the pytest process with possible worker threads.
    script = textwrap.dedent("""
        import json, os, sqlite3, sys
        from babylon60.bft.consensus_committer import BFT_Committer
        owner = BFT_Committer(sys.argv[1])
        child = os.fork()
        if child == 0:
            denied = False
            try:
                owner.conn
            except sqlite3.ProgrammingError:
                denied = True
            owner.close()
            os._exit(0 if denied else 7)
        _, status = os.waitpid(child, 0)
        blocked = False
        try:
            other = BFT_Committer(sys.argv[1])
        except SystemExit:
            blocked = True
        else:
            other.close()
        usable = owner.conn.execute('SELECT 1').fetchone() == (1,)
        owner.close()
        BFT_Committer(sys.argv[1]).close()
        print(json.dumps({'child_exit': os.waitstatus_to_exitcode(status), 'blocked': blocked, 'usable': usable}))
    """)
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(tmp_path / "fork.db")],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    assert json.loads(result.stdout) == {"child_exit": 0, "blocked": True, "usable": True}


@pytest.mark.parametrize("stage", ["pending", "committed"])
def test_sigkill_recovery_preserves_atomic_state_and_allows_replay(ledger, stage):
    instance, signer, path = ledger
    checkpoint = instance.get_checkpoint()
    mutation = StateMutation("operator", {"value": 1}, 0.0, "", "fixture")
    votes = {"node": signer.sign(mutation.signing_hash(0))}
    instance.close()
    script = textwrap.dedent("""
        import json, sys
        from babylon60.bft.consensus_ledger import BFT_Ledger, StateMutation
        from babylon60.core.crypto_utils import canonicalize_cbor
        data = json.loads(sys.stdin.readline())
        owner = BFT_Ledger(data['path'], {'node': data['key']})
        mutation = StateMutation('operator', {'value': 1}, 0.0, '', 'fixture')
        if data['stage'] == 'committed':
            owner.invoke_subagent(mutation, 0, data['votes'])
        else:
            digest = owner.validator.validate_votes(mutation.signing_payload(0), 0, data['votes'])
            owner.conn.execute('BEGIN IMMEDIATE')
            owner.conn.execute('INSERT INTO state_log '
                '(mutation_hash,agent_id,payload,ts,causal_taint,fault_budget,quorum_votes) VALUES (?,?,?,?,?,?,?)',
                (digest, mutation.agent_id, canonicalize_cbor(mutation.payload), 0.0, 'fixture', 0,
                 canonicalize_cbor(data['votes'])))
        print('READY', flush=True)
        sys.stdin.readline()
    """)
    child = subprocess.Popen(
        [sys.executable, "-I", "-c", script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert child.stdin is not None
        assert child.stdout is not None
        child.stdin.write(
            json.dumps({"path": path, "key": signer.public_key_hex, "votes": votes, "stage": stage}) + "\n"
        )
        child.stdin.flush()
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            assert selector.select(timeout=5), "Child did not reach the requested state"
        assert child.stdout.readline().strip() == "READY"
        child.kill()
        child.communicate(timeout=5)
        assert child.returncode == -signal.SIGKILL
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=5)
    reopened = BFT_Ledger(path, {"node": signer.public_key_hex})
    try:
        assert reopened.audit_integrity()
        assert reopened.get_checkpoint().entries == (1 if stage == "pending" else 2)
        if stage == "pending":
            assert reopened.audit_integrity(expected_checkpoint=checkpoint)
        assert reopened.invoke_subagent(mutation, 0, votes)
        assert reopened.get_checkpoint().entries == 2
    finally:
        reopened.close()
