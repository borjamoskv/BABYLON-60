# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""test_bounty_aeon_sealer.py — Validación de Transición de Aeón Conforme (INV_C5_AEON).

Comprueba con claves de software y datos temporales:
1. Construcción y verificación de pruebas de inclusión en ConformalMerkleTree.
2. Detección determinista de adulteración en pruebas de Merkle.
3. Manifiesto de un Cold Ledger autenticado con Ed25519 y ancla externa;
   UUID y TSA son registradores de prueba, sin atestación hardware o temporal real.
4. Aislamiento estricto de persistencia en temp_dir() (Cero-Fuga WAL).
"""

from __future__ import annotations

import base64
import importlib
import json
from pathlib import Path
from types import ModuleType

import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

from babylon60.attestation import (
    AeonVerifier,
    ConformalMerkleTree,
    MerkleCausalAnchor,
    extract_claims_from_ledger as extract_claims_for_sealing,
)
from babylon60.attestation.conformal_tree import canonical_aeon_manifest_bytes
from babylon60.bft.bounty_claim_attester import BountyClaimReceipt
from babylon60.bft.bounty_cold_ledger import BountyColdLedger
from babylon60.bft.bounty_remediation import synthesize_domain_remediation


@pytest.fixture(autouse=True)
def isolated_aeon_environment(tmp_path, monkeypatch):
    """Set the temporary environment before loading scripts with effect boundaries."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BABYLON60_SIGNING_SEED", "00" * 32)
    monkeypatch.delenv("CORTEX_VAULT_KEY", raising=False)
    monkeypatch.delenv("BABYLON_AEON_TRUSTED_PUBLIC_KEY_B64", raising=False)
    import dotenv

    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.setattr(dotenv, "dotenv_values", lambda *args, **kwargs: {})
    monkeypatch.setattr(
        MerkleCausalAnchor,
        "get_hardware_identity",
        lambda self: {"uuid": "TEST-SOFTWARE-UUID", "os": "Fixture", "machine": "Test", "enclave_type": "FIXTURE"},
    )


@pytest.fixture
def sealer(tmp_path, monkeypatch, isolated_aeon_environment):
    module = importlib.import_module("scripts.c5_l1_ledger.seal_bounty_aeon")
    monkeypatch.setattr(module, "_ROOT", tmp_path)
    monkeypatch.setattr(module.RFC3161Client, "request_timestamp", lambda self, root: {})
    return module


def _clean_sqlite_triplet(db_path: Path) -> None:
    """Aniquilación explícita del triplete SQLite para Cero-Fuga WAL."""
    for ext in ["", "-wal", "-shm"]:
        target = db_path.with_name(f"{db_path.name}{ext}")
        if target.exists():
            target.unlink()


def test_conformal_merkle_tree_inclusion_and_falsification() -> None:
    """Valida la generación de pruebas O(log N) y su resistencia a la adulteración."""
    leaves = [f"leaf_hash_{i:04d}" for i in range(17)]  # Número impar para probar padding
    tree = ConformalMerkleTree(leaves)

    assert tree.root is not None
    assert len(tree.root) == 64  # SHA3-256 hex string

    # 1. Validar inclusión de cada una de las 17 hojas
    for i, leaf in enumerate(leaves):
        proof = tree.get_inclusion_proof(i)
        is_valid = ConformalMerkleTree.verify_inclusion_proof(leaf, proof, tree.root)
        assert is_valid is True, f"Fallo al verificar inclusión de hoja #{i}"

    # 2. Falsación empírica: hoja adulterada debe ser rechazada
    tampered_leaf = "leaf_hash_TAMPERED"
    proof_0 = tree.get_inclusion_proof(0)
    assert ConformalMerkleTree.verify_inclusion_proof(tampered_leaf, proof_0, tree.root) is False

    # 3. Falsación empírica: raíz errónea debe ser rechazada
    fake_root = "0" * 64
    assert ConformalMerkleTree.verify_inclusion_proof(leaves[0], proof_0, fake_root) is False


