import os
import ast
import json
from collections import defaultdict
from typing import Any


class EpistemicHalt(Exception):
    """C5-REAL structural failure. Replaces os.kill(SIGKILL) per Ω26."""


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.complexity = 1

    def visit_If(self, node: Any) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: Any) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: Any) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: Any) -> None:
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: Any) -> None:
        self.complexity += 1
        self.generic_visit(node)


class ImportVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: set[str] = set()

    def visit_Import(self, node: Any) -> None:
        for alias in node.names:
            self.imports.add(alias.name)

    def visit_ImportFrom(self, node: Any) -> None:
        if node.module:
            self.imports.add(node.module)


def tarjan(graph: dict[str, list[str]]) -> list[list[str]]:
    index_counter = [0]
    stack = []
    lowlink = {}
    index = {}
    result = []

    def strongconnect(node: str) -> None:
        index[node] = index_counter[0]
        lowlink[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)

        for successor in graph.get(node, []):
            if successor not in index:
                strongconnect(successor)
                lowlink[node] = min(lowlink[node], lowlink[successor])
            elif successor in stack:
                lowlink[node] = min(lowlink[node], index[successor])

        if lowlink[node] == index[node]:
            connected_component = []
            while True:
                successor = stack.pop()
                connected_component.append(successor)
                if successor == node:
                    break
            if len(connected_component) > 1:
                result.append(connected_component)

    for node in graph:
        if node not in index:
            strongconnect(node)
    return result


def main() -> None:
    target_dir = os.environ.get(
        "CORTEX_TARGET_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    internal_namespaces = ["babylon60", "causal_isomorphism", "strike_rs", "cortex"]

    stats = {}
    import_graph = defaultdict(list)
    fan_in: dict[str, int] = defaultdict(int)
    fan_out: dict[str, int] = defaultdict(int)

    # 1. Recorrer archivos y parsear AST
    for root, dirs, files in os.walk(target_dir):
        if (
            ".venv" in root
            or "node_modules" in root
            or "__pycache__" in root
            or ".git" in root
            or ".uv_python" in root
        ):
            continue
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, target_dir)

                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        source = f.read()

                    loc = len(source.split("\n"))
                    tree = ast.parse(source)

                    c_visitor = ComplexityVisitor()
                    c_visitor.visit(tree)

                    i_visitor = ImportVisitor()
                    i_visitor.visit(tree)

                    # Filter internal imports
                    internal_imports = set()
                    for imp in i_visitor.imports:
                        base = imp.split(".")[0]
                        if base in internal_namespaces or any(
                            imp.startswith(n) for n in internal_namespaces
                        ):
                            internal_imports.add(imp)

                    stats[rel_path] = {
                        "loc": loc,
                        "complexity": c_visitor.complexity,
                        "internal_imports": list(internal_imports),
                        "all_imports": list(i_visitor.imports),
                    }

                    import_graph[rel_path] = list(internal_imports)
                    fan_out[rel_path] = len(internal_imports)

                except (SyntaxError, OSError, RuntimeError, ValueError, TypeError) as e:
                    raise EpistemicHalt(
                        f"Error parseando {rel_path}: {e}. Ejecutando purga (Ω26)."
                    )

    # 2. Calcular Fan-in
    for node, imports in import_graph.items():
        # Para hacer el mapeo de import (str) a file (str), aproximamos:
        # si un archivo importa "babylon60.bft.consensus", suma fan_in a ese módulo lógico.
        for imp in imports:
            fan_in[imp] += 1

    # 3. Detectar SCC (Circular Dependencies)
    # Transformamos el grafo de importaciones a nivel de módulo base para SCC
    module_graph = defaultdict(list)
    for node, imports in import_graph.items():
        base_module = node.replace(".py", "").replace("/", ".")
        for imp in imports:
            module_graph[base_module].append(imp)

    sccs = tarjan(module_graph)

    # 4. Generar reporte
    top_loc = sorted(stats.items(), key=lambda x: int(str(x[1]["loc"])), reverse=True)[
        :50
    ]
    top_complex = sorted(
        stats.items(), key=lambda x: int(str(x[1]["complexity"])), reverse=True
    )[:50]

    # Hotspots: top_complex + top_fan_in + top_fan_out
    # Aproximamos calculando un "Hotspot Score"
    hotspots = []
    for rel_path, s in stats.items():
        base_module = rel_path.replace(".py", "").replace("/", ".")
        score = (
            int(str(s["complexity"]))
            + fan_in.get(base_module, 0) * 2
            + fan_out.get(rel_path, 0)
        )
        hotspots.append(
            {
                "file": rel_path,
                "score": score,
                "complexity": s["complexity"],
                "fan_in": fan_in.get(base_module, 0),
                "fan_out": fan_out.get(rel_path, 0),
                "loc": s["loc"],
            }
        )
    hotspots = sorted(hotspots, key=lambda x: int(str(x["score"])), reverse=True)[:20]

    report = {
        "files_analyzed": len(stats),
        "circular_dependencies": sccs,
        "hotspots": hotspots,
        "top_50_complex": [
            {"file": k, "complexity": v["complexity"]} for k, v in top_complex
        ],
        "top_50_loc": [{"file": k, "loc": v["loc"]} for k, v in top_loc],
    }

    # Guardar JSON
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_json = os.path.join(
        project_root,
        "cortex",
        "artifacts",
        "reports",
        "BABYLON_60_QUANTITATIVE_AST.json",
    )
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(report, f, indent=2)

    print(out_json)


if __name__ == "__main__":
    main()
