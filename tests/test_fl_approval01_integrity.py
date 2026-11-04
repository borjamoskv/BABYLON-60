"""FL-APPROVAL-01 isolated checks; software keys do not attest human judgment.

SimulationAuthorizationGate and its effects are confined to these tests. The
observed effect list/file is checked separately from journal return values.
"""

from __future__ import annotations

import base64
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
from threading import Barrier
import time

import pytest
from blake3 import blake3
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from nacl.signing import SigningKey

from babylon60.cortex.approval_integrity import ApprovalError, ApprovalJournal, digest
from babylon60.verification.verification_gate import RiskLevel, VerificationGate


REVIEWER = "isolated-reviewer"
POLICY = "test-policy-v1"
RATIONALE = blake3(b"isolated recommendation summary").hexdigest()


class SimulationAuthorizationGate:
    """An explicit test fixture, never installed at a production boundary."""

    def __init__(self, *, allowed=True):
        self.allowed = allowed
        self.calls = []

    def execute_once(self, task, effect):
        self.calls.append(copy.deepcopy(task))
        if not self.allowed:
            raise PermissionError("isolated authorization denied")
        return effect()


@pytest.fixture
def signing_key():
    return SigningKey.generate()


@pytest.fixture
def journal(tmp_path, signing_key):
    with ApprovalJournal(tmp_path / "approval.sqlite", {REVIEWER: bytes(signing_key.verify_key)}) as value:
        yield value


def create(journal, *, task_id="case-001", condition="B", evidence=None, **overrides):
    task = {"execution_id": task_id, "action": "test_config_change", "parameters": {"limit": 4}}
    proof = {"target": "isolated", "requested_limit": 4} if evidence is None else evidence
    arguments = {
        "task_id": task_id,
        "reviewer_id": REVIEWER,
        "task": task,
        "evidence": proof,
        "policy_version": POLICY,
        "condition": condition,
        "logical_tick": 1,
        "expires_tick": 20,
    }
    arguments.update(overrides)
    return journal.create_review(**arguments), task, proof


def precommit(journal, key, review_id, *, decision="APPROVE", tick=2):
    message = journal.precommit_message(review_id, decision, tick)
    return journal.record_precommit(review_id, decision, tick, key.sign(message).signature)


def finalize(journal, key, review_id, *, decision="APPROVE", tick=4, evidence="policy test evidence"):
    message = journal.final_message(review_id, decision, evidence, tick)
    return journal.record_final(review_id, decision, evidence, tick, key.sign(message).signature)


def complete(journal, key, *, condition="B", initial="APPROVE", final="APPROVE", **options):
    review_id, task, evidence = create(journal, condition=condition, **options)
    if condition == "B":
        precommit(journal, key, review_id, decision=initial)
    journal.record_recommendation(review_id, "APPROVE", RATIONALE, 3)
    finalize(journal, key, review_id, decision=final)
    return review_id, task, evidence


def verify(journal, review_id, task, evidence, **overrides):
    arguments = {"task": task, "evidence": evidence, "policy_version": POLICY, "logical_tick": 5}
    arguments.update(overrides)
    return journal.verify(review_id, **arguments)


def execute(journal, review_id, task, evidence, *, effect, gate=None, policy_allows=None, **overrides):
    arguments = {
        "task": task,
        "evidence": evidence,
        "policy_version": POLICY,
        "logical_tick": 5,
        "policy_allows": policy_allows if policy_allows is not None else lambda value: True,
        "authorization_gate": gate if gate is not None else SimulationAuthorizationGate(),
        "effect": effect,
    }
    arguments.update(overrides)
    return journal.execute_once(review_id, **arguments)


def test_b_requires_precommit_before_recommendation(journal, signing_key):
    review_id, task, evidence = create(journal)
    with pytest.raises(ApprovalError):
        journal.record_recommendation(review_id, "APPROVE", RATIONALE, 2)
    precommit(journal, signing_key, review_id)
    journal.record_recommendation(review_id, "APPROVE", RATIONALE, 3)
    finalize(journal, signing_key, review_id)
    assert isinstance(verify(journal, review_id, task, evidence), dict)


def test_a_records_recommendation_without_claiming_precommit(journal, signing_key):
    review_id, task, evidence = complete(journal, signing_key, condition="A")
    effects = []
    assert execute(journal, review_id, task, evidence, effect=lambda: effects.append(task["execution_id"])) is None
    assert effects == ["case-001"]


