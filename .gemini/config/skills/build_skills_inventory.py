#!/usr/bin/env python3
# C5-REAL
"""Artifact compilation."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from resolve_skill import build_all_resolutions, load_resolution


ROOT = Path(__file__).resolve().parent
SKILLS_TO_SKIP = {".ruff_cache", "_archived", "__pycache__", "Sortu", "autodidact-omega", "_metrics", "scripts", ".tombstone", "DIAMOND-Sentinel-OMEGA"}
RESOLUTION_FILE = ROOT / "skills_resolution.json"
INVENTORY_JSON = ROOT / "skills_inventory.json"
INVENTORY_MD = ROOT / "SKILLS_INVENTORY.md"
CATALOG_JSON = ROOT / "skills_catalog.json"


def iter_skill_dirs() -> list[Path]:
    """Yield valid skill dirs."""
    return sorted(
        path
        for path in ROOT.iterdir()
        if path.is_dir() and path.name not in SKILLS_TO_SKIP and (path / "SKILL.md").exists()
    )


def load_front_matter(skill_dir: Path) -> dict[str, Any]:
    """Extract SKILL.md YAML."""
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{skill_md} missing valid front matter")
    data = yaml.safe_load(parts[1]) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{skill_md} front matter is not a mapping")
    return data


def build_inventory() -> dict[str, Any]:
    """Compile inventory."""
    resolution = json.loads(RESOLUTION_FILE.read_text(encoding="utf-8"))
    skill_dirs = iter_skill_dirs()

    duplicates: dict[str, list[str]] = {}
    duplicate_map: dict[str, list[str]] = {}
    script_backed: dict[str, str] = {}
    docs_only: list[str] = []
    yaml_ok = 0
    external_repo_refs = 0
    missing_script_links = 0

    for skill_dir in skill_dirs:
        duplicate_key = skill_dir.name.lower().replace("_", "-")
        duplicate_map.setdefault(duplicate_key, []).append(skill_dir.name)

        manifest = load_front_matter(skill_dir)
        yaml_ok += 1

        skill_md = skill_dir / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")
        if (
            "$CORTEX_ROOT/30_CORTEX" in text
            or "compiled_skills" in text
            or "worktrees/sigint-monitor-fix" in text
        ):
            external_repo_refs += 1

        script = manifest.get("script")
        status = manifest.get("status")
        if script and (skill_dir / str(script)).exists() and status != "alias-only":
            script_backed[skill_dir.name] = str(script)
        else:
            docs_only.append(skill_dir.name)

    for key, names in duplicate_map.items():
        if len(names) > 1:
            duplicates[key] = names

    docs_only_sorted = sorted(docs_only)
    script_backed_sorted = dict(sorted(script_backed.items()))

    return {
        "updated_at": str(date.today()),
        "totals": {
            "directories": len(skill_dirs),
            "yaml_ok": yaml_ok,
            "script_backed": len(script_backed_sorted),
            "docs_only": len(docs_only_sorted),
            "missing_script_links": missing_script_links,
            "external_repo_refs": external_repo_refs,
        },
        "duplicates": duplicates,
        "docs_only": docs_only_sorted,
        "script_backed": script_backed_sorted,
        "resolution_snapshot": {
            "canonical": sorted(resolution.get("canonical", {}).keys()),
            "alias_only": sorted(resolution.get("alias_only", {}).keys()),
            "local_stubs": sorted(resolution.get("local_stubs", {}).keys()),
        },
    }


def render_inventory_markdown(inventory: dict[str, Any]) -> str:
    """Render MD."""
    totals = inventory["totals"]
    lines: list[str] = []
    lines.append("# Skills Inventory")
    lines.append("")
    lines.append(f"Last updated: {inventory['updated_at']}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Dirs: `{totals['directories']}`")
    lines.append(f"- YAML OK: `{totals['yaml_ok']}`")
    lines.append(f"- Script-backed: `{totals['script_backed']}`")
    lines.append(f"- Docs-only: `{totals['docs_only']}`")
    lines.append(f"- Missing script links: `{totals['missing_script_links']}`")
    lines.append(f"- Ext repo refs: `{totals['external_repo_refs']}`")
    lines.append("")
    lines.append("## Duplicate Clusters")
    lines.append("")
    if inventory["duplicates"]:
        for key, names in sorted(inventory["duplicates"].items()):
            lines.append(f"- `{key}`")
            for name in names:
                lines.append(f"  - `{name}`")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Documentation-Only Skills")
    lines.append("")
    for name in inventory["docs_only"]:
        lines.append(f"- `{name}`")
    lines.append("")
    lines.append("## Script-Backed Skills")
    lines.append("")
    for name, script in inventory["script_backed"].items():
        lines.append(f"- `{name}` → `{script}`")
    lines.append("")
    lines.append("## Resolution Snapshot")
    lines.append("")
    for key in ("canonical", "alias_only", "local_stubs"):
        values = inventory["resolution_snapshot"][key]
        joined = ", ".join(f"`{value}`" for value in values) if values else "None"
        lines.append(f"- `{key}`: {joined}")
    lines.append("")
    lines.append("## Next Decisions")
    lines.append("")
    lines.append("1. Canonicalize duplicate clusters.")
    lines.append("2. Archive docs-only skills.")
    lines.append("3. Regenerate external registry.")
    lines.append("4. Use `resolve_skill.py` and `validate_skills_tree.py`.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    """Main execution."""
    inventory = build_inventory()
    resolution = load_resolution()
    catalog = sorted(
        build_all_resolutions(resolution),
        key=lambda item: item["requested"].lower(),
    )
    INVENTORY_JSON.write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    INVENTORY_MD.write_text(render_inventory_markdown(inventory), encoding="utf-8")
    CATALOG_JSON.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"C5-REAL: REBUILT {INVENTORY_MD.name} | {INVENTORY_JSON.name} | {CATALOG_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
