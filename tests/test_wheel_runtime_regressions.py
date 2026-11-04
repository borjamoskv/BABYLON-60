"""Regression cases from wheel 1.0.2, using real software keys and disposable DBs."""

import asyncio
from dataclasses import replace
import sqlite3

import pytest

from babylon60.bft.consensus_ledger import BFT_Ledger, StateMutation
from babylon60.bft.consensus_validator import BFT_Validator
from babylon60.bft.ledger_actor import BFTCausalInvariantError, BFTLedgerActor, LedgerEvent
from babylon60.core.crypto_utils import Ed25519Signer, canonicalize_cbor, hash_sha3_256


@pytest.fixture
def committee():
    signers = {str(i): Ed25519Signer() for i in range(4)}
    return signers, {node: signer.public_key_hex for node, signer in signers.items()}


def approve(ledger, signers, mutation=None):
    mutation = mutation or StateMutation("operator", {"value": 1}, 0.0, "", "test")
    votes = {node: signer.sign(mutation.signing_hash(1)) for node, signer in signers.items()}
    assert ledger.invoke_subagent(mutation, 1, votes)
    return mutation, votes


@pytest.mark.parametrize("attack", ["payload_and_hash", "agent", "timestamp", "taint", "delete_tail", "delete_all"])
def test_consensus_detects_external_mutations_after_reopen(tmp_path, committee, attack):
    signers, keys = committee
    path = tmp_path / "ledger.db"
    ledger = BFT_Ledger(str(path), keys)
    original, _ = approve(ledger, signers)
    if attack == "delete_tail":
        approve(ledger, signers, replace(original, payload={"value": 2}))
    checkpoint = ledger.get_checkpoint()
    ledger.close()
    with sqlite3.connect(path) as outside:
        if attack == "payload_and_hash":
            changed = canonicalize_cbor({"value": 99})
            forged_hash = replace(original, payload={"value": 99}).signing_hash(1)
            outside.execute("UPDATE state_log SET payload=?, mutation_hash=?", (changed, forged_hash))
        elif attack == "agent":
            outside.execute("UPDATE state_log SET agent_id='forged'")
        elif attack == "timestamp":
            outside.execute("UPDATE state_log SET ts=99")
        elif attack == "taint":
            outside.execute("UPDATE state_log SET causal_taint='forged'")
        elif attack == "delete_tail":
            outside.execute("DELETE FROM state_log WHERE id=2")
        else:
            outside.execute("DELETE FROM state_log")
    ledger = BFT_Ledger(str(path), keys)
    try:
        assert not ledger.audit_integrity(expected_checkpoint=checkpoint)
        assert not ledger.audit_integrity()
    finally:
        ledger.close()


def test_consensus_rejects_unsigned_external_insert(tmp_path, committee):
    _, keys = committee
    ledger = BFT_Ledger(str(tmp_path / "ledger.db"), keys)
    try:
        raw = canonicalize_cbor({"value": 1})
        ledger.conn.execute(
            "INSERT INTO state_log(mutation_hash,agent_id,payload,ts) VALUES (?,?,?,?)",
            (hash_sha3_256(raw), "unsigned", raw, 0.0),
        )
        assert not ledger.audit_integrity()
    finally:
        ledger.conn.close()


@pytest.mark.parametrize("changed", [{"agent_id": "forged"}, {"timestamp": 99.0}, {"causal_taint": "forged"}])
def test_votes_bind_mutation_metadata(tmp_path, committee, changed):
    signers, keys = committee
    ledger = BFT_Ledger(str(tmp_path / "ledger.db"), keys)
    original = StateMutation("operator", {"value": 1}, 0.0, "", "test")
    votes = {node: signer.sign(original.signing_hash(1)) for node, signer in signers.items()}
    try:
        with pytest.raises(PermissionError):
            ledger.invoke_subagent(replace(original, **changed), 1, votes)
        assert ledger.conn.execute("SELECT COUNT(*) FROM state_log").fetchone()[0] == 0
    finally:
        ledger.close()


