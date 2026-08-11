#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
runner.py - Central CLI Dispatcher for BABYLON-60 Sovereign Scripts Suite
Usage:
    ./scripts/runner.py status
    ./scripts/runner.py audit
    ./scripts/runner.py preserve --provider [agent|claude|all]
    ./scripts/runner.py swarm --tenants N
    ./scripts/runner.py sync
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent


def run_subcommand(script_name: str, extra_args: list[str]) -> int:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print(f"[-] Script not found: {script_path}")
        return 1
    cmd = [sys.executable, str(script_path)] + extra_args
    res = subprocess.run(cmd)
    return res.returncode


def cmd_status() -> None:
    print("============================================================")
    print(" 🚀  BABYLON-60 SCRIPT SUITE DASHBOARD & STATUS")
    print("============================================================")
    py_scripts = [p for p in SCRIPTS_DIR.rglob("*.py") if "__pycache__" not in p.parts]
    sh_scripts = [p for p in SCRIPTS_DIR.rglob("*.sh") if "__pycache__" not in p.parts]
    shebang_ok = 0
    for p in py_scripts:
        try:
            line1 = p.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
            if line1.startswith("#!/usr/bin/env python") or line1.startswith("#!/usr/bin/python"):
                shebang_ok += 1
        except Exception:
            pass

    pct = (shebang_ok / len(py_scripts) * 100.0) if py_scripts else 0.0
    print(f"  Python Scripts Registered  : {len(py_scripts)}")
    print(f"  Shell Scripts Registered   : {len(sh_scripts)}")
    print(f"  Shebang Compliance (Line 1): {shebang_ok} / {len(py_scripts)} ({pct:.1f}%)")
    print("============================================================\n")


def cmd_list(domain_filter: str | None = None, search_term: str | None = None) -> None:
    sys.path.insert(0, str(SCRIPTS_DIR))
    from generate_scripts_readme import collect_data
    data = collect_data()
    print("============================================================")
    print(" 📂  BABYLON-60 SCRIPT SUITE TAXONOMY LISTING")
    print("============================================================")
    total_matches = 0
    for cat_name, scripts in data["categories"].items():
        if domain_filter and domain_filter.lower() not in cat_name.lower():
            continue

        filtered_scripts = []
        for s in scripts:
            if search_term and (search_term.lower() not in s["path"].lower() and search_term.lower() not in s["description"].lower()):
                continue
            filtered_scripts.append(s)

        if filtered_scripts:
            print(f"\n{cat_name}")
            print("-" * 60)
            for s in filtered_scripts:
                stype = "PY" if s["type"] == "python" else "SH"
                desc = s["description"][:55] + "..." if len(s["description"]) > 55 else s["description"]
                print(f"  [{stype}] {s['path']:<45} | {desc}")
                total_matches += 1

    print("\n============================================================")
    print(f" Total Matched Scripts: {total_matches}")
    print("============================================================\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="BABYLON-60 Script Suite Unified Runner")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # status
    subparsers.add_parser("status", help="Show script suite status & health metrics")

    # audit
    audit_parser = subparsers.add_parser("audit", help="Run AST & anti-pattern quality gate audit")
    audit_parser.add_argument("--fix", action="store_true", help="Enable in-situ atomic remediation")

    # preserve
    preserve_parser = subparsers.add_parser("preserve", help="Harvest and hash local CLI logs")
    preserve_parser.add_argument("--provider", choices=["agent", "claude", "all"], default="all")

    # swarm
    swarm_parser = subparsers.add_parser("swarm", help="Run parallel BFT legion swarm")
    swarm_parser.add_argument("--tenants", "-n", type=int, default=100)
    swarm_parser.add_argument("--concurrency", "-c", type=int, default=None)

    # sync
    subparsers.add_parser("sync", help="Synchronize physical skills with docs/skills.json")

    # catalog
    catalog_parser = subparsers.add_parser("catalog", help="Generate or display scripts catalog")
    catalog_parser.add_argument("--json", action="store_true", help="Emit catalog JSON to stdout")

    # list
    list_parser = subparsers.add_parser("list", help="List and search scripts by domain or keyword")
    list_parser.add_argument("--domain", "-d", type=str, default=None, help="Filter by C5 domain name")
    list_parser.add_argument("--search", "-s", type=str, default=None, help="Search script path or description")

    # verify
    subparsers.add_parser("verify", help="Run invariant and axiom verification engine")

    args, unknown = parser.parse_known_args()

    if not args.command or args.command == "status":
        cmd_status()
        return

    if args.command == "list":
        cmd_list(domain_filter=args.domain, search_term=args.search)
        return

    if args.command == "audit":
        cmd_args = ["--fix"] if getattr(args, "fix", False) else []
        sys.exit(run_subcommand("c5_quality_gates/audit_scripts_quality.py", cmd_args + unknown))
    elif args.command == "preserve":
        sys.exit(run_subcommand("c5_log_custody/c5_preserve_logs.py", ["--provider", args.provider] + unknown))
    elif args.command == "swarm":
        cmd_args = ["--tenants", str(args.tenants)]
        if args.concurrency:
            cmd_args += ["--concurrency", str(args.concurrency)]
        sys.exit(run_subcommand("c5_legion/legion_swarm.py", cmd_args + unknown))
    elif args.command == "sync":
        rc1 = run_subcommand("c5_skills_ontology/sync_skills_registry.py", unknown)
        rc2 = run_subcommand("c5_quality_gates/sync_docs_index.py", [])
        sys.exit(rc1 if rc1 != 0 else rc2)
    elif args.command == "catalog":
        rc1 = run_subcommand("generate_scripts_readme.py", ["--json"] if getattr(args, "json", False) else [])
        rc2 = run_subcommand("c5_quality_gates/sync_docs_index.py", [])
        sys.exit(rc1 if rc1 != 0 else rc2)
    elif args.command == "verify":
        sys.exit(run_subcommand("c5_verifiers/autodetect_invariants.py", unknown))


if __name__ == "__main__":
    main()


