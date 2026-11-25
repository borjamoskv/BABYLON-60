#!/usr/bin/env python3
"""
BABYLON-60 · EU AI Act Compliance Audit Pack Generator (Arts. 12, 14, 15)
Author: Borja Fernández Angulo (borjamoskv)
Standard: C5-REAL Sovereign Trust Substrate
"""

import argparse
import os
import json
import hashlib
import datetime

import tomllib

def get_silicon_attestation():
    uname = os.uname()
    redacted_node = f"host-{hashlib.sha256(uname.nodename.encode('utf-8')).hexdigest()[:12]}"
    return {
        "attestation_status": "SOFTWARE_METADATA_ONLY",
        "hardware_attestation_verified": False,
        "evidence_source": "os.uname",
        "sysname": uname.sysname,
        "nodename": redacted_node,
        "release": uname.release,
        "machine": uname.machine,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

def parse_claims(claims_path):
    """Read canonical TOML without leaking fields across table boundaries."""
    with open(claims_path, "rb") as source:
        return tomllib.load(source)["claim"]

def generate_compliance_report(claims):
    # Mapping to European Union AI Act (Regulation EU 2024/1689)
    mapping = {
        "Article 12: Record-Keeping & Automatic Logging": {
            "mandate": "High-risk AI systems must technically allow automatic recording of events over their lifetime; applicability and conformity require a separate assessment.",
            "claims": ["cose_ed25519_receipt", "cortex_persist_sqlite", "merkle_attestation"],
            "silicon_solution": "Candidate technical contributions: COSE_Sign1 halt receipts, SQLite ledger and Merkle evidence. Read the mapped claims for evidence scope; RFC 9942 conformance is not implemented."
        },
        "Article 14: Human Oversight & Capability Invariants": {
            "mandate": "Natural persons must be enabled to oversee the AI system, prevent or minimize risks, and exercise an effective stop mechanism.",
            "claims": ["secure_enclave_p256", "inv_01_manifest_layout"],
            "silicon_solution": "Candidate technical contributions: P-256 signature verification and SharedManifest layout. Software tests do not establish hardware-backed human oversight."
        },
        "Article 15: Accuracy, Robustness & Cybersecurity": {
            "mandate": "AI systems must achieve an appropriate level of accuracy, robustness, fail-safe operation, and resilience against adversarial inputs or hallucinations.",
            "claims": ["inv_04_fail_stop_halt", "inv_02_seqlock_concurrency", "lean4_formal_trace"],
            "silicon_solution": "Candidate technical contributions: admission-state and halt evidence, bounded seqlock model checking, and abstract Lean trace results. These do not establish universal runtime or hardware guarantees."
        }
    }

    report_sections = []
    total_claims = 0
    testable_claims = 0

    for article, data in mapping.items():
        section = {
            "article": article,
            "legal_mandate": data["mandate"],
            "silicon_solution": data["silicon_solution"],
            "claims_evidence": []
        }
        for c_id in data["claims"]:
            c_info = claims.get(c_id, {"status": "unverified", "statement": "Claim missing"})
            total_claims += 1
            
            # Un reporte no ejecuta pruebas. Simplemente estructura la evidencia declarada
            # en CLAIMS.toml sin revalidarla ni ejecutar pruebas en tiempo de exportación.
            # evidence_available procede exclusivamente del estado declarado en CLAIMS.toml, sin revalidarlo.
            status_raw = c_info.get("status", "unverified")
            has_evidence = status_raw in ["verified", "verified_local", "verified_in_memory", "testable"]
            if has_evidence:
                testable_claims += 1
            
            section["claims_evidence"].append({
                "claim_id": c_id,
                "statement": c_info.get("statement"),
                "source_claim_status": status_raw,
                "evidence_available": has_evidence,
                "evidence_availability_basis": "DECLARED_SOURCE_STATUS_NOT_REVALIDATED",
                "test_execution_status": "NOT_EXECUTED_BY_EXPORTER",
                "executed_test": "pending_conformity_assessment",  # Control interno o externo según Anexo III (Art. 43)
                "result": "NOT_EVALUATED",
                "scope": c_info.get("scope", "Requires definition"),
                "pending_evaluation": True,
            })
        report_sections.append(section)

    return {
        "framework": "BABYLON-60 C5-REAL Sovereign Trust Substrate",
        "compliance_target": "Regulation (EU) 2024/1689 (EU Artificial Intelligence Act)",
        "report_type": "SOURCE_CLAIMS_EXPORT",
        "test_execution_status": "NOT_EXECUTED_BY_EXPORTER",
        "regulatory_assessment": "PENDING_REVIEW",
        "legal_conformity": "NOT_DETERMINED",
        "publication_authorized": False,
        "attestation": get_silicon_attestation(),
        "summary": {
            "articles_covered": [12, 14, 15],
            "total_evidence_points": total_claims,
            "testable_points": testable_claims,
            "evidence_collection_ratio": f"{(testable_claims / total_claims) * 100:.1f}%" if total_claims else "0%",
            "verdict": "EVIDENCE_COLLECTED_PENDING_AUDIT" if testable_claims == total_claims else "INCOMPLETE_EVIDENCE_PACK"
        },
        "sections": report_sections
    }

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    parser = argparse.ArgumentParser(description="Export source claims; not a conformity assessment.")
    parser.add_argument("--output", default=os.path.join(repo_root, "reports", "eu_ai_act_compliance_pack.json"))
    args = parser.parse_args()
    claims_file = os.path.join(repo_root, "CLAIMS.toml")

    with open(claims_file, "rb") as source:
        claims_bytes = source.read()
    claims = tomllib.loads(claims_bytes.decode("utf-8"))["claim"]
    report = generate_compliance_report(claims)
    report["source_claims_sha256"] = hashlib.sha256(claims_bytes).hexdigest()

    report_bytes = json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")
    report_hash = hashlib.sha256(report_bytes).hexdigest()
    report["report_sha256"] = report_hash

    # Use --output outside the checkout to preserve historical receipts.
    out_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "x", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("=" * 72)
    print("  BABYLON-60 · EU AI ACT EVIDENCE PACK EXPORTER")
    print("=" * 72)
    print("Target:      Regulation (EU) 2024/1689 (Articles 12, 14, 15)")
    print(f"Verdict:     {report['summary']['verdict']}")
    print(f"Evidence:    {report['summary']['evidence_collection_ratio']} ({report['summary']['testable_points']}/{report['summary']['total_evidence_points']} Declared source evidence points)")
    print(f"Digest:      sha256:{report_hash}")
    print(f"Pack Path:   {out_path}")
    print("=" * 72)

if __name__ == "__main__":
    main()
