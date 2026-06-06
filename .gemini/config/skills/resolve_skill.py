#!/usr/bin/env python3
"""C5-REAL. Resolve skill to execution contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent
RESOLUTION_FILE = ROOT / "skills_resolution.json"
SKILLS_TO_SKIP = {".ruff_cache", "_archived", "__pycache__", "Sortu", "autodidact-omega", "_metrics", "scripts"}


def load_resolution() -> dict[str, Any]:
    """Load resolution contract."""
    return json.loads(RESOLUTION_FILE.read_text(encoding="utf-8"))


def load_front_matter(skill_dir: Path) -> dict[str, Any]:
    """Extract YAML front matter."""
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{skill_md} missing valid front matter")
    data = yaml.safe_load(parts[1]) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{skill_md} front matter is not a mapping")
    return data


def infer_script(skill_dir: Path, manifest: dict[str, Any]) -> str | None:
    """Resolve explicit/implicit script path deterministically."""
    explicit = manifest.get("script")
    if explicit:
        return str(explicit)

    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir():
        return None

    candidates = sorted(path.name for path in scripts_dir.glob("*.py"))
    if len(candidates) == 1:
        return f"scripts/{candidates[0]}"

    return None


def list_skill_dirs() -> list[Path]:
    """Scan valid skill directories."""
    return sorted(
        path
        for path in ROOT.iterdir()
        if path.is_dir() and path.name not in SKILLS_TO_SKIP and (path / "SKILL.md").exists()
    )


def resolve_skill(name: str, resolution: dict[str, Any]) -> dict[str, Any]:
    """Map skill to execution payload."""
    skill_dir = ROOT / name
    if not skill_dir.is_dir():
        raise FileNotFoundError(f"Unknown skill directory: {name}")

    manifest = load_front_matter(skill_dir)
    canonical = resolution.get("canonical", {})
    alias_only = resolution.get("alias_only", {})
    local_stubs = resolution.get("local_stubs", {})
    docs_only = set(resolution.get("docs_only", []))

    script = infer_script(skill_dir, manifest)
    script_path = str(skill_dir / script) if script else None

    if name in canonical:
        return {
            "requested": name,
            "status": "canonical",
            "skill_dir": str(skill_dir),
            "canonical_skill_dir": str(skill_dir),
            "canonical_skill_md": str(skill_dir / "SKILL.md"),
            "script": script,
            "script_path": script_path,
            "runnable": bool(script),
            "aliases": canonical[name].get("aliases", []),
        }

    if name in alias_only:
        target = alias_only[name].get("canonical_skill")
        stub = alias_only[name].get("implementation_stub")
        return {
            "requested": name,
            "status": "alias-only",
            "skill_dir": str(skill_dir),
            "canonical_skill_md": str(skill_dir / target) if target else None,
            "canonical_skill_dir": str((skill_dir / target).resolve().parent) if target else None,
            "implementation": alias_only[name].get("implementation", "none"),
            "implementation_stub": str(skill_dir / stub) if stub else None,
            "runnable": False,
        }

    if name in local_stubs:
        target = local_stubs[name].get("canonical_skill")
        return {
            "requested": name,
            "status": "local-stub",
            "skill_dir": str(skill_dir),
            "canonical_skill_md": str(skill_dir / target) if target else None,
            "canonical_skill_dir": str((skill_dir / target).resolve().parent) if target else None,
            "script": script,
            "script_path": script_path,
            "runnable": bool(script),
        }

    if name in docs_only or manifest.get("status") == "docs-only":
        return {
            "requested": name,
            "status": "docs-only",
            "skill_dir": str(skill_dir),
            "canonical_skill_dir": str(skill_dir),
            "canonical_skill_md": str(skill_dir / "SKILL.md"),
            "script": None,
            "script_path": None,
            "runnable": False,
        }

    return {
        "requested": name,
        "status": "script-backed",
        "skill_dir": str(skill_dir),
        "canonical_skill_dir": str(skill_dir),
        "canonical_skill_md": str(skill_dir / "SKILL.md"),
        "script": script,
        "script_path": script_path,
        "runnable": bool(script),
    }


def build_all_resolutions(resolution: dict[str, Any]) -> list[dict[str, Any]]:
    """Batch resolve all skills."""
    resolved = [resolve_skill(skill_dir.name, resolution) for skill_dir in list_skill_dirs()]
    return sorted(resolved, key=lambda item: item["requested"].lower())


def parse_args() -> argparse.Namespace:
    """Parse args."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", nargs="?", help="Skill directory name to resolve")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Emit the resolution table for every local skill directory",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    return parser.parse_args()


def main() -> int:
    """Execute resolution and emit JSON."""
    args = parse_args()
    if not args.name and not args.all:
        print("Provide a skill name or use --all.", file=sys.stderr)
        return 2

    resolution = load_resolution()
    payload: Any
    if args.all:
        payload = build_all_resolutions(resolution)
    else:
        payload = resolve_skill(args.name, resolution)

    indent = 2 if args.pretty else None
    print(json.dumps(payload, indent=indent, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
