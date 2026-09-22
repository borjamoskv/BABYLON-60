#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.3 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
anti_slopsquatting_guard.py - Zero-Trust Anti-Slopsquatting & Ghost Import Pre-Commit Gate
Falsa empíricamente el grafo de imports contra la realidad física:
1. Python Standard Library (sys.stdlib_module_names)
2. Territorio Local (01_KISH_ENGINE, 02_EDIN_SWARMS, scripts, tools, crates) con resolución de rutas punteadas
3. Manifiesto Declarado (pyproject.toml + dependencias opcionales + alias canónicos)
4. Oráculo de Slopsquatting (Detección de trampas de secuestro y paquetes alucinados por LLMs)
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ROOT_PYPROJECT = REPO_ROOT / "pyproject.toml"

EXCLUDE_DIRS = {
    ".git",
    "target",
    ".lake",
    ".jj",
    ".hypothesis",
    ".audit",
    "site",
    "assets",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "scratch",
    "artifact_bundle_v3",
    "dist",
}

# Slopsquat Traps: Módulos inventados por modelos de lenguaje en revisiones previas
SLOPSQUAT_TRAPS = {
    "cortex_mamba_block",
    "cortex_mamba_network",
    "cortex_inference",
    "core_graph_ledger",
    "exergy_optimizer_agent",
    "net_mamba_ledger_engine",
    "io_persist_ledger",
    "ouroboros_prune",
    "ouroboros_absorb_runner",
    "cancer_isomorphism_pipeline",
    "premium_features",
    "license_manager",
}

# Crates Rust y extensiones binarias locales de BABYLON-60
LOCAL_COMPILED_CRATES = {
    "strike_rs",
    "strike-rs",
}

# Plataformas de hardware embebido permitidas bajo guardas try/except
OPTIONAL_HARDWARE_PLATFORMS = {
    "machine",
    "micropython",
}

# Alias canónicos: Mapeo de nombre de import a paquete PyPI declarado
CANONICAL_ALIASES: Dict[str, str] = {
    "yaml": "pyyaml",
    "dotenv": "python-dotenv",
    "nacl": "pynacl",
    "z3": "z3-solver",
    "google": "google-genai",
    "fastmcp": "fastmcp",
    "lingua": "lingua-language-detector",
    "whisper": "faster-whisper",
    "sounddevice": "sounddevice",
    "PIL": "pillow",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "dateutil": "python-dateutil",
    "jwt": "pyjwt",
    "bs4": "beautifulsoup4",
    "typing_extensions": "typing-extensions",
    "serial": "pyserial",
    "pydub": "pydub",
    "TTS": "coqui-tts",
    "capstone": "capstone",
    "web3": "web3",
    "ollama": "ollama",
    "textual": "textual",
    "pynput": "pynput",
    "openai": "openai",
    "gtts": "gtts",
    "matplotlib": "matplotlib",
    "psutil": "psutil",
    "nest_asyncio": "nest-asyncio",
    "tinygrad": "tinygrad",
    "torch": "torch",
    "scipy": "scipy",
    "pandas": "pandas",
    "numpy": "numpy",
    "fastapi": "fastapi",
    "networkx": "networkx",
    "cbor2": "cbor2",
    "aiosqlite": "aiosqlite",
    "cryptography": "cryptography",
    "pydantic": "pydantic",
    "httpx": "httpx",
    "pytest": "pytest",
    "hypothesis": "hypothesis",
    "ruff": "ruff",
    "mypy": "mypy",
    "jinja2": "jinja2",
    "urllib3": "urllib3",
    "uvicorn": "uvicorn",
    "starlette": "starlette",
    "click": "click",
    "mcp": "mcp",
    "rich": "rich",
    "keyring": "keyring",
    "websockets": "websockets",
    "strike_rs": "strike-rs",
    "tomli": "tomli",
}


