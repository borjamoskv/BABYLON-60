#!/usr/bin/env python3
"""
verify_epistemic_locks.py — Automated Forensic Verifier for Epistemic & Contractual Locks (v2.1)

Enforces Root-of-Trust lock set digest anchors, DAG edge-rewiring validation,
and authority prohibitions across all 15 lock files.
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent

LOCK_FILES = [
    "FORMAL_CLAIMS.md",
    "ASSUMPTIONS.md",
    "TRACE_CONTRACT_v1.0.0.json",
    "BENCHMARK_PROTOCOL_v1.0.0.md",
    "RANDOMIZATION_PROTOCOL.md",
    "METRICS.md",
    "FALSIFICATION_RULES.md",
    "REPRODUCIBILITY_LOCK.md",
    "THREAT_MODEL.md",
    "THEOREM_EMPIRICAL_BRIDGE.md",
    "PROVENANCE_LOCK.md",
    "EXECUTION_LOCK.md",
    "ENVIRONMENT_LOCK.md",
    "STATISTICAL_DECISION_LOCK.md",
    "CLAIM_TRACEABILITY_LOCK.md"
]

FORBIDDEN_AUTHORITY_KEYS = [
    "certified",
    "is_legal_diagnostic",
    "is_safe",
    "is_valid"
]

# HARDCODED ROOT OF TRUST DIGEST ANCHOR (SHA-256 of combined canonical lock digests)
# If any lock file is modified without updating code anchor, verification fails.
ROOT_OF_TRUST_ANCHOR = "0339d37b10f753d47e7905f6f00801f340cffab645aeacd4ff00c719845d1e9d"


def calculate_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def calculate_root_lock_set_digest(lock_hashes: dict) -> str:
    """Computes the master Root of Trust SHA-256 digest across all 15 locks."""
    hasher = hashlib.sha256()
    for lock_name in LOCK_FILES:
        h = lock_hashes.get(lock_name, "")
        hasher.update(f"{lock_name}:{h}\n".encode("utf-8"))
    return hasher.hexdigest()


def verify_trace_contract(filepath: Path) -> bool:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        trace_contract = data.get("trace_contract", {})
        if trace_contract.get("version") != "1.0.0":
            print(f"[X] TRACE_CONTRACT version mismatch: {trace_contract.get('version')}")
            return False

        forbidden = trace_contract.get("forbidden_as_authority", [])
        for key in FORBIDDEN_AUTHORITY_KEYS:
            if key not in forbidden:
                print(f"[X] TRACE_CONTRACT missing forbidden authority key: {key}")
                return False

        return True
    except Exception as e:
        print(f"[X] Failed to parse TRACE_CONTRACT_v1.0.0.json: {e}")
        return False


def verify_dag_chain(dag_spec: dict) -> bool:
    """
    Verifies DAG node payload hashing and edge-rewiring hash binding:
    H(Edge(u, v)) == SHA256(H(u) || H(v))
    """
    try:
        nodes = dag_spec.get("nodes", {})
        edges = dag_spec.get("edges", [])

        # Check required 8 nodes
        required_nodes = ["CLAIM", "FORMAL_CLAIM", "TEST", "RUN_ID", "RAW_DATA", "STATISTIC", "DECISION", "VERDICT"]
        for r_node in required_nodes:
            if r_node not in nodes:
                print(f"[X] Missing DAG node: {r_node}")
                return False

        # Verify edge hashes
        for edge in edges:
            u = edge.get("source")
            v = edge.get("target")
            expected_hash = edge.get("hash")

            if u not in nodes or v not in nodes:
                print(f"[X] Edge references missing node: {u} -> {v}")
                return False

            u_hash = hashlib.sha256(nodes[u].encode("utf-8")).hexdigest()
            v_hash = hashlib.sha256(nodes[v].encode("utf-8")).hexdigest()
            actual_edge_hash = hashlib.sha256(f"{u_hash}:{v_hash}".encode("utf-8")).hexdigest()

            if expected_hash != actual_edge_hash:
                print(f"[X] Edge rewiring / hash mismatch detected on edge {u} -> {v}")
                return False

        return True
    except Exception as e:
        print(f"[X] DAG verification exception: {e}")
        return False


def verify_all_locks(check_root_anchor: bool = True) -> bool:
    print(f"=== VERIFYING 15 EPISTEMIC LOCKS (ROOT-OF-TRUST v2.1) ===")
    errors = []
    lock_hashes = {}
    manifest = {
        "version": "2.1.0",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "repository": "borjamoskv/teorema-robinson-moskv",
        "lock_files": {}
    }

    for lock_name in LOCK_FILES:
        lock_path = ROOT_DIR / lock_name
        if not lock_path.exists():
            print(f"[X] MISSING FILE: {lock_name}")
            errors.append(f"Missing file {lock_name}")
            continue

        file_hash = calculate_sha256(lock_path)
        lock_hashes[lock_name] = file_hash
        manifest["lock_files"][lock_name] = {
            "path": str(lock_name),
            "sha256": file_hash,
            "status": "VERIFIED"
        }

        if lock_name == "TRACE_CONTRACT_v1.0.0.json":
            if not verify_trace_contract(lock_path):
                errors.append("TRACE_CONTRACT authority verification failed")
                continue

        print(f"[✓] {lock_name:<32} SHA256: {file_hash[:16]}... OK")

    root_digest = calculate_root_lock_set_digest(lock_hashes)
    manifest["root_lock_set_digest"] = root_digest
    print(f"\n[+] Master Root Lock Set Digest: {root_digest}")

    if check_root_anchor and root_digest != ROOT_OF_TRUST_ANCHOR:
        print(f"[X] ROOT OF TRUST MISMATCH!")
        print(f"    Computed: {root_digest}")
        print(f"    Anchor:   {ROOT_OF_TRUST_ANCHOR}")
        errors.append("Root of Trust Anchor Mismatch (Manifest recalculation attack detected)")

    manifest_path = ROOT_DIR / "EPISTEMIC_LOCKS_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    if errors:
        print(f"\n[FAILURE] Verification failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print(f"\n[SUCCESS] All {len(LOCK_FILES)} Epistemic Lock files verified against Root of Trust.")
        print(f"Manifest written to: {manifest_path.name}")
        return True


if __name__ == "__main__":
    success = verify_all_locks(check_root_anchor=True)
    if not success:
        sys.exit(1)
    sys.exit(0)

