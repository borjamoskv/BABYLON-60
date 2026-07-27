import base64
import binascii
import dataclasses
import logging
import sqlite3
import threading
from typing import Protocol

from babylon60.crypto.keys import KeyLifecycleManager, ZKSwarmIdentity
from babylon60.crypto.rekor_client import RekorClient
from babylon60.crypto.rfc3161 import RFC3161Client
from babylon60.ledger.models import LedgerEvent
from babylon60.ledger.queue import EnrichmentQueue
from babylon60.ledger.store import LedgerStore

logger = logging.getLogger("babylon60.ledger.writer")


def _spki_pem_from_b64(public_key_b64: str) -> str:
    """Encode a base64 public key as proper SubjectPublicKeyInfo PEM.

    KeyManager stores keys as base64 of the OpenSSH encoding
    (``ssh-ed25519 AAAA...``); raw 32-byte Ed25519 is accepted as fallback.
    Returns valid PEM or raises ValueError (FIND-003: never emit fake PEM).
    """
    from cryptography.exceptions import UnsupportedAlgorithm
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519

    try:
        decoded = base64.b64decode(public_key_b64, validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError(f"public_key_b64 is not valid base64: {e}") from e

    key = None
    try:
        key = serialization.load_ssh_public_key(decoded)
    except (ValueError, UnsupportedAlgorithm):
        pass
    if key is None:
        try:
            key = ed25519.Ed25519PublicKey.from_public_bytes(decoded)
        except ValueError as e:
            raise ValueError(f"unsupported public key encoding for Rekor anchor: {e}") from e

    return key.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("ascii")


class _OriginSignaturePolicy(Protocol):
    def validate_event(self, event: LedgerEvent) -> None: ...


class _ReplayAdmissionResult(Protocol):
    status: str
    event_id: str


class _ReplayAdmissionPolicy(Protocol):
    def validate_event(self, event: LedgerEvent) -> None: ...

    def admit_event(
        self,
        conn: sqlite3.Connection,
        event: LedgerEvent,
    ) -> _ReplayAdmissionResult: ...


class LedgerWriter:
    def __init__(
        self,
        store: LedgerStore,
        queue: EnrichmentQueue,
        *,
        origin_policy: _OriginSignaturePolicy | None = None,
        replay_policy: _ReplayAdmissionPolicy | None = None,
    ) -> None:
        self.store = store
        self.queue = queue
        self.origin_policy = origin_policy
        self.replay_policy = replay_policy

        self.rekor_client = RekorClient()
        self.rfc3161_client = RFC3161Client()
        self.key_manager = KeyLifecycleManager()

    def _async_anchor(self, event_hash: str) -> None:
        """Background thread to anchor the hash to Rekor and FreeTSA."""
        try:
            # 1. Get current identity
            keypair = self.key_manager.get_or_create_identity()

            # 2. Sign the hash
            signature_b64 = ZKSwarmIdentity.sign_payload(event_hash, keypair.private_key_b64)

            # 3. Anchor to Rekor (proper SPKI PEM; raises instead of anchoring garbage)
            from babylon60.crypto.hash_registry import cortex_hash_hex

            # External services strictly require SHA-256 Hex of the signed payload.
            # Here the signed payload is the event_hash (Base-60 string).
            hex_payload_hash = cortex_hash_hex(event_hash)

            pem = _spki_pem_from_b64(keypair.public_key_b64)
            self.rekor_client.anchor_payload(hex_payload_hash, signature_b64, pem)

            # 4. Request RFC3161 Timestamp
            tsr = self.rfc3161_client.request_timestamp(hex_payload_hash)
            if tsr:
                logger.info("Successfully received RFC3161 timestamp for hash %s", event_hash)
        except Exception as e:  # noqa: BLE001
            logger.error("Async anchoring failed: %s", e)

    def append(self, event: LedgerEvent) -> str:
        if self.origin_policy is not None:
            self.origin_policy.validate_event(event)
        if self.replay_policy is not None:
            self.replay_policy.validate_event(event)

        with self.store.tx() as conn:
            if self.replay_policy is not None:
                admission = self.replay_policy.admit_event(conn, event)
                if admission.status == "idempotent":
                    return admission.event_id

            # 1. Get last hash
            cursor = conn.execute("SELECT hash FROM ledger_events ORDER BY rowid DESC LIMIT 1")
            row = cursor.fetchone()
            prev_hash = row["hash"] if row else "GENESIS"

            # 2. Compute current hash
            new_hash = event.compute_hash(prev_hash)
            event = dataclasses.replace(event, prev_hash=prev_hash, hash=new_hash)

            from babylon60.database.core import causal_write

            with causal_write(conn):
                conn.execute(
                    """
                    INSERT INTO ledger_events (
                        event_id, ts, tool, actor, action, payload_json,
                        prev_hash, hash,
                        semantic_status, semantic_error, correlation_id, trace_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
                    """,
                    (
                        event.event_id,
                        event.ts,
                        event.tool,
                        event.actor,
                        event.action,
                        event.to_json(),
                        event.prev_hash,
                        event.hash,
                        event.semantic_status,
                        event.correlation_id,
                        event.trace_id,
                    ),
                )

        self.queue.enqueue(event.event_id)

        # Fire and forget external anchoring
        threading.Thread(target=self._async_anchor, args=(event.hash,), daemon=True).start()

        return event.event_id
