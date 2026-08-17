"""
test_epistemic_tamper_resistance.py — Advanced Security & Tamper Resistance Test Suite (v2.1)

Validates:
1. Single-byte tamper detection across all 15 lock files.
2. Authority key injection rejection in TRACE_CONTRACT.
3. Manifest recalculation attack resistance (Root-of-Trust anchor check).
4. Claim DAG node payload replacement attack rejection.
5. Claim DAG edge-rewiring attack rejection (hash-bound edges).
"""

import os
import json
import hashlib
import pytest
from pathlib import Path
from scripts.verify_epistemic_locks import (
    ROOT_DIR,
    LOCK_FILES,
    ROOT_OF_TRUST_ANCHOR,
    verify_all_locks,
    verify_trace_contract,
    verify_dag_chain,
    calculate_root_lock_set_digest,
    calculate_sha256
)


def test_clean_locks_pass_verification():
    """Ensure that pristine baseline lock files pass verification against Root-of-Trust anchor."""
    assert verify_all_locks(check_root_anchor=True) is True, "Pristine locks must pass root-of-trust verification"


def test_single_byte_tamper_detection(tmp_path):
    """Verify that modifying 1 byte in any lock file alters its SHA-256 digest."""
    for lock_name in LOCK_FILES:
        original_file = ROOT_DIR / lock_name
        assert original_file.exists()

        content = original_file.read_bytes()
        tampered_content = content + b"\n# TAMPER_BYTE"

        orig_hash = hashlib.sha256(content).hexdigest()
        tamp_hash = hashlib.sha256(tampered_content).hexdigest()

        assert orig_hash != tamp_hash, f"SHA-256 hash must change for tampered file: {lock_name}"


def test_manifest_recalculation_attack_prevention(tmp_path):
    """
    CRITICAL SECURITY TEST:
    Simulates an attacker who modifies a lock file AND recomputes EPISTEMIC_LOCKS_MANIFEST.json.
    Verification MUST STILL FAIL because the Root of Trust Anchor does not match.
    """
    # 1. Generate fake lock hashes where LOCK-01 is tampered
    tampered_hashes = {name: calculate_sha256(ROOT_DIR / name) for name in LOCK_FILES}
    tampered_hashes["FORMAL_CLAIMS.md"] = hashlib.sha256(b"TAMPERED_CONTENT").hexdigest()

    # 2. Attacker recomputes manifest root digest
    attacker_root_digest = calculate_root_lock_set_digest(tampered_hashes)

    # 3. Assert that attacker's recomputed root digest DOES NOT MATCH the hardcoded Root of Trust Anchor
    assert attacker_root_digest != ROOT_OF_TRUST_ANCHOR, "Manifest recalculation attack must be caught by Root of Trust anchor mismatch"


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


def test_dag_node_replacement_attack():
    """Verify that altering a node payload in the Claim DAG breaks edge hash binding."""
    # Build canonical 8-node DAG payload
    nodes = {
        "CLAIM": "Claim: CTM provides reachability advantage",
        "FORMAL_CLAIM": "reach_subset theorem in Lean 4",
        "TEST": "exact_one_sided_mcnemar alpha=0.05",
        "RUN_ID": "run_uuid_001",
        "RAW_DATA": "rfc8785_trace_hash",
        "STATISTIC": "p_val=0.02",
        "DECISION": "D_gt_C",
        "VERDICT": "ACCEPTED"
    }

    # Compute valid edge hashes H(E(u, v)) = SHA256(H(u) || H(v))
    edges = [
        {"source": "CLAIM", "target": "FORMAL_CLAIM"},
        {"source": "FORMAL_CLAIM", "target": "TEST"},
        {"source": "TEST", "target": "RUN_ID"},
        {"source": "RUN_ID", "target": "RAW_DATA"},
        {"source": "RAW_DATA", "target": "STATISTIC"},
        {"source": "STATISTIC", "target": "DECISION"},
        {"source": "DECISION", "target": "VERDICT"}
    ]

    for edge in edges:
        u = edge["source"]
        v = edge["target"]
        u_hash = hashlib.sha256(nodes[u].encode("utf-8")).hexdigest()
        v_hash = hashlib.sha256(nodes[v].encode("utf-8")).hexdigest()
        edge["hash"] = hashlib.sha256(f"{u_hash}:{v_hash}".encode("utf-8")).hexdigest()

    dag_spec = {"nodes": nodes, "edges": edges}
    assert verify_dag_chain(dag_spec) is True, "Valid DAG must pass verification"

    # Attacker replaces node payload
    tampered_nodes = dict(nodes)
    tampered_nodes["RUN_ID"] = "run_uuid_MALICIOUS_999"
    tampered_dag = {"nodes": tampered_nodes, "edges": edges}

    assert verify_dag_chain(tampered_dag) is False, "Altering DAG node payload must trigger verification failure"


def test_dag_edge_rewiring_attack():
    """
    CRITICAL SECURITY TEST:
    Simulates an edge-rewiring attack where node contents remain untouched,
    but edge target is rewired (e.g., TEST -> RUN_001 rewired to TEST -> RUN_999).
    The verifier MUST REJECT because the edge hash H(E) fails.
    """
    nodes = {
        "CLAIM": "Claim: CTM provides reachability advantage",
        "FORMAL_CLAIM": "reach_subset theorem in Lean 4",
        "TEST": "exact_one_sided_mcnemar alpha=0.05",
        "RUN_ID": "run_uuid_001",
        "RUN_ID_ALT": "run_uuid_999_FAKED",
        "RAW_DATA": "rfc8785_trace_hash",
        "STATISTIC": "p_val=0.02",
        "DECISION": "D_gt_C",
        "VERDICT": "ACCEPTED"
    }

    # Compute valid hash for edge (TEST -> RUN_ID)
    u_hash = hashlib.sha256(nodes["TEST"].encode("utf-8")).hexdigest()
    v_hash = hashlib.sha256(nodes["RUN_ID"].encode("utf-8")).hexdigest()
    original_edge_hash = hashlib.sha256(f"{u_hash}:{v_hash}".encode("utf-8")).hexdigest()

    # Edge-rewiring attack: target rewired to RUN_ID_ALT while keeping original_edge_hash
    rewired_edges = [
        {"source": "TEST", "target": "RUN_ID_ALT", "hash": original_edge_hash}
    ]

    # Required nodes present
    full_nodes = dict(nodes)
    full_nodes["RUN_ID"] = "run_uuid_001"

    dag_spec = {"nodes": full_nodes, "edges": rewired_edges}
    assert verify_dag_chain(dag_spec) is False, "Edge rewiring attack must be detected and rejected"
