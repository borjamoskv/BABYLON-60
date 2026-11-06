#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""Ring-2 SQLite Isolation Guard (INV_C5_RING2_NO_SQLITE).

Audits all Python code under `02_EDIN_SWARMS` to ensure no direct imports
of `sqlite3` or `aiosqlite` exist. Ring-2 is an untrusted/stochastic agent
layer and MUST NOT possess direct write or read capabilities to the SQLite
persistence substrate. All ledger mutations must flow through Ring-0 (Rust).
"""

import ast
import sys
from pathlib import Path
from typing import List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
EDIN_DIR = REPO_ROOT / "02_EDIN_SWARMS"

FORBIDDEN_MODULES = {"sqlite3", "aiosqlite"}


def _check_import_node(node: ast.Import) -> List[Tuple[int, str]]:
    violations = []
    for alias in node.names:
        root_pkg = alias.name.split(".")[0]
        if root_pkg in FORBIDDEN_MODULES:
            violations.append((node.lineno, f"import directo de '{alias.name}'"))
    return violations


def _check_import_from_node(node: ast.ImportFrom) -> List[Tuple[int, str]]:
    if not node.module:
        return []
    root_pkg = node.module.split(".")[0]
    if root_pkg in FORBIDDEN_MODULES:
        return [(node.lineno, f"from '{node.module}' import ...")]
    return []


def _extract_from_importfrom(node: ast.ImportFrom, aliases: set[str]) -> None:
    if node.module != "importlib":
        return
    for alias in node.names:
        if alias.name == "import_module":
            aliases.add(alias.asname or alias.name)


def _extract_from_import(node: ast.Import, aliases: set[str]) -> None:
    for alias in node.names:
        if alias.name in {"__import__", "import_module"}:
            aliases.add(alias.asname or alias.name)


def _extract_dynamic_aliases(tree: ast.AST) -> set[str]:
    aliases = {"__import__", "import_module"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            _extract_from_importfrom(node, aliases)
        elif isinstance(node, ast.Import):
            _extract_from_import(node, aliases)
    return aliases


def _check_call_node(node: ast.Call, dynamic_aliases: set[str]) -> List[Tuple[int, str]]:
    if not node.args or not isinstance(node.args[0], ast.Constant):
        return []
    mod_val = node.args[0].value
    if mod_val not in FORBIDDEN_MODULES:
        return []

    func = node.func
    if isinstance(func, ast.Name) and func.id in dynamic_aliases:
        return [(node.lineno, f"{func.id}('{mod_val}') dinámico detectado")]
    if isinstance(func, ast.Attribute) and func.attr in dynamic_aliases:
        return [(node.lineno, f"{func.attr}('{mod_val}') dinámico detectado")]
    return []


def _inspect_node(node: ast.AST, dynamic_aliases: set[str]) -> List[Tuple[int, str]]:
    if isinstance(node, ast.Import):
        return _check_import_node(node)
    if isinstance(node, ast.ImportFrom):
        return _check_import_from_node(node)
    if isinstance(node, ast.Call):
        return _check_call_node(node, dynamic_aliases)
    return []


def _parse_ast_safely(file_path: Path) -> Tuple[Optional[ast.AST], Optional[str]]:
    try:
        content = file_path.read_text(encoding="utf-8")
        return ast.parse(content, filename=str(file_path)), None
    except (SyntaxError, UnicodeDecodeError, OSError) as e:
        return None, f"Error al parsear AST: {e}"


def check_file_for_sqlite_imports(file_path: Path) -> List[Tuple[int, str]]:
    tree, err = _parse_ast_safely(file_path)
    if err or tree is None:
        return [(1, err or "AST is None")]

    dynamic_aliases = _extract_dynamic_aliases(tree)
    violations = []
    for node in ast.walk(tree):
        found = _inspect_node(node, dynamic_aliases)
        violations.extend(found)
    return violations


def _report_file_violations(py_file: Path, violations: List[Tuple[int, str]]) -> int:
    rel_path = py_file.relative_to(REPO_ROOT)
    for lineno, msg in violations:
        print(f"  🔴 [FRACTURA DE FRONTERA RING-2] {rel_path}:{lineno}: {msg}", file=sys.stderr)
    return len(violations)


def audit_ring2_isolation() -> bool:
    print("🛡️ Auditing Ring-2 SQLite Isolation Invariant (INV_C5_RING2_NO_SQLITE)...")
    if not EDIN_DIR.exists():
        print(f"  [?] Directorio {EDIN_DIR} no encontrado. Omitiendo.")
        return True

    py_files = sorted(list(EDIN_DIR.rglob("*.py")))
    total_violations = 0

    for py_file in py_files:
        violations = check_file_for_sqlite_imports(py_file)
        if violations:
            total_violations += _report_file_violations(py_file, violations)

    if total_violations > 0:
        print(f"\n❌ FALLO: Se detectaron {total_violations} violaciones de aislamiento en Ring-2.", file=sys.stderr)
        print("   02_EDIN_SWARMS tiene estrictamente prohibido mutar SQLite directamente.", file=sys.stderr)
        print("   El write-path del ledger pertenece exclusivamente a Ring-0 (Rust C-ABI).", file=sys.stderr)
        return False

    print(f"  🟢 Aislamiento verificado en {len(py_files)} archivos de Ring-2. 0 violaciones detectadas.")
    return True


if __name__ == "__main__":
    if not audit_ring2_isolation():
        sys.exit(1)
    sys.exit(0)
