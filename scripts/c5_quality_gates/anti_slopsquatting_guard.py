#!/usr/bin/env python3
"""
anti_slopsquatting_guard.py
=============================================================================
BABYLON-60 / C5-REAL — Anti-Slopsquatting & Ghost Import Pre-Commit Gate
Scans staged Python files for suspicious slopsquatting packages, typosquats,
and unverified external dependencies before allowing causal commit mutation.
=============================================================================
"""

import sys
import subprocess
import ast
from pathlib import Path

# Known slopsquatting / typosquatting targets and hallucinations
BANNED_IMPORTS = frozenset(
    {
        "cryptography_v2",
        "flask_json",
        "reqeusts",
        "requsets",
        "urllib4",
        "pytesseract_ocr",
        "torch_cuda",
        "langchain_core_v2",
    }
)


def get_staged_python_files() -> list[Path]:
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True,
        )
        files = []
        for line in res.stdout.strip().splitlines():
            line = line.strip()
            if line.endswith(".py") and Path(line).exists():
                files.append(Path(line))
        return files
    except Exception as e:
        print(f"[ANTI-SLOP] Warning: unable to retrieve staged files: {e}", file=sys.stderr)
        return []


def audit_file(file_path: Path) -> list[str]:
    violations = []
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    if root_mod in BANNED_IMPORTS:
                        violations.append(f"{file_path}:{node.lineno}: Banned/slopsquatting import '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    if root_mod in BANNED_IMPORTS:
                        violations.append(
                            f"{file_path}:{node.lineno}: Banned/slopsquatting import from '{node.module}'"
                        )
    except SyntaxError as e:
        violations.append(f"{file_path}:{e.lineno}: AST SyntaxError: {e.msg}")
    except Exception as e:
        violations.append(f"{file_path}: Error parsing: {e}")
    return violations


def get_all_python_files() -> list[Path]:
    repo_root = Path(__file__).resolve().parent.parent.parent
    targets = ["01_KISH_ENGINE", "02_EDIN_SWARMS", "scripts", "tests"]
    files = []
    for t in targets:
        dir_path = repo_root / t
        if dir_path.exists():
            for p in dir_path.rglob("*.py"):
                if not any(part.startswith(".") for part in p.parts):
                    files.append(p)
    return sorted(files)


def audit_zombie_core_dependencies(repo_root: Path, all_files: list[Path]) -> list[str]:
    import tomllib
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        return []
    try:
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
    except Exception as e:
        return [f"pyproject.toml parse error: {e}"]

    deps = pyproject.get("project", {}).get("dependencies", [])
    if not deps:
        return []

    pkg_to_import = {
        "pynacl": "nacl",
        "pyyaml": "yaml",
        "python_dotenv": "dotenv",
        "z3_solver": "z3",
    }
    hardware_peripheral_deps = {"pynput"}

    imported_modules = set()
    for f in all_files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_modules.add(alias.name.split(".")[0].lower())
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_modules.add(node.module.split(".")[0].lower())
        except Exception:
            pass

    violations = []
    for dep in deps:
        raw_name = dep.split(">=")[0].split("==")[0].split("<")[0].split("~=")[0].split(";")[0].strip().replace("-", "_").lower()
        import_name = pkg_to_import.get(raw_name, raw_name)
        if import_name in hardware_peripheral_deps:
            continue
        if import_name not in imported_modules:
            violations.append(f"pyproject.toml: Zombie core dependency '{dep}' (zero imports for '{import_name}')")
    return violations


def main() -> int:
    audit_all = "--all" in sys.argv
    repo_root = Path(__file__).resolve().parent.parent.parent
    if audit_all:
        files = get_all_python_files()
        label = "repository"
    else:
        files = get_staged_python_files()
        label = "staged"

    if not files:
        print(f"✓ [ANTI-SLOP] No {label} Python files to audit.")
        return 0

    all_violations = []
    for f in files:
        violations = audit_file(f)
        all_violations.extend(violations)

    if audit_all:
        zombie_violations = audit_zombie_core_dependencies(repo_root, files)
        all_violations.extend(zombie_violations)

    if all_violations:
        print(f"❌ [ANTI-SLOP] Violations detected in {label} files:", file=sys.stderr)
        for v in all_violations:
            print(f"   {v}", file=sys.stderr)
        return 1

    print(f"✓ [ANTI-SLOP] Audited {len(files)} {label} Python file(s). Zero slopsquatting/zombie violations detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
