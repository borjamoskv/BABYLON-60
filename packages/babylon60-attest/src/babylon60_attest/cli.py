# C5-REAL EXERGY CERTIFIED
"""
CLI entry point for babylon60-attest.

Usage:
    babylon60-attest attest --model gpt-4o --prompt "..." --output "..."
    babylon60-attest verify receipt.json
    babylon60-attest info
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from babylon60_attest import __version__
from babylon60_attest.receipt import build_receipt, ScittReceipt
from babylon60_attest.verify import verify_receipt


def cmd_attest(args: argparse.Namespace) -> int:
    receipt = build_receipt(
        operator_id=args.operator or "cli",
        model=args.model,
        prompt=args.prompt,
        output=args.output,
        metadata=json.loads(args.metadata) if args.metadata else None,
    )

    output_json = receipt.to_json()

    if args.out:
        Path(args.out).write_text(output_json + "\n", encoding="utf-8")
        print(f"[ATTEST] Receipt written to {args.out}")
    else:
        print(output_json)

    print(f"[ATTEST] attestation_digest: {receipt.attestation_digest}", file=sys.stderr)
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    path = Path(args.receipt)
    if not path.is_file():
        print(f"[ERR] File not found: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    receipt = ScittReceipt.from_dict(data)

    result = verify_receipt(
        receipt,
        prompt=args.prompt,
        output=args.output,
    )

    for check in result.checks:
        print(check)

    if result.valid:
        print("\n[C5-REAL] RECEIPT INTEGRITY VERIFIED.")
        return 0
    else:
        print("\n[FATAL] RECEIPT INTEGRITY FALSIFIED.", file=sys.stderr)
        return 1


def cmd_info(_: argparse.Namespace) -> int:
    print(f"babylon60-attest v{__version__}")
    print(f"Schema: babylon60.llm.attestation/v1")
    print(f"Hash: SHA3-256")
    print(f"Tree: Binary Merkle (4-leaf: prompt, output, model, operator)")
    print(f"Ledger: SQLite WAL, append-only (BFT triggers)")
    print(f"Standard: IETF SCITT RFC 9943")
    print(f"Dependencies: 0 (stdlib only)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="babylon60-attest",
        description="Deterministic LLM output attestation under IETF SCITT (RFC 9943).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    # attest
    p_attest = sub.add_parser("attest", help="Create a SCITT receipt for an LLM interaction.")
    p_attest.add_argument("--model", required=True, help="Model identifier (e.g., gpt-4o)")
    p_attest.add_argument("--prompt", required=True, help="Prompt text")
    p_attest.add_argument("--output", required=True, help="Model output text")
    p_attest.add_argument("--operator", default=None, help="Operator identity")
    p_attest.add_argument("--metadata", default=None, help="JSON metadata string")
    p_attest.add_argument("--out", default=None, help="Write receipt to file")

    # verify
    p_verify = sub.add_parser("verify", help="Verify a SCITT receipt.")
    p_verify.add_argument("receipt", help="Path to receipt JSON file")
    p_verify.add_argument("--prompt", default=None, help="Original prompt for I2 check")
    p_verify.add_argument("--output", default=None, help="Original output for I3 check")

    # info
    sub.add_parser("info", help="Show package info and capabilities.")

    args = parser.parse_args(argv)

    if args.command == "attest":
        return cmd_attest(args)
    elif args.command == "verify":
        return cmd_verify(args)
    elif args.command == "info":
        return cmd_info(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
