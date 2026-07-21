import os
import ast
import json
from collections import defaultdict
from typing import Any

class EpistemicHalt(Exception):
    """C5-REAL structural failure. Replaces os.kill(SIGKILL) per Ω26."""


class CallGraphVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.call_graph: dict[str, set[str]] = defaultdict(set)
        self.module_calls: set[str] = set()
        self.current_function: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        prev_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev_function

    def visit_Call(self, node: ast.Call) -> Any:
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            # Attempt to capture object.method calls
            if isinstance(node.func.value, ast.Name):
                func_name = f"{node.func.value.id}.{func_name}"
        else:
            func_name = "unknown"

        if self.current_function:
            self.call_graph[self.current_function].add(func_name)
        else:
            self.module_calls.add(func_name)

        self.generic_visit(node)


def main() -> None:
    target_dir = os.environ.get(
        "CORTEX_TARGET_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    if not target_dir:
        raise RuntimeError("CORTEX_TARGET_DIR env var is required (Ω23).")

    global_call_graph = {}

    for root, dirs, files in os.walk(target_dir):
        if any(x in root for x in [".venv", "node_modules", "__pycache__", ".git"]):
            continue
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, target_dir)

                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        source = f.read()

                    tree = ast.parse(source)
                    visitor = CallGraphVisitor()
                    visitor.visit(tree)

                    # Store as serializable dict
                    serializable_cg = {
                        k: list(v) for k, v in visitor.call_graph.items()
                    }
                    if serializable_cg or visitor.module_calls:
                        global_call_graph[rel_path] = {
                            "functions": serializable_cg,
                            "module_level_calls": list(visitor.module_calls),
                        }
                except (OSError, ValueError, TypeError, SyntaxError) as e:
                    raise EpistemicHalt(f"Error parseando {rel_path}: {e}. Ejecutando purga (Ω26).")

    # Extract specifically the path we care about (FastAPI -> strike_rs -> SQLite)
    # 1. Routes mapping
    # 2. TaintEngine / ledger calls

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_json = os.path.join(
        project_root, "cortex", "artifacts", "reports", "BABYLON_60_CALL_GRAPH.json"
    )
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(global_call_graph, f, indent=2)

    print(out_json)


if __name__ == "__main__":
    main()