def load_all_declared_dependencies() -> Set[str]:
    """Carga todas las dependencias declaradas en pyproject.toml del repo y subproyectos."""
    declared = set()
    pyproject_files = [ROOT_PYPROJECT]
    # Buscar pyproject.toml en subproyectos / experimentos
    for exp_pyp in (REPO_ROOT / "experiments").glob("*/pyproject.toml"):
        pyproject_files.append(exp_pyp)

    for pyp in pyproject_files:
        if not pyp.exists():
            continue
        try:
            with open(pyp, "rb") as f:
                data = tomllib.load(f)
            # Main dependencies
            for d in data.get("project", {}).get("dependencies", []):
                pkg_name = re.split(r"[><=~^;]", d)[0].strip().lower().replace("_", "-")
                declared.add(pkg_name)
            # Optional dependencies
            for group in data.get("project", {}).get("optional-dependencies", {}).values():
                for d in group:
                    pkg_name = re.split(r"[><=~^;]", d)[0].strip().lower().replace("_", "-")
                    declared.add(pkg_name)
        except Exception as e:
            print(f"[!] Error leyendo {pyp}: {e}", file=sys.stderr)

    return declared


def resolve_local_dotted_path(module_path: str, file_dir: Path) -> bool:
    """
    Comprueba si una ruta punteada (ej. 'babylon60.cli.onco_transducer')
    existe físicamente en el territorio local.
    """
    parts = module_path.split(".")
    first = parts[0]

    # 1. Comprobar relativo al propio directorio del archivo importador
    rel_file = file_dir.joinpath(*parts).with_suffix(".py")
    rel_dir = file_dir.joinpath(*parts)
    if rel_file.exists() or (rel_dir.exists() and (rel_dir / "__init__.py").exists()):
        return True

    # 2. Si el módulo es babylon60.*
    if first == "babylon60":
        kish_pkg = REPO_ROOT / "01_KISH_ENGINE" / "babylon60"
        if len(parts) == 1:
            return kish_pkg.exists()
        subparts = parts[1:]
        target_file = kish_pkg.joinpath(*subparts).with_suffix(".py")
        target_dir = kish_pkg.joinpath(*subparts)
        if target_file.exists():
            return True
        if target_dir.exists() and (target_dir / "__init__.py").exists():
            return True
        return False

    # 3. Paquetes en 02_EDIN_SWARMS (ej. agents_archi)
    edin_pkg = REPO_ROOT / "02_EDIN_SWARMS" / first
    if edin_pkg.exists():
        subparts = parts[1:]
        if not subparts:
            return True
        target_file = edin_pkg.joinpath(*subparts).with_suffix(".py")
        target_dir = edin_pkg.joinpath(*subparts)
        if target_file.exists():
            return True
        if target_dir.exists() and (target_dir / "__init__.py").exists():
            return True

    # 4. Si el archivo vive dentro de experiments/<name>/, resolver contra experiments/<name>/src/
    for exp_dir in (REPO_ROOT / "experiments").iterdir():
        if exp_dir.is_dir() and exp_dir in file_dir.parents:
            exp_src = exp_dir / "src"
            if exp_src.exists():
                target_file = exp_src.joinpath(*parts).with_suffix(".py")
                target_dir = exp_src.joinpath(*parts)
                if target_file.exists():
                    return True
                if target_dir.exists() and (target_dir / "__init__.py").exists():
                    return True

    # 5. Si el módulo cuelga de scripts.* o tools.* o experiments.*
    for base in ["scripts", "tools", "experiments", "crates", "src", "01_KISH_ENGINE", "02_EDIN_SWARMS", "00_ABZU_KERNEL"]:
        base_dir = REPO_ROOT / base
        if first == base:
            subparts = parts[1:]
            if not subparts:
                return base_dir.exists()
            t_file = base_dir.joinpath(*subparts).with_suffix(".py")
            t_dir = base_dir.joinpath(*subparts)
            if t_file.exists() or (t_dir.exists() and (t_dir / "__init__.py").exists()):
                return True

    # 6. Si first es un subdirectorio directo de scripts/ (ej. c5_verifiers)
    scripts_dir = REPO_ROOT / "scripts"
    if (scripts_dir / first).is_dir():
        subparts = parts[1:]
        if not subparts:
            return True
        sf = (scripts_dir / first).joinpath(*subparts).with_suffix(".py")
        sd = (scripts_dir / first).joinpath(*subparts)
        if sf.exists() or (sd.exists() and (sd / "__init__.py").exists()):
            return True

    # 7. Comprobar si es un archivo directo o paquete en la raíz del repositorio
    root_file = REPO_ROOT.joinpath(*parts).with_suffix(".py")
    root_dir = REPO_ROOT.joinpath(*parts)
    if root_file.exists() or (root_dir.exists() and (root_dir / "__init__.py").exists()):
        return True

    # 8. Comprobar si es un script local en cualquier subcarpeta de scripts/
    if scripts_dir.exists():
        for sub in scripts_dir.iterdir():
            if sub.is_dir() and not sub.name.startswith("."):
                sf = sub.joinpath(*parts).with_suffix(".py")
                sd = sub.joinpath(*parts)
                if sf.exists() or (sd.exists() and (sd / "__init__.py").exists()):
                    return True

    return False


