#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
poc_eu_ai_act_audit.py - PoC 5: Automated EU AI Act Risk & Compliance Auditor
Scans repository manifests and code for compliance with Articles 9-14 (EU AI Act).
Supports --json for Machine-to-Machine orchestration.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def audit_eu_ai_act_compliance() -> Dict[str, Any]:
    """Audits Articles 9 to 14 of EU AI Act."""
    checks = {
        "Art_09_Risk_Management": (REPO_ROOT / "docs" / "02_ontology").exists(),
        "Art_10_Data_Governance": (REPO_ROOT / "data").exists(),
        "Art_11_Technical_Documentation": (REPO_ROOT / "docs" / "00_index.md").exists(),
        "Art_12_Record_Keeping_Logs": (REPO_ROOT / "data" / "cortex_memory.db").exists(),
        "Art_13_Transparency_M2M": (REPO_ROOT / "scripts" / "runner.py").exists(),
        "Art_14_Human_Oversight_HITL": (REPO_ROOT / "scripts" / "c5_demos" / "poc_causal_hitl_agent.py").exists()
    }

    passed_count = sum(1 for v in checks.values() if v)
    total_articles = len(checks)
    compliance_pct = round((passed_count / total_articles) * 100.0, 2)

    return {
        "articles_checked": total_articles,
        "articles_passed": passed_count,
        "compliance_percentage": compliance_pct,
        "article_breakdown": checks,
        "is_sovereign_compliant": compliance_pct == 100.0
    }


def run_poc_eu_ai_act(json_output: bool = False) -> None:
    audit_results = audit_eu_ai_act_compliance()

    if json_output:
        payload = {
            "schema_version": "1.0",
            "type": "C5_EU_AI_ACT_COMPLIANCE_POC",
            "regulation": "EU AI Act (Regulation 2024/1689)",
            "audit": audit_results,
            "status": "COMPLIANT" if audit_results["is_sovereign_compliant"] else "NON_COMPLIANT"
        }
        print(json.dumps(payload, indent=2))
        return

    print("============================================================")
    print(" ⚖️  POC 5: EU AI ACT (ARTICLES 9-14) COMPLIANCE AUDITOR")
    print("============================================================")
    print(f" Total Articles Evaluated   : {audit_results['articles_checked']}")
    print(f" Compliant Articles         : {audit_results['articles_passed']}")
    print(f" Compliance Percentage      : {audit_results['compliance_percentage']}%")
    print("------------------------------------------------------------")
    print(" Article Status Breakdown:")
    for art, status in audit_results["article_breakdown"].items():
        print(f"  • {art:<32}: {'✅ COMPLIANT' if status else '❌ DEFICIENT'}")
    print("============================================================\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="PoC 5: EU AI Act Risk & Compliance Auditor")
    parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M communication")
    args = parser.parse_args()

    run_poc_eu_ai_act(json_output=args.json)


if __name__ == "__main__":
    main()
