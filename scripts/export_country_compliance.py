# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
#!/usr/bin/env python3
"""
BABYLON-60 v4.0 Multi-Country Compliance Exporter CLI Tool
Generates localized EU AI Act / NIST AI RMF compliance reports for target countries.

Usage:
  python scripts/export_country_compliance.py --locale es --output docs/audits/CERTIFICADO_ES.md
  python scripts/export_country_compliance.py --locale en --output docs/audits/CERTIFICATE_EN.md
  python scripts/export_country_compliance.py --locale de --output docs/audits/ZERTIFIKAT_DE.md
  python scripts/export_country_compliance.py --locale fr --output docs/audits/CERTIFICAT_FR.md
  python scripts/export_country_compliance.py --locale it --output docs/audits/CERTIFICATO_IT.md
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from babylon60.compliance_exporter import EUAIActComplianceExporter
from babylon60.attestation import MerkleCausalAnchor


def main():
    parser = argparse.ArgumentParser(description="BABYLON-60 Multi-Country Regulatory Compliance Exporter")
    parser.add_argument(
        "--locale",
        default="es",
        choices=["es", "en", "de", "fr", "it"],
        help="Target country/locale code (es=Spain, en=US/Global, de=Germany, fr=France, it=Italy)",
    )
    parser.add_argument("--system-id", default="BABYLON-60-AGENT-01", help="Target system identifier")
    parser.add_argument("--operator", default="ENTERPRISE_OPERATOR", help="Operator entity name")
    parser.add_argument("--bundle-path", default="artifact_bundle_v3", help="Path to artifact bundle")
    parser.add_argument("--output", help="Output markdown report filepath")

    args = parser.parse_args()

    exporter = EUAIActComplianceExporter(artifact_bundle_path=args.bundle_path)
    cert = exporter.generate_certificate(system_id=args.system_id, operator_name=args.operator, locale=args.locale)

    out_path = args.output if args.output else f"docs/audits/COMPLIANCE_CERTIFICATE_{args.locale.upper()}.md"
    saved_file = exporter.export_markdown_report(cert, out_path, locale=args.locale)

    anchor = MerkleCausalAnchor()
    quote = anchor.generate_hardware_pcr_quote(cert["global_merkle_root"])

    print(f"[OK] Compliance report generated for locale '{args.locale}': {saved_file}")
    print(f"[TPM Anchor] Hardware PCR Quote Signature: {quote['tpm_quote_signature'][:32]}...")


if __name__ == "__main__":
    main()