def test_aeon_sealing_end_to_end(tmp_path: Path, sealer: ModuleType) -> None:
    """Autentica un manifiesto completo con identidad de software temporal."""
    db_file = tmp_path / "test_aeon_ledger.db"
    out_dir = tmp_path / "L1_sink_test"
    _clean_sqlite_triplet(db_file)

    try:
        # 1. Poblar un Cold Ledger con atestaciones de prueba
        ledger = BountyColdLedger(db_path=str(db_file))
        ledger.start()

        domains = ["DOMAIN_EVM", "DOMAIN_NATIVE", "DOMAIN_AI"]
        for i in range(15):
            receipt = BountyClaimReceipt(
                claim_id=f"CLAIM-TEST-{i:03d}",
                advisory_id=f"GHSA-TEST-{i:03d}",
                domain=domains[i % 3],
                finding_summary=f"Synthetic risk pattern #{i}",
                risk_score=0.85,
                payload_hash=f"hash_{i:04d}",
                timestamp_utc="2026-09-12T20:00:00Z",
                hardware_anchor="HARDWARE-TEST-UUID",
                attestation_merkle_root=f"merkle_{i:04d}",
            )
            ledger.enqueue_receipt(receipt)

        ledger.stop()

        # 2. Verificar extracción determinista
        claims = extract_claims_for_sealing(str(db_file))
        assert len(claims) == 15

        # 3. Ejecutar sellado L1
        aeon_id = "AEON-TEST-OMEGA"
        artifact = sealer.seal_bounty_aeon(
            db_path=str(db_file),
            aeon_id=aeon_id,
            output_dir=str(out_dir),
        )

        assert artifact["aeon_id"] == aeon_id
        assert artifact["total_claims_sealed"] == 15
        assert artifact["status"] == "FROZEN_C5_REAL"
        assert len(artifact["merkle_root"]) == 64
        assert artifact["op_return_hex"] == artifact["merkle_root"]
        assert "hardware_attestation" in artifact
        assert "rfc3161_tsa" in artifact
        assert "sovereign_identity" in artifact

        # 4. Validar firma Ed25519 sobre todos los campos del manifiesto v2.
        pub_b64 = artifact["sovereign_identity"]["l0_public_key_b64"]
        sig_b64 = artifact["sovereign_identity"]["ed25519_signature_b64"]
        pub_bytes = base64.b64decode(pub_b64)
        sig_bytes = base64.b64decode(sig_b64)
        pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)

        # La verificación no debe lanzar InvalidSignature
        pub_key.verify(sig_bytes, canonical_aeon_manifest_bytes(artifact))
        assert artifact["schema"] == "babylon60.aeon-manifest.v2"
        assert artifact["hardware_attestation"]["hardware_attestation_verified"] is False
        assert artifact["hardware_attestation"]["attestation_status"] == "SOFTWARE_ONLY_UNATTESTED"

        # 5. Validar que el archivo JSON fue escrito correctamente en disco
        target_json = out_dir / f"{aeon_id.lower().replace('-', '_')}.json"
        assert target_json.exists()
        loaded = json.loads(target_json.read_text(encoding="utf-8"))
        assert loaded["merkle_root"] == artifact["merkle_root"]

        # 6. Validar mediante AeonVerifier (Oráculo L1)
        v_report = AeonVerifier.verify_manifest(
            manifest_path=target_json, db_path=str(db_file), expected_public_key_b64=pub_b64
        )
        assert v_report["overall_valid"] is True
        assert v_report["tree_integrity_valid"] is True
        assert v_report["ed25519_signature_valid"] is True
        assert v_report["recomputed_claims_count"] == 15
        assert v_report["identity_trusted"] is True
        assert v_report["hardware_attestation_verified"] is False
        assert v_report["verification_scope"] == "AUTHENTICATED_MANIFEST_AND_LEDGER"
        assert AeonVerifier.verify_manifest(target_json, db_file)["overall_valid"] is False
        assert (
            AeonVerifier.verify_manifest(target_json, db_file, expected_public_key_b64=pub_b64, require_hardware=True)[
                "overall_valid"
            ]
            is False
        )

        # 7. Validar prueba de inclusión de un claim mediante AeonVerifier
        c_report = AeonVerifier.verify_claim_membership(
            claim_id="CLAIM-TEST-005",
            manifest_path=target_json,
            db_path=str(db_file),
        )
        assert c_report["is_valid_inclusion"] is True
        assert c_report["proof_steps"] > 0
        assert c_report["claim_id"] == "CLAIM-TEST-005"

    finally:
        _clean_sqlite_triplet(db_file)


def test_exfiltration_remediation_heuristics(tmp_path: Path) -> None:
    """Valida la generación de planes de mitigación deterministas por dominios."""
    db_file = tmp_path / "test_exfilt_ledger.db"
    from scripts.c5_sharur.c5_bounty_sharur_exfiltration import fetch_scitt_claims

    _clean_sqlite_triplet(db_file)

    try:
        ledger = BountyColdLedger(db_path=str(db_file))
        ledger.start()

        # Insertar 3 hallazgos canónicos
        claims_input = [
            ("CLAIM-EVM-1", "GHSA-EVM-1", "DOMAIN_EVM", "TSTORE collision in proxy"),
            ("CLAIM-NAT-1", "GHSA-NAT-1", "DOMAIN_NATIVE", "Use-After-Free in IsoMalloc"),
            ("CLAIM-AI-1", "GHSA-AI-1", "DOMAIN_AI", "Unsafe pickle deserialization in PyTorch"),
        ]
        for cid, adv, dom, summary in claims_input:
            ledger.enqueue_receipt(
                BountyClaimReceipt(
                    claim_id=cid,
                    advisory_id=adv,
                    domain=dom,
                    finding_summary=summary,
                    risk_score=0.9,
                    payload_hash="hash123",
                    timestamp_utc="2026-09-12T20:00:00Z",
                    hardware_anchor="UUID",
                    attestation_merkle_root="root",
                )
            )
        ledger.stop()

        claims = fetch_scitt_claims(str(db_file), limit=10)
        assert len(claims) == 3

        for c in claims:
            remediation = synthesize_domain_remediation(c)
            assert len(remediation) > 20
            if c["domain"] == "DOMAIN_EVM":
                assert "EIP-1153" in remediation or "SKILL 41" in remediation
            elif c["domain"] == "DOMAIN_NATIVE":
                assert "WEBKIT" in remediation or "IsoMalloc" in remediation
            elif c["domain"] == "DOMAIN_AI":
                assert "MUSHUSHU-0" in remediation or "SafeTensors" in remediation

    finally:
        _clean_sqlite_triplet(db_file)
