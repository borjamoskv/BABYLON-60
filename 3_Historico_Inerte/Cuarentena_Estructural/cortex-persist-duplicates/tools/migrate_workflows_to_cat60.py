"""
cat_id: "migrate-workflows-to-cat60"
cat_type: "script"
version: "1.0.0"
reality_level: "C5-REAL"
owner: "borjamoskv"
exergy_tier: "P2"
"""

import logging
import re
from pathlib import Path

import yaml


def _parse_workflow_frontmatter(content: str) -> tuple[str, dict, str]:
    pattern = re.compile(r"^(<!--.*?-->\s*)?---(.*?)---(.*)$", re.DOTALL)
    match = pattern.match(content)
    if not match:
        return "", {}, content
    comment_part = match.group(1) or ""
    try:
        existing_yaml = yaml.safe_load(match.group(2)) or {}
    except Exception:  # noqa: BLE001
        existing_yaml = {}
    return comment_part, existing_yaml, match.group(3)


def _build_workflow_yaml(stem: str, existing_yaml: dict) -> str:
    cat_metadata = {
        "cat_id": existing_yaml.get("cat_id") or stem,
        "cat_type": existing_yaml.get("cat_type") or "workflow",
        "version": existing_yaml.get("version") or "1.0.0",
        "reality_level": existing_yaml.get("reality_level") or "C5-REAL",
        "owner": existing_yaml.get("owner") or "borjamoskv",
        "exergy_tier": existing_yaml.get("exergy_tier") or "P1",
    }
    for k, v in existing_yaml.items():
        if k not in cat_metadata:
            cat_metadata[k] = v
    return yaml.dump(cat_metadata, default_flow_style=False, sort_keys=False).strip()


def migrate_markdown_file(path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8")
        comment_part, existing_yaml, body_part = _parse_workflow_frontmatter(content)
        new_yaml_block = _build_workflow_yaml(path.stem, existing_yaml)
        new_content = f"{comment_part}---\n{new_yaml_block}\n---\n{body_part}"
        path.write_text(new_content, encoding="utf-8")
        return True
    except Exception as e:  # noqa: BLE001
        logging.getLogger(__name__).info("Error migrating %s: %s", path.name, e)
        return False


def main():
    workspace_root = Path(__file__).parent.parent.resolve()

    workflows_dirs = [
        workspace_root / ".agents" / "workflows",
        workspace_root / ".agent" / "workflows",
    ]

    migrated_count = 0
    for w_dir in workflows_dirs:
        if w_dir.exists():
            logging.getLogger(__name__).info(f"Migrating workflows in: {w_dir.relative_to(workspace_root)}")
            for file in w_dir.glob("*.md"):
                if migrate_markdown_file(file):
                    migrated_count += 1
                    logging.getLogger(__name__).info(f"  🟢 {file.name} -> Migrated")

    logging.getLogger(__name__).info(f"\nSuccessfully migrated {migrated_count} workflows to CAT-60 standard.")


if __name__ == "__main__":
    main()
