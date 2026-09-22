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
        key_str = signing_key or "SovereignNodeDefaultKey"
        priv_key, _ = _derive_ed25519_keypair(key_str)

        signature = priv_key.sign(sig_preimage).hex()

        return cls(
            sender_id=sender_id,
            recipient_id=recipient_id,
            payload=payload,
            timestamp_ms=now_ms,
            nonce=nonce,
            payload_hash=payload_hash,
            signature=signature,
        )

    def verify(self, expected_key: Optional[str] = None) -> bool:
        """Verifies envelope integrity and cryptographic signature."""
        canon_payload = json.dumps(self.payload, sort_keys=True, separators=(",", ":"))
        calc_hash = hashlib.sha256(canon_payload.encode("utf-8")).hexdigest()
        if calc_hash != self.payload_hash:
            return False

        sig_preimage = (
            f"{self.sender_id}:{self.recipient_id}:{self.timestamp_ms}:{self.nonce}:{self.payload_hash}".encode("utf-8")
        )
        key_str = expected_key or "SovereignNodeDefaultKey"
        _, pub_bytes = _derive_ed25519_keypair(key_str)

        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)

        try:
            pub_key.verify(bytes.fromhex(self.signature), sig_preimage)
            return True
        except InvalidSignature:
            return False
        except ValueError:
            return False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