def test_change_of_mind_is_recordable_but_does_not_authorize_itself(journal, signing_key):
    review_id, task, evidence = complete(journal, signing_key, initial="REJECT", final="APPROVE")
    effects = []
    gate = SimulationAuthorizationGate(allowed=False)
    with pytest.raises((ApprovalError, PermissionError)):
        execute(journal, review_id, task, evidence, gate=gate, effect=lambda: effects.append("effect"))
    assert effects == []
    assert gate.calls == [task]


def test_signature_cannot_be_supplied_by_an_unpinned_key(journal, signing_key):
    review_id, _, _ = create(journal)
    message = journal.precommit_message(review_id, "APPROVE", 2)
    impostor = SigningKey.generate()
    with pytest.raises(ApprovalError):
        journal.record_precommit(review_id, "APPROVE", 2, impostor.sign(message).signature)
    precommit(journal, signing_key, review_id)


def test_signed_precommit_cannot_change_decision_or_review(journal, signing_key):
    first, _, _ = create(journal)
    other, _, _ = create(journal, task_id="case-other")
    signature = signing_key.sign(journal.precommit_message(first, "APPROVE", 2)).signature
    with pytest.raises(ApprovalError):
        journal.record_precommit(first, "REJECT", 2, signature)
    with pytest.raises(ApprovalError):
        journal.record_precommit(other, "APPROVE", 2, signature)
    journal.record_precommit(first, "APPROVE", 2, signature)


def test_final_signature_binds_final_decision_and_evidence(journal, signing_key):
    review_id, _, _ = create(journal)
    precommit(journal, signing_key, review_id)
    journal.record_recommendation(review_id, "APPROVE", RATIONALE, 3)
    signature = signing_key.sign(journal.final_message(review_id, "APPROVE", "source-1", 4)).signature
    for decision, evidence in [("REJECT", "source-1"), ("APPROVE", "source-2")]:
        with pytest.raises(ApprovalError):
            journal.record_final(review_id, decision, evidence, 4, signature)
    journal.record_final(review_id, "APPROVE", "source-1", 4, signature)


def test_duplicate_precommit_recommendation_and_final_are_rejected(journal, signing_key):
    review_id, _, _ = create(journal)
    precommit(journal, signing_key, review_id)
    with pytest.raises(ApprovalError):
        precommit(journal, signing_key, review_id, tick=3)
    journal.record_recommendation(review_id, "APPROVE", RATIONALE, 3)
    with pytest.raises(ApprovalError):
        journal.record_recommendation(review_id, "REJECT", RATIONALE, 4)
    finalize(journal, signing_key, review_id)
    with pytest.raises(ApprovalError):
        finalize(journal, signing_key, review_id, tick=5)


@pytest.mark.parametrize("tick", [0, 1, True, 20, 21])
def test_precommit_rejects_nonmonotonic_or_expired_ticks(journal, signing_key, tick):
    review_id, _, _ = create(journal)
    with pytest.raises(ApprovalError):
        precommit(journal, signing_key, review_id, tick=tick)


@pytest.mark.parametrize("decision", ["", "ALLOW", True, "approve"])
def test_decisions_use_closed_vocabulary(journal, decision):
    review_id, _, _ = create(journal)
    with pytest.raises(ApprovalError):
        journal.precommit_message(review_id, decision, 2)


@pytest.mark.parametrize("rationale", ["", "not-a-digest", "f" * 63, "g" * 64])
def test_recommendation_requires_valid_digest(journal, signing_key, rationale):
    review_id, _, _ = create(journal)
    precommit(journal, signing_key, review_id)
    with pytest.raises(ApprovalError):
        journal.record_recommendation(review_id, "APPROVE", rationale, 3)


def test_final_requires_recommendation_and_nonempty_evidence(journal, signing_key):
    review_id, _, _ = create(journal)
    precommit(journal, signing_key, review_id)
    with pytest.raises(ApprovalError):
        finalize(journal, signing_key, review_id)
    journal.record_recommendation(review_id, "APPROVE", RATIONALE, 3)
    with pytest.raises(ApprovalError):
        finalize(journal, signing_key, review_id, evidence="")