def test_duplicate_public_key_aliases_are_not_independent_votes():
    key = Ed25519Signer().public_key_hex
    with pytest.raises(ValueError, match="unique"):
        BFT_Validator({str(i): key.upper() if i == 0 else key for i in range(4)})


def test_consensus_valid_reopen_idempotency_and_independent_checkpoint(tmp_path, committee):
    signers, keys = committee
    path = tmp_path / "ledger.db"
    ledger = BFT_Ledger(str(path), keys)
    first, votes = approve(ledger, signers)
    assert ledger.invoke_subagent(first, 1, votes)
    assert ledger.conn.execute("SELECT COUNT(*) FROM state_log").fetchone()[0] == 1
    approve(ledger, signers, replace(first, payload={"value": 2}))
    checkpoint = ledger.get_checkpoint()
    ledger.close()
    # An adversary can also reset SQLite's internal high-water mark. The caller's
    # separately retained checkpoint must still reject that otherwise valid prefix.
    with sqlite3.connect(path) as outside:
        outside.execute("DELETE FROM state_log WHERE id=2")
        outside.execute("UPDATE sqlite_sequence SET seq=1 WHERE name='state_log'")
    ledger = BFT_Ledger(str(path), keys)
    try:
        assert not ledger.audit_integrity(expected_checkpoint=checkpoint)
    finally:
        ledger.close()


def test_consensus_proof_survives_reopen_and_legacy_rows_fail_closed(tmp_path, committee):
    signers, keys = committee
    path = tmp_path / "ledger.db"
    ledger = BFT_Ledger(str(path), keys)
    approve(ledger, signers)
    checkpoint = ledger.get_checkpoint()
    ledger.close()
    ledger = BFT_Ledger(str(path), keys)
    try:
        assert ledger.audit_integrity(expected_checkpoint=checkpoint)
        ledger.conn.execute("UPDATE state_log SET fault_budget=0")
        assert not ledger.audit_integrity()
    finally:
        ledger.close()


def test_legacy_database_migrates_without_fabricating_proofs(tmp_path, committee):
    _, keys = committee
    path = tmp_path / "legacy.db"
    raw = canonicalize_cbor({"old": True})
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE state_log (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "mutation_hash TEXT UNIQUE NOT NULL, agent_id TEXT NOT NULL, payload BLOB NOT NULL, "
            "ts REAL NOT NULL, causal_taint TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO state_log(mutation_hash,agent_id,payload,ts,causal_taint) VALUES (?,?,?,?,?)",
            (hash_sha3_256(raw), "old-agent", raw, 0.0, "old-taint"),
        )
    ledger = BFT_Ledger(str(path), keys)
    try:
        assert not ledger.audit_integrity()
        assert ledger.conn.execute("SELECT payload, fault_budget, quorum_votes FROM state_log").fetchone() == (
            raw,
            None,
            None,
        )
    finally:
        ledger.close()


def test_payload_only_votes_cannot_authorize_a_full_mutation(tmp_path, committee):
    signers, keys = committee
    ledger = BFT_Ledger(str(tmp_path / "ledger.db"), keys)
    mutation = StateMutation("operator", {"value": 1}, 0.0, "", "test")
    old_digest = hash_sha3_256(canonicalize_cbor(mutation.payload))
    try:
        with pytest.raises(PermissionError):
            ledger.invoke_subagent(mutation, 1, {n: s.sign(old_digest) for n, s in signers.items()})
        assert ledger.conn.execute("SELECT COUNT(*) FROM state_log").fetchone()[0] == 0
    finally:
        ledger.close()


