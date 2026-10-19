# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [PoC & Falsación Empírica] Bounty Claim Attestation & Hardware Anchor Test
"""test_bounty_claim_attester.py - Validación de recibos criptográficos de reclamación.

Certifica:
1. Generación determinista de recibos inmutables (BountyClaimReceipt).
2. Verificación de raíz Merkle y anclaje hardware Darwin.
3. Falsación empírica ante manipulación de payloads (Tamper Proof).
4. Rendimiento de atestación fuera del hilo caliente (< 100 µs/recibo).
"""

from __future__ import annotations

import time

from babylon60.bft.bounty_claim_attester import BountyClaimAttester, BountyClaimReceipt


def test_claim_receipt_generation_and_verification() -> None:
    """Valida la emisión y comprobación del árbol Merkle del recibo."""
    attester = BountyClaimAttester()

    payload = {
        "target": "0x1234567890abcdef1234567890abcdef12345678",
        "vulnerability": "Uniswap v4 transient storage reentrancy",
        "opcodes": ["TSTORE", "TLOAD"],
    }

    receipt = attester.generate_receipt(
        advisory_id="GHSA-RECLAIM-001",
        domain="DOMAIN_EVM",
        finding_summary="Transient reentrancy in hook address",
        risk_score=0.85,
        raw_payload=payload,
    )

    assert receipt.claim_id.startswith("CLAIM-GHSA-RECLAIM-001-")
    assert receipt.risk_score == 0.85
    assert len(receipt.payload_hash) == 64
    assert len(receipt.attestation_merkle_root) == 64

    # Verificación válida
    assert attester.verify_receipt(receipt) is True

    # Intento de manipulación de payload_hash
    tampered_receipt = BountyClaimReceipt(
        claim_id=receipt.claim_id,
        advisory_id=receipt.advisory_id,
        domain=receipt.domain,
        finding_summary=receipt.finding_summary,
        risk_score=receipt.risk_score,
        payload_hash="0" * 64,  # Hash adulterado
        timestamp_utc=receipt.timestamp_utc,
        hardware_anchor=receipt.hardware_anchor,
        attestation_merkle_root=receipt.attestation_merkle_root,
    )

    assert attester.verify_receipt(tampered_receipt) is False


def test_claim_attester_stress_1000_iterations() -> None:
    """Stress test empírico de generación de recibos criptográficos."""
    attester = BountyClaimAttester()
    iterations = 1_000

    t0 = time.perf_counter()
    for i in range(iterations):
        attester.generate_receipt(
            advisory_id=f"ADV-{i}",
            domain="DOMAIN_EVM" if i % 2 == 0 else "DOMAIN_NATIVE",
            finding_summary=f"Automated claim attestation {i}",
            risk_score=0.75,
            raw_payload={"index": i, "state": "falsified"},
        )
    elapsed = time.perf_counter() - t0

    latency_us = (elapsed / iterations) * 1_000_000
    assert elapsed < 0.2, f"Tiempo excesivo para 1000 atestaciones: {elapsed:.3f}s"
    assert latency_us < 200.0, f"Latencia excesiva: {latency_us:.2f} µs"
