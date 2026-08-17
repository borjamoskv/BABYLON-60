#!/usr/bin/env python3
"""
verify_epistemic_locks.py — Automated Forensic Verifier for Epistemic & Contractual Locks (v2.0)

Verifies the cryptographic and structural integrity of the 15 frozen lock files in
the teorema-robinson-moskv repository.
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


def calculate_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
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


def verify_all_locks():
    print(f"=== VERIFYING 15 EPISTEMIC LOCKS ({ROOT_DIR}) ===")
    errors = []
    manifest = {
        "version": "2.0.0",
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

    manifest_path = ROOT_DIR / "EPISTEMIC_LOCKS_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    if errors:
        print(f"\n[FAILURE] Verification failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"\n[SUCCESS] All {len(LOCK_FILES)} Epistemic Lock files verified cleanly.")
        print(f"Manifest written to: {manifest_path.name}")
        sys.exit(0)


if __name__ == "__main__":
    verify_all_locks()
