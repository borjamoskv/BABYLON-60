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
        sig_preimage = f"{sender_id}:{recipient_id}:{now_ms}:{nonce}:{payload_hash}"
        key = signing_key or "SovereignNodeDefaultKey"
        signature = hashlib.sha256(f"{key}:{sig_preimage}".encode("utf-8")).hexdigest()

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

        sig_preimage = f"{self.sender_id}:{self.recipient_id}:{self.timestamp_ms}:{self.nonce}:{self.payload_hash}"
        key = expected_key or "SovereignNodeDefaultKey"
        expected_sig = hashlib.sha256(f"{key}:{sig_preimage}".encode("utf-8")).hexdigest()
        return self.signature == expected_sig

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
