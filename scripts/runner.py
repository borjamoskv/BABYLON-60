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

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


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
    py_scripts = list(SCRIPTS_DIR.glob("*.py"))
    sh_scripts = list(SCRIPTS_DIR.glob("*.sh"))
    shebang_ok = sum(1 for p in py_scripts if p.stat().st_size > 0 and p.read_text(encoding="utf-8").startswith("#!/usr/bin/env python3"))

    print(f"  Python Scripts Registered  : {len(py_scripts)}")
    print(f"  Shell Scripts Registered   : {len(sh_scripts)}")
    print(f"  Shebang Compliance (Line 1): {shebang_ok} / {len(py_scripts)} ({(shebang_ok/len(py_scripts))*100:.1f}%)")
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

    args, unknown = parser.parse_known_args()

    if not args.command or args.command == "status":
        cmd_status()
        return

    if args.command == "audit":
        cmd_args = ["--fix"] if getattr(args, "fix", False) else []
        sys.exit(run_subcommand("audit_scripts_quality.py", cmd_args + unknown))

    elif args.command == "preserve":
        sys.exit(run_subcommand("c5_preserve_logs.py", ["--provider", args.provider] + unknown))
    elif args.command == "swarm":
        cmd_args = ["--tenants", str(args.tenants)]
        if args.concurrency:
            cmd_args += ["--concurrency", str(args.concurrency)]
        sys.exit(run_subcommand("c5_legion/legion_swarm.py", cmd_args + unknown))
    elif args.command == "sync":
        sys.exit(run_subcommand("sync_skills_registry.py", unknown))


if __name__ == "__main__":
    main()