class ImportVisitor(ast.NodeVisitor):
    """Extrae imports identificando si están envueltos en bloques try-except."""

    def __init__(self) -> None:
        self.imports: List[Tuple[str, int, bool]] = []
        self._try_depth = 0

    def visit_Try(self, node: ast.Try) -> None:
        self._try_depth += 1
        self.generic_visit(node)
        self._try_depth -= 1

    def visit_Import(self, node: ast.Import) -> None:
        guarded = self._try_depth > 0
        for alias in node.names:
            self.imports.append((alias.name, node.lineno, guarded))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        guarded = self._try_depth > 0
        if node.level == 0 and node.module:
            self.imports.append((node.module, node.lineno, guarded))


def get_staged_python_files() -> List[Path]:
    """Obtiene los archivos Python en el área de staging de Git."""
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        if res.returncode == 0:
            lines = res.stdout.splitlines()
            return [REPO_ROOT / line for line in lines if line.endswith(".py") and (REPO_ROOT / line).exists()]
    except Exception:
        pass
    return []


def collect_python_files(staged_only: bool = False) -> List[Path]:
    """Recolecta los archivos a auditar."""
    if staged_only:
        return get_staged_python_files()

    py_files = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for f in files:
            if f.endswith(".py"):
                py_files.append(Path(root) / f)
    return py_files


