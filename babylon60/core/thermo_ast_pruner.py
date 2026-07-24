import argparse
import ast
from typing import Optional


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

    def visit_Module(self, node: ast.Module) -> ast.Module:
        visited = self.generic_visit(node)
        assert isinstance(visited, ast.Module)
        if self.injected_kill:
            import_os = ast.Import(names=[ast.alias(name="os", asname=None)])
            import_signal = ast.Import(names=[ast.alias(name="signal", asname=None)])
            insert_idx = 0
            has_os = False
            has_signal = False
            for idx, child in enumerate(visited.body):
                if isinstance(child, ast.ImportFrom) and child.module == "__future__":
                    insert_idx = idx + 1
                if isinstance(child, ast.Import):
                    for name_alias in child.names:
                        if name_alias.name == "os":
                            has_os = True
                        if name_alias.name == "signal":
                            has_signal = True
            if not has_signal:
                visited.body.insert(insert_idx, import_signal)
            if not has_os:
                visited.body.insert(insert_idx, import_os)
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
            raise RuntimeError("FAIL-FAST: General Exception intercepted.")
    print(f"Successfully pruned {len(args.files)} files.")
