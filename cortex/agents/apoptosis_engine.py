#!/usr/bin/env python3
# C5-REAL: Motor de Apoptosis AST (v2.0)
# Poda determinista de código muerto (Dead Code Pruner)
import ast
import sys
import os
import argparse

BABYLON_SCRIPTS = "$CORTEX_ROOT/10_PROJECTS/babylon-60/scripts"
if BABYLON_SCRIPTS not in sys.path:
    sys.path.append(BABYLON_SCRIPTS)
from c5_guarded_action import boot_sequence, guarded_action  # type: ignore  # noqa: E402


class ApoptosisVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.defined: set[str] = set()
        self.used: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.defined.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.defined.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.defined.add(node.name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.attr)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        self.generic_visit(node)


def prune_file(filepath: str, dead_nodes: set[str], execute: bool) -> bool:
    if not dead_nodes:
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    tree = ast.parse(code)
    lines = code.splitlines(keepends=True)

    to_remove = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in dead_nodes:
                # Include decorators if present
                start_lineno = node.lineno
                if hasattr(node, "decorator_list") and node.decorator_list:
                    start_lineno = min(d.lineno for d in node.decorator_list)
                to_remove.append((start_lineno, node.end_lineno))

    if not to_remove:
        return False

    # Sort and remove from bottom to top to avoid offset shifting
    to_remove.sort(key=lambda x: x[0], reverse=True)

    if execute:
        for start, end in to_remove:
            if end is not None:
                del lines[start - 1 : end]
            else:
                del lines[start - 1 :]

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)

    return True


def run_apoptosis(target_dir: str, execute: bool) -> None:
    mode = "EXECUTE (MUTACIÓN ATÓMICA)" if execute else "DRY-RUN (SIMULACIÓN)"
    print(
        f"[*] Detonando Apoptosis Ontológica (AST-Pruner) en {target_dir} | Modo: {mode}"
    )

    total_files = 0
    pruned_files = 0

    global_used: set[str] = set()
    global_defined: set[str] = set()
    file_map: dict[str, tuple[set[str], ast.AST]] = {}

    for root, _, files in os.walk(target_dir):
        if ".venv" in root or "__pycache__" in root or ".git" in root:
            continue

        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                total_files += 1
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                    visitor = ApoptosisVisitor()
                    visitor.visit(tree)
                    global_used.update(visitor.used)
                    global_defined.update(visitor.defined)
                    file_map[filepath] = (visitor.defined, tree)
                except Exception as e:
                    print(f"[!] Error parseando {filepath}: {e}")

    # Only prune nodes that are NEVER used anywhere in the codebase
    dead_global = global_defined - global_used

    # Exclude standard magic methods, testing, main, AST visitors, etc.
    dead_global = {
        d
        for d in dead_global
        if not d.startswith("__")
        and d != "main"
        and not d.startswith("test_")
        and not d.startswith("visit_")
    }

    print(
        f"[*] Escaneo completado: {total_files} archivos. Nodos muertos globales identificados: {len(dead_global)}"
    )

    if not dead_global:
        print("[+] Red neuronal limpia. Cero anergía.")
        return

    if execute:
        compensators = {
            "APOPTOSIS_FILE_": lambda p: print(
                f"         [SAGA] Verificando purga idempotente para {p}"
            )
        }
        conn, key = boot_sequence(compensators)

    for filepath, (defined, _) in file_map.items():
        local_dead = defined.intersection(dead_global)
        if local_dead:
            if execute:

                def _effect():
                    if prune_file(filepath, local_dead, execute):
                        print(
                            f"[-] Purgado: {os.path.basename(filepath)} ({len(local_dead)} nodos: {', '.join(local_dead)})"
                        )

                action_name = f"APOPTOSIS_FILE_{filepath}"
                guarded_action(conn, key, action_name, _effect)
                pruned_files += 1
            else:
                if prune_file(filepath, local_dead, execute):
                    print(
                        f"[-] Simulado: {os.path.basename(filepath)} ({len(local_dead)} nodos: {', '.join(local_dead)})"
                    )
                pruned_files += 1

    if execute:
        print(f"[*] Apoptosis finalizada. Archivos mutados físicamente: {pruned_files}")
    else:
        print(
            f"[*] Simulación finalizada. Archivos infectados identificados: {pruned_files}. Usa --execute para purgar."
        )


def main():
    parser = argparse.ArgumentParser(description="C5-REAL Apoptosis Engine")
    parser.add_argument(
        "dir", nargs="?", default=".", help="Directorio objetivo a analizar"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Fuerza la mutación atómica en disco (Purga)",
    )

    args = parser.parse_args()
    run_apoptosis(args.dir, args.execute)


if __name__ == "__main__":
    main()
