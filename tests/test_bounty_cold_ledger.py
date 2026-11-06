# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================

from pathlib import Path
import sqlite3


from babylon60.bft.bounty_cold_ledger import BountyColdLedger
from babylon60.bft.bounty_claim_attester import BountyClaimReceipt


def _clean_sqlite_triplet(db_path: Path) -> None:
    """Aniquilación explícita del triplete SQLite para Cero-Fuga WAL."""
    for ext in ["", "-wal", "-shm"]:
        target = db_path.with_name(f"{db_path.name}{ext}")
        if target.exists():
            target.unlink()


def test_bounty_cold_ledger_async_persistence(tmp_path: Path) -> None:
    """Valida la persistencia asíncrona de recibos SCITT fuera de la ruta caliente."""
    db_file = tmp_path / "test_ledger.db"
    _clean_sqlite_triplet(db_file)

    try:
        ledger = BountyColdLedger(db_path=str(db_file))
        ledger.start()

        # Generar un recibo mock
        receipt = BountyClaimReceipt(
            claim_id="CLAIM-MOCK-123",
            advisory_id="GHSA-mock",
            domain="DOMAIN_AI",
            finding_summary="Mock risk",
            risk_score=0.99,
            payload_hash="abcd1234abcd",
            timestamp_utc="2026-09-12T00:00:00Z",
            hardware_anchor="MOCK-UUID",
            attestation_merkle_root="root123",
        )

        # Encolar de forma asíncrona (lock-free en la ruta caliente)
        success = ledger.enqueue_receipt(receipt)
        assert success is True

        # Forzar el drenaje esperando al thread
        ledger.stop()

        # Validar persistencia en SQLite
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        cursor.execute("SELECT claim_id, advisory_id, risk_score FROM bounty_claims WHERE claim_id = 'CLAIM-MOCK-123'")
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == "CLAIM-MOCK-123"
        assert row[1] == "GHSA-mock"
        assert row[2] == 0.99

    finally:
        # Aislamiento de Persistencia en Tests (INV_C5_SHM)
        _clean_sqlite_triplet(db_file)
