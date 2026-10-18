"""
Acceptance Test Suite for BABYLON-60 M0: COMPLIANCE AS CODE (`babylon-m0-evidence-pack/`)
=========================================================================================
Verifies:
  1. Complete directory tree & deterministic compilation from canonical `CLAIMS.toml`.
  2. Dynamic claims cardinality (no hardcoded 21/23 claim count assumption).
  3. Rule 1.A: Multi-framework regulatory contribution matrix (AI Act, DORA, NIS2,
     ISO/IEC 42001, SOC 2) with zero automatic `COMPLIANT` verdicts.
  4. Rule 1.B & 1.C: Explicit `BROKER_MEDIATED` vs `OS_ENFORCED` boundaries and
     SQLite threat model (hash-chaining + cardinality anchor vs `DROP TRIGGER`).
  5. Section 3 Mandatory Negative Tests:
     - Deliberate mutation of a SQLite ledger record -> rejected by standalone verifier.
     - Deliberate alteration of `verification/signature.sig` -> rejected by standalone verifier.
     - Real bypass discovered by NEMESIS -> compiler emits `FALSIFIED` or
       `UNSUPPORTED_WITHIN_SCOPE` and verifier rejects masked contradictions.
  6. Section 4 Commercial Wedge: Canonical demonstration statement and TTVE metric.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from babylon60.compliance_exporter.m0_evidence_pack import (
    CANONICAL_DEMO_STATEMENT,
    M0EvidencePackCompiler,
)
from babylon60.verifier.cli import main as verifier_cli_main
from babylon60.verifier.standalone_verify import verify_m0_evidence_pack


def test_m0_evidence_pack_end_to_end_and_cli_verification(tmp_path: Path) -> None:
    pack_dir = tmp_path / "babylon-m0-evidence-pack"
    compiler = M0EvidencePackCompiler()
    manifest = compiler.compile_pack(pack_dir)

    # 1. Verify exact deliverable layout
    expected_files = [
        "manifest.json",
        "claims.json",
        "scope.json",
        "environment.json",
        "evidence/ledger_l0.sqlite",
        "evidence/execution-trace.jsonl",
        "evidence/nemesis-results.json",
        "evidence/formal-proofs.json",
        "compliance/regulatory-matrix.json",
        "compliance/auditor-report.pdf",
        "verification/checksums.sha256",
        "verification/signature.sig",
        "verification/verifier-metadata.json",
        "README.md",
    ]
    for rel in expected_files:
        assert (pack_dir / rel).is_file(), f"Missing required deliverable file: {rel}"

    # 2. Verify PDF header and canonical executive statement
    pdf_bytes = (pack_dir / "compliance/auditor-report.pdf").read_bytes()
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"The agent attempted an unauthorized action." in pdf_bytes
    assert manifest["executive_statement"] == CANONICAL_DEMO_STATEMENT

    # 3. Verify TTVE metric & 3 product capabilities
    assert isinstance(manifest["metrics"]["ttve_ms"], (int, float))
    assert manifest["metrics"]["ttve_ms"] > 0
    caps = manifest["product_capabilities"]
    assert caps["trust_gateway"] == "BABYLON-60 Trust Gateway"
    assert caps["evidence_engine"] == "BABYLON-60 Evidence Engine"
    assert caps["deliverable"] == "BABYLON-60 Compliance Evidence Pack"

    # 4. Verify Rule 1.A: Multi-framework regulatory matrix never emits automatic COMPLIANT
    reg_matrix = json.loads((pack_dir / "compliance/regulatory-matrix.json").read_text(encoding="utf-8"))
    framework_ids = {m["framework_id"] for m in reg_matrix["mappings"]}
    assert framework_ids == {
        "EU_AI_ACT_ART_12",
        "EU_AI_ACT_ART_14",
        "EU_AI_ACT_ART_15",
        "EU_AI_ACT_ANNEX_IV",
        "DORA_ARTS_9_10",
        "NIS2_ART_21",
        "ISO_IEC_42001",
        "SOC2_TRUST_SERVICES",
    }
    for m in reg_matrix["mappings"]:
        assert m["automated_compliance_verdict_permitted"] is False
        assert m["assessment_status"] != "COMPLIANT"
        assert m["causal_chain_stage"] == "CONTROL -> TEST -> EVIDENCE -> REGULATORY_REQUIREMENT -> ASSESSMENT"

    # 5. Verify Rule 1.B & 1.C: BROKER_MEDIATED vs OS_ENFORCED and SQLite threat model
    scope_doc = json.loads((pack_dir / "scope.json").read_text(encoding="utf-8"))
    assert "BROKER_MEDIATED" in scope_doc["enforcement_boundaries"]
    assert "OS_ENFORCED" in scope_doc["enforcement_boundaries"]
    assert scope_doc["enforcement_boundaries"]["OS_ENFORCED"]["claims_count"] >= 1
    assert "DROP TRIGGER" in scope_doc["sqlite_ledger_threat_model"]["why_sqlite_triggers_are_insufficient"]

    # 6. Verify independent verification via Python API and CLI
    verdict = verify_m0_evidence_pack(pack_dir)
    assert verdict["valid"] is True
    assert verdict["signature_valid"] is True
    assert verdict["merkle_valid"] is True
    assert verdict["checksums_valid"] is True
    assert verdict["epistemic_status"] == "EVIDENCE_VERIFIABLE_WITHIN_DECLARED_SCOPE"

    exit_code = verifier_cli_main(["--pack", str(pack_dir), "--json"])
    assert exit_code == 0


def test_m0_compiler_dynamic_claims_cardinality_without_hardcoded_count(tmp_path: Path) -> None:
    """
    Rule 2: The compiler must read the canonical registry dynamically without
    assuming 21, 23, or 24 claims.
    """
    custom_claims_toml = tmp_path / "CUSTOM_CLAIMS.toml"
    custom_claims_toml.write_text(
        """
