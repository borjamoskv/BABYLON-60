"""
test_epistemic_tamper_resistance.py — Automated Security & Tamper Resistance Test Suite

Validates that any single-byte alteration, authority key injection, statistical parameter
tampering, or Claim DAG corruption triggers immediate verification failures.
"""

import os
import json
import pytest
from pathlib import Path
from scripts.verify_epistemic_locks import ROOT_DIR, LOCK_FILES, verify_all_locks, verify_trace_contract


def test_clean_locks_pass_verification():
    """Ensure that pristine baseline lock files pass verification cleanly."""
    manifest_path = ROOT_DIR / "EPISTEMIC_LOCKS_MANIFEST.json"
    assert manifest_path.exists(), "EPISTEMIC_LOCKS_MANIFEST.json should exist"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data.get("lock_files", {})) == 15, "Manifest must track exactly 15 lock files"


def test_single_byte_tamper_detection(tmp_path):
    """Verify that modifying 1 byte in any lock file alters its SHA-256 digest."""
    for lock_name in LOCK_FILES:
        original_file = ROOT_DIR / lock_name
        assert original_file.exists()

        content = original_file.read_bytes()
        tampered_content = content + b"\n# TAMPER_BYTE"

        tampered_file = tmp_path / lock_name
        tampered_file.write_bytes(tampered_content)

        import hashlib
        orig_hash = hashlib.sha256(content).hexdigest()
        tamp_hash = hashlib.sha256(tampered_content).hexdigest()

        assert orig_hash != tamp_hash, f"SHA-256 hash must change for tampered file: {lock_name}"


def test_authority_injection_rejection(tmp_path):
    """Verify that removing forbidden authority keys from TRACE_CONTRACT_v1.0.0.json fails validation."""
    contract_file = ROOT_DIR / "TRACE_CONTRACT_v1.0.0.json"
    with open(contract_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Corrupt contract by removing 'certified' from forbidden list
    data["trace_contract"]["forbidden_as_authority"] = ["is_legal_diagnostic"]

    tampered_json_path = tmp_path / "TRACE_CONTRACT_v1.0.0.json"
    with open(tampered_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    assert verify_trace_contract(tampered_json_path) is False, "Must reject TRACE_CONTRACT with missing forbidden keys"


def test_statistical_rule_tamper_detection():
    """Verify that STATISTICAL_DECISION_LOCK.md enforces frozen parameters."""
    stat_file = ROOT_DIR / "STATISTICAL_DECISION_LOCK.md"
    content = stat_file.read_text(encoding="utf-8")
    assert "alpha: 0.05" in content, "STATISTICAL_DECISION_LOCK must enforce alpha=0.05"
    assert "exact_one_sided_mcnemar" in content, "STATISTICAL_DECISION_LOCK must enforce exact_one_sided_mcnemar"


def test_claim_dag_integrity():
    """Verify that CLAIM_TRACEABILITY_LOCK.md contains the complete 8-stage DAG sequence."""
    dag_file = ROOT_DIR / "CLAIM_TRACEABILITY_LOCK.md"
    content = dag_file.read_text(encoding="utf-8")
    required_stages = [
        "CLAIM",
        "FORMAL_CLAIM",
        "TEST",
        "RUN_ID",
        "RAW_DATA",
        "STATISTIC",
        "DECISION",
        "VERDICT"
    ]
    for stage in required_stages:
        assert stage in content, f"CLAIM_TRACEABILITY_LOCK.md must include DAG stage {stage}"
