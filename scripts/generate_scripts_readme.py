#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
generate_scripts_readme.py - Automated self-documenting catalog generator
Scans all scripts in scripts/ and builds scripts/README.md with docstrings and taxonomy.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
README_PATH = SCRIPTS_DIR / "README.md"

CATEGORIES = {
    "Core Dispatchers & Quality Gates": [
        "runner.py",
        "audit_scripts_quality.py",
        "pre_push_ledger_guard.py",
        "audit_fixer.py",
        "symlink_depth_auditor.py",
    ],
    "Swarm & Legion Execution Engines": [
        "legion_swarm.py",
        "legion_swarm_core.py",
        "legion_100_swarm.py",
        "legion_10000_swarm.py",
        "legion_1000_audit_swarm.py",
        "legion_10000_orchestrator.py",
        "legion_222_agentes.py",
        "centuria_swarm_commander.py",
        "centuria_swarm_runner.py",
        "remotion_swarm_orchestrator.py",
        "secret_swarm_auditor.py",
        "swarm_lock_guard.py",
    ],
    "Skill Synchronization & Ontology": [
        "sync_skills_registry.py",
        "optimize_all_skill_triggers.py",
        "audit_skills_execution.py",
        "sync_vault_uuids.py",
    ],
    "Log Custody & Forensic Attestation": [
        "c5_preserve_logs.py",
        "c5_preserve_agent_local_logs.py",
        "c5_preserve_claude_local_logs.py",
        "c5_organize_captures.py",
        "c5_verifiers/verify_captures.py",
    ],
    "Thermodynamic Benchmarks & Stress Tests": [
        "stress_100m_bft.py",
        "stress_10m.py",
        "stress_sqlite_wal.py",
        "benchmark_ledger_throughput.py",
        "cache_1000_memoization_bench.py",
        "c5_exergy_optimizer_monitor.py",
        "exergy_arbitrage_engine.py",
        "exergy_dashboard_server.py",
        "exergy_optimizer_agent.py",
    ],
    "Formal Verification & Axiom Oracles": [
        "axiom_verifier_z3.py",
        "c5_verifiers/verify_anergy_token_purge.py",
        "autodetect_invariants.py",
        "c5_verifiers/verify_claims.py",
        "c5_verifiers/verify_tonnetz_falsification.py",
        "conformance_test.py",
        "deterministic_audit.py",
    ],
    "C5 Demos & Proofs of Concept": [
        "c5_demos/poc_browser_pipeline.py",
        "c5_demos/poc_causal_hitl_agent.py",
        "c5_demos/poc_f60_time_domain.py",
        "c5_demos/poc_fast_failure_guard.py",
        "c5_demos/poc_graph_isomorphism_wl.py",
        "c5_demos/poc_logop_veto.py",
        "c5_demos/poc_two_tier_planner_worker.py",
        "c5_demos/demo_exergy_poc.py",
        "c5_demos/demo_logos_ethos_ship.py",
    ],
    "L1 Anchor & Ledger Engines": [
        "anchor_l1_sink.py",
        "l1_sink_bitcoin.py",
        "ledger_snapshot_engine.py",
        "bittensor_yuma_consensus_c5.py",
    ],
}


def extract_docstring(py_path: Path) -> str:
    try:
        content = py_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
        doc = ast.get_docstring(tree)
        if doc:
            first_paragraph = doc.strip().split("\n\n")[0].replace("\n", " ")
            return first_paragraph
    except Exception:
        pass

    # Fallback to first line of text
    lines = py_path.read_text(encoding="utf-8").splitlines()
    for line in lines[1:15]:
        if line.strip().startswith('"""') or line.strip().startswith("'''"):
            return line.strip().strip('"').strip("'")
        if line.strip().startswith("#") and not line.startswith("# =") and not line.startswith("#!"):
            return line.strip().lstrip("#").strip()
    return "Sovereign execution script"


def generate_readme() -> None:
    py_files = sorted(SCRIPTS_DIR.rglob("*.py"))
    sh_files = sorted(SCRIPTS_DIR.rglob("*.sh"))

    categorized_files = set()
    for cat, files in CATEGORIES.items():
        categorized_files.update(files)

    md_lines = [
        "# ⚡ BABYLON-60 Sovereign Scripts Suite",
        "",
        "> **Directorio de Automatización, Enjambres BFT, Calidad AST y Preservación de Logs**  ",
        "> **Estándar:** C5-REAL | **Shebang Compliance:** 100.0% Line 1",
        "",
        "## 🛠️ CLI Runner Centralizado",
        f"Cualquier tarea del suite se puede ejecutar a través de la CLI unificada [runner.py](file://{SCRIPTS_DIR / 'runner.py'}):",
        "```bash",
        "./scripts/runner.py status              # Diagnóstico y métricas de salud",
        "./scripts/runner.py audit               # Portón de calidad AST & anti-patrones",
        "./scripts/runner.py preserve --provider all # Custodia forense de logs",
        "./scripts/runner.py swarm -n 100        # Enjambre paralelo BFT en RAM",
        "./scripts/runner.py sync                # Sincronización de skills con docs/skills.json",
        "```",
        "",
        "---",
        "",
        "## 📂 Catálogo por Categorías",
        "",
    ]

    for cat_name, file_list in CATEGORIES.items():
        md_lines.append(f"### {cat_name}")
        md_lines.append("")
        md_lines.append("| Script | Descripción / Propósito |")
        md_lines.append("| :--- | :--- |")
        for fn in file_list:
            fp = SCRIPTS_DIR / fn
            if fp.exists():
                doc = extract_docstring(fp)
                md_lines.append(f"| [`{fn}`](file://{fp}) | {doc} |")
        md_lines.append("")

    # General Utilities (uncategorized)
    uncategorized = [f for f in py_files if f.relative_to(SCRIPTS_DIR).as_posix() not in categorized_files and f.name != "generate_scripts_readme.py"]
    if uncategorized:
        md_lines.append("### Herramientas de Dominio & Utilidades")
        md_lines.append("")
        md_lines.append("| Script | Descripción / Propósito |")
        md_lines.append("| :--- | :--- |")
        for fp in uncategorized:
            fn = fp.relative_to(SCRIPTS_DIR).as_posix()
            doc = extract_docstring(fp)
            md_lines.append(f"| [`{fn}`](file://{fp}) | {doc} |")
        md_lines.append("")

    # Shell Scripts
    if sh_files:
        md_lines.append("### Shell Scripts (`*.sh`)")
        md_lines.append("")
        md_lines.append("| Script | Tipo |")
        md_lines.append("| :--- | :--- |")
        for fp in sh_files:
            fn = fp.relative_to(SCRIPTS_DIR).as_posix()
            md_lines.append(f"| [`{fn}`](file://{fp}) | Executable Bash Script |")
        md_lines.append("")

    md_lines.append("---")
    md_lines.append("*Catálogo auto-generado dinámicamente por `generate_scripts_readme.py`.*")

    README_PATH.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[+] Successfully generated catalog README at: {README_PATH}")


if __name__ == "__main__":
    generate_readme()