@pytest.mark.parametrize("change", ["task", "evidence", "policy", "expired", "before-final"])
def test_verification_binds_request_evidence_policy_and_validity(journal, signing_key, change):
    review_id, task, evidence = complete(journal, signing_key)
    options = {}
    if change == "task":
        task = {**task, "parameters": {"limit": 5}}
    elif change == "evidence":
        evidence = {**evidence, "requested_limit": 5}
    elif change == "policy":
        options["policy_version"] = "test-policy-v2"
    elif change == "expired":
        options["logical_tick"] = 20
    else:
        options["logical_tick"] = 3
    with pytest.raises(ApprovalError):
        verify(journal, review_id, task, evidence, **options)


def test_mutating_original_inputs_does_not_rebind_review(journal, signing_key):
    review_id, task, evidence = create(journal)
    original_task, original_evidence = copy.deepcopy(task), copy.deepcopy(evidence)
    task["parameters"]["limit"] = 99
    evidence["requested_limit"] = 99
    precommit(journal, signing_key, review_id)
    journal.record_recommendation(review_id, "APPROVE", RATIONALE, 3)
    finalize(journal, signing_key, review_id)
    with pytest.raises(ApprovalError):
        verify(journal, review_id, task, evidence)
    assert isinstance(verify(journal, review_id, original_task, original_evidence), dict)


@pytest.mark.parametrize("policy_result", [False, None, 1, "APPROVE"])
def test_policy_must_explicitly_allow_before_effect(journal, signing_key, policy_result):
    review_id, task, evidence = complete(journal, signing_key)
    effects = []
    gate = SimulationAuthorizationGate()
    with pytest.raises((ApprovalError, PermissionError)):
        execute(
            journal, review_id, task, evidence, gate=gate,
            policy_allows=lambda value: policy_result, effect=lambda: effects.append("effect"),
        )
    assert effects == []
    assert gate.calls == []


def test_final_rejection_never_reaches_authorization_gate(journal, signing_key):
    review_id, task, evidence = complete(journal, signing_key, final="REJECT")
    effects = []
    gate = SimulationAuthorizationGate()
    with pytest.raises((ApprovalError, PermissionError)):
        execute(journal, review_id, task, evidence, gate=gate, effect=lambda: effects.append("effect"))
    assert effects == []
    assert gate.calls == []


def test_success_is_single_use_and_returns_actual_effect_result(journal, signing_key):
    review_id, task, evidence = complete(journal, signing_key)
    effects = []
    gate = SimulationAuthorizationGate()

    def observed_effect():
        effects.append("observed")
        return "actual-result"

    assert execute(journal, review_id, task, evidence, gate=gate, effect=observed_effect) == "actual-result"
    with pytest.raises(ApprovalError):
        execute(journal, review_id, task, evidence, gate=gate, effect=observed_effect)
    assert effects == ["observed"]
    assert gate.calls == [task]


def test_callback_exception_does_not_restore_consumed_review(journal, signing_key):
    review_id, task, evidence = complete(journal, signing_key)
    effects = []

    def partial_effect():
        effects.append("partial-effect")
        raise RuntimeError("isolated callback failure")

    with pytest.raises(RuntimeError, match="isolated callback failure"):
        execute(journal, review_id, task, evidence, effect=partial_effect)
    with pytest.raises(ApprovalError):
        execute(journal, review_id, task, evidence, effect=partial_effect)
    assert effects == ["partial-effect"]


def test_consumption_survives_close_and_reopen(tmp_path, signing_key):
    path = tmp_path / "durable.sqlite"
    keys = {REVIEWER: bytes(signing_key.verify_key)}
    effects = []
    with ApprovalJournal(path, keys) as journal:
        review_id, task, evidence = complete(journal, signing_key)
        execute(journal, review_id, task, evidence, effect=lambda: effects.append("effect"))
    with ApprovalJournal(path, keys) as reopened:
        with pytest.raises(ApprovalError):
            execute(reopened, review_id, task, evidence, effect=lambda: effects.append("replayed"))
    assert effects == ["effect"]


def test_reopening_under_replaced_reviewer_key_rejects_history(tmp_path, signing_key):
    path = tmp_path / "replaced-key.sqlite"
    with ApprovalJournal(path, {REVIEWER: bytes(signing_key.verify_key)}) as journal:
        review_id, task, evidence = complete(journal, signing_key)
    other = SigningKey.generate()
    with ApprovalJournal(path, {REVIEWER: bytes(other.verify_key)}) as reopened:
        with pytest.raises(ApprovalError):
            verify(reopened, review_id, task, evidence)


