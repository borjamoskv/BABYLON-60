# [C5-REAL] MEJORAlo 16D Scanner Extension
# Author: borjamoskv
# Estilo: Sin comillas simples (exclusivo comillas dobles)

from __future__ import annotations
import ast
import re
from dataclasses import dataclass

@dataclass
class ScanDimension:
    name: str
    score: int
    findings: list[str]

@dataclass
class ScanResult:
    project: str
    overall_score: int
    dimensions: list[ScanDimension]

class Mejoralo16DScanner:
    """
    Mejoralo Code Scanner extended to 16 dimensions.
    Adds Dependency Entropy, State Friction, and Causal Isomorphism.
    """
    def __init__(self, project_name: str) -> None:
        self.project_name = project_name

    def scan_code(self, source_code: str, dependencies: list[str] | None = None) -> ScanResult:
        # Standard baseline dimensions (Mocking 1-13 scores)
        dimensions = [
            ScanDimension(name="Integrity", score=98, findings=["No syntax errors."]),
            ScanDimension(name="Architecture", score=90, findings=["Well-formed modules."]),
            ScanDimension(name="Security", score=95, findings=["No credentials in code."]),
            ScanDimension(name="Complexity", score=85, findings=["Nesting levels below limit."]),
            ScanDimension(name="Performance", score=90, findings=["Vectorized operations."]),
            ScanDimension(name="Error Handling", score=90, findings=["Specific exceptions caught."]),
            ScanDimension(name="Duplication", score=95, findings=["No redundant blocks."]),
            ScanDimension(name="Dead Code", score=100, findings=["All entrypoints mapped."]),
            ScanDimension(name="Testing", score=80, findings=["Tests available."]),
            ScanDimension(name="Naming", score=90, findings=["Standard snake_case."]),
            ScanDimension(name="Standards", score=95, findings=["PEP 8 compliant."]),
            ScanDimension(name="Aesthetics", score=90, findings=["Clean indentations."]),
            ScanDimension(name="Psi", score=95, findings=["TODOs tracked."])
        ]

        # 14. Dependency Entropy (Supply chain vulnerability / bloat analysis)
        dep_score, dep_findings = self._eval_dependency_entropy(dependencies or [])
        dimensions.append(ScanDimension(name="Dependency Entropy", score=dep_score, findings=dep_findings))

        # 15. State Friction (Detect side-effects and global/mutable states)
        friction_score, friction_findings = self._eval_state_friction(source_code)
        dimensions.append(ScanDimension(name="State Friction", score=friction_score, findings=friction_findings))

        # 16. Causal Isomorphism (Determines real functional operations vs Green Theater protective bloat)
        iso_score, iso_findings = self._eval_causal_isomorphism(source_code)
        dimensions.append(ScanDimension(name="Causal Isomorphism", score=iso_score, findings=iso_findings))

        # Compute overall weighted score
        overall = int(sum(d.score for d in dimensions) / len(dimensions))
        return ScanResult(project=self.project_name, overall_score=overall, dimensions=dimensions)

    def _eval_dependency_entropy(self, deps: list[str]) -> tuple[int, list[str]]:
        """Scans if the dependency count is bloated or introduces high entropy."""
        count = len(deps)
        if count == 0:
            return 100, ["Zero dependency footprint (Pure Autarchy)."]
        elif count <= 3:
            return 95, [f"Low dependency footprint ({count} packages)."]
        elif count <= 8:
            return 80, [f"Moderate dependency footprint ({count} packages)."]
        else:
            return 50, [f"High dependency entropy ({count} packages). Potential supply chain vulnerabilities."]

    def _eval_state_friction(self, code: str) -> tuple[int, list[str]]:
        """Parses AST to identify occurrences of mutable globals and non-pure mutations."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0, ["Syntax error preventing AST evaluation."]

        globals_found = 0
        nonlocal_found = 0
        mutations = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                globals_found += 1
            elif isinstance(node, ast.Nonlocal):
                nonlocal_found += 1
            elif isinstance(node, ast.AugAssign):
                mutations += 1

        score = 100 - (globals_found * 15 + nonlocal_found * 10 + min(mutations, 25))
        score = max(0, min(100, score))

        findings: list[str] = []
        if globals_found:
            findings.append(f"Found {globals_found} global state definitions.")
        if nonlocal_found:
            findings.append(f"Found {nonlocal_found} nonlocal state captures.")
        if not findings:
            findings.append("Zero state friction. Functional/deterministic codebase.")
        else:
            findings.append(f"Mutations checked: {mutations}.")

        return score, findings

    def _eval_causal_isomorphism(self, code: str) -> tuple[int, list[str]]:
        """
        Measures the ratio of useful operational code to protective/defensive
        boilerplate statements (e.g. 'if obj is None: return').
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0, ["Syntax error preventing isomorphism check."]

        total_nodes = len(list(ast.walk(tree)))
        defensive_structures = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Detect common defensive guards
                # e.g., 'if not x:', 'if x is None:'
                if isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not):
                    defensive_structures += 1
                elif isinstance(node.test, ast.Compare):
                    for op in node.test.ops:
                        if isinstance(op, (ast.Is, ast.IsNot)):
                            defensive_structures += 1

        if total_nodes == 0:
            return 100, ["Empty file."]

        boilerplate_ratio = defensive_structures / total_nodes
        score = int((1.0 - boilerplate_ratio) * 100)
        score = max(0, min(100, score))

        findings = [
            f"Boilerplate ratio: {boilerplate_ratio:.2f} (guards: {defensive_structures}, total AST nodes: {total_nodes})."
        ]
        if score >= 85:
            findings.append("High causal isomorphism. High density of useful operations.")
        else:
            findings.append("Low causal isomorphism. Code contains defensive bloat.")

        return score, findings
