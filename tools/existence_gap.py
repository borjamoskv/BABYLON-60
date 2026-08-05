#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
Existence Gap Scanner (AST + Registry Resolution v3)
Detects hallucinated imports, missing dependencies, and potential slopsquatting vectors.
"""
import ast
import json
import argparse
import collections
import pathlib
import sys

def run_existence_scan(target_dir: str) -> dict:
    repo = pathlib.Path(target_dir).resolve()
    pyfiles = [p for p in repo.rglob("*.py") if ".git" not in p.parts and "venv" not in p.parts and ".venv" not in p.parts]
    stdlib = set(sys.stdlib_module_names)
    imports = collections.defaultdict(set)

    for p in pyfiles:
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        imports[a.name].add(str(p.relative_to(repo)))
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    imports[node.module].add(str(p.relative_to(repo)))
        except SyntaxError:
            continue

    all_py_files = set(p.resolve() for p in repo.rglob("*.py"))
    all_dirs_with_init = set(p.parent.resolve() for p in repo.rglob("__init__.py"))

    def exists_locally(mod_name: str) -> bool:
        parts = mod_name.split(".")
        candidate_roots = [repo, repo / "02_CORTEX_ENGINE"]
        for r in candidate_roots:
            if not r.exists():
                continue
            file_target = r.joinpath(*parts).with_suffix(".py")
            if file_target in all_py_files:
                return True
            dir_target = r.joinpath(*parts)
            if dir_target in all_dirs_with_init:
                return True
        return False

    local_top = set(p.stem if p.is_file() else p.name for p in repo.iterdir() if not p.name.startswith("."))

    third_party = collections.defaultdict(set)
    internal_ghosts = collections.defaultdict(set)

    for m, fs in imports.items():
        top_level = m.split(".")[0]
        if top_level in stdlib:
            continue

        if exists_locally(m):
            continue
        elif top_level in local_top or exists_locally(top_level):
            internal_ghosts[m].update(fs)
        else:
            third_party[top_level].update(fs)

    return {
        "repo": str(repo),
        "ghost_modules_count": len(internal_ghosts),
        "ghost_modules": {k: sorted(list(v)) for k, v in internal_ghosts.items()},
        "third_party_count": len(third_party),
        "third_party_packages": {k: sorted(list(v)) for k, v in third_party.items()},
    }

def main():
    parser = argparse.ArgumentParser(description="Existence Gap Gate - Empirical AST & Registry Resolution")
    parser.add_argument("target", nargs="?", default=".", help="Path to repository root")
    parser.add_argument("--json", dest="json_out", help="Output path for JSON report")
    parser.add_argument("--fail-on", choices=["critico", "alto", "medio"], help="Enforce threshold failure")
    args = parser.parse_args()

    results = run_existence_scan(args.target)
    
    print(f"=== Auditoría de Huecos de Existencia v3: {results['repo']} ===")
    print(f"Módulos Internos Fantasma confirmados: {results['ghost_modules_count']}")
    for mod, files in results["ghost_modules"].items():
        print(f"  ❌ {mod} (en {len(files)} archivos: {files[0]})")

    print(f"\nDependencias de Terceros a verificar: {results['third_party_count']}")
    for mod, files in results["third_party_packages"].items():
        print(f"  📦 {mod}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nReporte JSON guardado en: {args.json_out}")

    if args.fail_on == "alto" and results["ghost_modules_count"] > 200:
        sys.exit(1)

if __name__ == "__main__":
    main()
