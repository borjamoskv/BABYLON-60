import ast
from typing import Any


class AntipatternVisitor(ast.NodeVisitor):
    def __init__(self, filename: str, source_lines: list[str] = None):
        self.filename: str = filename
        self.source_lines: list[str] = source_lines or []
        self.violations: list[dict[str, Any]] = []
        self.in_async_func: bool = False
        self._current_func: str | None = None
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.in_async_func = True
        self._current_func = node.name
        self.generic_visit(node)
        self.in_async_func = False
        self._current_func = None
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.in_async_func = False
        self._current_func = node.name
        self.generic_visit(node)
        self._current_func = None

    def visit_Call(self, node: ast.Call):
        # Detect bare print()
        if isinstance(node.func, ast.Name) and node.func.id == 'print':
            line_text = self.source_lines[node.lineno - 1] if self.source_lines and node.lineno <= len(self.source_lines) else ""
            if "# noqa" not in line_text:
                self.violations.append({
                    "type": "BARE_PRINT",
                    "line": node.lineno,
                    "col": node.col_offset,
                    "msg": "Bare print() detectado. Usar logging.getLogger(__name__)."
                })
            
        # Detect time.sleep() inside async def
        if self.in_async_func:
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == 'time' and node.func.attr == 'sleep':
                    self.violations.append({
                        "type": "ASYNC_TIME_SLEEP",
                        "line": node.lineno,
                        "col": node.col_offset,
                        "msg": "time.sleep() bloqueante dentro de async def. Usar asyncio.sleep()."
                    })
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        # Check for noqa
        line_text = self.source_lines[node.lineno - 1] if self.source_lines and node.lineno <= len(self.source_lines) else ""
        if "# noqa: BLE001" in line_text or "# noqa" in line_text:
            self.generic_visit(node)
            return

        # Detect bare except Exception:
        # Si type es Name y el id es 'Exception', es capturar todo genéricamente
        if node.type is not None and isinstance(node.type, ast.Name) and node.type.id == 'Exception':
            self.violations.append({
                "type": "BARE_EXCEPTION",
                "line": node.lineno,
                "col": node.col_offset,
                "msg": "except Exception: genérico (Falla K1). Acotar excepción o delegar a Git Sentinel."
            })
        elif node.type is None:
            # except desnudo
            self.violations.append({
                "type": "NAKED_EXCEPT",
                "line": node.lineno,
                "col": node.col_offset,
                "msg": "except: desnudo. Entropía estocástica inaceptable."
            })
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):
        # Detect text[:N] physical slicing on AST/JSON context?
        # Very hard to statically type check "is this structured data" without runtime.
        # For now, we flag broad slicing as a warning if it looks like arbitrary truncation.
        # We will keep this basic.
        self.generic_visit(node)


def audit_file(filepath: str) -> list[dict[str, Any]]:
    """Transduce the file into AST and extracts antipattern violations."""
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
    except Exception as e:  # noqa: BLE001
        return [{"type": "IO_ERROR", "line": 0, "col": 0, "msg": str(e)}]
        
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as e:
        return [{"type": "SYNTAX_ERROR", "line": e.lineno, "col": e.offset, "msg": "Error de sintaxis, no se puede parsear AST."}]
        
    visitor = AntipatternVisitor(filepath, source.split('\n'))
    visitor.visit(tree)
    return visitor.violations
