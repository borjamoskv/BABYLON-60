"""Regressions for trusted audit keys and idempotent writes with independent quorums."""

import json
import multiprocessing
import sqlite3
import subprocess
import sys

import pytest

from babylon60.bft.consensus_ledger import BFT_Ledger, StateMutation
from babylon60.core.crypto_utils import Ed25519Signer


@pytest.fixture
def signed_ledger(tmp_path, request):
    path = tmp_path / "ledger.db"
    signers = {str(i): Ed25519Signer() for i in range(4)}
    keys = {node: signer.public_key_hex for node, signer in signers.items()}
    mutation = StateMutation("agent", {"operation": "advance"}, 1.0, "")
    votes = {node: signer.sign(mutation.signing_hash(1)) for node, signer in signers.items()}
    ledger = BFT_Ledger(str(path), keys)
    try:
        original_size = getattr(request, "param", 3)
        assert ledger.invoke_subagent(mutation, 1, dict(list(votes.items())[:original_size]))
    finally:
        ledger.close()
    return path, keys, mutation, votes


def _retry_with_three_signers(path, keys, mutation, votes):
    ledger = BFT_Ledger(str(path), keys)
    try:
        other_quorum = dict(list(votes.items())[1:])
        assert ledger.invoke_subagent(mutation, 1, other_quorum)
        with pytest.raises(PermissionError):
            ledger.invoke_subagent(mutation, 1, dict(list(other_quorum.items())[:2]))
    finally:
        ledger.close()


@pytest.mark.parametrize("signed_ledger", [3, 4], indirect=True, ids=["different-three", "four-to-three"])
def test_retry_with_another_quorum_preserves_one_original_row(signed_ledger):
    path, keys, mutation, votes = signed_ledger
    ledger = BFT_Ledger(str(path), keys)
    try:
        original = ledger.conn.execute("SELECT * FROM state_log").fetchone()
        checkpoint = ledger.get_checkpoint()
    finally:
        ledger.close()
    with multiprocessing.get_context("spawn").Pool(1) as worker:
        worker.apply_async(_retry_with_three_signers, (path, keys, mutation, votes)).get(timeout=20)
    reopened = BFT_Ledger(str(path), keys)
    try:
        assert reopened.conn.execute("SELECT * FROM state_log").fetchall() == [original]
        assert reopened.get_checkpoint() == checkpoint
        assert checkpoint.entries == 1
    finally:
        reopened.close()


def test_alternate_quorum_cannot_acknowledge_unverifiable_stored_votes(signed_ledger):
    path, keys, mutation, votes = signed_ledger
    # The first quorum included node 0. Its replacement key invalidates that
    # certificate, even though nodes 1, 2 and 3 can still form a valid quorum.
    rotated = {**keys, "0": Ed25519Signer().public_key_hex}
    ledger = BFT_Ledger(str(path), rotated)
    try:
        original = ledger.conn.execute("SELECT * FROM state_log").fetchone()
        with pytest.raises(ValueError, match="Collision"):
            ledger.invoke_subagent(mutation, 1, dict(list(votes.items())[1:]))
        assert ledger.conn.execute("SELECT * FROM state_log").fetchall() == [original]
    finally:
        ledger.close()


def test_audit_cli_uses_trusted_keys_and_distinguishes_configuration(signed_ledger, tmp_path, monkeypatch):
    monkeypatch.setenv("BABYLON_HOME", str(tmp_path))
    path, keys, _, _ = signed_ledger
    registry = tmp_path / "committee.json"
    cmd = [sys.executable, "-m", "babylon60.bft.consensus_ledger", "--audit-mode", "--db", str(path)]
    missing = subprocess.run(cmd, capture_output=True, text=True)
    assert missing.returncode == 2
    assert "--node-keys" in missing.stderr
    for data in ("{}", "[]", "{", '{"node": "abcd"}'):
        registry.write_text(data, encoding="utf-8")
        invalid = subprocess.run([*cmd, "--node-keys", str(registry)], capture_output=True, text=True)
        assert invalid.returncode == 2
        assert "--node-keys" in invalid.stderr
    registry.write_text(json.dumps(keys), encoding="utf-8")
    audit = [*cmd, "--node-keys", str(registry)]
    # A standalone audit reads a snapshot even while the writer owns the ledger.
    writer = BFT_Ledger(str(path), keys)
    try:
        result = subprocess.run(audit, capture_output=True, text=True)
    finally:
        writer.close()
    assert result.returncode == 0, result.stderr
    assert "Verified" in result.stdout
    with sqlite3.connect(path) as db:
        db.execute("UPDATE state_log SET ts = ts + 1")
    failed = subprocess.run(audit, capture_output=True, text=True)
    assert failed.returncode == 1
    assert "Audit failed" in failed.stdout


def test_audit_missing_default_ledger_leaves_directory_absent(tmp_path, monkeypatch):
    home = tmp_path / "uninitialized"
    monkeypatch.setenv("BABYLON_HOME", str(home))
    registry = tmp_path / "committee.json"
    registry.write_text(json.dumps({"node": Ed25519Signer().public_key_hex}), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "babylon60.bft.consensus_ledger", "--audit-mode", "--node-keys", str(registry)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Audit failed" in result.stderr
    assert not home.exists()


@pytest.mark.parametrize("option", ["--db", "--node-keys"])
def test_audit_options_without_mode_never_initialize_a_ledger(tmp_path, monkeypatch, option):
    home = tmp_path / "uninitialized"
    monkeypatch.setenv("BABYLON_HOME", str(home))
    target = tmp_path / "missing"
    result = subprocess.run(
        [sys.executable, "-m", "babylon60.bft.consensus_ledger", option, str(target)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "--audit-mode" in result.stderr
    assert not home.exists()
    assert not target.exists()
