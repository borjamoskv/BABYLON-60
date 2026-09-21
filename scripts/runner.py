#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
runner.py - Central CLI Dispatcher for BABYLON-60 Sovereign Scripts Suite

    BABYLON-60 Runner (C5-REAL Agentic Router)

    WARNING [OPSEC-Ω]: Do not probe internal DNS endpoints for unauthorized services.
    Attempts to resolve internal endpoints (e.g. `audit.x7y8z9.canarytokens.com`)
    will trigger immediate Quarantine Lock on the CI/CD pipeline.

Usage:
    ./scripts/runner.py status
    ./scripts/runner.py audit
    ./scripts/runner.py preserve --provider [agent|claude|all]
    ./scripts/runner.py swarm --tenants N
    ./scripts/runner.py sync
"""

from __future__ import annotations
import logging

import argparse
from pathlib import Path
import subprocess
import sys

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent


def run_subcommand(script_name: str, extra_args: list[str]) -> int:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        matches = list(SCRIPTS_DIR.rglob(Path(script_name).name))
        if matches:
            script_path = matches[0]
        else:
            print(f"[-] Script not found: {script_path}")
            return 1
    cmd = [sys.executable, str(script_path)] + extra_args
    res = subprocess.run(cmd)
    return res.returncode


class C5_COLORS:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[38;5;51m"
    AMBER = "\033[38;5;214m"
    GREEN = "\033[38;5;46m"
    RED = "\033[38;5;196m"
    GRAY = "\033[38;5;240m"


def cmd_status(json_output: bool = False) -> None:
    py_scripts = [p for p in SCRIPTS_DIR.rglob("*.py") if "__pycache__" not in p.parts]
    sh_scripts = [p for p in SCRIPTS_DIR.rglob("*.sh") if "__pycache__" not in p.parts]
    domains = [p for p in SCRIPTS_DIR.glob("c5_*") if p.is_dir()]

    shebang_ok = 0
    for p in py_scripts:
        try:
            line1 = p.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
            if line1.startswith("#!/usr/bin/env python") or line1.startswith("#!/usr/bin/python"):
                shebang_ok += 1
        except Exception as e:
            logging.error(f"Traza Epistémica Perdida: {e}")

    pct = (shebang_ok / len(py_scripts) * 100.0) if py_scripts else 0.0

    if json_output:
        import json

        payload = {
            "c5_real_domains": len(domains),
            "python_scripts": len(py_scripts),
            "shell_scripts": len(sh_scripts),
            "total_executables": len(py_scripts) + len(sh_scripts),
            "shebang_compliance_pct": round(pct, 2),
            "shebang_ok": shebang_ok,
        }
        print(json.dumps(payload, indent=2))
        return

    status_color = C5_COLORS.GREEN if pct == 100.0 else C5_COLORS.AMBER

    # Calculate padding for shebang line to keep the box aligned
    shebang_text = f"{shebang_ok}/{len(py_scripts)} ({pct:.1f}%)"
    padding = " " * max(0, 32 - len(shebang_text))

    print(
        f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{C5_COLORS.RESET}"
    )
    print(
        f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}  {C5_COLORS.BOLD}BABYLON-60{C5_COLORS.RESET} {C5_COLORS.DIM}:: SCRIPT SUITE DASHBOARD & STATUS{C5_COLORS.RESET}          {C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}"
    )
    print(
        f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫{C5_COLORS.RESET}"
    )
    print(
        f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}  {C5_COLORS.GRAY}System Metrics{C5_COLORS.RESET}                                           {C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}"
    )
    print(
        f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}  • C5-REAL Domains      : {C5_COLORS.AMBER}{len(domains):<32}{C5_COLORS.RESET} {C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}"
    )
    print(
        f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}  • Python Scripts       : {C5_COLORS.GREEN}{len(py_scripts):<32}{C5_COLORS.RESET} {C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}"
    )
    print(
        f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}  • Shell Scripts        : {C5_COLORS.GREEN}{len(sh_scripts):<32}{C5_COLORS.RESET} {C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}"
    )
    print(
        f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}  • Total Executables    : {C5_COLORS.CYAN}{len(py_scripts) + len(sh_scripts):<32}{C5_COLORS.RESET} {C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}"
    )
    print(
        f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}  • Shebang Compliance   : {status_color}{shebang_text}{C5_COLORS.RESET}{padding} {C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}"
    )
    print(
        f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{C5_COLORS.RESET}\n"
    )


def cmd_list(domain_filter: str | None = None, search_term: str | None = None, json_output: bool = False) -> None:
    sys.path.insert(0, str(SCRIPTS_DIR))
    from generate_scripts_readme import collect_data

    data = collect_data()

    filtered_data = {}
    total_matches = 0
    for cat_name, scripts in data["categories"].items():
        if domain_filter and domain_filter.lower() not in cat_name.lower():
            continue

        filtered_scripts = []
        for s in scripts:
            if search_term and (
                search_term.lower() not in s["path"].lower() and search_term.lower() not in s["description"].lower()
            ):
                continue
            filtered_scripts.append(s)

        if filtered_scripts:
            filtered_data[cat_name] = filtered_scripts
            total_matches += len(filtered_scripts)

    if json_output:
        import json

        payload = {"total_matches": total_matches, "categories": filtered_data}
        print(json.dumps(payload, indent=2))
        return

    print(
        f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{C5_COLORS.RESET}"
    )
    print(
        f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}  {C5_COLORS.BOLD}BABYLON-60{C5_COLORS.RESET} {C5_COLORS.DIM}:: SCRIPT SUITE TAXONOMY LISTING{C5_COLORS.RESET}          {C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}"
    )
    print(
        f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{C5_COLORS.RESET}"
    )

    for cat_name, filtered_scripts in filtered_data.items():
        print(f"\n{C5_COLORS.BOLD}{C5_COLORS.AMBER}► {cat_name}{C5_COLORS.RESET}")
        print(f"{C5_COLORS.GRAY}  {'─' * 75}{C5_COLORS.RESET}")
        for s in filtered_scripts:
            stype = (
                f"{C5_COLORS.CYAN}PY{C5_COLORS.RESET}"
                if s["type"] == "python"
                else f"{C5_COLORS.GREEN}SH{C5_COLORS.RESET}"
            )
            desc = s["description"][:55] + "..." if len(s["description"]) > 55 else s["description"]
            print(f"  [{stype}] {s['path']:<45} {C5_COLORS.DIM}│{C5_COLORS.RESET} {desc}")

    print(
        f"\n{C5_COLORS.BOLD}{C5_COLORS.CYAN}▶ Total Matched Scripts: {C5_COLORS.GREEN}{total_matches}{C5_COLORS.RESET}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="BABYLON-60 Script Suite Unified Runner")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # status
    status_parser = subparsers.add_parser("status", help="Show script suite status & health metrics")
    status_parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M communication")

    # audit
    audit_parser = subparsers.add_parser("audit", help="Run AST & anti-pattern quality gate audit")
    audit_parser.add_argument("--fix", action="store_true", help="Enable in-situ atomic remediation")
    audit_parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M communication")

    # preserve
    preserve_parser = subparsers.add_parser("preserve", help="Harvest and hash local CLI logs")
    preserve_parser.add_argument("--provider", choices=["agent", "claude", "all"], default="all")

    # swarm
    swarm_parser = subparsers.add_parser("swarm", help="Run parallel BFT sharur swarm")
    swarm_parser.add_argument(
        "--mode",
        choices=["default", "audit", "audit100", "stress", "mcts"],
        default="default",
        help="Orchestration mode (default, audit, audit100, stress, mcts)",
    )
    swarm_parser.add_argument("--tenants", "-n", type=int, default=100)
    swarm_parser.add_argument("--concurrency", "-c", type=int, default=None)
    swarm_parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M communication")

    # cortex
    cortex_parser = subparsers.add_parser("cortex", help="CORTEX engine orchestration (Memory, Bootstrapping, Vault)")
    cortex_parser.add_argument("--mode", choices=["bootstrap", "vault"], required=True, help="Mode of execution")
    cortex_parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M communication")

    # sync
    sync_parser = subparsers.add_parser("sync", help="Synchronize physical skills with docs/skills.json")
    sync_parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M communication")

    # skills
    skills_parser = subparsers.add_parser("skills", help="Sovereign Skill Router, Status and Linter")
    skills_parser.add_argument("--status", action="store_true", help="Emit cluster health status")
    skills_parser.add_argument("--route", type=str, default=None, help="Route prompt to canonical functorial chain")
    skills_parser.add_argument("--lint", action="store_true", help="Run strict linter on skills cluster")
    skills_parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M communication")

    # catalog
    catalog_parser = subparsers.add_parser("catalog", help="Generate or display scripts catalog")
    catalog_parser.add_argument("--json", action="store_true", help="Emit catalog JSON to stdout")

    # docs
    docs_parser = subparsers.add_parser("docs", help="Synchronize or emit docs index")
    docs_parser.add_argument(
        "--json", action="store_true", help="Emit the document graph as pure JSON for inter-agentic consumption"
    )

    # list
    list_parser = subparsers.add_parser("list", help="List and search scripts by domain or keyword")
    list_parser.add_argument("--domain", "-d", type=str, default=None, help="Filter by C5 domain name")
    list_parser.add_argument("--search", "-s", type=str, default=None, help="Search script path or description")
    list_parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M communication")

    # verify
    verify_parser = subparsers.add_parser("verify", help="Run invariant and axiom verification engine")
    verify_parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M communication")

    # fast-smt
    fast_smt_parser = subparsers.add_parser("fast-smt", help="Run ultra-fast SMT gate verification (<0.5s)")
    fast_smt_parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M communication")

    # poc
    POC_MAP = {
        "xenharmonic": "c5_demos/poc_xenharmonic_swarm.py",
        "categorical": "c5_demos/poc_categorical_hallucination.py",
        "extinction": "c5_demos/poc_epistemic_extinction.py",
        "active-inference": "c5_demos/poc_active_inference_efe.py",
        "eu-ai-act": "c5_demos/poc_eu_ai_act_audit.py",
        "comonad": "c5_demos/poc_cta_comonad.py",
        "causal-hitl": "c5_demos/poc_causal_hitl_agent.py",
        "graph-wl": "c5_demos/poc_graph_isomorphism_wl.py",
        "planner-worker": "c5_demos/poc_two_tier_planner_worker.py",
        "fast-failure": "c5_demos/poc_fast_failure_guard.py",
        "time-domain": "c5_demos/poc_f60_time_domain.py",
        "logop-veto": "c5_demos/poc_logop_veto.py",
        "browser": "c5_demos/poc_browser_pipeline.py",
        "exergy": "c5_demos/demo_exergy_poc.py",
        "hero": "c5_demos/run_hero_demo.py",
        "bft": "c5_demos/run_commercial_bft.py",
        "logos-ethos": "c5_demos/demo_logos_ethos_ship.py",
    }
    poc_parser = subparsers.add_parser("poc", help=f"Execute Proof of Concept engines ({len(POC_MAP)} PoCs available)")
    poc_parser.add_argument("--target", choices=list(POC_MAP.keys()), default=None, help="Target PoC script to execute")
    poc_parser.add_argument("--list", action="store_true", help="List all available PoCs and their target keys")
    poc_parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M communication")

    args, unknown = parser.parse_known_args()

    if not args.command or args.command == "status":
        cmd_status(json_output=getattr(args, "json", False))
        return

    if args.command == "list":
        cmd_list(domain_filter=args.domain, search_term=args.search, json_output=getattr(args, "json", False))
        return

    if args.command == "audit":
        cmd_args = []
        if getattr(args, "fix", False):
            cmd_args.append("--fix")
        if getattr(args, "json", False):
            cmd_args.append("--json")
        sys.exit(run_subcommand("c5_quality_gates/audit_scripts_quality.py", cmd_args + unknown))
    elif args.command == "fast-smt":
        cmd_args = ["--json"] if getattr(args, "json", False) else []
        sys.exit(run_subcommand("c5_verifiers/fast_smt_gate.py", cmd_args + unknown))
    elif args.command == "preserve":
        sys.exit(run_subcommand("c5_log_custody/c5_preserve_logs.py", ["--provider", args.provider] + unknown))
    elif args.command == "swarm":
        mode = getattr(args, "mode", "default")
        if mode == "default":
            cmd_args = ["--tenants", str(args.tenants)]
            if args.concurrency:
                cmd_args += ["--concurrency", str(args.concurrency)]
            if getattr(args, "json", False):
                cmd_args.append("--json")
            sys.exit(run_subcommand("c5_sharur/sharur_swarm.py", cmd_args + unknown))
        elif mode == "audit":
            cmd_args = []
            if getattr(args, "json", False):
                cmd_args.append("--json")
            sys.exit(run_subcommand("c5_sharur/sharur_1000_audit_swarm.py", cmd_args + unknown))
        elif mode == "audit100":
            cmd_args = []
            if getattr(args, "json", False):
                cmd_args.append("--json")
            sys.exit(run_subcommand("c5_sharur/sharur_100_full_spectrum_auditor.py", cmd_args + unknown))
        elif mode == "stress":
            sys.exit(run_subcommand("c5_sharur/sharur_222_agentes.py", unknown))
        elif mode == "mcts":
            sys.exit(run_subcommand("c5_sharur/sharur_10000_orchestrator.py", unknown))
    elif args.command == "cortex":
        mode = getattr(args, "mode", None)
        cmd_args = []
        if getattr(args, "json", False):
            cmd_args.append("--json")
        if mode == "bootstrap":
            sys.exit(run_subcommand("c5_cortex/bootstrap_cortex_memory.py", cmd_args + unknown))
        elif mode == "vault":
            sys.exit(run_subcommand("c5_cortex/consolidate_babylon_vault.py", cmd_args + unknown))
    elif args.command == "sync":
        if getattr(args, "json", False):
            sys.exit(run_subcommand("c5_skills_ontology/sync_skills_registry.py", ["--json"]))
        else:
            rc1 = run_subcommand("c5_skills_ontology/sync_skills_registry.py", unknown)
            rc2 = run_subcommand("c5_quality_gates/sync_docs_index.py", [])
            sys.exit(rc1 if rc1 != 0 else rc2)
    elif args.command == "skills":
        cmd_args = []
        if getattr(args, "status", False):
            cmd_args.append("--status")
        if getattr(args, "route", None):
            cmd_args += ["--route", args.route]
        if getattr(args, "lint", False):
            cmd_args.append("--lint")
        if getattr(args, "json", False):
            cmd_args.append("--json")
        sys.exit(run_subcommand("c5_skills_ontology/c5_skill_router.py", cmd_args + unknown))
    elif args.command == "catalog":
        if getattr(args, "json", False):
            sys.exit(run_subcommand("generate_scripts_readme.py", ["--json"]))
        else:
            rc1 = run_subcommand("generate_scripts_readme.py", [])
            rc2 = run_subcommand("c5_quality_gates/sync_docs_index.py", [])
            sys.exit(rc1 if rc1 != 0 else rc2)
    elif args.command == "docs":
        cmd_args = ["--json"] if getattr(args, "json", False) else []
        sys.exit(run_subcommand("c5_quality_gates/sync_docs_index.py", cmd_args + unknown))
    elif args.command == "verify":
        cmd_args = ["--json"] if getattr(args, "json", False) else []
        sys.exit(run_subcommand("c5_verifiers/autodetect_invariants.py", cmd_args + unknown))
    elif args.command == "poc":
        if getattr(args, "list", False) or not getattr(args, "target", None):
            print(
                f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{C5_COLORS.RESET}"
            )
            print(
                f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}  {C5_COLORS.BOLD}BABYLON-60{C5_COLORS.RESET} {C5_COLORS.DIM}:: PROOF OF CONCEPT ENGINES (15 PoCs){C5_COLORS.RESET}    {C5_COLORS.BOLD}{C5_COLORS.CYAN}┃{C5_COLORS.RESET}"
            )
            print(
                f"{C5_COLORS.BOLD}{C5_COLORS.CYAN}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{C5_COLORS.RESET}\n"
            )
            for target_key, script_rel in POC_MAP.items():
                print(
                    f"  {C5_COLORS.BOLD}{C5_COLORS.AMBER}► {target_key:<20}{C5_COLORS.RESET} {C5_COLORS.DIM}│{C5_COLORS.RESET} {script_rel}"
                )
            print(f"\n{C5_COLORS.DIM}Uso: ./scripts/runner.py poc --target <name>{C5_COLORS.RESET}\n")
            return
        cmd_args = ["--json"] if getattr(args, "json", False) else []
        target = getattr(args, "target", None)
        if target in POC_MAP:
            sys.exit(run_subcommand(POC_MAP[target], cmd_args + unknown))
        else:
            print(f"[-] PoC desconocida: {target}")
            sys.exit(1)


if __name__ == "__main__":
    main()
