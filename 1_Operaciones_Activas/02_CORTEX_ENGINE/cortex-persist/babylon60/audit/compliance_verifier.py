# [C5-REAL] Exergy-Maximized
"""
EU AI Act Compliance Verifier (H5.1).

Offline verification CLI core. Ingests an `audit_bundle.zip` and
mathematically proves the Merkle chain continuity and Ed25519 signatures
without relying on the local database or network.
"""

import base64
import json
import logging
import zipfile
from pathlib import Path
from typing import Any

from babylon60.audit.smt import SparseMerkleTree
from babylon60.crypto.hash_registry import cortex_hash

logger = logging.getLogger("babylon60.audit.verifier")

GENESIS_PREV_HASH = "0" * 64


class ComplianceVerifier:
    """Offline cryptographic verifier for EU AI Act compliance bundles."""

    def __init__(self, bundle_path: str, public_key_b64: str) -> None:
        """
        Initialize the verifier.

        Args:
            bundle_path: Path to the `audit_bundle.zip`.
            public_key_b64: Base64-encoded Ed25519 public key of the ledger authority.
        """
        self.bundle_path = Path(bundle_path)
        self.public_key_b64 = public_key_b64

    def verify(self) -> dict[str, Any]:
        """
        Runs the verification.

        Returns:
            A dictionary report with status and details.
        """
        if not self.bundle_path.exists():
            return {"status": "INVALID", "reason": "Bundle not found."}

        try:
            with zipfile.ZipFile(self.bundle_path, "r") as zipf:
                if "metadata.json" not in zipf.namelist():
                    return {"status": "INVALID", "reason": "Missing metadata.json."}
                if "ledger_export.json" not in zipf.namelist():
                    return {"status": "INVALID", "reason": "Missing ledger_export.json."}

                metadata = json.loads(zipf.read("metadata.json"))
                if metadata.get("format") != "EU_AI_ACT_COMPLIANCE":
                    return {"status": "INVALID", "reason": "Unsupported bundle format."}

                export_data = json.loads(zipf.read("ledger_export.json"))

                return self._verify_chain(export_data)

        except Exception:  # noqa: BLE001
            logger.exception("[ComplianceVerifier] Error during verification")
            return {"status": "ERROR", "reason": "Verification failed unexpectedly."}

    def _verify_chain(self, export_data: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Iterates over the exported data to reconstruct the Merkle Root
        and verify the cryptographic signatures batch by batch.
        """
        if not export_data:
            return {"status": "VALID", "details": "Ledger is empty.", "records_verified": 0}

        # The signatures in ledger.py are generated per *batch*, meaning all items in a
        # batch share the same prev_hash and signature.
        # We need to group them.

        batches = []
        current_batch = []
        current_sig = export_data[0]["signature"]
        current_prev_hash = export_data[0]["prev_hash"]

        for row in export_data:
            if row["signature"] == current_sig and row["prev_hash"] == current_prev_hash:
                current_batch.append(row)
            else:
                batches.append((current_prev_hash, current_sig, current_batch))
                current_batch = [row]
                current_sig = row["signature"]
                current_prev_hash = row["prev_hash"]
        if current_batch:
            batches.append((current_prev_hash, current_sig, current_batch))

        # CRIT-2: Track chain linkage — each batch's prev_hash must match
        # the previous batch's computed entry_hash.
        expected_prev_hash = GENESIS_PREV_HASH
        verified_batches = 0

        for prev_hash, signature, rows in batches:
            # CRIT-2: Verify chain linkage
            if prev_hash != expected_prev_hash:
                batch_id = rows[0]["audit_id"]
                return {
                    "status": "CRITICAL_TAMPER_DETECTED",
                    "reason": (
                        f"Chain linkage broken at batch starting at {batch_id}. "
                        f"Expected prev_hash {expected_prev_hash[:16]}..., "
                        f"got {prev_hash[:16]}..."
                    ),
                }

            # CRIT-1: Reconstruct merkle root using SparseMerkleTree (matching ledger.py)
            smt = SparseMerkleTree()
            for audit_id in (r["audit_id"] for r in rows):
                smt.update(cortex_hash(audit_id.encode()), audit_id)
            merkle_root = smt.root

            # Reconstruct the entry_hash that was signed
            entry_hash = cortex_hash(f"merkle_batch:{merkle_root}:{prev_hash}".encode())

            # The signature is hex in the db. We need it in bytes for Ed25519 verification.
            try:
                sig_bytes = bytes.fromhex(signature)
            except ValueError:
                return {
                    "status": "CRITICAL_TAMPER_DETECTED",
                    "reason": f"Signature format invalid for batch starting at {rows[0]['audit_id']}.",
                }

            # Verify the signature over the entry_hash directly as ledger.py does
            try:
                import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519
                from cryptography.exceptions import InvalidSignature
                from cryptography.hazmat.primitives import serialization

                pub_bytes = base64.b64decode(self.public_key_b64)
                try:
                    public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
                except ValueError:
                    public_key = serialization.load_ssh_public_key(pub_bytes)

                public_key.verify(sig_bytes, entry_hash.encode())  # type: ignore
            except (InvalidSignature, ValueError, TypeError, OSError, KeyError):
                return {
                    "status": "CRITICAL_TAMPER_DETECTED",
                    "reason": f"Signature mismatch for batch starting at {rows[0]['audit_id']}. Ledger forged.",
                }

            # Advance chain linkage: next batch's prev_hash must equal this entry_hash
            expected_prev_hash = entry_hash
            verified_batches += 1

        return {
            "status": "VALID",
            "records_verified": len(export_data),
            "batches_verified": verified_batches,
            "details": "All Ed25519 signatures, Merkle roots, and chain linkages verified offline.",
        }
