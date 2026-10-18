#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ SCITT ATTESTATION ENVELOPE | DOMAIN: agents.archi | STATE: C5-REAL
# ============================================================================
"""
Cryptographic Attestation Envelope for Multi-Agent Messaging (RFC 9942 / SCITT).

Guarantees:
  - Nonce-based replay protection
  - SHA256 / BLAKE3 payload integrity hashing
  - Inter-agent message attestation before BFT submission
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature


def _derive_ed25519_keypair(seed_str: str) -> tuple[Ed25519PrivateKey, bytes]:
    """Derive deterministic Ed25519 keypair from a string seed."""
    seed_bytes = hashlib.sha256(seed_str.encode("utf-8")).digest()
    priv_key = Ed25519PrivateKey.from_private_bytes(seed_bytes)
    pub_bytes = priv_key.public_key().public_bytes_raw()
    return priv_key, pub_bytes


# In-memory replay-protection NonceStore (Law O13: Authoritative Host Window + Single-Use Nonce)
_SEEN_NONCES: Dict[str, int] = {}
_NONCE_TTL_MS: int = 300_000


class NonceStore:
    """Authoritative host-clock replay protection store (Law O13)."""

    @staticmethod
    def check_and_record(nonce: str, host_now_ms: int) -> bool:
        expired = [k for k, ts in _SEEN_NONCES.items() if host_now_ms - ts > _NONCE_TTL_MS]
        for k in expired:
            _SEEN_NONCES.pop(k, None)
        if not nonce or nonce in _SEEN_NONCES:
            return False
        _SEEN_NONCES[nonce] = host_now_ms
        return True


@dataclass
class AttestationEnvelope:
    sender_id: str
    recipient_id: str
    payload: Dict[str, Any]
    timestamp_ms: int
    nonce: str
    payload_hash: str
    signature: str

    @classmethod
    def create(
        cls,
        sender_id: str,
        recipient_id: str,
        payload: Dict[str, Any],
        signing_key: Optional[str] = None,
    ) -> "AttestationEnvelope":
        now_ms = int(time.time() * 1000)
        nonce = os.urandom(8).hex()

        # Deterministic JSON canonicalization for hashing
        canon_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload_hash = hashlib.sha256(canon_payload.encode("utf-8")).hexdigest()

        # Envelope signature digest
        sig_preimage = f"{sender_id}:{recipient_id}:{now_ms}:{nonce}:{payload_hash}".encode("utf-8")

        if signing_key:
            # Software Ed25519 path for tests and CI
            priv_key, _ = _derive_ed25519_keypair(signing_key)
            signature = priv_key.sign(sig_preimage).hex()
        else:
            # [APEX C5-REAL]: Delegación estricta de la firma al Enclave Seguro (Secure Enclave).
            # La generación de clave y firma abandona el espacio de memoria de Python.
            import subprocess

            try:
                result = subprocess.run(
                    [
                        "c5_biometric_gate",
                        "--action",
                        "attest_swarm_message",
                        "--agent",
                        sender_id,
                        "--scope",
                        recipient_id,
                        "--causal-hash",
                        payload_hash,
                        "--no-sound",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                gate_data = json.loads(result.stdout)
                signature = gate_data.get("secure_enclave_signature", "")
                if (
                    gate_data.get("status") != "ATTESTED"
                    or not isinstance(signature, str)
                    or len(signature) < 64
                    or gate_data.get("causal_hash", payload_hash) != payload_hash
                ):
                    raise ValueError(
                        "C5-REAL INVARIANT FAILURE: Atestación biométrica inválida o denegada por Secure Enclave."
                    )
            except Exception as e:
                raise ValueError(f"C5-REAL INVARIANT FAILURE: Falla de hardware biométrico. {e}")

        return cls(
            sender_id=sender_id,
            recipient_id=recipient_id,
            payload=payload,
            timestamp_ms=now_ms,
            nonce=nonce,
            payload_hash=payload_hash,
            signature=signature,
        )

    def verify(self, expected_key: Optional[str] = None, enforce_replay: bool = True) -> bool:
        """Verifies envelope integrity, host-clock freshness, single-use nonce (O13), and cryptographic signature."""
        canon_payload = json.dumps(self.payload, sort_keys=True, separators=(",", ":"))
        calc_hash = hashlib.sha256(canon_payload.encode("utf-8")).hexdigest()
        if calc_hash != self.payload_hash:
            return False

        now_ms = int(time.time() * 1000)
        if abs(now_ms - self.timestamp_ms) > _NONCE_TTL_MS:  # 5 min window
            return False  # Replay / Stale rejection

        sig_preimage = (
            f"{self.sender_id}:{self.recipient_id}:{self.timestamp_ms}:{self.nonce}:{self.payload_hash}".encode("utf-8")
        )
        if not expected_key or expected_key == "SovereignNodeDefaultKey":
            return False
        _, pub_bytes = _derive_ed25519_keypair(expected_key)

        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)

        try:
            pub_key.verify(bytes.fromhex(self.signature), sig_preimage)
        except (InvalidSignature, ValueError):
            return False

        if enforce_replay and not NonceStore.check_and_record(self.nonce, now_ms):
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
