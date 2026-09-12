import hashlib
import json
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
) -> str:
    """Computa SHA3-256 de entrada Cortex (pura, sin I/O)."""
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
) -> bool:
    """
    Verifica una prueba de inclusión de Merkle O(log N) con separación de dominio.
    Retorna True si la prueba es matemáticamente válida contra expected_root.
    """
    if not leaf_hash or not expected_root or total_leaves <= 0:
        return False

    current = bytes.fromhex(leaf_hash)
    for step in proof:
        sibling = bytes.fromhex(step["sibling"])
        level = step.get("level", 0)
        domain_tag = b"\x00" if level == 0 else b"\x01"

        if step["position"] == "left":
            combined = domain_tag + sibling + current
        else:
            combined = domain_tag + current + sibling

        current = hashlib.sha3_256(combined).digest()

    root_with_cardinality = b"\x02" + current + total_leaves.to_bytes(8, "little")
    computed_root = hashlib.sha3_256(root_with_cardinality).hexdigest()
    return computed_root == expected_root


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
) -> Tuple[bool, str]:
    """
    Verifica todos los invariantes criptográficos de una fila.
    Retorna: (is_valid, error_message)
    Incluye FIX C5-04 (seq contiguo).
    """
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
    Resuelve la ineficiencia O(N) de árboles estáticos para flujos agénticos continuos.
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
        bit = 1 << 62
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
