import ast
import unicodedata


class SecurityViolation(Exception):
    pass


class AntiHomoglyphVisitor(ast.NodeVisitor):
    def __init__(self):
        self.homoglyphs_found = []

    def check_name(self, name: str, node: ast.AST) -> None:
        for char in name:
            category = unicodedata.category(char)
            if ord(char) > 127 or category not in {"Ll", "Lu", "Nd", "Pc"}:
                self.homoglyphs_found.append((name, char, getattr(node, "lineno", 0)))

    def visit_Name(self, node: ast.Name) -> None:
        self.check_name(node.id, node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.check_name(node.name, node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.check_name(node.name, node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.check_name(node.name, node)
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        self.check_name(node.arg, node)
        self.generic_visit(node)


def cassandra_validate_identifiers(tree: ast.AST) -> None:
    visitor = AntiHomoglyphVisitor()
    visitor.visit(tree)
    if visitor.homoglyphs_found:
        raise SecurityViolation("HOMOGLYPH_ATTACK detected in AST identifiers")
