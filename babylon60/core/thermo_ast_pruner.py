import argparse
import ast


class AnergiaPurger(ast.NodeTransformer):
    def __init__(self) -> None:
        self.injected_kill = False

    def visit_Expr(self, node: ast.Expr) -> ast.AST | None:
        if isinstance(node.value, ast.Constant):
            return None
        return self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> ast.AST:
        for i, handler in enumerate(node.handlers):
            if handler.type is None or (isinstance(handler.type, ast.Name) and handler.type.id == "Exception"):
                raise_node = ast.Raise(
                    exc=ast.Call(
                        func=ast.Name(id="RuntimeError", ctx=ast.Load()),
                        args=[ast.Constant(value="FAIL-FAST: General Exception intercepted.")],
                        keywords=[],
                    ),
                    cause=None,
                )
                node.handlers[i].body = [raise_node]
        return self.generic_visit(node)

    def visit_Module(self, node: ast.Module) -> ast.Module:
        visited = self.generic_visit(node)
        assert isinstance(visited, ast.Module)
        return visited


def transmute_file(filepath: str) -> None:
    with open(filepath, encoding="utf-8") as f:
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
        except (OSError, SyntaxError, ValueError, AttributeError, TypeError) as e:
            raise RuntimeError("FAIL-FAST: General Exception intercepted.") from e
    print(f"Successfully pruned {len(args.files)} files.")
