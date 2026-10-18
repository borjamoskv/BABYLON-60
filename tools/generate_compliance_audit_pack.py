#!/usr/bin/env python3
"""
BABYLON-60 · EU AI Act Compliance Audit Pack Generator (Arts. 12, 14, 15)
Author: Borja Fernández Angulo (borjamoskv)
Standard: C5-REAL Sovereign Trust Substrate
"""

import os
import sys
import json
import hashlib
import datetime
import subprocess

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None

def get_silicon_attestation():
    uname = os.uname()
    return {
        "sysname": uname.sysname,
        "nodename": uname.nodename,
        "release": uname.release,
        "machine": uname.machine,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

def parse_claims(claims_path):
    if not os.path.exists(claims_path):
        return {"error": f"CLAIMS.toml not found at {claims_path}"}
    
    with open(claims_path, "r", encoding="utf-8") as f:
        content = f.read()

    claims = {}
    current_claim = None
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("[claim.") and line.endswith("]"):
            current_claim = line[7:-1]
            claims[current_claim] = {}
        elif current_claim and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            claims[current_claim][k] = v
    return claims

def generate_compliance_report(claims):
    # Mapping to European Union AI Act (Regulation EU 2024/1689)
    mapping = {
        "Article 12: Record-Keeping & Automatic Logging": {
            "mandate": "High-risk and autonomous AI systems must technically enable automatic recording of events (logs) throughout lifecycle, ensuring tamper-evident traceability.",
            "claims": ["cose_ed25519_receipt", "cortex_persist_sqlite", "merkle_attestation"],
            "silicon_solution": "RFC 9942 COSE_Sign1 cryptographic receipts per action dispatch + WORM SQLite WAL with SHA3-256 hash chaining."
        },
        "Article 14: Human Oversight & Capability Invariants": {
            "mandate": "Natural persons must be enabled to oversee the AI system, prevent or minimize risks, and exercise an effective stop mechanism.",
            "claims": ["secure_enclave_p256", "inv_01_manifest_layout"],
            "silicon_solution": "Apple Secure Enclave P-256 biometric friction (Touch ID with zero reuse duration) for irreversible side-effects + 64-byte SharedManifest gate."
        },
        "Article 15: Accuracy, Robustness & Cybersecurity": {
            "mandate": "AI systems must achieve an appropriate level of accuracy, robustness, fail-safe operation, and resilience against adversarial inputs or hallucinations.",
            "claims": ["inv_04_fail_stop_halt", "inv_02_seqlock_concurrency", "lean4_formal_trace"],
            "silicon_solution": "Deterministic apoptosis (0xDEAD_6060 / Fail-Stop) on capability taint + Seqlock SPMC (RFO=0) + Lean 4 machine-checked trace induction."
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
            
            # Un reporte no ejecuta pruebas. Simplemente estructura la evidencia recopilada 
            # para el control interno o el organismo notificado.
            status_raw = c_info.get("status", "unverified")
            has_evidence = status_raw in ["verified", "verified_local", "verified_in_memory", "testable"]
            if has_evidence:
                testable_claims += 1
            
            section["claims_evidence"].append({
                "claim_id": c_id,
                "statement": c_info.get("statement"),
                "evidence_available": has_evidence,
                "executed_test": "pending_conformity_assessment", # Control interno o externo según Anexo III (Art. 43)
                "result": status_raw,
                "scope": c_info.get("scope", "Requires definition"),
                "pending_evaluation": not has_evidence or status_raw == "testable"
            })
        report_sections.append(section)

    return {
        "framework": "BABYLON-60 C5-REAL Sovereign Trust Substrate",
        "compliance_target": "Regulation (EU) 2024/1689 (EU Artificial Intelligence Act)",
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
    claims_file = os.path.join(repo_root, "CLAIMS.toml")

    claims = parse_claims(claims_file)
    report = generate_compliance_report(claims)

    report_bytes = json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")
    report_hash = hashlib.sha256(report_bytes).hexdigest()
    report["report_sha256"] = report_hash

    # Save artifact
    out_dir = os.path.join(repo_root, "compliance_reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "eu_ai_act_compliance_pack.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("=" * 72)
    print("  BABYLON-60 · EU AI ACT EVIDENCE PACK EXPORTER")
    print("=" * 72)
    print(f"Target:      Regulation (EU) 2024/1689 (Articles 12, 14, 15)")
    print(f"Verdict:     {report['summary']['verdict']}")
    print(f"Evidence:    {report['summary']['evidence_collection_ratio']} ({report['summary']['testable_points']}/{report['summary']['total_evidence_points']} Claims Ready for Audit)")
    print(f"Digest:      sha256:{report_hash}")
    print(f"Pack Path:   {out_path}")
    print("=" * 72)

if __name__ == "__main__":
    main()
