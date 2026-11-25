# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))

from babylon60.verifiable_inference import checksum_matches, generate_proof, verify_payload


def test_verifiable_inference_valid() -> None:
    payload = b"Syntactic Hologram Hypothesis #42"
    nonce = 1337
    proof = generate_proof(payload, nonce)

    # C0201/C0202: un SHA256 que cualquiera puede calcular no certifica inferencia.
    assert verify_payload(payload, nonce, proof) is False
    assert checksum_matches(payload, nonce, proof) is True


def test_verifiable_inference_invalid() -> None:
    payload = b"Syntactic Hologram Hypothesis #42"
    nonce = 1337
    invalid_proof = b"deadbeef_invalid_hash_proof_00000000000000000000000000000000"

    assert verify_payload(payload, nonce, invalid_proof) is False
    assert checksum_matches(payload, nonce, invalid_proof) is False