def audit_anti_slopsquatting(staged_only: bool = False, json_output: bool = False) -> bool:
    """Ejecuta el cortafuegos anti-slopsquatting y devuelve True si todo es limpio."""
    stdlib = set(sys.stdlib_module_names)
    stdlib.update({"__future__", "_thread", "posix", "nt"})

    declared_deps = load_all_declared_dependencies()
    py_files = collect_python_files(staged_only=staged_only)

    violations: List[Dict[str, Any]] = []
    traps_found: List[Dict[str, Any]] = []

    for p in py_files:
        rel_path = str(p.relative_to(REPO_ROOT)) if p.is_relative_to(REPO_ROOT) else str(p)
        file_dir = p.parent

        try:
            content = p.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content, filename=str(p))
            visitor = ImportVisitor()
            visitor.visit(tree)
            imports = visitor.imports
        except SyntaxError:
            continue

        for mod_name, line_no, is_guarded in imports:
            top_level = mod_name.split(".")[0]

            # 1. Detección de trampa explícita de Slopsquatting (Zero Tolerance)
            if top_level in SLOPSQUAT_TRAPS or mod_name in SLOPSQUAT_TRAPS:
                traps_found.append({
                    "file": rel_path,
                    "line": line_no,
                    "module": mod_name,
                    "type": "TRAMPA_SLOPSQUAT",
                    "reason": f"Módulo alucinado/trampa de secuestro conocida: '{mod_name}'",
                })
                continue

            # 2. Oráculo 1: ¿Es librería estándar de Python?
            if top_level in stdlib:
                continue

            # 3. Módulos de hardware embebido permitidos bajo guarda try/except
            if is_guarded and top_level in OPTIONAL_HARDWARE_PLATFORMS:
                continue

            # 4. Crates binarios locales en C-ABI / PyO3 (ej. strike_rs)
            if top_level in LOCAL_COMPILED_CRATES:
                continue

            # 5. Oráculo 2: ¿Existe en el territorio local?
            if resolve_local_dotted_path(mod_name, file_dir):
                continue

            # Si el módulo es babylon60.* y no resolvió: es un Dotted-path Blindspot
            if top_level == "babylon60":
                violations.append({
                    "file": rel_path,
                    "line": line_no,
                    "module": mod_name,
                    "type": "FANTASMA_INTERNO",
                    "reason": f"El submódulo local '{mod_name}' no existe en 01_KISH_ENGINE/babylon60/.",
                })
                continue

            # 6. Oráculo 3: ¿Es una dependencia de terceros declarada en pyproject.toml?
            canonical_pkg = CANONICAL_ALIASES.get(top_level, top_level.lower().replace("_", "-"))
            if canonical_pkg in declared_deps or top_level in declared_deps:
                continue

            # Si no está en stdlib, no está en local y no está declarada en pyproject:
            violations.append({
                "file": rel_path,
                "line": line_no,
                "module": mod_name,
                "type": "DEPENDENCIA_NO_DECLARADA",
                "reason": f"Dependencia externa '{mod_name}' (paquete '{canonical_pkg}') no está declarada en pyproject.toml ni es local.",
            })

    total_issues = len(traps_found) + len(violations)
    passed = total_issues == 0

    if json_output:
        report = {
            "schema_version": "1.0",
            "type": "ANTI_SLOPSQUATTING_AUDIT",
            "passed": passed,
            "staged_only": staged_only,
            "total_files_scanned": len(py_files),
            "traps_count": len(traps_found),
            "violations_count": len(violations),
            "traps": traps_found,
            "violations": violations,
        }
        print(json.dumps(report, indent=2))
        return passed

    print("=================================================================")
    print(f" 🛡️  CORTAFUEGOS ANTI-SLOPSQUATTING C5-REAL (MODO: {'STAGED' if staged_only else 'FULL REPO'})")
    print("=================================================================")
    print(f"[*] Archivos Python escaneados: {len(py_files)}")
    print(f"[*] Dependencias declaradas en pyproject.toml: {len(declared_deps)}")

    if traps_found:
        print("\n🚨 \033[91m[CRÍTICO] TRAMPAS DE SLOPSQUATTING / MÓDULOS ALUCINADOS DETECTADOS:\033[0m")
        for t in traps_found:
            print(f"  ❌ {t['file']}:{t['line']} -> \033[93m{t['module']}\033[0m: {t['reason']}")

    if violations:
        print("\n❌ \033[91m[VIOLACIÓN] IMPORTACIONES FANTASMA O DEPENDENCIAS NO VERIFICADAS:\033[0m")
        for v in violations:
            print(f"  ❌ [{v['type']}] {v['file']}:{v['line']} -> \033[93m{v['module']}\033[0m: {v['reason']}")

    if passed:
        print("\n\033[92m[✓] CADENA DE SUMINISTRO VERIFICADA: CERO SLOPSQUATTING Y CERO IMPORTS FANTASMA.\033[0m")
        print("=================================================================\n")
    else:
        print("\n\033[91m[!] CORTAFUEGOS DISPARADO: Se rechaza la operación para prevenir inyección de dependencias.\033[0m")
        print("    Remediación: Declare la dependencia en pyproject.toml o elimine el import fantasma.")
        print("=================================================================\n")

    return passed


def main() -> None:
    parser = argparse.ArgumentParser(description="Cortafuegos Anti-Slopsquatting & Ghost Imports")
    parser.add_argument("--staged", action="store_true", help="Auditar exclusivamente archivos en staging de Git")
    parser.add_argument("--all", action="store_true", help="Auditar todo el repositorio")
    parser.add_argument("--json", action="store_true", help="Emitir reporte en JSON")
    args = parser.parse_args()

    success = audit_anti_slopsquatting(staged_only=args.staged, json_output=args.json)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