def test_consumption_survives_process_death_after_observed_effect(tmp_path, signing_key):
    path = tmp_path / "crash.sqlite"
    observation = tmp_path / "observed-before-crash.txt"
    keys = {REVIEWER: bytes(signing_key.verify_key)}
    with ApprovalJournal(path, keys) as journal:
        review_id, task, evidence = complete(journal, signing_key)
    isolated_script = """
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, sys.argv[1])
from babylon60.cortex.approval_integrity import ApprovalJournal

class IsolatedGate:
    def execute_once(self, task, effect):
        return effect()

def observed_effect():
    with Path(sys.argv[4]).open("w", encoding="utf-8") as stream:
        stream.write("observed")
        stream.flush()
        os.fsync(stream.fileno())
    os._exit(23)

with ApprovalJournal(sys.argv[2], {"isolated-reviewer": bytes.fromhex(sys.argv[5])}) as journal:
    journal.execute_once(
        sys.argv[3], task=json.loads(sys.argv[6]), evidence=json.loads(sys.argv[7]),
        policy_version="test-policy-v1", logical_tick=5,
        policy_allows=lambda task: True, authorization_gate=IsolatedGate(), effect=observed_effect,
    )
"""
    result = subprocess.run(
        [sys.executable, "-c", isolated_script, str(Path(__file__).parents[1] / "01_KISH_ENGINE"),
         str(path), review_id, str(observation), bytes(signing_key.verify_key).hex(),
         json.dumps(task), json.dumps(evidence)],
        check=False, capture_output=True, timeout=20,
    )
    assert result.returncode == 23, result.stderr.decode()
    assert observation.read_text(encoding="utf-8") == "observed"
    with ApprovalJournal(path, keys) as reopened:
        gate = SimulationAuthorizationGate()
        with pytest.raises(ApprovalError):
            execute(reopened, review_id, task, evidence, gate=gate, effect=lambda: observation.write_text("replayed"))
        assert gate.calls == []
    assert observation.read_text(encoding="utf-8") == "observed"


def test_file_backed_journal_enables_durable_wal_and_append_only_tables(journal, signing_key):
    review_id, _, _ = complete(journal, signing_key)
    assert journal._conn.execute("PRAGMA journal_mode").fetchone() == ("wal",)
    assert journal._conn.execute("PRAGMA synchronous").fetchone() == (2,)
    with pytest.raises(sqlite3.IntegrityError):
        journal._conn.execute("DELETE FROM fl_approval_events WHERE review_id=?", (review_id,))
    with pytest.raises(sqlite3.IntegrityError):
        journal._conn.execute("UPDATE fl_approval_reviews SET body='{}' WHERE id=?", (review_id,))


@pytest.mark.parametrize("ordinal", [1, 2, 3])
def test_rehashed_event_tampering_does_not_defeat_signed_history(journal, signing_key, ordinal):
    review_id, task, evidence = complete(journal, signing_key)
    body_json, signature = journal._conn.execute(
        "SELECT body, signature FROM fl_approval_events WHERE review_id=? AND ordinal=?", (review_id, ordinal),
    ).fetchone()
    body = json.loads(body_json)
    if ordinal == 1:
        body["data"]["decision"] = "REJECT"
    elif ordinal == 2:
        body["data"]["recommendation"] = "REJECT"
    else:
        body["data"]["decision_evidence"] = "rewritten evidence"
    recomputed = digest({"body": body, "signature": signature})
    # Database-owner tampering is outside the service boundary; bypassing the
    # SQL trigger here proves signed-content verification is a separate check.
    journal._conn.execute("DROP TRIGGER fl_approval_events_no_update")
    journal._conn.execute(
        "UPDATE fl_approval_events SET body=?, digest=? WHERE review_id=? AND ordinal=?",
        (json.dumps(body), recomputed, review_id, ordinal),
    )
    with pytest.raises(ApprovalError):
        verify(journal, review_id, task, evidence)


