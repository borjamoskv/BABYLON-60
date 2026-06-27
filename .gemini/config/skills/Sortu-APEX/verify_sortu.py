# C5-REAL
# SORTU-Ω v14.0.0
import hashlib
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent
REQUIRED_ARTIFACTS = ["SKILL.md", "schema.json", "verify_sortu.py"]
REQUIRED_FRONTMATTER_KEYS = {"name", "version", "description"}
MIN_VERSION = "14.0.0"


def verify_tripartite() -> tuple[bool, list[str]]:
    """Artifact verification."""
    errors: list[str] = []
    for artifact in REQUIRED_ARTIFACTS:
        path = SKILL_DIR / artifact
        if not path.exists():
            errors.append(f"MISSING: {artifact}")
    return len(errors) == 0, errors


def verify_frontmatter() -> tuple[bool, list[str]]:
    """SKILL.md frontmatter validation."""
    errors: list[str] = []
    skill_md = SKILL_DIR / "SKILL.md"
    if not skill_md.exists():
        return False, ["SKILL.md not found"]

    content = skill_md.read_text()
    if not content.startswith("---"):
        errors.append("SKILL.md missing YAML frontmatter delimiter")
        return False, errors

    parts = content.split("---", 2)
    if len(parts) < 3:
        errors.append("SKILL.md frontmatter not properly closed")
        return False, errors

    frontmatter = parts[1].strip()
    keys_found: set[str] = set()
    for line in frontmatter.split("\n"):
        if ":" in line:
            key = line.split(":")[0].strip()
            keys_found.add(key)

    missing = REQUIRED_FRONTMATTER_KEYS - keys_found
    if missing:
        errors.append(f"Missing frontmatter keys: {missing}")

    for line in frontmatter.split("\n"):
        if line.strip().startswith("version:"):
            version = line.split(":", 1)[1].strip().strip('"').strip("'")
            if version < MIN_VERSION:
                errors.append(f"Version {version} < minimum {MIN_VERSION}")

    return len(errors) == 0, errors


def verify_schema() -> tuple[bool, list[str]]:
    """schema.json validation."""
    errors: list[str] = []
    schema_path = SKILL_DIR / "schema.json"
    if not schema_path.exists():
        return False, ["schema.json not found"]

    try:
        schema = json.loads(schema_path.read_text())
    except json.JSONDecodeError as e:
        return False, [f"schema.json invalid JSON: {e}"]

    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("schema.json: $schema is not 2020-12")

    if "properties" not in schema:
        errors.append("schema.json: missing 'properties'")

    if "required" not in schema:
        errors.append("schema.json: missing 'required'")

    props = schema.get("properties", {})
    v14_fields = {
        "hours_saved", "complexity", "centuria_mode",
        "recombine_genes", "silicon_eval", "death_protocol",
    }
    missing_v14 = v14_fields - set(props.keys())
    if missing_v14:
        errors.append(f"schema.json missing v14 fields: {missing_v14}")

    return len(errors) == 0, errors


def verify_engine() -> tuple[bool, list[str]]:
    """scripts/sortu.py validation."""
    errors: list[str] = []
    engine_path = SKILL_DIR / "scripts" / "sortu.py"
    if not engine_path.exists():
        return False, ["scripts/sortu.py not found"]

    content = engine_path.read_text()

    required_classes = [
        "SortuForgeX1000",
        "VSAEngine",
        "LyapunovGovernor",
        "ForgeResult",
        "CenturiaSquad",
        "SortuSkill",
        "ASTBridge",
    ]

    for cls in required_classes:
        if f"class {cls}" not in content:
            errors.append(f"Engine missing class: {cls}")

    required_methods = [
        "async def forge",
        "def audit_yield",
        "def recombine",
        "_gate_0_audit",
        "_gate_1_lyapunov",
        "_gate_6_vsa_anchor",
        "_silicon_score",
    ]

    for method in required_methods:
        if method not in content:
            errors.append(f"Engine missing method: {method}")

    required_ast_methods = ["compile_ir_to_ast", "verify_ast_determinism"]
    for method in required_ast_methods:
        if method not in content:
            errors.append(f"Engine ASTBridge missing method: {method}")

    return len(errors) == 0, errors


def verify_death_protocol() -> tuple[bool, list[str]]:
    """scripts/death_protocol.py validation."""
    errors: list[str] = []
    dp_path = SKILL_DIR / "scripts" / "death_protocol.py"
    if not dp_path.exists():
        return False, ["scripts/death_protocol.py not found"]

    content = dp_path.read_text()

    required = ["DeathProtocol", "DeathTrigger", "DeathCertificate"]
    for cls in required:
        if f"class {cls}" not in content:
            errors.append(f"Death Protocol missing class: {cls}")

    return len(errors) == 0, errors


def verify_registry() -> tuple[bool, list[str]]:
    """registry.yaml validation."""
    errors: list[str] = []
    reg_path = SKILL_DIR / "registry.yaml"
    if not reg_path.exists():
        return False, ["registry.yaml not found"]

    content = reg_path.read_text()
    required_keys = ["version:", "compilation_mode:", "max_active_skills:", "active_skills:"]
    for key in required_keys:
        if key not in content:
            errors.append(f"registry.yaml missing key: {key}")

    return len(errors) == 0, errors


def compute_package_hash() -> str:
    """SHA-256 computation."""
    h = hashlib.sha256()
    for artifact in sorted(REQUIRED_ARTIFACTS):
        path = SKILL_DIR / artifact
        if path.exists():
            h.update(path.read_bytes())
    return h.hexdigest()


def run_verification() -> dict:
    """Verification execution."""
    results: dict = {
        "skill": "Sortu-APEX",
        "version": "14.0.0",
        "checks": {},
        "package_hash": "",
        "verdict": "PASS",
    }

    checks = [
        ("tripartite", verify_tripartite),
        ("frontmatter", verify_frontmatter),
        ("schema", verify_schema),
        ("engine", verify_engine),
        ("death_protocol", verify_death_protocol),
        ("registry", verify_registry),
    ]

    all_passed = True
    for name, check_fn in checks:
        passed, errors = check_fn()
        results["checks"][name] = {
            "passed": passed,
            "errors": errors,
        }
        if not passed:
            all_passed = False

    results["package_hash"] = compute_package_hash()
    results["verdict"] = "PASS" if all_passed else "FAIL"
    return results


if __name__ == "__main__":
    result = run_verification()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["verdict"] == "PASS" else 1)
