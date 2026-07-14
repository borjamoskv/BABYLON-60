import ast
from typing import Optional


class AnergiaPurger(ast.NodeTransformer):
    def __init__(self):
        self.injected_kill = False

    def visit_Expr(self, node: ast.Expr) -> Optional[ast.AST]:
        if isinstance(node.value, ast.Constant):
            return None
        return self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> ast.AST:
        for i, handler in enumerate(node.handlers):
            if handler.type is None or (
                isinstance(handler.type, ast.Name) and handler.type.id == "Exception"
            ):
                kill_node = ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="os", ctx=ast.Load()),
                            attr="kill",
                            ctx=ast.Load(),
                        ),
                        args=[
                            ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id="os", ctx=ast.Load()),
                                    attr="getpid",
                                    ctx=ast.Load(),
                                ),
                                args=[],
                                keywords=[],
                            ),
                            ast.Attribute(
                                value=ast.Name(id="signal", ctx=ast.Load()),
                                attr="SIGKILL",
                                ctx=ast.Load(),
                            ),
                        ],
                        keywords=[],
                    )
                )
                node.handlers[i].body = [kill_node]
                self.injected_kill = True
        return self.generic_visit(node)

    def visit_Module(self, node: ast.Module) -> ast.AST:
        node = self.generic_visit(node)  # type: ignore
        if self.injected_kill:
            import_os = ast.Import(names=[ast.alias(name="os", asname=None)])
            import_signal = ast.Import(names=[ast.alias(name="signal", asname=None)])
            node.body.insert(0, import_signal)
            node.body.insert(0, import_os)
        return node


def transmute_file(filepath: str) -> None:
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    purger = AnergiaPurger()
    mutated_tree = purger.visit(tree)
    ast.fix_missing_locations(mutated_tree)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(ast.unparse(mutated_tree))
