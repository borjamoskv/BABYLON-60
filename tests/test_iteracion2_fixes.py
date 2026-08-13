# ============================================================================
# BABYLON-60 Iteración 2 — Verification Test Suite
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================

import pytest
from pathlib import Path
from babylon60.bft.cortex_persist_ledger import CortexPersistLedger, CortexEvent, compute_cortex_hash
from babylon60.crypto.hash_registry import (
    cortex_hash_truncated,
    cortex_hmac,
    cortex_hmac_b60,
    configure,
    HashAlgorithm,
)
from babylon60.compliance_exporter.eu_ai_act import EUAIActComplianceExporter
from babylon60.compliance_exporter.i18n import get_translation


def test_ledger_provenance_hash_sensitivity(tmp_path: Path) -> None:
    """
    Validates that two events differing ONLY in agent_id or domain
    produce different entry_hash values and do not collide.
    """
    db_path = tmp_path / "provenance_test.db"
    ledger = CortexPersistLedger(db_path)

    ev1 = CortexEvent(
        event_type="AGENT_EXECUTION",
        payload={"action": "RUN_TOOL"},
        cortex_taint="C5_REAL_TAINT_01",
        agent_id="AGENT_ALPHA",
        domain="babylon60.com",
    )

    ev2 = CortexEvent(
        event_type="AGENT_EXECUTION",
        payload={"action": "RUN_TOOL"},
        cortex_taint="C5_REAL_TAINT_01",
        agent_id="AGENT_BETA",  # Different agent_id
        domain="babylon60.com",
    )

    h1 = compute_cortex_hash(
        seq=1,
        event_id="evt_01",
        event_type=ev1.event_type,
        payload_json='{"action":"RUN_TOOL"}',
        cortex_taint=ev1.cortex_taint,
        lamport_t=1,
        prev_hash="0" * 64,
        timestamp="2026-08-13T00:00:00Z",
        agent_id=ev1.agent_id,
        domain=ev1.domain,
    )

    h2 = compute_cortex_hash(
        seq=1,
        event_id="evt_01",
        event_type=ev2.event_type,
        payload_json='{"action":"RUN_TOOL"}',
        cortex_taint=ev2.cortex_taint,
        lamport_t=1,
        prev_hash="0" * 64,
        timestamp="2026-08-13T00:00:00Z",
        agent_id=ev2.agent_id,
        domain=ev2.domain,
    )

    assert h1 != h2, "Hashes must differ when agent_id differs!"

    # Append to ledger and verify integrity
    res1 = ledger.append_event(ev1)
    res2 = ledger.append_event(ev2)

    assert res1["entry_hash"] != res2["entry_hash"]
    assert ledger.verify_integrity() is True


def test_hash_registry_truncated_hex() -> None:
    """
    Validates that cortex_hash_truncated returns a valid hex string of requested length.
    """
    data = b"babylon60_test_payload"
    short_hash = cortex_hash_truncated(data, length=16)

    assert len(short_hash) == 16
    # Check that all characters are hex characters
    int(short_hash, 16)


def test_hash_registry_hmac_sha256_and_sha3() -> None:
    """
    Validates that cortex_hmac and cortex_hmac_b60 operate safely across hash algorithms without errors.
    """
    key = "secret_key"
    data = "test_message"

    # Default SHA256
    configure(HashAlgorithm.SHA256)
    mac1 = cortex_hmac(key, data)
    assert len(mac1) == 64

    # SHA3-256 (should fallback to standard HMAC-SHA256 without CPython class errors)
    configure(HashAlgorithm.SHA3_256)
    mac2 = cortex_hmac(key, data)
    mac_b60 = cortex_hmac_b60(key, data)

    assert len(mac2) == 64
    assert len(mac_b60) > 0

    # Reset default
    configure(HashAlgorithm.SHA256)


def test_compliance_exporter_self_assessment_disclaimer(tmp_path: Path) -> None:
    """
    Validates that EUAIActComplianceExporter generates self-assessment reports
    with explicit legal disclaimers.
    """
    # Create mock manifest
    bundle_dir = tmp_path / "mock_bundle"
    bundle_dir.mkdir(parents=True)
    manifest_file = bundle_dir / "manifest.json"
    manifest_file.write_text('{"global_hash": "0x123456789abcdef"}', encoding="utf-8")

    exporter = EUAIActComplianceExporter(artifact_bundle_path=str(bundle_dir))
    report = exporter.generate_report(system_id="SYS_ALPHA", operator_name="OPERATOR_X", locale="es")

    assert "Informe de Auto-Evaluación" in report["title"]
    assert "legal_disclaimer" in report
    assert "Organismo Notificado" in report["legal_disclaimer"]

    # Test i18n English
    report_en = exporter.generate_report(system_id="SYS_ALPHA", operator_name="OPERATOR_X", locale="en")
    assert "Self-Assessment Report" in report_en["title"]
    assert "Notified Body" in report_en["legal_disclaimer"]
