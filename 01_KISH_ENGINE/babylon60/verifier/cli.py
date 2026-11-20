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
import os
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
    if crl_arg is None:
        return None
    if not crl_arg.strip():
        raise ValueError("CRL_INVALID: empty revocation input")
    path = Path(crl_arg)
    if path.exists() or "/" in crl_arg or path.suffix.lower() == ".json":
        try:
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(path, flags)
            with os.fdopen(fd, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                keys = set(data) & {"revoked_certificates", "revocations"}
                if len(keys) != 1:
                    raise ValueError("CRL requires exactly one revocation list")
                data = data[keys.pop()]
            if not isinstance(data, list) or any(not isinstance(x, str) or not x.strip() for x in data):
                raise ValueError("CRL must contain a list of nonempty certificate IDs")
            return data
        except (OSError, ValueError) as exc:
            raise ValueError(f"CRL_INVALID: {path}: {exc}") from exc
    # Inline IDs are a separate input format, never recovery from a failed file.
    ids = [x.strip() for x in crl_arg.split(",")]
    if any(not x for x in ids):
        raise ValueError("CRL_INVALID: empty certificate ID")
    return ids


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
                        "merkle_valid": None,
                        "detail": f"CERT_FILE_NOT_FOUND: '{args.cert}'",
                    },
                    indent=2,
                )
            )
        else:
            print(f"[✗] Error: Certificate file not found: {args.cert}", file=sys.stderr)
        return 1

    try:
        crl_list = parse_crl_arg(args.crl)
    except ValueError as exc:
        if args.json:
            print(json.dumps({"valid": False, "signature_valid": False, "merkle_valid": None, "detail": str(exc)}))
        else:
            print(f"[✗] {exc}", file=sys.stderr)
        return 1
    try:
        with cert_path.open(encoding="utf-8") as stream:
            cert_summary = json.load(stream)
        if not isinstance(cert_summary, dict):
            raise ValueError("certificate must be a JSON object")
    except (OSError, ValueError) as exc:
        detail = f"CERT_READ_ERROR: {exc}"
        if args.json:
            print(json.dumps({"valid": False, "signature_valid": False, "merkle_valid": None, "detail": detail}))
        else:
            print(f"[✗] {detail}", file=sys.stderr)
        return 1

    result = verify_compliance_certificate(cert_summary, ledger_path=args.ledger, crl=crl_list)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 1
    if not result["valid"]:
        print(f"[✗] CERTIFICATE VERIFICATION FAILED: {result['detail']}")
        return 1

    cert_id = cert_summary.get("certificate_id", "UNKNOWN")
    system_id = cert_summary.get("system_identifier", "UNKNOWN")
    operator = cert_summary.get("operator", "UNKNOWN")
    issued_at = cert_summary.get("issued_at", "UNKNOWN")
    valid_until = cert_summary.get("valid_until", "UNKNOWN")
    merkle_root = cert_summary.get("global_merkle_root", "UNKNOWN")
    sig_block = cert_summary.get("signature", {})
    algorithm = sig_block.get("algorithm", "Ed25519")
    pubkey = sig_block.get("public_key", "UNKNOWN")

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

    print("  [✓] Ed25519 signature verified")
    if result["merkle_valid"] is True:
        print("  [✓] Merkle Evidence Root: VERIFIED MATCH")
    else:
        print(f"  [–] Merkle Evidence Root: NOT RECOMPUTED ({result['detail']})")
    print(f"  Reported regulatory assessment: {result['regulatory_assessment']}")
    print(f"  Reported legal conformity: {result['legal_conformity']}")
    print("  VERDICT: [✓] CERTIFICATE SIGNATURE AND LIFECYCLE CHECKS PASSED")
    print(sep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
