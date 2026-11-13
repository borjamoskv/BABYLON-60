"""Shared submission path for a verified ledger snapshot."""

import base64
import hashlib
import logging
import os
from collections.abc import Mapping
from typing import Any

from babylon60.bft.cortex_crypto_kernel import _canonical_json

logger = logging.getLogger(__name__)


def anchor_verified_state(
    attestation: Mapping[str, object],
    rekor_client: Any | None,
    seed_hex: str | None,
) -> dict[str, object] | None:
    if attestation["integrity_verified"] is not True:
        logger.warning("Rekor anchoring skipped because ledger integrity verification failed")
        return None

    seed = seed_hex if seed_hex is not None else os.environ.get("BABYLON60_SIGNING_SEED", "")
    try:
        seed_bytes = bytes.fromhex(seed)
    except ValueError:
        logger.warning("Rekor anchoring requires a valid Ed25519 signing seed")
        return None
    if len(seed_bytes) != 32:
        logger.warning("Rekor anchoring requires a valid Ed25519 signing seed")
        return None

    from nacl.signing import SigningKey

    signing_key = SigningKey(seed_bytes)
    head = {
        "merkle_root": attestation["merkle_root"],
        "max_lamport": attestation["max_lamport"],
        "total_entries": attestation["total_entries"],
        "attested_at": attestation["attested_at"],
    }
    payload = _canonical_json(head).encode("utf-8")
    payload_hash = hashlib.sha256(payload).hexdigest()
    signature = base64.b64encode(signing_key.sign(payload).signature).decode("utf-8")
    public_key = base64.b64encode(signing_key.verify_key.encode()).decode("utf-8")

    if rekor_client is None:
        try:
            from babylon60.crypto.rekor_client import RekorClient
        except ImportError:
            return None
        rekor_client = RekorClient()

    result = rekor_client.anchor_payload(payload_hash, signature, public_key)
    return dict(result) if result else None
