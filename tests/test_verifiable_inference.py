# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))

from babylon60.verifiable_inference import verify_payload, generate_proof


def test_verifiable_inference_valid():
    payload = b"Syntactic Hologram Hypothesis #42"
    nonce = 1337
    proof = generate_proof(payload, nonce)

    assert verify_payload(payload, nonce, proof) is True


def test_verifiable_inference_invalid():
    payload = b"Syntactic Hologram Hypothesis #42"
    nonce = 1337
    invalid_proof = b"deadbeef_invalid_hash_proof_00000000000000000000000000000000"

    assert verify_payload(payload, nonce, invalid_proof) is False
