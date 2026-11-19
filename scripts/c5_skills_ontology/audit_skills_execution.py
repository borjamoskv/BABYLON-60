#!/usr/bin/env python3
# ruff: noqa: E402
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized

"""
audit_skills_execution.py - Comprehensive verification & benchmark suite for
BABYLON-60 / CORTEX skills system using native c5_skill_router.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Add project root and ontology scripts to sys.path
REPO_ROOT = Path(__file__).absolute().parent.parent.parent
ONTOLOGY_SCRIPTS = REPO_ROOT / "scripts" / "c5_skills_ontology"
if str(ONTOLOGY_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ONTOLOGY_SCRIPTS))

import c5_skill_router
from c5_skill_router import collect_all_skills, load_canonical_data

REPO_GLOBAL_SKILLS = REPO_ROOT / "tools" / "skill_library" / "global"
if REPO_GLOBAL_SKILLS.is_dir():
    c5_skill_router.GLOBAL_SKILLS_DIR = REPO_GLOBAL_SKILLS
    c5_skill_router.GLOBAL_SKILLS_JSON = REPO_GLOBAL_SKILLS / "skills.json"


def run_full_skills_audit() -> bool:
    print("=================================================================")
    print("  BABYLON-60 v4.0 — CORTEX SKILLS EXECUTION & AUDIT SUITE")
    print("=================================================================")

    start_time = time.time()
    skills = collect_all_skills()
    entries, adjacency = load_canonical_data()

    total_physical = len(skills)
    registered = sum(1 for s in skills if s in entries)

    print(f"[*] Total Loaded Manifests:    {total_physical}")
    print(f"[*] Registered in Catalog:    {registered}/{total_physical}")
    print(f"[*] Functorial DAG Edges:      {len(adjacency)}")

    # 1. Frontmatter Integrity Checks
    malformed = [k for k, v in skills.items() if v.get("description") == "[manifest parse error]"]
    if malformed:
        print(f"[!] WARNING: Found {len(malformed)} malformed manifests: {malformed}")
    else:
        print(f"[+] All {total_physical} SKILL.md manifests passed YAML frontmatter validation.")

    # 2. Scope Distribution
    print("\n--- Skill Distribution by Scope ---")
    scopes: dict[str, int] = {}
    for s in skills.values():
        sc = s.get("scope", "unknown")
        scopes[sc] = scopes.get(sc, 0) + 1
    for sc, count in sorted(scopes.items()):
        print(f"  - {sc:20s}: {count} skills")

    # 3. Intent Resolution & Routing Verification Suite
    from c5_skill_router import score_skills_for_query

    print("\n--- Intent Resolution Benchmark Suite ---")
    test_benchmarks = [
        ("Alpha Extraction & arXiv", "alpha extraction pipeline arXiv", "c5-alpha-extraction-pipeline"),
        ("Existence Gap Audit", "auditar existencia de imports ghost", "existence-gap-audit"),
        ("Categorical Hallucination", "audit alucinacion categorica Markov", "categorical-hallucination-audit"),
        ("Thermo Audit & Branch Review", "thermos audit revision termonuclear de rama", "c5-thermos-audit"),
        ("LARSA Consensus", "consenso bft isostatico larsa-120", "c5-larsa-120"),
        ("Swarm Quantum Collapse", "orquestar enjambre swarm quantum collapse", "swarm-quantum-collapse"),
        ("Mushushu Firewall", "firewall epistemico mushushu-0 apoptosis", "c5-mushushu-0"),
        ("Handoff Protocol", "handoff traspaso de contexto y sesion", "handoff"),
        ("Linguistic Entropy Audit", "auditoría de entropía de lenguaje", "c5-information-thermodynamics"),
        ("Typo-Resilient Entropy Route", "auditorai de entropai de lenguaje", "c5-information-thermodynamics"),
        ("Skill Trigger Optimization", "mejora de triggers y solapamiento de skills", "cortex-skill-auditor"),
    ]

    passed_intents = 0
    for name, intent, expected_top in test_benchmarks:
        ranked = score_skills_for_query(intent, skills)
        best_name = ranked[0][0] if ranked else "None"

        success = best_name == expected_top
        status_str = "PASS" if success else "FAIL"
        if success:
            passed_intents += 1
        print(f"  [{status_str}] {name:28s} -> Intent: '{intent}' => Elected: {best_name}")

    elapsed = (time.time() - start_time) * 1000
    print("\n-----------------------------------------------------------------")
    print(f"[+] Audit Finished in {elapsed:.2f} ms")
    print(f"[+] Passed Intent Tests: {passed_intents}/{len(test_benchmarks)}")
    print("=================================================================")

    return len(malformed) == 0 and passed_intents == len(test_benchmarks)


if __name__ == "__main__":
    success = run_full_skills_audit()
    sys.exit(0 if success else 1)
