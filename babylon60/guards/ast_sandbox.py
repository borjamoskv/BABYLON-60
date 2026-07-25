"""
AST Sandbox Evasion Guard — MOSKV-1 APEX C5-REAL Security Core
Provides deterministic AST static analysis to prevent code injection, introspection exploits,
dunder attribute traversal, and unauthorized import statements within sandboxed execution contexts.
"""

import ast


class SecurityError(Exception):
    """Raised when source code violates sandboxed AST execution rules."""

    pass


PROHIBITED_FUNCTIONS: set[str] = {
    "getattr",
    "setattr",
    "delattr",
    "eval",
    "exec",
    "compile",
    "__import__",
    "open",
    "breakpoint",
    "globals",
    "locals",
    "vars",
    "dir",
    "input",
}


def validate_ast_sandbox(source_code: str) -> bool:
    """
    Parses and inspects the AST of `source_code`.
    Rejects any construct attempting introspective attribute access, dunder traversal,
    prohibited function calls, or module imports.

    Args:
        source_code: Python code string to validate.

    Returns:
        True if valid and compliant with sandbox rules.

    Raises:
        SecurityError: If an AST rule violation or syntax anomaly is detected.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        raise SecurityError(f"Syntax error (safe): {e}")

    for node in ast.walk(tree):
        # Rule 1: Prohibit dunder attribute access (e.g. .__class__, .__subclasses__)
        if isinstance(node, ast.Attribute):
            if isinstance(node.attr, str) and node.attr.startswith("__") and node.attr.endswith("__"):
                raise SecurityError(f"Acceso a atributo dunder prohibido: {node.attr}")

        # Rule 2: Prohibit introspection and code execution functions
        if isinstance(node, ast.Name):
            if node.id in PROHIBITED_FUNCTIONS:
                raise SecurityError(f"Llamada a función de introspección prohibida: {node.id}")

        # Rule 3: Prohibit imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise SecurityError("Importación no permitida en entorno sandboxed")

        # Rule 4: Prohibit dynamic string formatting tricks inside JoinedStr (f-strings) accessing dunders
        if isinstance(node, ast.FormattedValue):
            # Inspect internal AST of f-string expression
            for subnode in ast.walk(node.value):
                if isinstance(subnode, ast.Attribute) and isinstance(subnode.attr, str):
                    if subnode.attr.startswith("__") and subnode.attr.endswith("__"):
                        raise SecurityError(f"Acceso a atributo dunder en f-string prohibido: {subnode.attr}")

    return True
