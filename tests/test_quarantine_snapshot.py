# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import hashlib
import json

class MockQuarantineSnapshot:
    def __init__(self, timestamp: int, causal_hash: str, payload: dict):
        self.timestamp = timestamp
        self.causal_hash = causal_hash
        self.payload = payload
        self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        serialized = f"{self.timestamp}:{self.causal_hash}:{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def verify_integrity(self) -> bool:
        return self._compute_checksum() == self.checksum


def test_quarantine_snapshot_integrity_pass():
    snapshot = MockQuarantineSnapshot(
        timestamp=1000,
        causal_hash="0000000000000000000000000000000000000000000000000000000000000000",
        payload={"event": "CRITICAL_HALT", "reason": "CausalInversionDetected"}
    )
    assert snapshot.verify_integrity() is True


def test_quarantine_snapshot_integrity_fail_on_tampering():
    snapshot = MockQuarantineSnapshot(
        timestamp=1000,
        causal_hash="0000000000000000000000000000000000000000000000000000000000000000",
        payload={"event": "CRITICAL_HALT", "reason": "CausalInversionDetected"}
    )
    # Alter payload after instantiation
    snapshot.payload["reason"] = "AlteredReason"
    assert snapshot.verify_integrity() is False
