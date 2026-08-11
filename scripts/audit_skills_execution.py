#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized

"""
audit_skills_execution.py - Comprehensive verification & benchmark suite for
BABYLON-60 / CORTEX skills system.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from babylon60.extensions.skills.registry import SkillRegistry
from babylon60.extensions.skills.router import SkillRouter


def run_full_skills_audit() -> bool:
    print("=================================================================")
    print("  BABYLON-60 v4.0 — CORTEX SKILLS EXECUTION & AUDIT SUITE")
    print("=================================================================")

    start_time = time.time()
    registry = SkillRegistry().load()
    router = SkillRouter(registry=registry)

    total_physical = registry.count
    stats = registry.discovery_stats

    print(f"[*] Physical Skills Directory: {registry._base_dir}")
    print(f"[*] Total Loaded Manifests:    {total_physical}")
    print(f"[*] Manifest Discovery Stats:  {stats}")

    # 1. Frontmatter Integrity Checks
    malformed = [m for m in registry.all() if m.description == "[manifest parse error]"]
    if malformed:
        print(f"[!] WARNING: Found {len(malformed)} malformed manifests: {[m.name for m in malformed]}")
    else:
        print(f"[+] All {total_physical} SKILL.md manifests passed YAML frontmatter validation.")


    # 2. Category Distribution
    print("\n--- Skill Distribution by Category ---")
    for cat in sorted(registry.categories):
        skills_in_cat = registry.by_category(cat)
        print(f"  - {cat:20s}: {len(skills_in_cat)} skills")

    # 3. Intent Resolution & Routing Verification Suite
    print("\n--- Intent Resolution Benchmark Suite ---")
    test_benchmarks = [
        ("Deep Research & arXiv", "deep research arXiv paper", "autodidact-omega-deep-research"),
        ("Existence Gap Audit", "auditar existencia de imports ghost", "existence-gap-audit"),
        ("Categorical Hallucination", "audit alucinacion categorica Markov", "categorical-hallucination-audit"),
        ("DevSecOps & CI/CD", "generar patch devsecops", "c5-real-devsecops-scaffold"),
        ("Cloudflare Workers", "desplegar worker cloudflare", "cloudflare-mcp-automation"),
        ("Swarm Quantum Collapse", "orquestar enjambre swarm quantum collapse", "swarm-quantum-collapse"),
        ("FL Studio MCP DSP", "generar script piano roll FL Studio MIDI", "flstudio-mcp-production"),
        ("Frontier Prompting", "prompting de frontera Qwen Claude", "frontier-prompting"),
        ("Handoff Protocol", "handoff traspaso de contexto y sesion", "handoff"),
    ]

    passed_intents = 0
    for name, intent, expected_top in test_benchmarks:
        routes = router.route_intent(intent)
        top_name = routes[0].name if routes else "None"
        success = top_name == expected_top or expected_top in [r.name for r in routes]
        status_str = "PASS" if success else "FAIL"
        if success:
            passed_intents += 1
        print(f"  [{status_str}] {name:25s} -> Intent: '{intent}' => Elected: {top_name}")

    elapsed = (time.time() - start_time) * 1000
    print("\n-----------------------------------------------------------------")
    print(f"[+] Audit Finished in {elapsed:.2f} ms")
    print(f"[+] Passed Intent Tests: {passed_intents}/{len(test_benchmarks)}")
    print("=================================================================")

    return len(malformed) == 0 and passed_intents == len(test_benchmarks)


if __name__ == "__main__":
    success = run_full_skills_audit()
    sys.exit(0 if success else 1)