@pytest.mark.parametrize("attack", ["metadata", "proof"])
def test_idempotent_replay_does_not_hide_a_corrupted_existing_row(tmp_path, committee, attack):
    signers, keys = committee
    ledger = BFT_Ledger(str(tmp_path / "ledger.db"), keys)
    mutation, votes = approve(ledger, signers)
    try:
        if attack == "metadata":
            ledger.conn.execute("UPDATE state_log SET agent_id='forged'")
        else:
            ledger.conn.execute("UPDATE state_log SET quorum_votes=?", (b"invalid-proof",))
        with pytest.raises(ValueError, match="Collision"):
            ledger.invoke_subagent(mutation, 1, votes)
    finally:
        ledger.close()


def test_negative_zero_timestamp_survives_sqlite_roundtrip(tmp_path, committee):
    signers, keys = committee
    ledger = BFT_Ledger(str(tmp_path / "ledger.db"), keys)
    try:
        approve(ledger, signers, StateMutation("operator", {"value": 1}, -0.0, "", "test"))
        assert ledger.audit_integrity()
    finally:
        ledger.close()


def test_consensus_bounded_reopen_stress(tmp_path, committee):
    signers, keys = committee
    path = tmp_path / "stress.db"
    ledger = BFT_Ledger(str(path), keys)
    original, _ = approve(ledger, signers)  # Warmup includes schema and crypto initialization.
    for i in range(1, 65):
        approve(ledger, signers, replace(original, payload={"value": i + 1}))
    checkpoint = ledger.get_checkpoint()
    assert checkpoint.entries == 65
    ledger.close()
    ledger = BFT_Ledger(str(path), keys)
    try:
        assert ledger.audit_integrity(expected_checkpoint=checkpoint)
    finally:
        ledger.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("reset_sequence", [False, True])
async def test_actor_detects_removed_tail(tmp_path, reset_sequence):
    path = tmp_path / "actor.db"
    actor = BFTLedgerActor(path)
    await actor.start()
    try:
        for i in range(3):
            event = LedgerEvent("test", str(i), "created", {"i": i}, "test", "fixture", "events", str(i))
            await asyncio.wait_for(actor.append(event), timeout=5)
        checkpoint = await actor.get_checkpoint()
    finally:
        await asyncio.wait_for(actor.stop(), timeout=5)
    assert await BFTLedgerActor(path).verify_chain(expected_checkpoint=checkpoint)
    with sqlite3.connect(path) as outside:
        outside.execute("DROP TRIGGER trg_ledger_immutable_delete")
        outside.execute("DELETE FROM ledger_entries WHERE seq=3")
        if reset_sequence:
            outside.execute("UPDATE sqlite_sequence SET seq=2 WHERE name='ledger_entries'")
    with pytest.raises(BFTCausalInvariantError, match="truncat|checkpoint"):
        await BFTLedgerActor(path).verify_chain(expected_checkpoint=checkpoint)
    if not reset_sequence:
        with pytest.raises(BFTCausalInvariantError, match="truncat"):
            await BFTLedgerActor(path).verify_chain()


def test_types_compatibility_import_is_already_fixed():
    from babylon60 import types
    from babylon60.c5_types import algebraic

    assert types.Ok is algebraic.Ok
    assert types.Err is algebraic.Err
    assert types.Ok(3).unwrap() == 3


@pytest.mark.asyncio
async def test_actor_concurrent_reads_use_consistent_snapshots(tmp_path):
    actor = BFTLedgerActor(tmp_path / "snapshot.db")
    await actor.start()

    async def write(i):
        return await actor.append(LedgerEvent("test", str(i), "created", {"i": i}, "test", "fixture", "events", str(i)))

    async def writer():
        for i in range(1, 49):
            await write(i)

    async def reader():
        for _ in range(24):
            assert await actor.verify_chain()

    try:
        await asyncio.wait_for(write(0), timeout=5)  # Warmup: schema and first committed row.
        await asyncio.wait_for(asyncio.gather(writer(), reader(), reader()), timeout=15)
        assert (await actor.get_checkpoint()).entries == 49
    finally:
        await asyncio.wait_for(actor.stop(), timeout=5)
