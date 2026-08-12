# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import os
import signal
import ast
from typing import Optional
import argparse


class AnergiaPurger(ast.NodeTransformer):
    def __init__(self) -> None:
        self.injected_kill = False

    def visit_Expr(self, node: ast.Expr) -> Optional[ast.AST]:
        if isinstance(node.value, ast.Constant):
            return None
        return self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> ast.AST:
        for i, handler in enumerate(node.handlers):
            if handler.type is None or (isinstance(handler.type, ast.Name) and handler.type.id == "Exception"):
                kill_node = ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(value=ast.Name(id="os", ctx=ast.Load()), attr="kill", ctx=ast.Load()),
                        args=[
                            ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id="os", ctx=ast.Load()), attr="getpid", ctx=ast.Load()
                                ),
                                args=[],
                                keywords=[],
                            ),
                            ast.Attribute(value=ast.Name(id="signal", ctx=ast.Load()), attr="SIGKILL", ctx=ast.Load()),
                        ],
                        keywords=[],
                    )
                )
                raise_node = ast.Raise(
                    exc=ast.Call(
                        func=ast.Name(id="RuntimeError", ctx=ast.Load()),
                        args=[ast.Constant(value="FAIL-FAST: General Exception intercepted.")],
                        keywords=[],
                    ),
                    cause=None,
                )
                node.handlers[i].body = [kill_node, raise_node]
                self.injected_kill = True
        return self.generic_visit(node)

    def _find_import_flags(self, body: list[ast.stmt]) -> tuple[int, bool, bool]:
        insert_idx = 0
        has_os = False
        has_signal = False
        for idx, child in enumerate(body):
            if isinstance(child, ast.ImportFrom) and child.module == "__future__":
                insert_idx = idx + 1
            if isinstance(child, ast.Import):
                names = [na.name for na in child.names]
                if "os" in names:
                    has_os = True
                if "signal" in names:
                    has_signal = True
        return insert_idx, has_os, has_signal

    def visit_Module(self, node: ast.Module) -> ast.Module:
        visited = self.generic_visit(node)
        assert isinstance(visited, ast.Module)
        if self.injected_kill:
            insert_idx, has_os, has_signal = self._find_import_flags(visited.body)
            if not has_signal:
                visited.body.insert(insert_idx, ast.Import(names=[ast.alias(name="signal", asname=None)]))
            if not has_os:
                visited.body.insert(insert_idx, ast.Import(names=[ast.alias(name="os", asname=None)]))
        return visited


def transmute_file(filepath: str) -> None:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        tree = ast.parse(content)
    purger = AnergiaPurger()
    mutated_tree = purger.visit(tree)
    ast.fix_missing_locations(mutated_tree)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(ast.unparse(mutated_tree))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BABYLON-60 Thermo AST Pruner")
    parser.add_argument("files", nargs="+", help="Files to prune")
    args = parser.parse_args()
    for f in args.files:
        try:
            transmute_file(f)
        except (OSError, SyntaxError, ValueError, AttributeError, TypeError):
            os.kill(os.getpid(), signal.SIGKILL)
            raise RuntimeError("FAIL-FAST: General Exception intercepted.")
    print(f"Successfully pruned {len(args.files)} files.")
