#!/usr/bin/env python3
"""
Apoptosis Engine - BABYLON-60 (C5-REAL)
Elimina quirúrgicamente código muerto no alcanzado en el grafo de dependencias de babylon60/extensions.
"""

import ast
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXT_ROOT = REPO_ROOT / "packages" / "babylon60" / "extensions"

# Módulos semilla identificados como consumidores externos
SEED_MODULES = [
    "daemon/sync_engine.py",
    "ha/raft.py",
    "skills/registry.py",
    "skills/router.py",
    "swarm/verification_gate.py",
    "sync/common.py"
]

def calculate_transitive_closure():
    visited = set()
    to_visit = list(SEED_MODULES)

    while to_visit:
        rel = to_visit.pop(0)
        if rel in visited:
            continue
        visited.add(rel)
        filepath = EXT_ROOT / rel
        if not filepath.exists():
            continue
        try:
            tree = ast.parse(filepath.read_text(encoding="utf-8", errors="ignore"))
            for node in ast.walk(tree):
                mod = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        mod = alias.name
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module
                if mod and "babylon60.extensions" in mod:
                    sub = mod.replace("babylon60.extensions.", "").replace(".", "/") + ".py"
                    if (EXT_ROOT / sub).exists() and sub not in visited:
                        to_visit.append(sub)
        except Exception as e:
            print(f"Error parseando {rel}: {e}")

    return visited

def run_apoptosis(dry_run=False):
    if not EXT_ROOT.exists():
        print(f"ERROR: No se encontró la ruta {EXT_ROOT}")
        sys.exit(1)

    all_files = set(str(p.relative_to(EXT_ROOT)) for p in EXT_ROOT.rglob("*.py"))
    keep_files = calculate_transitive_closure()
    to_delete = all_files - keep_files

    print("=== APOPTOSIS ENGINE: BABYLON-60 EXTENSIONS ===")
    print(f"Ruta: {EXT_ROOT}")
    print(f"Total de archivos .py: {len(all_files)}")
    print(f"Archivos necesarios (Invariantes conservadas): {len(keep_files)}")
    for k in sorted(keep_files):
        print(f"  [CONSERVAR] {k}")

    print(f"\nArchivos a purgar (Código Muerto / Anergía): {len(to_delete)}")

    if dry_run:
        print("\n[DRY RUN] Ningún archivo ha sido modificado.")
        return len(to_delete)

    deleted_count = 0
    for rel_path in sorted(to_delete):
        target = EXT_ROOT / rel_path
        if target.exists():
            target.unlink()
            deleted_count += 1

    # Limpiar directorios vacíos
    for p in sorted(EXT_ROOT.rglob("*"), key=lambda x: len(x.parts), reverse=True):
        if p.is_dir() and not any(p.iterdir()):
            p.rmdir()

    print(f"\n✅ APOPTOSIS COMPLETADA: {deleted_count} archivos eliminados exitosamente.")
    return deleted_count

if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    run_apoptosis(dry_run=is_dry)
