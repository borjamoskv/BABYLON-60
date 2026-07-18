"""
C5-REAL Architect Agent
Protocolo anti-entropía. Detecta y reduce deuda técnica analizando el AST real sin cambiar el comportamiento observable.
"""

import ast
import os
from typing import Dict, List, Tuple
from cortex.swarm.memory_store import AgentMemory


class CyclomaticComplexityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.complexity: int = 1  # Base complexity for any function is 1

    def visit_If(self, node: ast.If) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # Each boolean operator in (a and b and c) adds decision complexity
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


class ArchitectAgent:
    def __init__(self, target_dir: str = "cortex") -> None:
        self.memory = AgentMemory()
        self.target_dir = target_dir

    def measure_file_complexity(self, filepath: str) -> List[Tuple[str, int]]:
        """Calcula la complejidad ciclomática por función usando ast.NodeVisitor."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=filepath)
        except Exception:
            return []

        results: List[Tuple[str, int]] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visitor = CyclomaticComplexityVisitor()
                visitor.visit(node)
                results.append((node.name, visitor.complexity))

        return results

    def audit_cyclomatic_complexity(
        self, threshold: int = 10
    ) -> Dict[str, List[Tuple[str, int]]]:
        """Audita recursivamente el directorio target para detectar funciones con complejidad superior al umbral."""
        high_complexity_map: Dict[str, List[Tuple[str, int]]] = {}

        for root, _, files in os.walk(self.target_dir):
            for file in files:
                if file.endswith(".py") and not file.endswith("_test.py"):
                    filepath = os.path.join(root, file)
                    func_complexities = self.measure_file_complexity(filepath)
                    high_complex = [fc for fc in func_complexities if fc[1] > threshold]
                    if high_complex:
                        high_complexity_map[filepath] = high_complex

        if high_complexity_map:
            for path, funcs in high_complexity_map.items():
                self.memory.log(
                    0, "architect", "tech_debt_detected", f"File={path}|Funcs={funcs}"
                )
        else:
            self.memory.log(0, "architect", "ast_audit_pass", f"Threshold={threshold}")

        return high_complexity_map

    def trigger_refactoring(self, threshold: int = 10) -> bool:
        """Fuerza un ciclo de refactorización si la entropía AST excede el umbral."""
        debt = self.audit_cyclomatic_complexity(threshold)
        if debt:
            print(
                f"[Architect] Entropía detectada en {len(debt)} archivos. Activando protocolo de refactorización..."
            )
            self.memory.log(
                0,
                "architect",
                "refactoring_cycle_initiated",
                f"AffectedFiles={len(debt)}",
            )
            return True
        else:
            print(
                "[Architect] Repositorio en equilibrio termodinámico (complejidad bajo umbral)."
            )
            return False


if __name__ == "__main__":
    agent = ArchitectAgent()
    agent.trigger_refactoring(threshold=5)
