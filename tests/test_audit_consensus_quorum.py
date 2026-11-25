"""Regressions for invalid Byzantine fault budgets; software keys are test-only."""

from pathlib import Path

import pytest

from babylon60.bft.consensus_ledger import BFT_Ledger, StateMutation
from babylon60.bft.consensus_validator import BFT_Validator
from babylon60.core.crypto_utils import Ed25519Signer, canonicalize_cbor, hash_sha3_256


@pytest.mark.parametrize("f", [-1, -100, True, False, 0.0, 1.5, "0", None])
def test_invalid_fault_budget_is_rejected_before_commit(tmp_path: Path, f: int) -> None:
    ledger = BFT_Ledger(str(tmp_path / "ledger.db"))
    mutation = StateMutation("test", {"op": "advance"}, 0.0, "")
    try:
        with pytest.raises(ValueError, match="non-negative integer"):
            ledger.invoke_subagent(mutation, f, {})
        assert ledger.conn.execute("SELECT COUNT(*) FROM state_log").fetchone()[0] == 0
    finally:
        ledger.conn.close()


def test_insufficient_population_cannot_claim_fault_tolerance() -> None:
    signers = {str(i): Ed25519Signer() for i in range(3)}
    validator = BFT_Validator({node: signer.public_key_hex for node, signer in signers.items()})
    payload = {"op": "advance"}
    digest = hash_sha3_256(canonicalize_cbor(payload))
    votes = {node: signer.sign(digest) for node, signer in signers.items()}
    with pytest.raises(PermissionError, match="population"):
        validator.validate_votes(payload, 1, votes)


@pytest.mark.parametrize(("f", "population", "quorum"), [(0, 1, 1), (1, 4, 3), (1, 5, 4), (2, 7, 5)])
def test_real_quorum_and_one_vote_short(tmp_path: Path, f: int, population: int, quorum: int) -> None:
    signers = {str(i): Ed25519Signer() for i in range(population)}
    ledger = BFT_Ledger(str(tmp_path / "ledger.db"), {n: s.public_key_hex for n, s in signers.items()})
    mutation = StateMutation("test", {"op": "advance"}, 0.0, "")
    digest = mutation.signing_hash(f)
    votes = {node: signer.sign(digest) for node, signer in list(signers.items())[:quorum]}
    try:
        with pytest.raises(PermissionError, match="BFT_CONSENSUS_FAILURE"):
            ledger.invoke_subagent(mutation, f, dict(list(votes.items())[:-1]))
        assert ledger.conn.execute("SELECT COUNT(*) FROM state_log").fetchone()[0] == 0
        assert ledger.invoke_subagent(mutation, f, votes)
        assert ledger.conn.execute("SELECT COUNT(*) FROM state_log").fetchone()[0] == 1
        assert ledger.audit_integrity()
    finally:
        ledger.conn.close()
