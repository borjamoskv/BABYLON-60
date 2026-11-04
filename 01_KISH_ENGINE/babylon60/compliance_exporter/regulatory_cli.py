"""CLI orchestration; diagnostic reports cannot authorize protected effects."""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

from .i18n import get_translation
from .regulatory import assess, load_json
from .regulatory_gate import authorization, invoke_native, verify_receipt


def render(result: dict, output_format: str, locale: str) -> str:
    if output_format == "json":
        return json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    t = get_translation(locale)
    if output_format == "html":
        rows = "".join(
            "<tr>"
            + "".join(f"<td>{html.escape(str(r.get(k, '')))}</td>" for k in ("id", "description", "owner", "status"))
            + "</tr>"
            for r in result.get("requirements", [])
        )
        return f'<!DOCTYPE html><html lang="{locale}"><meta charset="utf-8"><title>{html.escape(t["title"])}</title><body><h1>{html.escape(t["title"])}</h1><p>{html.escape(t["legal_disclaimer"])}</p><table>{rows}</table><pre>{html.escape(json.dumps(result, ensure_ascii=False, indent=2))}</pre></body></html>'

    # Escape HTML and Markdown delimiters from untrusted metadata.
    def escape(value: object) -> str:
        return html.escape(str(value)).replace("|", "\\|").replace("\n", " ").replace("`", "\\`")

    lines = [
        f"# {escape(t['title'])}",
        "",
        escape(t["legal_disclaimer"]),
        "",
        f"Legal conformity: {escape(result.get('legal_conformity', 'NOT_DETERMINED'))}",
        "",
        "| Requirement | Owner | Status |",
        "| --- | --- | --- |",
    ]
    lines += [
        f"| {escape(r['id'])} | {escape(r['owner'])} | {escape(r['status'])} |" for r in result.get("requirements", [])
    ]
    return "\n".join(lines) + "\n"


def run(args) -> int:
    try:
        if not args.profile or not args.assessment:
            raise ValueError("--profile and --assessment are required")
        profile = load_json(args.profile)
        assessment = load_json(args.assessment)
        policy = load_json(args.trust_store) if args.trust_store else {}
        result = assess(profile, assessment, Path(args.bundle), policy)
        if args.mode in {"approve", "authorize-release"}:
            if args.format != "json":
                raise ValueError("Protected operations emit verifiable JSON only")
            if not args.trust_store or not args.ledger or not args.native_gate:
                raise ValueError("Explicit trust store, existing L0 ledger and native gate are required")
            intent = authorization(
                args.mode,
                result,
                commit=args.commit,
                artifact_sha256=args.artifact_sha256,
                destination=args.destination,
                run_id=args.run_id,
                run_attempt=args.run_attempt,
            )
            receipt = invoke_native(
                {"mode": args.mode, "source_record": assessment["review"], "authorization": intent},
                binary=args.native_gate,
                policy_path=args.trust_store,
                ledger_path=args.ledger,
            )
            expected = {
                k: intent[k]
                for k in (
                    "action",
                    "profile_digest",
                    "commit",
                    "artifact_sha256",
                    "destination",
                    "run_id",
                    "run_attempt",
                )
            }
            verify_receipt(receipt, policy, expected)
            result = receipt
        content = render(result, args.format, args.locale)
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(content, encoding="utf-8")
        else:
            print(content, end="")
        return 2 if args.mode == "assess" and not result["gate_eligible"] else 0
    except Exception as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 2
