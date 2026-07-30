# [C5-REAL] Exergy-Maximized
"""
cat_id: "validate-taxonomy"
cat_type: "script"
version: "1.0.0"
reality_level: "C5-REAL"
owner: "borjamoskv"
exergy_tier: "P2"
"""

import logging
import re
import sys
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def _validate_cat_fields(data: dict, expected_types: list[str]) -> tuple[bool, str]:
    required_keys = ["cat_id", "cat_type", "version", "reality_level", "owner", "exergy_tier"]
    for key in required_keys:
        if key not in data:
            return False, f"Missing required metadata field: {key}"
    if data.get("cat_type") not in expected_types:
        return False, f"Incorrect cat_type: expected one of {expected_types}, got '{data.get('cat_type')}'"
    return True, "Valid"


def check_yaml_agent(path: Path) -> tuple[bool, str]:
    """Verify if a YAML agent definition contains valid CAT-60 metadata."""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or not isinstance(data, dict):
            return False, "Invalid YAML structure (not a dictionary)"
        metadata = data.get("metadata")
        if not metadata or not isinstance(metadata, dict):
            return False, "Missing or invalid 'metadata' root key"
        return _validate_cat_fields(metadata, ["agent"])
    except Exception as e:  # noqa: BLE001
        return False, f"Error parsing: {e}"


def check_markdown_workflow(path: Path) -> tuple[bool, str]:
    """Verify if a markdown workflow contains valid CAT-60 frontmatter."""
    try:
        content = path.read_text(encoding="utf-8")
        pattern = re.compile(r"^(?:<!--.*?-->\s*)?---(.*?)---", re.DOTALL)
        match = pattern.match(content)
        if not match:
            return False, "Missing frontmatter delimiter"
        data = yaml.safe_load(match.group(1))
        if not isinstance(data, dict):
            return False, "Frontmatter is not a dictionary"
        return _validate_cat_fields(data, ["workflow", "policy", "skill"])
    except Exception as e:  # noqa: BLE001
        return False, f"Error parsing: {e}"


def _extract_docstring_yaml(content: str) -> dict | None:
    pattern = re.compile(r'^(?:#[^\n]*\n)*\s*"""(.*?)"""', re.DOTALL)
    match = pattern.match(content)
    if not match:
        return None
    meta_lines = []
    for line in match.group(1).strip().splitlines():
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            break
        meta_lines.append(line)
    return yaml.safe_load("\n".join(meta_lines)) if meta_lines else None


def check_python_script(path: Path) -> tuple[bool, str]:
    """Verify if a Python script contains valid CAT-60 docstring metadata."""
    try:
        content = path.read_text(encoding="utf-8")
        data = _extract_docstring_yaml(content)
        if not isinstance(data, dict):
            return False, "Docstring metadata is not a valid YAML dictionary"
        return _validate_cat_fields(data, ["script"])
    except Exception as e:  # noqa: BLE001
        return False, f"Error parsing: {e}"


def _audit_agents_directory(agents_dir: Path, workspace_root: Path) -> bool:
    if not agents_dir.exists():
        return True
    failed = False
    logger.info("\nScanning Agents in: %s", agents_dir.relative_to(workspace_root))
    for file in sorted(agents_dir.glob("*.yaml")):
        ok, reason = check_yaml_agent(file)
        status_char = "🟢" if ok else "🔴"
        logger.info("  %s %s -> %s", status_char, file.name, reason)
        if not ok:
            failed = True
    return not failed


def _audit_workflows_directories(workflows_dirs: list[Path], workspace_root: Path) -> bool:
    failed = False
    for w_dir in workflows_dirs:
        if not w_dir.exists():
            continue
        logger.info("\nScanning Workflows in: %s", w_dir.relative_to(workspace_root))
        for file in sorted(w_dir.glob("*.md")):
            ok, reason = check_markdown_workflow(file)
            status_char = "🟢" if ok else "🔴"
            logger.info("  %s %s -> %s", status_char, file.name, reason)
            if not ok:
                failed = True
    return not failed


def _audit_scripts_directories(scripts_dirs: list[Path], workspace_root: Path) -> bool:
    failed = False
    for s_dir in scripts_dirs:
        if not s_dir.exists():
            continue
        logger.info("\nScanning Scripts in: %s", s_dir.relative_to(workspace_root))
        for file in sorted(s_dir.glob("*.py")):
            ok, reason = check_python_script(file)
            status_char = "🟢" if ok else "🔴"
            logger.info("  %s %s -> %s", status_char, file.name, reason)
            if not ok and s_dir.name == "tools":
                failed = True
    return not failed


def main() -> int:
    workspace_root = Path(__file__).parent.parent.resolve()

    agents_dir = workspace_root / "babylon60" / "extensions" / "agents" / "definitions"
    workflows_dirs = [
        workspace_root / ".agents" / "workflows",
        workspace_root / ".agent" / "workflows",
    ]
    scripts_dirs = [workspace_root / "tools", workspace_root / "scripts"]

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("=== CAT-60 TAXONOMY AUDIT ===")

    ok_agents = _audit_agents_directory(agents_dir, workspace_root)
    ok_workflows = _audit_workflows_directories(workflows_dirs, workspace_root)
    ok_scripts = _audit_scripts_directories(scripts_dirs, workspace_root)

    if not (ok_agents and ok_workflows and ok_scripts):
        logger.info("\n❌ TAXONOMY VERIFICATION FAILED: Incompliant critical assets detected.")
        return 1

    logger.info("\n🟢 TAXONOMY VERIFICATION PASSED: Scanned assets check completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
