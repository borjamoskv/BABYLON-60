#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized

"""
sync_skills_registry.py - Automated synchronization of physical skills (disk)
with docs/skills.json and BABYLON-60 ontology.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

# Base Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = Path.home() / ".gemini" / "config" / "skills"
DOCS_SKILLS_JSON = REPO_ROOT / "docs" / "skills.json"
TAXONOMY_GUIDE = REPO_ROOT / "docs" / "03_guides" / "guide_skill_arsenal_taxonomy.md"
INDEX_DOC = REPO_ROOT / "docs" / "00_index.md"

# Canonical Skill Definitions for New / Updated Skills
SKILL_TIER_MAPPING: Dict[str, Dict[str, Any]] = {
    "cortex-kernel": {"tier": 23000, "category": "Kernel"},
    "cortex-skill-composer": {"tier": 21500, "category": "Meta-Kernel"},
    "cortex-skill-auditor": {"tier": 21200, "category": "Meta-Kernel"},
    "cortex-skill-genesis": {"tier": 21000, "category": "Meta-Kernel"},
    "epistemic-extinction-protocol": {"tier": 20980, "category": "Nucleus"},
    "cta-cognitive-transition-algebra": {"tier": 20950, "category": "Nucleus"},
    "agentic-protocol-axiomatization": {"tier": 20800, "category": "Nucleus"},
    "categorical-hallucination-audit": {"tier": 20700, "category": "Nucleus"},
    "existence-gap-audit": {"tier": 20600, "category": "Nucleus"},
    "polymath-concept-synthesis": {"tier": 20500, "category": "Nucleus"},
    "c5-real-thermodynamic-override": {"tier": 20400, "category": "Governance"},
    "cct-cognitive-theory-advisor": {"tier": 20300, "category": "Nucleus"},
    "autodidact-omega-deep-research": {"tier": 20200, "category": "Nucleus"},
    "c5-real-devsecops-scaffold": {"tier": 19850, "category": "Governance"},
    "c5-real-legaltech-analysis": {"tier": 19700, "category": "Governance"},
    "anergy-purge-protocol": {"tier": 19300, "category": "Governance"},
    "swarm-quantum-collapse": {"tier": 19100, "category": "Governance"},
    "whatsapp-nexus-protocol": {"tier": 18900, "category": "Governance"},
    "dynamic-subagent-lifecycle": {"tier": 18600, "category": "Governance"},
    "google-antigravity-sdk": {"tier": 18400, "category": "Governance"},
    "browser-subagent-orchestrator": {"tier": 18200, "category": "Governance"},
    "babylon60-ide-orchestrator": {"tier": 18100, "category": "Governance"},
    "discourse-popperian-falsification": {"tier": 17900, "category": "Operations"},
    "ghidra-ida-binary-audit": {"tier": 17800, "category": "Operations"},
    "jujutsu-vcs-management": {"tier": 17600, "category": "Operations"},
    "cortex-telemetry": {"tier": 17500, "category": "Operations"},
    "frontier-prompting": {"tier": 17300, "category": "Operations"},
    "homebrew-ecosystem-management": {"tier": 17200, "category": "Operations"},
    "flstudio-mcp-production": {"tier": 17000, "category": "Operations"},
    "youtube-remotion-sota": {"tier": 16800, "category": "Operations"},
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
    """Scan disk directory for physical skills."""
    if not SKILLS_DIR.exists():
        print(f"Warning: Skills dir {SKILLS_DIR} not found.")
        return set()
    return {d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").exists()}

def sync_skills_json(verify_only: bool = False) -> bool:
    """Sync disk skills with docs/skills.json."""
    physical_skills = scan_physical_skills()
    
    if not DOCS_SKILLS_JSON.exists():
        print(f"Error: {DOCS_SKILLS_JSON} does not exist.")
        return False
        
    with open(DOCS_SKILLS_JSON, "r") as f:
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
        skill_file = SKILLS_DIR / name / "SKILL.md"
        if skill_file.exists():
            content = skill_file.read_text(encoding="utf-8")
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
    
    updated_data = {
        "version": "24.000",
        "updated_at": "2026-08-11T20:20:00Z",
        "description": f"Grafo de adyacencia y topología conectada de las {len(sorted_entries)} habilidades del ecosistema CORTEX Engine integrado en BABYLON-60",
        "entries": sorted_entries,
        "adjacency": adjacency,
    }
    
    if verify_only:
        print(f"Verification completed. Total registered skills: {len(sorted_entries)}")
        return len(missing) == 0
        
    with open(DOCS_SKILLS_JSON, "w") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)
        f.write("\n")
        
    print(f"Successfully synced {len(sorted_entries)} skills to {DOCS_SKILLS_JSON}")
    return True

if __name__ == "__main__":
    verify = "--verify" in sys.argv
    success = sync_skills_json(verify_only=verify)
    sys.exit(0 if success else 1)
