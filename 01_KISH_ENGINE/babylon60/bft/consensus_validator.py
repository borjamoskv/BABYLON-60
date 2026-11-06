# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] BFT consensus validator — Operador ortogonal (V) puro.
# No muta disco. Solo atestación matemática.
from typing import Dict, Mapping
import cbor2
import json
from babylon60.core.crypto_utils import canonicalize_cbor, hash_sha3_256, verify_ed25519

_UNDECODABLE = object()


class BFT_Validator:
    def __init__(self, node_keys: Dict[str, str]) -> None:
        self._node_keys = dict(node_keys)
        raw_keys = [bytes.fromhex(key) for key in self._node_keys.values()]
        if any(len(key) != 32 for key in raw_keys) or len(set(raw_keys)) != len(raw_keys):
            raise ValueError("BFT node public keys must be valid and unique")

    def verify_signature(self, node_id: str, data_hash: str, sig: str) -> bool:
        public_key_hex = self._node_keys.get(node_id)
        if public_key_hex is None or not isinstance(sig, str):
            return False
        return verify_ed25519(public_key_hex, data_hash, sig)

    def validate_votes(
        self, payload: Mapping[str, object] | Dict[str, object], f: int, swarm_signatures: Dict[str, str]
    ) -> str:
        if type(f) is not int or f < 0:
            raise ValueError("BFT_INVALID_CONFIGURATION: f must be a non-negative integer")
        population = len(self._node_keys)
        if population < (3 * f) + 1:
            raise PermissionError(f"BFT_CONSENSUS_FAILURE: population {population} cannot tolerate f={f}")
        # N-f equals 2f+1 for N=3f+1 and preserves quorum intersection for larger committees.
        required_votes = population - f
        mutation_hash = hash_sha3_256(canonicalize_cbor(payload))
        valid_votes = sum(
            1 for node_id, sig in swarm_signatures.items() if self.verify_signature(node_id, mutation_hash, sig)
        )
        if valid_votes < required_votes:
            raise PermissionError(f"BFT_CONSENSUS_FAILURE: {valid_votes}/{required_votes} votes. State compromised.")
        return mutation_hash

    def validate_fuzzy_opinions(
        self, opinions: Dict[str, Dict[str, float]], weights: Dict[str, float] | None = None
    ) -> Dict[str, float]:
        """
        [Causal-Determinist] Evaluate heuristic / fuzzy inputs from the swarm using LogOP.
        If any BFT agent vetoes (p=0), the hypothesis probability collapses to 0.
        """
        from babylon60.bft.bayesian_swarm import BayesianSwarm

        swarm = BayesianSwarm(list(opinions.keys()))
        return swarm.logarithmic_opinion_pool(opinions, weights)

    @staticmethod
    def decode_payload(payload_bytes: bytes | memoryview | str | object) -> object:
        if isinstance(payload_bytes, memoryview):
            payload_bytes = payload_bytes.tobytes()
        if isinstance(payload_bytes, (bytes, bytearray)):
            try:
                return cbor2.loads(payload_bytes)
            except (cbor2.CBORDecodeError, ValueError, TypeError):
                pass
        try:
            raw = payload_bytes.decode("utf-8") if isinstance(payload_bytes, bytes) else payload_bytes
            if isinstance(raw, (str, bytes, bytearray)):
                return json.loads(raw)
            return _UNDECODABLE
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
            return _UNDECODABLE

    @staticmethod
    def audit_payload(payload_data: object, stored_hash: str) -> bool:
        if payload_data is _UNDECODABLE:
            return False
        try:
            computed_hash = hash_sha3_256(canonicalize_cbor(payload_data))
        except (cbor2.CBOREncodeError, ValueError, TypeError):
            return False
        return computed_hash == stored_hash
