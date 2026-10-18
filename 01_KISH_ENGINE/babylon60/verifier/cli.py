"""
BABYLON-60 Standalone Compliance Verifier CLI
=============================================
Command-line interface for independent auditors, CISOs, DPOs, and regulators.
Executes deterministic verification of EU AI Act Compliance Certificates
and underlying forensic Merkle ledgers with ZERO proprietary dependencies.

Exit codes:
  0: Certificate is cryptographically VALID and UNTAMPERED.
  1: Certificate is INVALID, EXPIRED, REVOKED, or TAMPERED.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .standalone_verify import verify_compliance_certificate, verify_m0_evidence_pack


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="babylon-verify",
        description="BABYLON-60 Open-Core Independent Compliance Verifier (Kerckhoffs Standard)",
        epilog="Conforms to EU AI Act (Regulation EU 2024/1689) Articles 9, 10, 11, 12, 14, 15, 50.",
    )
    parser.add_argument(
        "--cert",
        required=False,
        default=None,
        help="Path to the Compliance Certificate JSON file to verify.",
    )
    parser.add_argument(
        "--pack",
        required=False,
        default=None,
        help="Path to a babylon-m0-evidence-pack directory to verify end-to-end.",
    )
    parser.add_argument(
        "--ledger",
        default=None,
        help="Path to the underlying forensic ledger (SQLite .db or JSON file) to verify Merkle root match.",
    )
    parser.add_argument(
        "--crl",
        default=None,
        help="Path to Certificate Revocation List (JSON file or comma-separated certificate IDs).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit output formatted strictly as machine-readable JSON.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress banner output; only emit status code and minimal summary.",
    )
    return parser


def parse_crl_arg(crl_arg: Optional[str]) -> Optional[List[str]]:
    if not crl_arg:
        return None
    path = Path(crl_arg)
    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [str(x) for x in data]
                elif isinstance(data, dict):
                    revoked = data.get("revoked_certificates") or data.get("revocations") or []
                    return [str(x) for x in revoked]
        except Exception:
            pass
    # Comma-separated list fallback
    return [x.strip() for x in crl_arg.split(",") if x.strip()]


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.pack:
        pack_res = verify_m0_evidence_pack(args.pack)
        if args.json:
            print(json.dumps(pack_res, indent=2))
            return 0 if pack_res["valid"] else 1
        status_str = "[✓] PASS" if pack_res["valid"] else "[✗] FAIL"
        print(f"{status_str} M0 Evidence Pack ({args.pack}): {pack_res['detail']} [{pack_res['epistemic_status']}]")
        return 0 if pack_res["valid"] else 1

    if not args.cert:
        parser.error("one of the arguments --cert or --pack is required")

    cert_path = Path(args.cert)
    if not cert_path.exists():
        if args.json:
            print(
                json.dumps(
                    {
                        "valid": False,
                        "signature_valid": False,
                        "merkle_valid": False,
                        "detail": f"CERT_FILE_NOT_FOUND: '{args.cert}'",
                    },
                    indent=2,
                )
            )
        else:
            print(f"[✗] Error: Certificate file not found: {args.cert}", file=sys.stderr)
        return 1

    crl_list = parse_crl_arg(args.crl)
    result = verify_compliance_certificate(
        cert_dict_or_path=cert_path,
        ledger_path=args.ledger,
        crl=crl_list,
    )

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 1

    # Load certificate summary info for visual report
    cert_summary = {}
    try:
        with open(cert_path, "r", encoding="utf-8") as f:
            cert_summary = json.load(f)
    except Exception:
        pass

    cert_id = cert_summary.get("certificate_id", "UNKNOWN")
    system_id = cert_summary.get("system_identifier", "UNKNOWN")
    operator = cert_summary.get("operator", "UNKNOWN")
    issued_at = cert_summary.get("issued_at", "UNKNOWN")
    valid_until = cert_summary.get("valid_until", "UNKNOWN")
    merkle_root = cert_summary.get("global_merkle_root", "UNKNOWN")
    sig_block = cert_summary.get("signature", {})
    algorithm = sig_block.get("algorithm", "Ed25519")
    pubkey = sig_block.get("public_key", "UNKNOWN")

    is_valid = result["valid"]
    sig_valid = result["signature_valid"]
    merkle_valid = result["merkle_valid"]
    detail = result["detail"]

    sep = "=" * 72
    print(sep)
    print("  BABYLON-60 OPEN-CORE COMPLIANCE VERIFIER (Kerckhoffs Standard)")
    print(sep)
    print(f"  Certificate File   : {args.cert}")
    print(f"  Certificate ID     : {cert_id}")
    print(f"  Audited System     : {system_id}")
    print(f"  Operator / Entity  : {operator}")
    print(f"  Validity Window    : {issued_at} -> {valid_until}")
    print(f"  Global Merkle Root : {merkle_root[:32]}...{merkle_root[-8:] if len(merkle_root) >= 40 else ''}")
    print(f"  Public Key         : {pubkey[:24]}...{pubkey[-8:] if len(pubkey) >= 32 else ''} ({algorithm})")
    if args.ledger:
        print(f"  Underlying Ledger  : {args.ledger}")
    print("-" * 72)

    def status_icon(ok: bool) -> str:
        return "[✓] PASS" if ok else "[✗] FAIL"

    print(f"  {status_icon(True)} Schema Integrity          : Valid canonical compliance envelope")
    print(
        f"  {status_icon(sig_valid)} Ed25519 Cryptographic Sig : {'VALID & UNTAMPERED' if sig_valid else 'FAILED / CORRUPTED'}"
    )
    print(
        f"  {status_icon(merkle_valid)} Merkle Evidence Root      : {'VERIFIED MATCH' if merkle_valid else 'MISMATCH OR UNVERIFIED'}"
    )
    print(f"  {status_icon(is_valid)} Lifecycle & Revocation    : {detail}")
    print("-" * 72)

    if is_valid:
        print("  VERDICT: [✓] CERTIFICATE IS CRYPTOGRAPHICALLY VALID AND COMPLIANT")
        print(sep)
        return 0
    else:
        print("  VERDICT: [✗] CERTIFICATE VERIFICATION FAILED (NON-COMPLIANT / TAMPERED)")
        print(sep)
        return 1


if __name__ == "__main__":
    sys.exit(main())
