import ast
from typing import Any


def canonicalize_ast(node: Any) -> Any:
    if isinstance(node, ast.AST):
        result = {"_type": node.__class__.__name__}
        for field, value in ast.iter_fields(node):
            if field in ("lineno", "col_offset", "end_lineno", "end_col_offset", "ctx"):
                continue
            result[field] = canonicalize_ast(value)
        return result
    elif isinstance(node, list):
        return [canonicalize_ast(item) for item in node]
    elif isinstance(node, (str, int, float, bool, bytes, type(None))):
        return node
    else:
        return str(node)
