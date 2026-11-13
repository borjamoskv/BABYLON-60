import hashlib
import json
import os
import uuid
from typing import Dict, List, Mapping, Tuple, TypedDict

NAMESPACE_CORTEX = uuid.UUID("a291bb18-79ad-4fc7-94e6-e6060ffd51f1")
ZERO_HASH_256 = "0" * 64


class MerkleProofStep(TypedDict):
    sibling: str
    position: str
    level: int


class MerkleProof(TypedDict):
    target_index: int
    leaf_hash: str
    total_leaves: int
    proof: List[MerkleProofStep]


class MMRProofStep(TypedDict):
    sibling: str
    position: str
    level: int


class MMRProofPacket(TypedDict):
    leaf_index: int
    total_leaves: int
    peak_index: int
    inner_proof: List[MMRProofStep]
    other_peaks: List[str]
    mmr_root: str


def _canonical_json(data: object) -> str:
    """Serialización canónica determinista."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def require_ed25519_seed(seed_hex: str | None = None) -> bytes:
    """Return the 32-byte Ed25519 seed. A missing or invalid seed is an error.

    Anchoring must not invent a signing key. Without this seed the signature
    does not identify the operator.
    """
    raw_text = seed_hex if seed_hex is not None else os.environ.get("BABYLON60_SIGNING_SEED", "")
    seed = raw_text.strip()
    if not seed:
        raise ValueError(
            "BABYLON60_SIGNING_SEED is required to anchor the ledger; refusing to generate an ephemeral signing key"
        )
    try:
        material = bytes.fromhex(seed)
    except ValueError as exc:
        raise ValueError("BABYLON60_SIGNING_SEED must be a hex-encoded Ed25519 seed") from exc
    if len(material) != 32:
        raise ValueError("BABYLON60_SIGNING_SEED must be 32 bytes")
    return material


def publish_rekor_anchor(
    head_json: bytes,
    rekor_client: object | None = None,
    seed_hex: str | None = None,
) -> dict[str, object] | None:
    """Sign one ledger head and submit it. Shared by both Python ledger classes.

    The seed requirement is strict: a missing or invalid ``BABYLON60_SIGNING_SEED``
    raises ``ValueError`` instead of generating an ephemeral key.
    """
    import base64

    from nacl.signing import SigningKey

    signing_key = SigningKey(require_ed25519_seed(seed_hex))
    signed = signing_key.sign(head_json)
    payload_hash = hashlib.sha256(head_json).hexdigest()
    signature_b64 = base64.b64encode(signed.signature).decode("utf-8")
    public_key_b64 = base64.b64encode(signing_key.verify_key.encode()).decode("utf-8")
    if rekor_client is None:
        try:
            from babylon60.crypto.rekor_client import RekorClient

            rekor_client = RekorClient()
        except ImportError:
            return None
    anchor = rekor_client.anchor_payload(payload_hash, signature_b64, public_key_b64)  # type: ignore[attr-defined]
    return dict(anchor) if anchor else None


def compute_envelope_hash(envelope: Mapping[str, object] | Dict[str, object]) -> str:
    """Computa el digest criptográfico SHA3-256 inmutable de cualquier sobre canónico."""
    return hashlib.sha3_256(_canonical_json(envelope).encode("utf-8")).hexdigest()


def compute_cortex_hash(
    seq: int,
    event_id: str,
    event_type: str,
    payload_json: str,
    cortex_taint: str,
    lamport_t: int,
    prev_hash: str,
    timestamp: str,
    agent_id: str = "ULTRATHINK-APEX",
    domain: str = "babylon60.com",
    hash_version: int = 1,
) -> str:
    """Hash v1 histórico; v2 liga el reloj lógico y excluye metadatos físicos."""
    if type(hash_version) is not int or hash_version not in (1, 2):
        raise ValueError(f"Unsupported Cortex hash version: {hash_version}")
    body = {
        "seq": seq,
        "event_id": event_id,
        "event_type": event_type,
        "payload_json": payload_json,
        "cortex_taint": cortex_taint,
        "agent_id": agent_id,
        "domain": domain,
        "lamport_t": lamport_t,
        "prev_hash": prev_hash,
        "timestamp": timestamp,
    }
    if hash_version == 2:
        if type(lamport_t) is not int or lamport_t <= 0:
            raise ValueError("Cortex logical_tick must be a positive integer")
        del body["timestamp"]
        del body["lamport_t"]
        body["logical_tick"] = lamport_t
        body["hash_version"] = hash_version
    return compute_envelope_hash(body)


def build_merkle_tree(entry_hashes: list[str]) -> str:
    """
    Construye Merkle tree con Domain Separation (FIX C5-05).
    Entrada: lista de hashes SHA3-256 (hex strings).
    Salida: merkle_root (hex string).
    """
    if not entry_hashes:
        return ZERO_HASH_256

    total_leaves = len(entry_hashes)
    layer = [bytes.fromhex(h) for h in entry_hashes]
    level = 0

    while len(layer) > 1:
        if len(layer) % 2 != 0:
            layer.append(layer[-1])

        next_layer = []
        for i in range(0, len(layer), 2):
            combined = layer[i] + layer[i + 1]
            domain_tag = b"\x00" if level == 0 else b"\x01"
            next_layer.append(hashlib.sha3_256(domain_tag + combined).digest())
        layer = next_layer
        level += 1

    root_with_cardinality = b"\x02" + layer[0] + total_leaves.to_bytes(8, "little")
    return hashlib.sha3_256(root_with_cardinality).hexdigest()


def generate_merkle_proof(entry_hashes: List[str], target_index: int) -> MerkleProof:
    """
    Genera una prueba de inclusión de Merkle O(log N) con separación de dominio.
    """
    if not entry_hashes or target_index < 0 or target_index >= len(entry_hashes):
        raise IndexError("target_index fuera de rango o lista vacía")

    total_leaves = len(entry_hashes)
    proof: List[MerkleProofStep] = []
    layer = [bytes.fromhex(h) for h in entry_hashes]
    idx = target_index
    level = 0

    while len(layer) > 1:
        if len(layer) % 2 != 0:
            layer.append(layer[-1])

        is_right_child = idx % 2 == 1
        sibling_idx = idx - 1 if is_right_child else idx + 1
        sibling_bytes = layer[sibling_idx]

        proof.append(
            {
                "sibling": sibling_bytes.hex(),
                "position": "left" if is_right_child else "right",
                "level": level,
            }
        )

        next_layer = []
        for i in range(0, len(layer), 2):
            combined = layer[i] + layer[i + 1]
            domain_tag = b"\x00" if level == 0 else b"\x01"
            next_layer.append(hashlib.sha3_256(domain_tag + combined).digest())
        layer = next_layer
        idx = idx // 2
        level += 1

    return {
        "target_index": target_index,
        "leaf_hash": entry_hashes[target_index],
        "total_leaves": total_leaves,
        "proof": proof,
    }


def verify_merkle_proof(
    leaf_hash: str,
    proof: List[MerkleProofStep],
    expected_root: str,
    total_leaves: int,
    target_index: int | None = None,
) -> bool:
    """
    Verifica una prueba de inclusión de Merkle O(log N) con separación de dominio.
    Liga la profundidad y orientación a la cardinalidad y al índice de hoja.
    Los llamantes antiguos pueden omitir el índice: se deduce de la ruta.
    """
    if type(total_leaves) is not int or not 0 < total_leaves < (1 << 64):
        return False
    depth = (total_leaves - 1).bit_length()
    if not isinstance(proof, list) or len(proof) != depth:
        return False

    inferred_index = 0
    for level, step in enumerate(proof):
        if not isinstance(step, dict):
            return False
        if type(step.get("level")) is not int or step.get("level") != level:
            return False
        position = step.get("position")
        if position not in ("left", "right"):
            return False
        if position == "left":
            inferred_index |= 1 << level

    if target_index is None:
        target_index = inferred_index
    if type(target_index) is not int or not 0 <= target_index < total_leaves:
        return False
    if target_index != inferred_index:
        return False

    def decode_hash(value: str) -> bytes | None:
        if not isinstance(value, str) or len(value) != 64:
            return None
        try:
            decoded = bytes.fromhex(value)
        except ValueError:
            return None
        return decoded if len(decoded) == 32 else None

    current = decode_hash(leaf_hash)
    root = decode_hash(expected_root)
    if current is None or root is None:
        return False
    index, width = target_index, total_leaves
    for level, step in enumerate(proof):
        sibling = decode_hash(step.get("sibling", ""))
        if sibling is None:
            return False
        # The unpaired final node is duplicated, never an extra leaf.
        if index % 2 == 0 and index + 1 == width and sibling != current:
            return False
        domain_tag = b"\x00" if level == 0 else b"\x01"

        if step["position"] == "left":
            combined = domain_tag + sibling + current
        else:
            combined = domain_tag + current + sibling

        current = hashlib.sha3_256(combined).digest()
        index //= 2
        width = (width + 1) // 2

    root_with_cardinality = b"\x02" + current + total_leaves.to_bytes(8, "little")
    return hashlib.sha3_256(root_with_cardinality).digest() == root


def verify_row_invariants(
    seq: int,
    event_id: str,
    event_type: str,
    payload_json: str,
    cortex_taint: str,
    agent_id: str,
    domain: str,
    lamport_t: int,
    prev_hash: str,
    entry_hash: str,
    timestamp: str,
    expected_seq: int,
    last_lamport: int,
    expected_prev_hash: str,
    hash_version: int = 1,
) -> Tuple[bool, str]:
    """
    Verifica todos los invariantes criptográficos de una fila.
    Retorna: (is_valid, error_message)
    Incluye FIX C5-04 (seq contiguo).
    """
    if type(hash_version) is not int or hash_version not in (1, 2):
        return False, f"Unsupported Cortex hash version: {hash_version}"

    if seq != expected_seq:
        return False, f"Seq discontinuity: expected {expected_seq}, got {seq}"

    if lamport_t <= last_lamport:
        return False, f"Lamport violation: {lamport_t} <= {last_lamport}"

    if prev_hash != expected_prev_hash:
        return False, f"Hash chain broken: expected {expected_prev_hash}, got {prev_hash}"

    computed = compute_cortex_hash(
        seq=seq,
        event_id=event_id,
        event_type=event_type,
        payload_json=payload_json,
        cortex_taint=cortex_taint,
        lamport_t=lamport_t,
        prev_hash=expected_prev_hash,
        timestamp=timestamp,
        agent_id=agent_id,
        domain=domain,
        hash_version=hash_version,
    )
    if computed != entry_hash:
        return False, f"Entry hash mismatch: computed {computed}, stored {entry_hash}"

    return True, ""


# =============================================================================
# MERKLE MOUNTAIN RANGE (MMR) ACCUMULATOR & O(LOG N) INCLUSION PROOFS
# Cumplimiento: EU AI Act Arts. 10, 12, 14 | Draft IETF COSE-MMR Proofs
# =============================================================================

DOMAIN_MMR_LEAF = b"\x00"
DOMAIN_MMR_NODE = b"\x01"
DOMAIN_MMR_PEAKS = b"\x02"


class MerkleMountainRange:
    """
    Acumulador append-only inmutable Merkle Mountain Range (MMR).
    Resuelve la Ineficiencia O(N) de árboles estáticos para flujos agénticos continuos.
    Genera pruebas de inclusión O(log N) para expedientes forenses del EU AI Act.
    """

    def __init__(self) -> None:
        self.leaves: List[str] = []

    def append(self, leaf_hash: str) -> int:
        """Agrega un leaf_hash (hex) y retorna su índice canónico en el MMR."""
        self.leaves.append(leaf_hash)
        return len(self.leaves) - 1

    def _get_peak_slices(self) -> List[Tuple[int, int]]:
        n = len(self.leaves)
        slices = []
        start = 0
        bit = 1 << (n.bit_length() - 1) if n else 0
        while bit > 0:
            if n & bit:
                size = bit
                slices.append((start, start + size))
                start += size
            bit >>= 1
        return slices

    def _build_subtree_root_and_proof(
        self, leaf_slice: List[str], target_idx: int = -1
    ) -> Tuple[bytes, List[MMRProofStep]]:
        layer = [bytes.fromhex(h) for h in leaf_slice]
        proof: List[MMRProofStep] = []
        idx = target_idx
        level = 0

        while len(layer) > 1:
            if idx >= 0:
                is_right = idx % 2 == 1
                sibling_idx = idx - 1 if is_right else idx + 1
                proof.append(
                    {"sibling": layer[sibling_idx].hex(), "position": "left" if is_right else "right", "level": level}
                )
                idx //= 2

            next_layer = []
            for i in range(0, len(layer), 2):
                combined = layer[i] + layer[i + 1]
                next_layer.append(hashlib.sha3_256(DOMAIN_MMR_NODE + combined).digest())
            layer = next_layer
            level += 1

        return layer[0], proof

    def get_peaks(self) -> List[bytes]:
        slices = self._get_peak_slices()
        peaks = []
        for start, end in slices:
            peak_root, _ = self._build_subtree_root_and_proof(self.leaves[start:end])
            peaks.append(peak_root)
        return peaks

    def get_root(self) -> str:
        if not self.leaves:
            return ZERO_HASH_256
        peaks = self.get_peaks()
        bag = DOMAIN_MMR_PEAKS + b"".join(peaks) + len(self.leaves).to_bytes(8, "little")
        return hashlib.sha3_256(bag).hexdigest()

    def generate_proof(self, target_index: int) -> MMRProofPacket:
        if target_index < 0 or target_index >= len(self.leaves):
            raise IndexError("target_index fuera de rango")
        slices = self._get_peak_slices()
        peaks = self.get_peaks()

        peak_idx = 0
        rel_idx = 0
        found_start, found_end = 0, 0
        for i, (start, end) in enumerate(slices):
            if start <= target_index < end:
                peak_idx = i
                rel_idx = target_index - start
                found_start, found_end = start, end
                break

        _, inner_proof = self._build_subtree_root_and_proof(self.leaves[found_start:found_end], rel_idx)
        other_peaks = [p.hex() for j, p in enumerate(peaks) if j != peak_idx]

        return {
            "leaf_index": target_index,
            "total_leaves": len(self.leaves),
            "peak_index": peak_idx,
            "inner_proof": inner_proof,
            "other_peaks": other_peaks,
            "mmr_root": self.get_root(),
        }

    @staticmethod
    def verify_proof(leaf_hash: str, proof_packet: MMRProofPacket, expected_root: str) -> bool:
        try:
            total = proof_packet["total_leaves"]
            index = proof_packet["leaf_index"]
            peak = proof_packet["peak_index"]
            if any(type(value) is not int for value in (total, index, peak)):
                return False
            if not 0 < total < (1 << 64) or not 0 <= index < total or peak < 0:
                return False
            if proof_packet["mmr_root"] != expected_root:
                return False
            start = 0
            peak_count = 0
            selected_peak = -1
            height = 0
            relative_index = 0
            for bit in range(total.bit_length() - 1, -1, -1):
                width = 1 << bit
                if total & width:
                    if start <= index < start + width:
                        selected_peak, height, relative_index = peak_count, bit, index - start
                    start += width
                    peak_count += 1
            path = proof_packet["inner_proof"]
            others = proof_packet["other_peaks"]
            if peak != selected_peak or not isinstance(path, list) or not isinstance(others, list):
                return False
            if len(path) != height or len(others) != peak_count - 1:
                return False
            digests = [leaf_hash, expected_root, *others]
            for level, step in enumerate(path):
                side = "left" if (relative_index >> level) & 1 else "right"
                if not isinstance(step, dict) or type(step["level"]) is not int:
                    return False
                if step["level"] != level or step["position"] != side:
                    return False
                digests.append(step["sibling"])
            for digest in digests:
                if not isinstance(digest, str) or len(digest) != 64 or len(bytes.fromhex(digest)) != 32:
                    return False
        except (KeyError, TypeError, ValueError, OverflowError):
            return False
        curr = bytes.fromhex(leaf_hash)
        for step in proof_packet["inner_proof"]:
            sibling = bytes.fromhex(step["sibling"])
            combined = sibling + curr if step["position"] == "left" else curr + sibling
            curr = hashlib.sha3_256(DOMAIN_MMR_NODE + combined).digest()

        recomputed_peak = curr
        other_peaks = [bytes.fromhex(h) for h in proof_packet["other_peaks"]]
        peak_idx = proof_packet["peak_index"]
        all_peaks = other_peaks[:peak_idx] + [recomputed_peak] + other_peaks[peak_idx:]

        total_leaves = proof_packet["total_leaves"]
        bag = DOMAIN_MMR_PEAKS + b"".join(all_peaks) + total_leaves.to_bytes(8, "little")
        computed_root = hashlib.sha3_256(bag).hexdigest()
        return computed_root == expected_root
