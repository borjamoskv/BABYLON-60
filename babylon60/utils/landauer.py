import ast
import os
from pathlib import Path
from typing import Any


class LandauerAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.complexity: int = 0
        self.stats: dict[str, int] = {"functions": 0, "classes": 0, "decisions": 0}
        self.node_metrics: list[dict[str, Any]] = []
        self._current_node_stack: list[dict[str, Any]] = []

    def _visit_node(self, node: ast.AST, key: str | None = None) -> None:
        if key:
            self.stats[key] += 1
        self.complexity += 1
        for item in self._current_node_stack:
            item["complexity"] = int(item["complexity"]) + 1
        self.generic_visit(node)

    def _push_node(self, node: ast.AST, node_type: str) -> None:
        node_info: dict[str, Any] = {
            "name": getattr(node, "name", "<anonymous>"),
            "type": node_type,
            "start_line": getattr(node, "lineno", 1),
            "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 1)),
            "complexity": 1,
        }
        self._current_node_stack.append(node_info)

    def _pop_node(self) -> None:
        if self._current_node_stack:
            self.node_metrics.append(self._current_node_stack.pop())

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._push_node(node, "function")
        self._visit_node(node, "functions")
        self._pop_node()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._push_node(node, "async_function")
        self._visit_node(node, "functions")
        self._pop_node()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._push_node(node, "class")
        self._visit_node(node, "classes")
        self._pop_node()

    def visit_If(self, node: ast.If) -> None:
        self._visit_node(node, "decisions")

    def visit_For(self, node: ast.For) -> None:
        self._visit_node(node, "decisions")

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._visit_node(node, "decisions")

    def visit_While(self, node: ast.While) -> None:
        self._visit_node(node, "decisions")

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self._visit_node(node, "decisions")

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        for _ in range(len(node.values) - 1):
            self._visit_node(node, "decisions")

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._visit_node(node, "functions")

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._visit_node(node, "decisions")

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._visit_node(node, "decisions")

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._visit_node(node, "decisions")

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._visit_node(node, "decisions")

    def visit_Try(self, node: ast.Try) -> None:
        self._visit_node(node)

    def visit_With(self, node: ast.With) -> None:
        self._visit_node(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self._visit_node(node)


def calculate_calcification(file_path: Path) -> dict[str, Any] | None:
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        analyzer = LandauerAnalyzer()
        analyzer.visit(tree)
        loc = len(content.splitlines())
        calcification_score = analyzer.complexity * loc / 100
        for node in analyzer.node_metrics:
            node_loc = int(node["end_line"]) - int(node["start_line"]) + 1
            node["score"] = round(int(node["complexity"]) * node_loc / 10, 2)
            node["is_parasite"] = float(node["score"]) > 30
        return {
            "file": str(file_path.name),
            "loc": loc,
            "complexity": analyzer.complexity,
            "score": round(calcification_score, 2),
            "is_parasite": calcification_score > 50,
            "nodes": sorted(analyzer.node_metrics, key=lambda x: float(x["score"]), reverse=True),
        }
    except (OSError, SyntaxError):
        return None


def audit_calcification(directory: Path, limit: int = 10) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    skip_dirs = {".venv", "venv", ".cortex", ".git", "__pycache__", "node_modules"}
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file in files:
            if file.endswith(".py") and (not file.startswith("__")):
                res = calculate_calcification(Path(root) / file)
                if res:
                    results.append(res)
    return sorted(results, key=lambda x: float(x["score"]), reverse=True)[:limit]
