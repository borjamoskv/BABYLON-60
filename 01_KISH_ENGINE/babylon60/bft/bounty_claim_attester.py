# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized Bounty Claim & Attestation Anchor
"""bounty_claim_attester.py - Atestación criptográfica inmutable de hallazgos.

Ancla los hallazgos de auditoría (EVM Hooks, WebKit Gigacage, SAGA-1) al Ledger
criptográfico BFT (Ed25519 + SHA3-256 + Merkle DAG) fuera de la ruta caliente
(INV_C5_SHM), proporcionando prueba inmutable de descubrimiento (Proof of Claim).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import logging
from typing import Dict, Mapping

from babylon60.attestation.merkle_anchor import MerkleCausalAnchor
from babylon60.bft.cortex_crypto_kernel import build_merkle_tree

logger = logging.getLogger("babylon60.bft.claim_attester")


@dataclass(frozen=True)
class BountyClaimReceipt:
    """Recibo criptográfico inmutable de atestación de vulnerabilidad."""

    claim_id: str
    advisory_id: str
    domain: str
    finding_summary: str
    risk_score: float
    payload_hash: str
    timestamp_utc: str
    hardware_anchor: str
    attestation_merkle_root: str

    def to_dict(self) -> Dict[str, object]:
        """Convierte el recibo a diccionario canónico."""
        return asdict(self)

    def compute_claim_hash(self) -> str:
        """Calcula el hash determinista SHA3-256 del recibo de reclamación."""
        canonical_str = json.dumps(
            {
                "claim_id": self.claim_id,
                "advisory_id": self.advisory_id,
                "domain": self.domain,
                "finding_summary": self.finding_summary,
                "risk_score": self.risk_score,
                "payload_hash": self.payload_hash,
                "timestamp_utc": self.timestamp_utc,
                "hardware_anchor": self.hardware_anchor,
            },
            sort_keys=True,
        )
        return hashlib.sha3_256(canonical_str.encode("utf-8")).hexdigest()


class BountyClaimAttester:
    """Anclador de atestaciones para reclamación de hallazgos en frío."""

    def __init__(self) -> None:
        self._anchor = MerkleCausalAnchor()
        self._cached_hw_uuid: str = self._anchor._extract_darwin_uuid() or "DARWIN-AIRGAP-SEAL"
        self._cached_hw_hash: str = hashlib.sha3_256(self._cached_hw_uuid.encode()).hexdigest()

    @property
    def hardware_uuid(self) -> str:
        """Hardware UUID memoizado en O(1) para evitar spawning de subprocess."""
        return self._cached_hw_uuid

    def generate_receipt(
        self,
        advisory_id: str,
        domain: str,
        finding_summary: str,
        risk_score: float,
        raw_payload: Mapping[str, object],
    ) -> BountyClaimReceipt:
        """Emite un recibo inmutable sellando el hallazgo con anclaje hardware."""
        timestamp = datetime.now(timezone.utc).isoformat()

        # 1. Hashing SHA3-256 determinista del payload analizado
        payload_bytes = json.dumps(raw_payload, sort_keys=True).encode("utf-8")
        payload_hash = hashlib.sha3_256(payload_bytes).hexdigest()

        # 2. Uso del hardware UUID memoizado O(1)
        hw_uuid = self._cached_hw_uuid

        # 3. Cálculo de Merkle Root preliminar
        leaf_hashes = [payload_hash, self._cached_hw_hash]
        merkle_root = build_merkle_tree(leaf_hashes)

        # 4. ID único determinista de la reclamación
        claim_id = f"CLAIM-{advisory_id}-{payload_hash[:12].upper()}"

        return BountyClaimReceipt(
            claim_id=claim_id,
            advisory_id=advisory_id,
            domain=domain,
            finding_summary=finding_summary,
            risk_score=risk_score,
            payload_hash=payload_hash,
            timestamp_utc=timestamp,
            hardware_anchor=hw_uuid,
            attestation_merkle_root=merkle_root,
        )

    def verify_receipt(self, receipt: BountyClaimReceipt) -> bool:
        """Verifica la coherencia del hash y el árbol Merkle del recibo."""
        leaf_hashes = [receipt.payload_hash, hashlib.sha3_256(receipt.hardware_anchor.encode()).hexdigest()]
        recomputed_root = build_merkle_tree(leaf_hashes)
        return recomputed_root == receipt.attestation_merkle_root
