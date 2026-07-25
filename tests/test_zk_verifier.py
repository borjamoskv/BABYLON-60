from pathlib import Path

import pytest

from babylon60.bft.ledger_actor import BFTLedgerActor
from babylon60.crypto.zk_verifier import NULZKVerifier, ZKVerificationError, verify_nul_zk_proof, verify_zk_attestation


@pytest.fixture
def example_circuit_path() -> Path:
    return Path(__file__).resolve().parents[1] / "proof_kernel" / "NUL-ZK" / "example.nul"


def test_zk_verifier_success(example_circuit_path: Path):
    attestation = {
        "circuit_file": str(example_circuit_path),
        "public_inputs": {"c": 6},
        "private_inputs": {"a": 2, "b": 3},
    }
    assert verify_zk_attestation(attestation) is True


def test_zk_verifier_assertion_failure(example_circuit_path: Path):
    attestation = {
        "circuit_file": str(example_circuit_path),
        "public_inputs": {"c": 7},
        "private_inputs": {"a": 2, "b": 3},
    }
    assert verify_zk_attestation(attestation) is False


def test_inv_c5_18_float_rejection(example_circuit_path: Path):
    # Float in public_inputs
    attestation = {
        "circuit_file": str(example_circuit_path),
        "public_inputs": {"c": 6.0},
        "private_inputs": {"a": 2, "b": 3},
    }
    with pytest.raises(ValueError, match="Flotantes"):
        verify_zk_attestation(attestation)


def test_inv_c5_18_float_rejection_nested(example_circuit_path: Path):
    # Float in nested field
    attestation = {
        "circuit_file": str(example_circuit_path),
        "public_inputs": {"c": 6},
        "private_inputs": {"a": 2, "b": 3},
        "metadata": {"weight": 1.5},
    }
    with pytest.raises(ValueError, match="Flotantes"):
        verify_zk_attestation(attestation)


def test_inv_c5_33_safe_subprocess(example_circuit_path: Path, monkeypatch: pytest.MonkeyPatch):
    verifier = NULZKVerifier()
    bin_path = verifier.find_nul_zk_binary()
    assert bin_path.exists()
    assert bin_path.is_file()

    # Test that compile_circuit returns valid IR without shell=True
    ir = verifier.compile_circuit(example_circuit_path)
    assert ir["name"] == "Multiplier"
    assert "gates" in ir


@pytest.mark.asyncio
async def test_bft_ledger_actor_zk_verification(tmp_path: Path, example_circuit_path: Path):
    actor = BFTLedgerActor(tmp_path / "test_zk.db")
    attestation = {
        "circuit_file": str(example_circuit_path),
        "public_inputs": {"c": 6},
        "private_inputs": {"a": 2, "b": 3},
    }
    res = await actor.verify_zk_attestation(attestation)
    assert res is True
