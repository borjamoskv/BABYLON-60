#!/usr/bin/env python3
# C5-REAL
"""
Invariants:
- SKILL.md: YAML valid
- Target: script exists
- State: sync
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from resolve_skill import build_all_resolutions, load_resolution


ROOT = Path(__file__).resolve().parent.parent
SKILLS_TO_SKIP = {".ruff_cache", "_archived", "__pycache__", "Sortu", "autodidact-omega", "_metrics", "scripts"}
RESOLUTION_FILE = ROOT / "skills_resolution.json"
CATALOG_FILE = ROOT / "skills_catalog.json"


def load_front_matter(skill_md: Path) -> dict[str, Any]:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError("missing front matter opener")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("missing front matter closer")

    data = yaml.safe_load(parts[1]) or {}
    if not isinstance(data, dict):
        raise ValueError("front matter is not a mapping")
    return data


def iter_skill_dirs(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and path.name not in SKILLS_TO_SKIP
    )


def validate_skill_manifests(skill_dirs: list[Path]) -> list[str]:
    errors: list[str] = []

    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"{skill_dir.name}: missing SKILL.md")
            continue

        try:
            data = load_front_matter(skill_md)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{skill_dir.name}: invalid front matter ({exc})")
            continue

        script = data.get("script")
        if script:
            script_path = skill_dir / str(script)
            if not script_path.exists():
                errors.append(f"{skill_dir.name}: missing script target {script}")

    return errors


def validate_resolution_contract(skill_dirs: list[Path]) -> list[str]:
    errors: list[str] = []

    if not RESOLUTION_FILE.exists():
        return ["skills_resolution.json: missing"]

    data = json.loads(RESOLUTION_FILE.read_text(encoding="utf-8"))

    canonical = data.get("canonical", {})
    alias_only = data.get("alias_only", {})
    local_stubs = data.get("local_stubs", {})
    docs_only = set(data.get("docs_only", []))

    names = {path.name for path in skill_dirs}

    for name, payload in canonical.items():
        if name not in names:
            errors.append(f"resolution: canonical skill missing from tree: {name}")
            continue
        script = payload.get("script")
        if script and not (ROOT / name / script).exists():
            errors.append(f"resolution: canonical script missing: {name}/{script}")

    for name, payload in alias_only.items():
        if name not in names:
            errors.append(f"resolution: alias skill missing from tree: {name}")
            continue
        target = payload.get("canonical_skill")
        if target and not (ROOT / name / target).exists():
            errors.append(f"resolution: alias target missing: {name}/{target}")

    for name, payload in local_stubs.items():
        if name not in names:
            errors.append(f"resolution: local stub missing from tree: {name}")
            continue
        script = payload.get("script")
        if script and not (ROOT / name / script).exists():
            errors.append(f"resolution: local stub script missing: {name}/{script}")
        target = payload.get("canonical_skill")
        if target and not (ROOT / name / target).exists():
            errors.append(f"resolution: local stub canonical target missing: {name}/{target}")

    for name in docs_only:
        if name not in names:
            errors.append(f"resolution: docs-only skill missing from tree: {name}")
            continue
        scripts_dir = ROOT / name / "scripts"
        if scripts_dir.exists() and any(scripts_dir.glob("*.py")):
            errors.append(f"resolution: docs-only skill unexpectedly has scripts: {name}")

    return errors


def validate_catalog_snapshot() -> list[str]:
    if not CATALOG_FILE.exists():
        return ["skills_catalog.json: missing"]

    expected = build_all_resolutions(load_resolution())
    actual = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    if actual != expected:
        return ["skills_catalog.json: out of sync with resolve_skill.py --all"]
    return []


def main() -> int:
    skill_dirs = iter_skill_dirs(ROOT)
    errors = [
        *validate_skill_manifests(skill_dirs),
        *validate_resolution_contract(skill_dirs),
        *validate_catalog_snapshot(),
    ]

    if errors:
        print("SKILLS TREE INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print("SKILLS TREE OK")
    print(f"- directories: {len(skill_dirs)}")
    print(f"- resolution: {RESOLUTION_FILE.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
