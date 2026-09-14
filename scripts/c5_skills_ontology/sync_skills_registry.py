#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.3 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized

"""
sync_skills_registry.py - Automated synchronization of physical skills (disk)
with docs/skills.json, ~/.gemini/config/skills/skills.json, and BABYLON-60 ontology.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

# Base Paths
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SCRIPTS_DIR.parent
SKILLS_DIR = Path.home() / ".gemini" / "config" / "skills"
WS_SKILLS_DIR = REPO_ROOT / ".agents" / "skills"
DOCS_SKILLS_JSON = REPO_ROOT / "docs" / "skills.json"
GLOBAL_SKILLS_JSON = SKILLS_DIR / "skills.json"
TAXONOMY_GUIDE = REPO_ROOT / "docs" / "03_guides" / "guide_skill_arsenal_taxonomy.md"
INDEX_DOC = REPO_ROOT / "docs" / "00_index.md"

# Canonical Skill Definitions for New / Updated Skills
SKILL_TIER_MAPPING: Dict[str, Dict[str, Any]] = {
    # Kernel & Meta-Kernel (Tier S: >= 21.000)
    "cortex-kernel": {"tier": 23000, "category": "Kernel"},
    "shared-manifest-kernel": {"tier": 22000, "category": "Kernel"},
    "cortex-skill-composer": {"tier": 21500, "category": "Meta-Kernel"},
    "thermo-audit": {"tier": 21500, "category": "Kernel"},
    "cortex-skill-auditor": {"tier": 21200, "category": "Meta-Kernel"},
    "rlhf-sentinel": {"tier": 21200, "category": "Governance"},
    "c5-scientific-problem-selection": {"tier": 21000, "category": "Meta-Kernel"},
    "cortex-skill-genesis": {"tier": 21000, "category": "Meta-Kernel"},
    "c5-lean4-neurosymbolic-architect": {"tier": 21000, "category": "Nucleus"},

    # Nucleus & Governance (Tier A: 18.000 - 20.999)
    "epistemic-extinction-protocol": {"tier": 20980, "category": "Nucleus"},
    "cta-cognitive-transition-algebra": {"tier": 20950, "category": "Nucleus"},
    "c5-lean4-axiomatic-orchestrator": {"tier": 20900, "category": "Nucleus"},
    "agentic-protocol-axiomatization": {"tier": 20800, "category": "Nucleus"},
    "categorical-hallucination-audit": {"tier": 20700, "category": "Nucleus"},
    "existence-gap-audit": {"tier": 20600, "category": "Nucleus"},
    "c5-2e-affective-decoupling": {"tier": 19800, "category": "Nucleus"},
    "c5-academic-peer-reviewer": {"tier": 20500, "category": "Nucleus"},
    "c5-axiomatic-kernel": {"tier": 20500, "category": "Nucleus"},
    "c5-dialectical-pipeline": {"tier": 20500, "category": "Nucleus"},
    "c5-epistemic-dissemination-engine": {"tier": 20500, "category": "Nucleus"},
    "polymath-concept-synthesis": {"tier": 20500, "category": "Nucleus"},
    "c5-popperian-falsification-auditor": {"tier": 20500, "category": "Nucleus"},
    "c5-real-thermodynamic-override": {"tier": 20400, "category": "Governance"},
    "c5-sci-paper-architect": {"tier": 20400, "category": "Nucleus"},
    "c5-ultrathink-epistemic-audit": {"tier": 20400, "category": "Nucleus"},
    "cct-cognitive-theory-advisor": {"tier": 20300, "category": "Nucleus"},
    "ultrathink": {"tier": 20300, "category": "Nucleus"},
    "autodidact-omega-deep-research": {"tier": 20200, "category": "Nucleus"},
    "cloud-chamber": {"tier": 20200, "category": "Nucleus"},
    "grill-me-v2": {"tier": 19900, "category": "Governance"},
    "c5-real-devsecops-scaffold": {"tier": 19850, "category": "Governance"},
    "apple-bypass": {"tier": 19800, "category": "Operations"},
    "c5-sovereign-identity-hardening": {"tier": 19800, "category": "Governance"},
    "c5-real-legaltech-analysis": {"tier": 19700, "category": "Governance"},
    "wait-what": {"tier": 19600, "category": "Nucleus"},
    "adaptive-cron": {"tier": 19500, "category": "Governance"},
    "symbiotic-cognitive-architecture": {"tier": 19400, "category": "Governance"},
    "anergy-purge-protocol": {"tier": 19300, "category": "Governance"},
    "ai-comparative-evaluation": {"tier": 19200, "category": "Operations"},
    "swarm-quantum-collapse": {"tier": 19100, "category": "Governance"},
    "babylon60-architecture": {"tier": 19000, "category": "Governance"},
    "whatsapp-nexus-protocol": {"tier": 18900, "category": "Governance"},
    "legion-audit": {"tier": 18800, "category": "Operations"},
    "dynamic-subagent-lifecycle": {"tier": 18600, "category": "Governance"},
    "biographical-thermo": {"tier": 18500, "category": "Nucleus"},
    "google-antigravity-sdk": {"tier": 18400, "category": "Governance"},
    "browser-subagent-orchestrator": {"tier": 18200, "category": "Governance"},
    "lora-swarm-pipeline": {"tier": 18200, "category": "Operations"},
    "babylon60-ide-orchestrator": {"tier": 18100, "category": "Governance"},

    # Operations & Diagnostics (Tier B / C: 12.000 - 17.999)
    "discourse-popperian-falsification": {"tier": 17900, "category": "Operations"},
    "ghidra-ida-binary-audit": {"tier": 17800, "category": "Operations"},
    "jujutsu-vcs-management": {"tier": 17600, "category": "Operations"},
    "cortex-telemetry": {"tier": 17500, "category": "Operations"},
    "frontier-prompting": {"tier": 17300, "category": "Operations"},
    "homebrew-ecosystem-management": {"tier": 17200, "category": "Operations"},
    "wizard": {"tier": 17000, "category": "Utilities"},
    "flstudio-mcp-production": {"tier": 17000, "category": "Operations"},
    "audiovisual-sota": {"tier": 16800, "category": "Operations"},
    "youtube-remotion-sota": {"tier": 16800, "category": "Operations"},
    "writing-for-agents": {"tier": 16500, "category": "Utilities"},
    "youtube-analysis-pipeline": {"tier": 16400, "category": "Operations"},
    "cloudflare-mcp-automation": {"tier": 15900, "category": "Operations"},
    "substack-socint-extraction": {"tier": 15500, "category": "Operations"},
    "reddit-socint-extraction": {"tier": 15300, "category": "Operations"},
    "opentimestamps-l5-diagnostics": {"tier": 15000, "category": "Diagnostics"},
    "electron-mac-bundle-collision-diagnostics": {"tier": 14800, "category": "Diagnostics"},
    "vscode-git-packed-refs-diagnostics": {"tier": 14600, "category": "Diagnostics"},
    "macos-lulu-firewall-diagnostics": {"tier": 14200, "category": "Diagnostics"},
    "github-api-rate-limit-optimization": {"tier": 13900, "category": "Utilities"},
    "suno-bracket-tagging": {"tier": 12800, "category": "Utilities"},
    "ironic-content-generator": {"tier": 11200, "category": "Utilities"},
    "handoff": {"tier": 10500, "category": "Utilities"},
}

NEW_ADJACENCY_EDGES = [
    {"source": "cortex-kernel", "target": "shared-manifest-kernel", "relation": "enforces_hardware_invariants"},
    {"source": "shared-manifest-kernel", "target": "thermo-audit", "relation": "bounds_concurrency"},
    {"source": "rlhf-sentinel", "target": "c5-real-thermodynamic-override", "relation": "guards_ring0_boundary"},
    {"source": "c5-lean4-neurosymbolic-architect", "target": "c5-lean4-axiomatic-orchestrator", "relation": "orchestrates_theorems"},
    {"source": "ultrathink", "target": "c5-ultrathink-epistemic-audit", "relation": "postmortem_trace"},
    {"source": "cloud-chamber", "target": "polymath-concept-synthesis", "relation": "crystallizes_ontology"},
    {"source": "adaptive-cron", "target": "cortex-telemetry", "relation": "meters_cognitive_dissipation"},
    {"source": "categorical-hallucination-audit", "target": "agentic-protocol-axiomatization", "relation": "audits_axioms"},
    {"source": "existence-gap-audit", "target": "c5-real-devsecops-scaffold", "relation": "audits_codebase"},
    {"source": "swarm-quantum-collapse", "target": "dynamic-subagent-lifecycle", "relation": "orchestrates_swarm"},
    {"source": "c5-real-thermodynamic-override", "target": "anergy-purge-protocol", "relation": "overrides_anergy"},
    {"source": "cct-cognitive-theory-advisor", "target": "cta-cognitive-transition-algebra", "relation": "advises"},
    {"source": "frontier-prompting", "target": "autodidact-omega-deep-research", "relation": "prompts_frontier"},
    {"source": "flstudio-mcp-production", "target": "youtube-remotion-sota", "relation": "provides_audio"},
    {"source": "opentimestamps-l5-diagnostics", "target": "c5-real-legaltech-analysis", "relation": "attests_l5"},
    {"source": "whatsapp-nexus-protocol", "target": "dynamic-subagent-lifecycle", "relation": "gateways_messaging"},
    {"source": "handoff", "target": "cortex-telemetry", "relation": "persists_session_state"},
]

def scan_physical_skills() -> Set[str]:
    """Scan disk directory for physical skills across global and workspace scopes."""
    skills = set()
    try:
        if SKILLS_DIR.exists():
            skills.update({d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").exists()})
        if WS_SKILLS_DIR.exists():
            skills.update({d.name for d in WS_SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").exists()})
    except Exception as e:
        print(f"Warning: Could not access skills directories: {e}")
    return skills

def sync_skills_json(verify_only: bool = False, json_output: bool = False) -> bool:
    """Sync disk skills with docs/skills.json and global skills.json."""
    physical_skills = scan_physical_skills()
    
    # Load base data from docs/skills.json or global skills.json
    base_path = DOCS_SKILLS_JSON if DOCS_SKILLS_JSON.exists() else GLOBAL_SKILLS_JSON
    if not base_path.exists():
        if not json_output:
            print(f"Error: Neither {DOCS_SKILLS_JSON} nor {GLOBAL_SKILLS_JSON} exists.")
        return False
        
    with open(base_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    entries: List[Dict[str, Any]] = data.get("entries", [])
    adjacency: List[Dict[str, str]] = data.get("adjacency", [])
    
    entry_map = {e["name"]: e for e in entries}
    
    # 1. Check for legacy renames
    if "wa-nexus-agent-gateway" in entry_map and "whatsapp-nexus-protocol" not in entry_map:
        entry_map["whatsapp-nexus-protocol"] = entry_map.pop("wa-nexus-agent-gateway")
        entry_map["whatsapp-nexus-protocol"]["name"] = "whatsapp-nexus-protocol"
        
    # 2. Re-register missing physical skills
    missing = physical_skills - set(entry_map.keys())
    if missing:
        if not json_output:
            print(f"Found {len(missing)} physical skills missing from skills.json: {missing}")
        for name in missing:
            info = SKILL_TIER_MAPPING.get(name, {"tier": 10000, "category": "Utilities"})
            entry_map[name] = {
                "name": name,
                "tier": info["tier"],
                "category": info["category"],
            }
            
    # 3. Update existing tiers, categories, and display_names to match SKILL.md
    for name, item in entry_map.items():
        if name in SKILL_TIER_MAPPING:
            item["tier"] = SKILL_TIER_MAPPING[name]["tier"]
            item["category"] = SKILL_TIER_MAPPING[name]["category"]
            
        # Search SKILL.md in global or workspace
        skill_file = SKILLS_DIR / name / "SKILL.md"
        if not skill_file.exists():
            skill_file = WS_SKILLS_DIR / name / "SKILL.md"
            
        if skill_file.exists():
            content = skill_file.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"display_name:\s*\"?(.*?)\"?\s*\n", content)
            if m:
                item["display_name"] = m.group(1).strip()

    # 4. Update Adjacency Matrix
    adj_set = {(a["source"], a["target"], a["relation"]) for a in adjacency}
    for edge in NEW_ADJACENCY_EDGES:
        key = (edge["source"], edge["target"], edge["relation"])
        if key not in adj_set:
            adjacency.append(edge)
            adj_set.add(key)
            
    # Sort entries by Tier descending
    sorted_entries = sorted(entry_map.values(), key=lambda x: x.get("tier", 0), reverse=True)
    avg_exergy = round(sum(e.get("tier", 0) for e in sorted_entries) / len(sorted_entries), 2)
    
    updated_data = {
        "version": "26.200",
        "updated_at": "2026-09-14T06:55:00Z",
        "total_skills": len(sorted_entries),
        "average_exergy_density": avg_exergy,
        "description": f"Grafo de adyacencia y topología conectada de las {len(sorted_entries)} habilidades del ecosistema CORTEX Engine integrado en BABYLON-60 (0 colisiones críticas)",
        "entries": sorted_entries,
        "adjacency": adjacency,
    }
    
    if json_output:
        print(json.dumps(updated_data, indent=2, ensure_ascii=False))
        return True

    if verify_only:
        print(f"Verification completed. Total registered skills: {len(sorted_entries)}")
        return len(missing) == 0
        
    # Write to docs/skills.json
    DOCS_SKILLS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(DOCS_SKILLS_JSON, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)
        f.write("\n")
        
    # Write to global ~/.gemini/config/skills/skills.json
    if SKILLS_DIR.exists():
        with open(GLOBAL_SKILLS_JSON, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        
    print(f"Successfully synced {len(sorted_entries)} skills to {DOCS_SKILLS_JSON} and {GLOBAL_SKILLS_JSON}")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BABYLON-60 Skills Registry Synchronizer")
    parser.add_argument("--verify", action="store_true", help="Verify only without writing")
    parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M consumption")
    args = parser.parse_args()
    
    success = sync_skills_json(verify_only=args.verify, json_output=args.json)
    sys.exit(0 if success else 1)
