import pytest
from unittest.mock import patch, MagicMock

from babylon60.swarm.gatekeeper import ZeroKnowledgeGatekeeper, SecurityViolationError

@pytest.fixture
def mock_km():
    km = MagicMock()
    return km

@pytest.fixture
def gatekeeper(mock_km):
    return ZeroKnowledgeGatekeeper(km=mock_km)

def test_incomplete_proof_raises_error(gatekeeper):
    proof = {
        "judge_id": "test_judge",
        # missing ast_code
    }

    with pytest.raises(SecurityViolationError, match="Incomplete Consensus Proof"):
        gatekeeper.execute_consensus(proof)

def test_unknown_judge_raises_error(gatekeeper, mock_km):
    mock_km.get_public_key_b64.return_value = None
    proof = {
        "judge_id": "test_judge",
        "ast_code": "print('hello')",
        "consensus_timestamp": "12345",
        "consensus_signature_b64": "dummy_sig"
    }

    with pytest.raises(SecurityViolationError, match="Unknown Judge test_judge"):
        gatekeeper.execute_consensus(proof)

@patch("babylon60.swarm.gatekeeper.Verifier")
def test_forged_signature_raises_error(mock_verifier, gatekeeper, mock_km):
    mock_km.get_public_key_b64.return_value = "dummy_pub"
    mock_verifier.verify_signature.return_value = False

    proof = {
        "judge_id": "test_judge",
        "ast_code": "print('hello')",
        "consensus_timestamp": "12345",
        "consensus_signature_b64": "dummy_sig"
    }

    with pytest.raises(SecurityViolationError, match="Cryptographic forgery detected"):
        gatekeeper.execute_consensus(proof)

@patch("babylon60.swarm.gatekeeper.Verifier")
def test_valid_execution_dry_run(mock_verifier, gatekeeper, mock_km):
    mock_km.get_public_key_b64.return_value = "dummy_pub"
    mock_verifier.verify_signature.return_value = True

    proof = {
        "judge_id": "test_judge",
        "ast_code": "print('hello')",
        "consensus_timestamp": "12345",
        "consensus_signature_b64": "dummy_sig"
    }

    result = gatekeeper.execute_consensus(proof, dry_run=True)
    assert result is True

@patch("babylon60.swarm.gatekeeper.Verifier")
def test_valid_execution_compiles(mock_verifier, gatekeeper, mock_km):
    mock_km.get_public_key_b64.return_value = "dummy_pub"
    mock_verifier.verify_signature.return_value = True

    proof = {
        "judge_id": "test_judge",
        "ast_code": "x = 10\nprint(x)",
        "consensus_timestamp": "12345",
        "consensus_signature_b64": "dummy_sig"
    }

    result = gatekeeper.execute_consensus(proof, dry_run=False)
    assert result is True
