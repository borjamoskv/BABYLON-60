# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""Build skill_registry.json from disabled plugins.

Scans all SKILL.md files in ~/.gemini/config/plugins_disabled/*/skills/*/
and extracts YAML frontmatter (name, description) plus file metadata.

Output: 2_Nucleo_Estatico/skill_registry.json
"""

import json
import os
import re
from pathlib import Path

def _find_repo_root() -> Path:
    curr = Path(__file__).resolve()
    for parent in [curr] + list(curr.parents):
        if (parent / "2_Nucleo_Estatico").exists():
            return parent
    return curr.parents[3]

PLUGINS_DIR = Path.home() / ".gemini" / "config" / "plugins_disabled"
OUTPUT = _find_repo_root() / "2_Nucleo_Estatico" / "skill_registry.json"


def extract_frontmatter(md_path: Path) -> dict[str, str]:
    """Extract YAML frontmatter fields from a SKILL.md file."""
    text = md_path.read_text(encoding="utf-8", errors="replace")
    # Match YAML frontmatter between --- delimiters
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}

    fm = {}
    block = m.group(1)
    for line in block.splitlines():
        # Simple key: value extraction (handles quoted values)
        kv = re.match(r'^(\w+)\s*:\s*(.+)$', line)
        if kv:
            key = kv.group(1).strip()
            val = kv.group(2).strip().strip('"').strip("'")
            fm[key] = val
    return fm


def extract_keywords(name: str, description: str) -> list[str]:
    """Extract searchable keywords from name and description."""
    stopwords = {
        "the", "and", "for", "use", "when", "this", "that", "with",
        "from", "you", "are", "not", "has", "will", "can", "its",
        "also", "into", "was", "been", "have", "does", "did", "don",
        "skill", "user", "asks", "about",
    }
    text = f"{name} {description}"
    tokens = re.split(r"[^a-z0-9]+", text.lower())
    seen = set()
    keywords = []
    for t in tokens:
        if len(t) >= 3 and t not in stopwords and t not in seen:
            seen.add(t)
            keywords.append(t)
    return keywords


def main() -> None:
    if not PLUGINS_DIR.exists():
        print(f"[ABORT] Plugins directory not found: {PLUGINS_DIR}")
        return

    registry: list[dict] = []

    for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
        if not plugin_dir.is_dir():
            continue
        plugin_name = plugin_dir.name
        skills_dir = plugin_dir / "skills"
        if not skills_dir.exists():
            continue

        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            md_path = skill_dir / "SKILL.md"
            if not md_path.exists():
                continue

            fm = extract_frontmatter(md_path)
            name = fm.get("name", skill_dir.name)
            description = fm.get("description", "")
            size_bytes = md_path.stat().st_size
            keywords = extract_keywords(name, description)

            entry = {
                "name": name,
                "description": description,
                "plugin": plugin_name,
                "skill_dir_name": skill_dir.name,
                "skill_md_path": str(md_path),
                "size_bytes": size_bytes,
                "keywords": keywords,
            }
            registry.append(entry)

    # Write registry
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"[NODO 4] Built registry: {len(registry)} skills → {OUTPUT}")

    # Stats
    total_bytes = sum(e["size_bytes"] for e in registry)
    by_plugin = {}
    for e in registry:
        by_plugin.setdefault(e["plugin"], []).append(e)

    print(f"[NODO 4] Total skill bytes: {total_bytes:,} ({total_bytes/1024:.0f} KB)")
    for plugin, skills in sorted(by_plugin.items()):
        plugin_bytes = sum(s["size_bytes"] for s in skills)
        print(f"  {plugin}: {len(skills)} skills, {plugin_bytes:,} bytes")


if __name__ == "__main__":
    main()