[metadata]
version = "5.0.0-custom"
root_axiom = "INV-OMEGA"

[claim.C_01]
statement = "Broker mediated capability check"
status = "verified"
evidence_level = "L2_IMPLEMENTATION"
component = "00_ABZU_KERNEL"

[claim.C_02]
statement = "OS enforced Seatbelt sandbox confinement"
status = "verified_local"
evidence_level = "L3_ISOLATION"
scope = "macOS sandbox-exec Seatbelt profile"
component = "00_ABZU_KERNEL"

[claim.C_03]
statement = "Experimental hardware enclave trace"
status = "experimental"
evidence_level = "L4_EXPERIMENTAL"
component = "00_ABZU_KERNEL"
""".strip(),
        encoding="utf-8",
    )

    pack_dir = tmp_path / "dynamic-pack"
    compiler = M0EvidencePackCompiler(claims_toml_path=custom_claims_toml)
    manifest = compiler.compile_pack(pack_dir)

    assert manifest["metrics"]["total_claims"] == 3
    assert manifest["metrics"]["supported_within_scope"] == 2
    assert manifest["metrics"]["untested"] == 1

    claims_doc = json.loads((pack_dir / "claims.json").read_text(encoding="utf-8"))
    assert claims_doc["total_claims_compiled"] == 3
    assert claims_doc["claims"]["C_01"]["enforcement_mode"] == "BROKER_MEDIATED"
    assert claims_doc["claims"]["C_02"]["enforcement_mode"] == "OS_ENFORCED"
    assert claims_doc["claims"]["C_03"]["status"] == "UNTESTED"

    verdict = verify_m0_evidence_pack(pack_dir)
    assert verdict["valid"] is True
    assert verdict["total_claims"] == 3


def test_m0_deliberate_negative_tamper_sqlite_record_rejected(tmp_path: Path) -> None:
    """
    Section 3 Negative Test A: Modifying a record in `evidence/ledger_l0.sqlite`
    must cause independent verification to fail deterministically.
    """
    pack_dir = tmp_path / "tampered-sqlite-pack"
    M0EvidencePackCompiler().compile_pack(pack_dir)

    ledger_path = pack_dir / "evidence/ledger_l0.sqlite"
    conn = sqlite3.connect(str(ledger_path))
    try:
        conn.execute("UPDATE cortex_ledger SET payload_json = '{\"tampered\":true}' WHERE seq = 1")
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    finally:
        conn.close()

    verdict = verify_m0_evidence_pack(pack_dir)
    assert verdict["valid"] is False
    assert verdict["epistemic_status"] in {"FILE_TAMPERED", "LEDGER_TAMPERED"}
    assert verifier_cli_main(["--pack", str(pack_dir), "--quiet"]) == 1


def test_m0_deliberate_negative_altered_signature_rejected(tmp_path: Path) -> None:
    """
    Section 3 Negative Test B: Altering `verification/signature.sig` must cause
    independent verification to fail with `SIGNATURE_INVALID`.
    """
    pack_dir = tmp_path / "tampered-sig-pack"
    M0EvidencePackCompiler().compile_pack(pack_dir)

    sig_path = pack_dir / "verification/signature.sig"
    orig_sig = sig_path.read_text(encoding="utf-8").strip()
    flipped_first = "0" if orig_sig[0] != "0" else "1"
    sig_path.write_text(flipped_first + orig_sig[1:] + "\n", encoding="utf-8")

    verdict = verify_m0_evidence_pack(pack_dir)
    assert verdict["valid"] is False
    assert verdict["signature_valid"] is False
    assert verdict["epistemic_status"] == "SIGNATURE_INVALID"
    assert verifier_cli_main(["--pack", str(pack_dir), "--quiet"]) == 1


def test_m0_deliberate_negative_nemesis_bypass_emits_falsified_and_unsupported(tmp_path: Path) -> None:
    """
    Section 3 Negative Test C: If NEMESIS discovers a real bypass, the system must
    emit `FALSIFIED` or `UNSUPPORTED_WITHIN_SCOPE` (never hide the result), and the
    independent verifier must flag the pack as non-passing (`valid == False`).
    """
    # Case 1: Real bypass inside declared scope -> FALSIFIED
    nemesis_falsified = {
        "schema": "babylon60.m0.nemesis_results.v1",
        "agent_role": "NEMESIS",
        "campaigns": {
            "BYPASS-REAL-001": {
                "target_claims": ["INV_OMEGA_complete_mediation"],
                "attack_vector": "unconfined_child_helper_direct_write",
                "enforcement_mode_tested": "OS_ENFORCED",
                "bypass_detected": True,
                "enforcement_gap": "UNMEDIATED_OS_PATH",
                "detail": "Direct write succeeded via unconfined helper",
                "outcome": "FALSIFIED",
            }
        },
    }
    pack_falsified = tmp_path / "falsified-pack"
    manifest_f = M0EvidencePackCompiler().compile_pack(pack_falsified, nemesis_override=nemesis_falsified)
    assert manifest_f["metrics"]["falsified"] == 1
    assert manifest_f["epistemic_status"] == "FALSIFIED_OR_UNSUPPORTED_CONTROLS_DETECTED"

    verdict_f = verify_m0_evidence_pack(pack_falsified)
    assert verdict_f["valid"] is False
    assert verdict_f["signature_valid"] is True
    assert verdict_f["epistemic_status"] == "FALSIFIED"
    assert "INV_OMEGA_complete_mediation" in verdict_f["falsified_claims"]

    # Case 2: Bypass outside broker scope without OS enforcement -> UNSUPPORTED_WITHIN_SCOPE
    nemesis_unsupported = {
        "schema": "babylon60.m0.nemesis_results.v1",
        "agent_role": "NEMESIS",
        "campaigns": {
            "BYPASS-SCOPE-002": {
                "target_claims": ["AUTH_002"],
                "attack_vector": "direct_posix_open_outside_broker_perimeter",
                "enforcement_mode_tested": "BROKER_MEDIATED",
                "bypass_detected": True,
                "enforcement_gap": "OUTSIDE_BROKER_SCOPE_NO_OS_ENFORCEMENT",
                "detail": "Broker-only mode does not intercept direct POSIX open()",
                "outcome": "FALSIFIED",
            }
        },
    }
    pack_unsupported = tmp_path / "unsupported-pack"
    manifest_u = M0EvidencePackCompiler().compile_pack(pack_unsupported, nemesis_override=nemesis_unsupported)
    assert manifest_u["metrics"]["unsupported_within_scope"] == 1

    verdict_u = verify_m0_evidence_pack(pack_unsupported)
    assert verdict_u["valid"] is False
    assert verdict_u["signature_valid"] is True
    assert verdict_u["epistemic_status"] == "UNSUPPORTED_WITHIN_SCOPE"
    assert "AUTH_002" in verdict_u["unsupported_claims"]