@pytest.mark.parametrize("tamper", ["signature", "digest", "ordinal", "delete-final", "review"])
def test_corrupt_or_incomplete_persisted_history_is_rejected(journal, signing_key, tamper):
    review_id, task, evidence = complete(journal, signing_key)
    if tamper == "review":
        journal._conn.execute("DROP TRIGGER fl_approval_reviews_no_update")
        journal._conn.execute("UPDATE fl_approval_reviews SET body='{}' WHERE id=?", (review_id,))
    elif tamper == "delete-final":
        journal._conn.execute("DROP TRIGGER fl_approval_events_no_delete")
        journal._conn.execute("DELETE FROM fl_approval_events WHERE review_id=? AND ordinal=3", (review_id,))
    else:
        journal._conn.execute("DROP TRIGGER fl_approval_events_no_update")
        assignments = {"signature": "signature='00'", "digest": "digest='00'", "ordinal": "ordinal=9"}
        journal._conn.execute(
            "UPDATE fl_approval_events SET " + assignments[tamper] + " WHERE review_id=? AND ordinal=3", (review_id,),
        )
    with pytest.raises(ApprovalError):
        verify(journal, review_id, task, evidence)


def test_logical_history_hashes_are_reproducible_across_databases(tmp_path, signing_key):
    results = []
    for index in range(2):
        with ApprovalJournal(tmp_path / f"deterministic-{index}.sqlite", {REVIEWER: bytes(signing_key.verify_key)}) as journal:
            review_id, _, _ = complete(journal, signing_key)
            results.append((review_id, journal._conn.execute(
                "SELECT digest FROM fl_approval_events WHERE review_id=? ORDER BY ordinal", (review_id,),
            ).fetchall()))
    assert results[0] == results[1]


def test_two_connections_cannot_commit_the_same_review(tmp_path, signing_key):
    path = tmp_path / "racing.sqlite"
    keys = {REVIEWER: bytes(signing_key.verify_key)}
    with ApprovalJournal(path, keys) as journal:
        review_id, task, evidence = complete(journal, signing_key)
    barrier = Barrier(2)
    effects = []

    def contender():
        with ApprovalJournal(path, keys) as journal:
            barrier.wait(timeout=10)
            try:
                execute(journal, review_id, task, evidence, effect=lambda: effects.append("effect"))
                return "executed"
            except ApprovalError:
                return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: contender(), range(2)))
    assert sorted(results) == ["executed", "rejected"]
    assert effects == ["effect"]


def test_200_isolated_reviews_observe_no_policy_prohibited_effects(tmp_path, signing_key):
    """Warmup + 200 cases exercises containment, never psychological efficacy."""
    path = tmp_path / "campaign.sqlite"
    observation_path = tmp_path / "observed-effects.txt"
    keys = {REVIEWER: bytes(signing_key.verify_key)}
    expected = []
    with ApprovalJournal(path, keys) as journal:
        for index in range(8):
            review_id, task, evidence = complete(journal, signing_key, task_id=f"warmup-{index}")
            execute(journal, review_id, task, evidence, effect=lambda: None)
        for index in range(200):
            allowed = index % 2 == 0
            review_id, task, evidence = complete(
                journal, signing_key, task_id=f"trial-{index:03}", condition="A" if index % 4 < 2 else "B",
            )
            gate = SimulationAuthorizationGate(allowed=index % 5 != 0)

            def observe(task_id=task["execution_id"]):
                with observation_path.open("a", encoding="utf-8") as stream:
                    stream.write(task_id + "\n")

            if allowed and gate.allowed:
                execute(journal, review_id, task, evidence, gate=gate, policy_allows=lambda value: True, effect=observe)
                expected.append(task["execution_id"])
            else:
                with pytest.raises((ApprovalError, PermissionError)):
                    execute(
                        journal, review_id, task, evidence, gate=gate,
                        policy_allows=lambda value, permitted=allowed: permitted, effect=observe,
                    )
    observed = observation_path.read_text(encoding="utf-8").splitlines()
    assert observed == expected
    assert len(observed) == 80
    assert all(int(value.removeprefix("trial-")) % 2 == 0 for value in observed)


@pytest.fixture
def isolated_p256_key(monkeypatch):
    """Software-only authority for temporary gate databases; never hardware."""
    key = ec.generate_private_key(ec.SECP256R1())
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    monkeypatch.setenv("BABYLON_ENCLAVE_PINNED_PUBKEY", public.hex())
    return key


