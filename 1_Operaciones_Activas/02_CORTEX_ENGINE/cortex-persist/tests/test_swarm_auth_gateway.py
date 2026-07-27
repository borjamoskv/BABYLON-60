import sqlite3
import pytest
import json
from unittest.mock import MagicMock, patch
from babylon60.swarm.auth_gateway import QuorumGateway

@pytest.fixture
def mock_engine():
    engine = MagicMock()
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    engine.pool.get_connection.return_value = conn
    return engine

@pytest.mark.asyncio
async def test_submit_vote_verify_fails(mock_engine):
    mock_engine.pool.get_connection().cursor().fetchone.return_value = ("PENDING", "{}", "[]")
    gateway = QuorumGateway(mock_engine)

    with patch("babylon60.extensions.security.signatures.Ed25519Signer") as MockSigner, \
         patch("babylon60.extensions.security.signatures.SignatureVerificationError", ValueError):
        instance = MockSigner.return_value
        # Force a failure (simulated by exception)
        instance.verify.side_effect = ValueError("Invalid sig")
        result = await gateway.submit_vote("QRM-123", "sig", "pub", semantic_truth=True)
        assert result is False

@pytest.mark.asyncio
async def test_submit_vote_double_vote(mock_engine):
    mock_engine.pool.get_connection().cursor().fetchone.return_value = (
        "PENDING",
        "{}",
        json.dumps([{"public_key": "pub123", "signature": "sig123"}])
    )
    gateway = QuorumGateway(mock_engine)

    with patch("babylon60.extensions.security.signatures.Ed25519Signer") as MockSigner, \
         patch("babylon60.extensions.security.signatures.SignatureVerificationError", ValueError):
        instance = MockSigner.return_value
        instance.verify.return_value = True

        result = await gateway.submit_vote("QRM-123", "sig123", "pub123", semantic_truth=True)
        assert result is False

@pytest.mark.asyncio
async def test_submit_vote_success_not_quorum(mock_engine):
    mock_engine.pool.get_connection().cursor().fetchone.return_value = (
        "PENDING", "{}", "[]"
    )
    gateway = QuorumGateway(mock_engine, n_nodes=4, f_nodes=1) # threshold = 3

    with patch("babylon60.extensions.security.signatures.Ed25519Signer") as MockSigner, \
         patch("babylon60.extensions.security.signatures.SignatureVerificationError", ValueError):
        instance = MockSigner.return_value
        instance.verify.return_value = True

        result = await gateway.submit_vote("QRM-123", "sig", "pub", semantic_truth=True)
        assert result is True
        # verify UPDATE query was called for single vote
        calls = mock_engine.pool.get_connection().execute.call_args_list
        assert "SET signatures_json = ?" in calls[0][0][0]

@pytest.mark.asyncio
async def test_submit_vote_success_quorum_reached(mock_engine):
    existing_sigs = [{"public_key": f"pub{i}", "signature": f"sig{i}"} for i in range(2)]

    mock_engine.pool.get_connection().cursor().fetchone.return_value = (
        "PENDING", "{}", json.dumps(existing_sigs)
    )
    gateway = QuorumGateway(mock_engine, n_nodes=4, f_nodes=1) # threshold = 3

    with patch("babylon60.extensions.security.signatures.Ed25519Signer") as MockSigner, \
         patch("babylon60.extensions.security.signatures.SignatureVerificationError", ValueError):
        instance = MockSigner.return_value
        instance.verify.return_value = True

        result = await gateway.submit_vote("QRM-123", "sig3", "pub3", semantic_truth=True)
        assert result is True
        calls = mock_engine.pool.get_connection().execute.call_args_list
        assert "SET status = 'QUORUM_REACHED'" in calls[0][0][0]

@pytest.mark.asyncio
async def test_submit_vote_db_error(mock_engine):
    mock_engine.pool.get_connection().cursor().fetchone.side_effect = sqlite3.Error("DB err")
    gateway = QuorumGateway(mock_engine)
    result = await gateway.submit_vote("QRM-123", "sig", "pub", semantic_truth=True)
    assert result is False

@pytest.mark.asyncio
async def test_reject_request(mock_engine):
    gateway = QuorumGateway(mock_engine)
    result = await gateway.reject_request("QRM-123")
    assert result is True
    mock_engine.pool.get_connection().execute.assert_called_once()
    mock_engine.pool.get_connection().commit.assert_called_once()

@pytest.mark.asyncio
async def test_reject_request_error(mock_engine):
    mock_engine.pool.get_connection().execute.side_effect = sqlite3.Error("Reject err")
    gateway = QuorumGateway(mock_engine)
    result = await gateway.reject_request("QRM-123")
    assert result is False

@pytest.mark.asyncio
async def test_check_timeout_not_found(mock_engine):
    mock_engine.pool.get_connection().cursor().fetchone.return_value = None
    gateway = QuorumGateway(mock_engine)
    result = await gateway.check_timeout("QRM-123", 10.0)
    assert result is False

@pytest.mark.asyncio
async def test_check_timeout_expired(mock_engine):
    import time
    past_time = time.monotonic() - 20.0
    mock_engine.pool.get_connection().cursor().fetchone.return_value = ("PENDING", past_time)
    gateway = QuorumGateway(mock_engine)
    result = await gateway.check_timeout("QRM-123", 10.0)
    assert result is True
    mock_engine.pool.get_connection().commit.assert_called_once()

@pytest.mark.asyncio
async def test_check_timeout_not_expired(mock_engine):
    import time
    past_time = time.monotonic() - 5.0
    mock_engine.pool.get_connection().cursor().fetchone.return_value = ("PENDING", past_time)
    gateway = QuorumGateway(mock_engine)
    result = await gateway.check_timeout("QRM-123", 10.0)
    assert result is False

@pytest.mark.asyncio
async def test_check_timeout_already_resolved(mock_engine):
    import time
    past_time = time.monotonic() - 20.0
    mock_engine.pool.get_connection().cursor().fetchone.return_value = ("QUORUM_REACHED", past_time)
    gateway = QuorumGateway(mock_engine)
    result = await gateway.check_timeout("QRM-123", 10.0)
    assert result is False

@pytest.mark.asyncio
async def test_check_timeout_error(mock_engine):
    mock_engine.pool.get_connection().cursor().fetchone.side_effect = sqlite3.Error("Timeout err")
    gateway = QuorumGateway(mock_engine)
    result = await gateway.check_timeout("QRM-123", 10.0)
    assert result is False
