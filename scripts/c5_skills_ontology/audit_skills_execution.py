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
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
SKILLS_DIR = SCRIPTS_DIR / "c5_skills_ontology"
for p in [REPO_ROOT, SCRIPTS_DIR, SKILLS_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from c5_skill_router import collect_all_skills, load_canonical_data, GLOBAL_SKILLS_DIR, WS_SKILLS_DIR


def route_query_top(query: str, skills: dict) -> list[str]:
    import re
    q_norm = query.lower()
    q_words = set(re.findall(r"\b[a-záéíóúñ0-9_-]{3,}\b", q_norm))

    scored_skills = []
    for name, s in skills.items():
        if name == "cortex-kernel":
            continue
        score: float = 0.0
        for trig in s.get("triggers", []):
            if trig in q_norm:
                score += 15.0
            else:
                trig_words = set(trig.split())
                common = trig_words.intersection(q_words)
                if common:
                    score += len(common) * 3.0

        name_words = set(name.replace("-", " ").split())
        score += len(name_words.intersection(q_words)) * 2.0

        desc_words = set(re.findall(r"\b[a-záéíóúñ0-9_-]{3,}\b", s.get("description", "").lower()))
        score += len(desc_words.intersection(q_words)) * 0.5

        if score > 0:
            scored_skills.append((name, score))

    scored_skills.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _ in scored_skills[:3]]


def run_full_skills_audit() -> bool:
    print("=================================================================")
    print("  BABYLON-60 v4.0 — CORTEX SKILLS EXECUTION & AUDIT SUITE")
    print("=================================================================")

    start_time = time.time()
    skills = collect_all_skills()
    entries, adjacency = load_canonical_data()

    total_physical = len(skills)

    print(f"[*] Physical Skills Directory: {GLOBAL_SKILLS_DIR}")
    print(f"[*] Workspace Skills Directory: {WS_SKILLS_DIR}")
    print(f"[*] Total Loaded Manifests:    {total_physical}")

    # 1. Frontmatter Integrity Checks
    malformed = [name for name, s in skills.items() if s.get("description") == "[manifest parse error]"]
    if malformed:
        print(f"[!] WARNING: Found {len(malformed)} malformed manifests: {malformed}")
    else:
        print(f"[+] All {total_physical} SKILL.md manifests passed YAML frontmatter validation.")

    # 2. Category Distribution
    categories: dict[str, list[str]] = {}
    for name, s in skills.items():
        cat = s.get("category", "General")
        categories.setdefault(cat, []).append(name)

    print("\n--- Skill Distribution by Category ---")
    for cat in sorted(categories.keys()):
        print(f"  - {cat:20s}: {len(categories[cat])} skills")

    # 3. Intent Resolution & Routing Verification Suite
    print("\n--- Intent Resolution Benchmark Suite ---")
    test_benchmarks = [
        ("Deep Research & arXiv", "deep research arXiv paper", "autodidact-omega-deep-research"),
        ("Existence Gap Audit", "auditar existencia de imports ghost", "existence-gap-audit"),
        ("Categorical Hallucination", "alucinacion categorica Markov", "categorical-hallucination-audit"),
        ("DevSecOps & CI/CD", "generar patch devsecops", "c5-real-devsecops-scaffold"),
        ("Cloudflare Workers", "desplegar worker cloudflare", "cloudflare-mcp-usage"),
        ("Swarm Quantum Collapse", "enjambre swarm quantum collapse", "swarm-quantum-collapse"),
        ("FL Studio MCP DSP", "generar script piano roll FL Studio MIDI", "flstudio-mcp-production"),
        ("Handoff Protocol", "handoff traspaso de contexto y sesion", "handoff"),
    ]

    passed_intents = 0
    for name, intent, expected_target in test_benchmarks:
        candidates = route_query_top(intent, skills)
        primary = candidates[0] if candidates else "None"
        success = expected_target in candidates
        status_str = "PASS" if success else "FAIL"
        if success:
            passed_intents += 1
        print(f"  [{status_str}] {name:25s} -> Intent: '{intent}' => Elected: {primary} (in {candidates})")

    elapsed = (time.time() - start_time) * 1000
    print("\n-----------------------------------------------------------------")
    print(f"[+] Audit Finished in {elapsed:.2f} ms")
    print(f"[+] Passed Intent Tests: {passed_intents}/{len(test_benchmarks)}")
    print("=================================================================")

    return len(malformed) == 0 and passed_intents == len(test_benchmarks)


if __name__ == "__main__":
    success = run_full_skills_audit()
    sys.exit(0 if success else 1)
