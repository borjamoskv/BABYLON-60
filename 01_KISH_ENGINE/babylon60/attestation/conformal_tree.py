# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Conformal Merkle Tree & Aeon Verifier
"""conformal_tree.py - Árbol de Merkle balanceado y motor de verificación de Aeones Conformes.

Proporciona las estructuras criptográficas y oráculos para:
1. Construir árboles de Merkle binarios balanceados O(log N) sobre recibos SCITT.
2. Generar y verificar pruebas de inclusión formales (Membership Proofs).
3. Verificar la validez de manifiestos de Aeones Conformes sellados en L1 (INV_C5_AEON).
4. Anclar pruebas a identidades soberanas Ed25519 y hardware local Ring-0.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import sqlite3
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519

from babylon60.attestation.merkle_anchor import MerkleCausalAnchor

import blake3

logger = logging.getLogger("babylon60.attestation.conformal_tree")


def canonical_aeon_manifest_bytes(manifest: Mapping[str, Any]) -> bytes:
    """Encode the complete v2 manifest, excluding only its signature field."""
    body = dict(manifest)
    identity = body.get("sovereign_identity")
    if not isinstance(identity, dict):
        raise ValueError("Manifest sovereign identity must be an object")
    body["sovereign_identity"] = {name: value for name, value in identity.items() if name != "ed25519_signature_b64"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("Duplicate manifest JSON field")
        result[name] = value
    return result


def _blake3_hex(data: bytes) -> str:
    return blake3.blake3(data).hexdigest()


def compute_claim_leaf_hash(
    claim_id: str,
    advisory_id: str,
    domain: str,
    payload_hash: str,
    attestation_merkle_root: str,
) -> str:
    """Calcula el hash BLAKE3 canónico (256 bits) de la hoja de un claim para el árbol de Aeón."""
    leaf_repr = f"{claim_id}:{advisory_id}:{domain}:{payload_hash}:{attestation_merkle_root}"
    return _blake3_hex(leaf_repr.encode("utf-8"))


class ConformalMerkleTree:
    """Árbol de Merkle balanceado O(log N) para compactación conforma de Aeones (BLAKE3 canónico)."""

    def __init__(self, leaves: Sequence[str]) -> None:
        if not leaves:
            raise ValueError("El árbol de Merkle requiere al menos una hoja.")
        self.leaves: List[str] = list(leaves)
        self.tree_levels: List[List[str]] = [self.leaves]
        self._build_tree()

    def _build_tree(self) -> None:
        current_level = self.leaves
        while len(current_level) > 1:
            next_level: List[str] = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = f"{left}:{right}".encode("utf-8")
                parent = _blake3_hex(combined)
                next_level.append(parent)
            self.tree_levels.append(next_level)
            current_level = next_level

    @property
    def root(self) -> str:
        return self.tree_levels[-1][0]

    def get_inclusion_proof(self, index: int) -> List[Tuple[str, str]]:
        """Genera prueba de inclusión: lista de tuplas (posicion, hash_hermano)."""
        if index < 0 or index >= len(self.leaves):
            raise IndexError(f"Índice de hoja fuera de rango: {index} (total: {len(self.leaves)})")
        proof: List[Tuple[str, str]] = []
        curr_idx = index
        for level in self.tree_levels[:-1]:
            is_right = curr_idx % 2 == 1
            if is_right:
                sibling_idx = curr_idx - 1
                sibling_pos = "LEFT"
            else:
                sibling_idx = curr_idx + 1 if curr_idx + 1 < len(level) else curr_idx
                sibling_pos = "RIGHT"

            proof.append((sibling_pos, level[sibling_idx]))
            curr_idx = curr_idx // 2
        return proof

    @staticmethod
    def verify_inclusion_proof(leaf: str, proof: Sequence[Tuple[str, str]], expected_root: str) -> bool:
        """Verifica deterministamente una prueba de inclusión O(log N) en BLAKE3 (con soporte legado SHA3-256/SHA-256)."""
        for hash_fn in (
            _blake3_hex,
            lambda b: hashlib.sha3_256(b).hexdigest(),
            lambda b: hashlib.sha256(b).hexdigest(),
        ):
            curr = leaf
            for pos, sibling in proof:
                if pos == "LEFT":
                    combined = f"{sibling}:{curr}".encode("utf-8")
                else:
                    combined = f"{curr}:{sibling}".encode("utf-8")
                curr = hash_fn(combined)
            if curr == expected_root:
                return True
        return False


def extract_claims_from_ledger(db_path: str | Path) -> List[Dict[str, Any]]:
    """Extrae todos los registros de atestación SCITT ordenados deterministamente."""
    path_str = str(db_path)
    if not Path(path_str).exists():
        raise FileNotFoundError(f"Cold Ledger no encontrado: {path_str}")

    uri = f"file:{Path(path_str).resolve()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT claim_id, advisory_id, domain, risk_score, payload_hash, "
        "timestamp_utc, hardware_anchor, attestation_merkle_root "
        "FROM bounty_claims ORDER BY timestamp_utc ASC, claim_id ASC"
    )
    rows = cursor.fetchall()
    claims: List[Dict[str, Any]] = [dict(row) for row in rows]
    conn.close()
    return claims


class AeonVerifier:
    """Motor de verificación determinista de Aeones Conformes sellados en L1."""

    @staticmethod
    def verify_ed25519_signature(public_key_b64: str, signature_b64: str, root_hex: str) -> bool:
        """Verifica la firma Ed25519 de la identidad L0 sobre la raíz de Merkle."""
        try:
            pub_bytes = base64.b64decode(public_key_b64)
            sig_bytes = base64.b64decode(signature_b64)
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            pub_key.verify(sig_bytes, bytes.fromhex(root_hex))
            return True
        except (InvalidSignature, ValueError, Exception) as exc:
            logger.warning("Fallo en verificación de firma Ed25519: %s", exc)
            return False

    @classmethod
    def verify_manifest(
        cls,
        manifest_path: str | Path,
        db_path: Optional[str | Path] = None,
        *,
        expected_public_key_b64: str | None = None,
        require_hardware: bool = False,
    ) -> Dict[str, Any]:
        """Authenticate a v2 manifest against an external Ed25519 trust anchor.

        The environment fallback serves CLI consumers that have no key argument.
        Without a database only the signed manifest is checked. Host identifiers
        are informational; this software verifier cannot approve hardware proof.
        """
        path = Path(manifest_path)
        if not path.exists():
            raise FileNotFoundError(f"Manifiesto L1 no encontrado: {path}")

        raw_data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_json_object)
        if not isinstance(raw_data, dict):
            raise ValueError("Manifest must be a JSON object")
        aeon_id = str(raw_data.get("aeon_id", ""))
        status = str(raw_data.get("status", ""))
        merkle_root = str(raw_data.get("merkle_root", ""))
        total_claims = int(raw_data.get("total_claims_sealed", 0))

        # 1. Trust originates outside the supplied manifest; authenticate all fields.
        sovereign = raw_data.get("sovereign_identity") or {}
        if not isinstance(sovereign, dict):
            raise ValueError("Manifest sovereign identity must be an object")
        pub_key_b64 = str(sovereign.get("l0_public_key_b64", ""))
        sig_b64 = str(sovereign.get("ed25519_signature_b64", ""))
        trusted_key_b64 = (
            expected_public_key_b64
            if expected_public_key_b64 is not None
            else os.environ.get("BABYLON_AEON_TRUSTED_PUBLIC_KEY_B64", "")
        )
        identity_trusted = False
        sig_valid = False
        schema_valid = (
            raw_data.get("schema") == "babylon60.aeon-manifest.v2"
            and sovereign.get("signed_payload") == "manifest-canonical-json-v2"
            and isinstance(raw_data.get("total_claims_sealed"), int)
            and not isinstance(raw_data.get("total_claims_sealed"), bool)
            and total_claims > 0
            and bool(aeon_id)
            and re.fullmatch(r"[0-9a-fA-F]{64}", merkle_root) is not None
        )
        try:
            embedded = base64.b64decode(pub_key_b64, validate=True)
            trusted = base64.b64decode(trusted_key_b64, validate=True)
            identity_trusted = len(embedded) == 32 and len(trusted) == 32 and embedded == trusted
            bytes.fromhex(merkle_root)
            if identity_trusted and schema_valid:
                signature = base64.b64decode(sig_b64, validate=True)
                ed25519.Ed25519PublicKey.from_public_bytes(trusted).verify(
                    signature, canonical_aeon_manifest_bytes(raw_data)
                )
                sig_valid = True
        except (InvalidSignature, ValueError, TypeError):
            sig_valid = False

        # 2. Verificar atestación de hardware
        hw = raw_data.get("hardware_attestation") or {}
        if not isinstance(hw, dict):
            raise ValueError("Manifest hardware attestation must be an object")
        hw_uuid = str(hw.get("hardware_uuid", ""))
        current_hw = MerkleCausalAnchor().get_hardware_identity()
        is_same_host = current_hw.get("uuid") == hw_uuid

        # 3. Si se provee la base de datos de Cold Ledger, recomputar Merkle Tree
        tree_valid: Optional[bool] = None
        recomputed_root: Optional[str] = None
        recomputed_claims_count: Optional[int] = None
        if db_path is not None:
            claims = extract_claims_from_ledger(db_path)
            recomputed_claims_count = len(claims)
            leaf_hashes = [
                compute_claim_leaf_hash(
                    claim_id=str(c["claim_id"]),
                    advisory_id=str(c["advisory_id"]),
                    domain=str(c["domain"]),
                    payload_hash=str(c["payload_hash"]),
                    attestation_merkle_root=str(c["attestation_merkle_root"]),
                )
                for c in claims
            ]
            if leaf_hashes:
                tree = ConformalMerkleTree(leaf_hashes)
                recomputed_root = tree.root
                tree_valid = (recomputed_root == merkle_root) and (recomputed_claims_count == total_claims)
            else:
                tree_valid = False

        overall_valid = (
            sig_valid
            and identity_trusted
            and (tree_valid is not False)
            and (status == "FROZEN_C5_REAL")
            and not require_hardware
        )

        return {
            "aeon_id": aeon_id,
            "status": status,
            "merkle_root": merkle_root,
            "total_claims": total_claims,
            "ed25519_signature_valid": sig_valid,
            "identity_trusted": identity_trusted,
            "manifest_schema_valid": schema_valid,
            "hardware_attestation_verified": False,
            "hardware_attestation_status": "NOT_VERIFIED",
            "verification_scope": (
                ("AUTHENTICATED_MANIFEST_AND_LEDGER" if db_path is not None else "AUTHENTICATED_MANIFEST_ONLY")
                if overall_valid
                else "REJECTED"
            ),
            "hardware_anchor_uuid": hw_uuid,
            "is_origin_host": is_same_host,
            "recomputed_root": recomputed_root,
            "recomputed_claims_count": recomputed_claims_count,
            "tree_integrity_valid": tree_valid,
            "overall_valid": overall_valid,
        }

    @classmethod
    def verify_claim_membership(
        cls,
        claim_id: str,
        manifest_path: str | Path,
        db_path: str | Path,
    ) -> Dict[str, Any]:
        """Verifica la inclusión criptográfica formal O(log N) de un claim en el Aeón sellado."""
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        expected_root = str(manifest.get("merkle_root", ""))
        if not expected_root:
            raise ValueError("Manifiesto inválido: no contiene 'merkle_root'.")

        claims = extract_claims_from_ledger(db_path)
        target_idx: Optional[int] = None
        target_claim: Optional[Dict[str, Any]] = None

        leaf_hashes: List[str] = []
        for idx, c in enumerate(claims):
            cid = str(c["claim_id"])
            if cid == claim_id:
                target_idx = idx
                target_claim = c
            leaf_hash = compute_claim_leaf_hash(
                claim_id=cid,
                advisory_id=str(c["advisory_id"]),
                domain=str(c["domain"]),
                payload_hash=str(c["payload_hash"]),
                attestation_merkle_root=str(c["attestation_merkle_root"]),
            )
            leaf_hashes.append(leaf_hash)

        if target_idx is None or target_claim is None:
            raise KeyError(f"Reclamación {claim_id} no encontrada en Cold Ledger {db_path}")

        tree = ConformalMerkleTree(leaf_hashes)
        proof = tree.get_inclusion_proof(target_idx)
        leaf = leaf_hashes[target_idx]
        is_valid = ConformalMerkleTree.verify_inclusion_proof(leaf, proof, expected_root)

        return {
            "claim_id": claim_id,
            "advisory_id": target_claim["advisory_id"],
            "domain": target_claim["domain"],
            "risk_score": target_claim["risk_score"],
            "leaf_hash": leaf,
            "expected_merkle_root": expected_root,
            "computed_merkle_root": tree.root,
            "proof_steps": len(proof),
            "proof_path": proof,
            "is_valid_inclusion": is_valid,
        }
