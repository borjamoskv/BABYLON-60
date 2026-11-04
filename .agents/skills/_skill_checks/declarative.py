#!/usr/bin/env python3
"""Independent structural check. Role contracts apply only to skills declaring them."""

import argparse
import json
from pathlib import Path
import sys
import yaml


def inspect(root: Path) -> dict[str, object]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    roles: dict[str, int] = {}
    files = sorted(root.glob("*/SKILL.md"))
    if not files:
        errors.append({"file": str(root), "rule": "empty-scope", "message": "No skills in requested scope"})
    for path in files:

        def fail(rule: str, message: str) -> None:
            errors.append({"file": str(path.relative_to(root)), "rule": rule, "message": message})

        try:
            text = path.read_text()
            parts = text.split("---", 2)
            if not text.startswith("---") or len(parts) != 3:
                fail("yaml", "Missing YAML frontmatter")
                continue
            fm = yaml.safe_load(parts[1])
            if not isinstance(fm, dict):
                fail("yaml", "Frontmatter is not a mapping")
                continue
            if fm.get("name") != path.parent.name:
                fail("identity", "Name differs from folder")
            if not isinstance(fm.get("description"), str) or not fm["description"].strip():
                fail("description", "Missing capability description")
            if not parts[2].strip():
                fail("procedure", "Missing procedure or reference")
            if "role" not in fm and "directives" not in fm:
                continue
            role = fm.get("role")
            if role not in {"arquitecto", "ejecutor", "auditor"}:
                fail("role", "Invalid declared role")
            else:
                roles[role] = roles.get(role, 0) + 1
            if role not in fm.get("allowed_roles", []):
                fail("allowed-role", "Primary role is not allowed")
            directives = fm.get("directives", {})
            if not isinstance(directives, dict):
                fail("directives", "Directives must be a mapping")
                continue
            if directives.get("worktree_mode") not in {"spec-only", "read-write", "audit-only"}:
                fail("worktree-mode", "Invalid access scope")
            if directives.get("phase") not in {"design", "implementation", "verification"}:
                fail("phase", "Invalid phase")
            handoff = directives.get("handoff", {})
            if not isinstance(handoff, dict) or not handoff.get("upstream") or not handoff.get("downstream"):
                fail("handoff", "Incomplete declared handoff")
        except (OSError, UnicodeError, yaml.YAMLError, TypeError) as exc:
            fail("read-parse", str(exc))
    return {
        "check": "declarative",
        "status": "fail" if errors else "pass",
        "skills": len(files),
        "roles": roles,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--plugin-root", type=Path, action="append", default=[])
    parser.add_argument("--include-plugins", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root
    if root is None:
        root = next(
            (p for p in Path(__file__).absolute().parents if (p / "skill_catalog.generated.json").is_file()), None
        )
    if root is None:
        parser.error("Specify --root; no installed distribution was found")
    if args.include_plugins and not args.plugin_root:
        parser.error("Specify --plugin-root explicitly; no host-specific roots are assumed")
    results = [inspect(root), *[inspect(p) for p in args.plugin_root]]
    report = {
        "schema_version": 1,
        "check": "declarative",
        "status": "fail" if any(r["status"] == "fail" for r in results) else "pass",
        "results": results,
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text, end="")
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
