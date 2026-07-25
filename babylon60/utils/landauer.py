import ast
import os
from pathlib import Path


class LandauerAnalyzer(ast.NodeVisitor):
    def __init__(self):  # type: ignore[no-untyped-def]
        self.complexity = 0
        self.stats = {"functions": 0, "classes": 0, "decisions": 0}
        self.node_metrics: list[dict] = []  # type: ignore[type-arg]
        self._current_node_stack: list[dict] = []  # type: ignore[type-arg]

    def _visit_node(self, node, key=None):  # type: ignore[no-untyped-def]
        if key:
            self.stats[key] += 1
        self.complexity += 1
        for item in self._current_node_stack:
            item["complexity"] += 1
        self.generic_visit(node)

    def _push_node(self, node, node_type):  # type: ignore[no-untyped-def]
        node_info = {
            "name": getattr(node, "name", "<anonymous>"),
            "type": node_type,
            "start_line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "complexity": 1,
        }
        self._current_node_stack.append(node_info)

    def _pop_node(self):  # type: ignore[no-untyped-def]
        if self._current_node_stack:
            self.node_metrics.append(self._current_node_stack.pop())

    def visit_FunctionDef(self, node):  # type: ignore[no-untyped-def]
        self._push_node(node, "function")  # type: ignore[no-untyped-call]
        self._visit_node(node, "functions")  # type: ignore[no-untyped-call]
        self._pop_node()  # type: ignore[no-untyped-call]

    def visit_AsyncFunctionDef(self, node):  # type: ignore[no-untyped-def]
        self._push_node(node, "async_function")  # type: ignore[no-untyped-call]
        self._visit_node(node, "functions")  # type: ignore[no-untyped-call]
        self._pop_node()  # type: ignore[no-untyped-call]

    def visit_ClassDef(self, node):  # type: ignore[no-untyped-def]
        self._push_node(node, "class")  # type: ignore[no-untyped-call]
        self._visit_node(node, "classes")  # type: ignore[no-untyped-call]
        self._pop_node()  # type: ignore[no-untyped-call]

    def visit_If(self, node):  # type: ignore[no-untyped-def]
        self._visit_node(node, "decisions")  # type: ignore[no-untyped-call]

    def visit_For(self, node):  # type: ignore[no-untyped-def]
        self._visit_node(node, "decisions")  # type: ignore[no-untyped-call]

    def visit_AsyncFor(self, node):  # type: ignore[no-untyped-def]
        self._visit_node(node, "decisions")  # type: ignore[no-untyped-call]

    def visit_While(self, node):  # type: ignore[no-untyped-def]
        self._visit_node(node, "decisions")  # type: ignore[no-untyped-call]

    def visit_ExceptHandler(self, node):  # type: ignore[no-untyped-def]
        self._visit_node(node, "decisions")  # type: ignore[no-untyped-call]

    def visit_BoolOp(self, node):  # type: ignore[no-untyped-def]
        for _ in range(len(node.values) - 1):
            self._visit_node(node, "decisions")  # type: ignore[no-untyped-call]

    def visit_Lambda(self, node):  # type: ignore[no-untyped-def]
        self._visit_node(node, "functions")  # type: ignore[no-untyped-call]

    def visit_ListComp(self, node):  # type: ignore[no-untyped-def]
        self._visit_node(node, "decisions")  # type: ignore[no-untyped-call]

    def visit_DictComp(self, node):  # type: ignore[no-untyped-def]
        self._visit_node(node, "decisions")  # type: ignore[no-untyped-call]

    def visit_SetComp(self, node):  # type: ignore[no-untyped-def]
        self._visit_node(node, "decisions")  # type: ignore[no-untyped-call]

    def visit_GeneratorExp(self, node):  # type: ignore[no-untyped-def]
        self._visit_node(node, "decisions")  # type: ignore[no-untyped-call]

    def visit_Try(self, node):  # type: ignore[no-untyped-def]
        self._visit_node(node)  # type: ignore[no-untyped-call]

    def visit_With(self, node):  # type: ignore[no-untyped-def]
        self._visit_node(node)  # type: ignore[no-untyped-call]

    def visit_AsyncWith(self, node):  # type: ignore[no-untyped-def]
        self._visit_node(node)  # type: ignore[no-untyped-call]


def calculate_calcification(file_path: Path) -> dict | None:  # type: ignore[type-arg]
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        analyzer = LandauerAnalyzer()  # type: ignore[no-untyped-call]
        analyzer.visit(tree)
        loc = len(content.splitlines())
        calcification_score = analyzer.complexity * loc / 100
        for node in analyzer.node_metrics:
            node_loc = node["end_line"] - node["start_line"] + 1
            node["score"] = round(node["complexity"] * node_loc / 10, 2)
            node["is_parasite"] = node["score"] > 30
        return {
            "file": str(file_path.name),
            "loc": loc,
            "complexity": analyzer.complexity,
            "score": round(calcification_score, 2),
            "is_parasite": calcification_score > 50,
            "nodes": sorted(analyzer.node_metrics, key=lambda x: x["score"], reverse=True),
        }
    except (OSError, SyntaxError):
        return None


def audit_calcification(directory: Path, limit: int = 10) -> list[dict]:  # type: ignore[type-arg]
    results = []
    skip_dirs = {".venv", "venv", ".cortex", ".git", "__pycache__", "node_modules"}
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file in files:
            if file.endswith(".py") and (not file.startswith("__")):
                res = calculate_calcification(Path(root) / file)
                if res:
                    results.append(res)
    return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]
