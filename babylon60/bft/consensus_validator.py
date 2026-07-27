# [C5-REAL] BFT consensus validator — Operador ortogonal (V) puro.
# No muta disco. Solo atestación matemática.
from typing import Any, Dict
import cbor2
import json
from babylon60.core.crypto import canonicalize_cbor, hash_sha3_256, verify_ed25519

_UNDECODABLE = object()

class BFT_Validator:
    def __init__(self, node_keys: Dict[str, str]):
        self._node_keys = node_keys

    def verify_signature(self, node_id: str, data_hash: str, sig: str) -> bool:
        public_key_hex = self._node_keys.get(node_id)
        if public_key_hex is None:
            return False
        return verify_ed25519(public_key_hex, data_hash, sig)

    def validate_votes(self, payload: Dict[str, Any], f: int, swarm_signatures: Dict[str, str]) -> str:
        required_votes = (2 * f) + 1
        mutation_hash = hash_sha3_256(canonicalize_cbor(payload))
        valid_votes = sum(
            1 for node_id, sig in swarm_signatures.items() if self.verify_signature(node_id, mutation_hash, sig)
        )
        if valid_votes < required_votes:
            raise PermissionError(f"BFT_CONSENSUS_FAILURE: {valid_votes}/{required_votes} votes. State compromised.")
        return mutation_hash

    @staticmethod
    def decode_payload(payload_bytes: Any) -> Any:
        if isinstance(payload_bytes, memoryview):
            payload_bytes = payload_bytes.tobytes()
        try:
            return cbor2.loads(payload_bytes)
        except (cbor2.CBORDecodeError, ValueError):
            # Fallback to JSON payload parsing
            _ = None
        try:
            raw = payload_bytes.decode("utf-8") if isinstance(payload_bytes, bytes) else payload_bytes
            return json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
            return _UNDECODABLE

    @staticmethod
    def audit_payload(payload_data: Any, stored_hash: str) -> bool:
        if payload_data is _UNDECODABLE:
            return False
        try:
            computed_hash = hash_sha3_256(canonicalize_cbor(payload_data))
        except (cbor2.CBOREncodeError, ValueError, TypeError):
            return False
        return computed_hash == stored_hash
