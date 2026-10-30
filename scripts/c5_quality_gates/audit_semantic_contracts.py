#!/usr/bin/env python3
"""Check the public documentation contract using checkout files only.

This is a documentary gate: it checks known contract regressions and delegates
links, headings and index coverage to docs_lint. It neither executes claim suites
nor certifies runtime, hardware or legal compliance. No host settings or telemetry
are read, including when --workspace-only is omitted.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

REQUIRED_DOCS = (
    "docs/README.md",
    "docs/00_index.md",
    "docs/DOCS_GRAMMAR.md",
    "docs/05_compliance_eu_ai_act.md",
    "docs/01_spec/spec_cryptographic_profile.md",
    "docs/01_spec/spec_security_model.md",
)
FORMAL_DOCS = (
    "docs/PROJECT.md",
    "docs/RESULTADOS.md",
    "docs/04_research/README_APEX.md",
    "docs/06_theory/AUDIT_AXIOMS_2026.md",
)


def semantic_errors(root: Path) -> list[str]:
    """Reject specific known regressions; this is not a general truth oracle."""
    errors = []
    contents = {}
    for name in dict.fromkeys((*REQUIRED_DOCS, *FORMAL_DOCS)):
        try:
            contents[name] = (root / name).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"{name}: required document unreadable ({error})")
    for name in FORMAL_DOCS:
        if re.search(r"axiom\s+ax_canonical_invariant\s*:", contents.get(name, "")):
            errors.append(f"{name}: empty canonical axiom is not implementation evidence")
    hub = contents.get("docs/README.md", "")
    if re.search(r"es el único sustrato[^\n]*físicamente imposible", hub, re.IGNORECASE):
        errors.append("docs/README.md: unsupported universal human-oversight guarantee")
    compliance = contents.get("docs/05_compliance_eu_ai_act.md", "")
    for active_name in ("BABYLON60_SIGNING_SEED", "evidence_verification"):
        if f"[OBSOLETO: {active_name}]" in compliance:
            errors.append(f"docs/05_compliance_eu_ai_act.md: active interface {active_name} marked obsolete")
    for name in (
        "docs/05_compliance_eu_ai_act.md",
        "docs/03_guides/tutorial_hello_causal.md",
        "docs/03_guides/guide_repository_source_of_truth.md",
    ):
        try:
            text = (root / name).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"{name}: required document unreadable ({error})")
            continue
        if re.search(r"^\s*cortex-compliance\s", text, re.MULTILINE):
            errors.append(f"{name}: unregistered cortex-compliance command")
        if re.search(r"target/(?:release|debug)/b60_kernel\b", text):
            errors.append(f"{name}: undeclared b60_kernel target")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).absolute().parents[2])
    parser.add_argument(
        "--workspace-only",
        action="store_true",
        help="Explicit checkout-only scope (also the default); never inspect global settings",
    )
    args = parser.parse_args()
    root = args.repo_root.absolute()
    errors = semantic_errors(root)
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)
    result = subprocess.run(
        [sys.executable, str(root / "scripts/docs_lint.py"), "docs/"],
        cwd=root,
        check=False,
    )
    if errors or result.returncode:
        return 1
    print("PASS: documentation contracts, links and indexes (workspace only; no runtime claims)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
