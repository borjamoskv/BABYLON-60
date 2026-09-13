#!/usr/bin/env python3
# ruff: noqa: E402
# ============================================================================
# BABYLON-60 v4.1 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
BABYLON-60 v4.1 Multi-Country Compliance Exporter CLI Tool
Generates localized EU AI Act / NIST AI RMF compliance reports with physical
hardware-bound attestation (Apple Silicon SEP / Linux DMI) and certificate lifecycle.

Usage:
  python scripts/c5_utils/export_country_compliance.py --all
  python scripts/c5_utils/export_country_compliance.py --locale es
"""

import argparse
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "01_ORCHESTRATOR"))
sys.path.insert(0, PROJECT_ROOT)

from babylon60.compliance_exporter import EUAIActComplianceExporter
from babylon60.attestation import MerkleCausalAnchor


def export_single_locale(exporter, system_id, operator, locale, bundle_path, output=None):
    cert = exporter.generate_certificate(
        system_id=system_id,
        operator_name=operator,
        locale=locale,
        validity_days=90,
    )

    out_path = output if output else f"docs/audits/COMPLIANCE_CERTIFICATE_{locale.upper()}.md"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    saved_file = exporter.export_markdown_report(cert, out_path, locale=locale)

    anchor = MerkleCausalAnchor()
    quote = anchor.generate_hardware_pcr_quote(cert["global_merkle_root"])

    print(f"[OK] Compliance certificate generated for locale '{locale}': {saved_file}")
    print(f"     -> Hardware Anchor: {quote['hardware_enclave']}")
    print(f"     -> Hardware UUID:   {quote['hardware_uuid']}")
    print(f"     -> Valid Until:     {cert['valid_until']}")
    print(f"     -> Revocation Hash: {cert['revocation']['check_hash'][:16]}...")
    return saved_file


def main() -> None:
    parser = argparse.ArgumentParser(description="BABYLON-60 Multi-Country Regulatory Compliance Exporter")
    parser.add_argument(
        "--locale",
        default="es",
        choices=["es", "en", "de", "fr", "it"],
        help="Target country/locale code (es=Spain, en=US/Global, de=Germany, fr=France, it=Italy)",
    )
    parser.add_argument("--all", action="store_true", help="Export certificates for all 5 supported locales")
    parser.add_argument("--system-id", default="BABYLON-60-AGENT-01", help="Target system identifier")
    parser.add_argument("--operator", default="ENTERPRISE_OPERATOR", help="Operator entity name")
    parser.add_argument("--bundle-path", default="artifact_bundle_v3", help="Path to artifact bundle")
    parser.add_argument("--output", help="Output markdown report filepath")

    args = parser.parse_args()

    exporter = EUAIActComplianceExporter(artifact_bundle_path=args.bundle_path)

    if args.all:
        for loc in ["es", "en", "de", "fr", "it"]:
            export_single_locale(exporter, args.system_id, args.operator, loc, args.bundle_path)
    else:
        export_single_locale(exporter, args.system_id, args.operator, args.locale, args.bundle_path, args.output)


if __name__ == "__main__":
    main()