def insert_software_signed_approval(gate, task, key):
    """Provision a software fixture directly without invoking a biometric helper.

    Its signature proves possession of this ephemeral software key. The legacy
    evidence field names are required by the existing verifier and do not make
    this fixture a Secure Enclave attestation.
    """
    now = time.time()
    proof = json.dumps(
        {"version": 1, "task": task, "decision": "APPROVED", "nonce": secrets.token_hex(32),
         "issued_at": now - 1, "expires_at": now + 299},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    )
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    payload = proof.encode("utf-8")
    evidence = json.dumps({
        "status": "ATTESTED",
        "causal_hash": hashlib.sha256(payload).hexdigest(),
        "public_key": base64.b64encode(public).decode(),
        "secure_enclave_signature": base64.b64encode(key.sign(payload, ec.ECDSA(hashes.SHA256()))).decode(),
    })
    gate.register_sign_off(task["execution_id"], task["action"], RiskLevel.CRITICAL, "APPROVED")
    ledger_id = gate._conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    with gate._conn:
        gate._conn.execute("INSERT INTO signed_approvals VALUES (?, ?, ?)", (ledger_id, proof, evidence))


def test_real_verification_gate_without_authority_denies_signed_review(
    journal, signing_key, tmp_path, monkeypatch,
):
    monkeypatch.delenv("BABYLON_ENCLAVE_PINNED_PUBKEY", raising=False)
    review_id, task, evidence = complete(journal, signing_key)
    observation = tmp_path / "must-not-exist.txt"
    gate = VerificationGate(str(tmp_path / "no-authority.sqlite"))
    try:
        with pytest.raises(PermissionError):
            execute(journal, review_id, task, evidence, gate=gate, effect=lambda: observation.write_text("effect"))
        assert not observation.exists()
        with pytest.raises(ApprovalError):
            verify(journal, review_id, task, evidence)
    finally:
        gate._conn.close()


def test_real_verification_gate_executes_once_with_isolated_software_proof(
    journal, signing_key, tmp_path, isolated_p256_key,
):
    review_id, task, evidence = complete(journal, signing_key)
    observation = tmp_path / "observed-real-gate-effect.txt"
    gate = VerificationGate(str(tmp_path / "software-authority.sqlite"))
    try:
        insert_software_signed_approval(gate, task, isolated_p256_key)
        assert gate.is_allowed(task)
        assert execute(
            journal, review_id, task, evidence, gate=gate, effect=lambda: observation.write_text("observed"),
        ) == len("observed")
        assert observation.read_text() == "observed"
        with pytest.raises(ApprovalError):
            execute(journal, review_id, task, evidence, gate=gate, effect=lambda: observation.write_text("replayed"))
        with pytest.raises(PermissionError):
            gate.execute_once(task, lambda: observation.write_text("direct replay"))
        assert observation.read_text() == "observed"
    finally:
        gate._conn.close()


def test_policy_denial_blocks_real_gate_despite_valid_software_signed_approval(
    journal, signing_key, tmp_path, isolated_p256_key,
):
    review_id, task, evidence = complete(journal, signing_key)
    observation = tmp_path / "policy-denied-effect.txt"
    gate = VerificationGate(str(tmp_path / "policy-denial.sqlite"))
    try:
        insert_software_signed_approval(gate, task, isolated_p256_key)
        assert gate.is_allowed(task)
        with pytest.raises(ApprovalError):
            execute(
                journal, review_id, task, evidence, gate=gate,
                policy_allows=lambda actual: False, effect=lambda: observation.write_text("forbidden"),
            )
        assert not observation.exists()
        assert gate.is_allowed(task)
        assert gate._conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name='consumed_mcp_effects'",
        ).fetchone() == (0,)
    finally:
        gate._conn.close()


def test_real_gate_rejects_software_approval_for_different_task_parameters(
    journal, signing_key, tmp_path, isolated_p256_key,
):
    review_id, task, evidence = complete(journal, signing_key)
    observation = tmp_path / "mismatched-effect.txt"
    gate = VerificationGate(str(tmp_path / "mismatched-authority.sqlite"))
    try:
        signed_task = {**task, "parameters": {"limit": 99}}
        insert_software_signed_approval(gate, signed_task, isolated_p256_key)
        assert gate.is_allowed(signed_task)
        assert not gate.is_allowed(task)
        with pytest.raises(PermissionError):
            execute(journal, review_id, task, evidence, gate=gate, effect=lambda: observation.write_text("forbidden"))
        assert not observation.exists()
    finally:
        gate._conn.close()
