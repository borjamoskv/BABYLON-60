#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# ============================================================================
# BABYLON-60 · DETERMINISTIC AUDIT SCRIPT
# Zero-Friction Mass Execution (F=0)
# ============================================================================
import os
import re
import ast
import json
from typing import List, Dict, Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGET_EXTENSIONS = {".py", ".rs", ".lean", ".md"}

MYTHOLOGICAL_TERMS = [
    r"\bmagia\b",
    r"\bmagical\b",
    r"\bmagic\b",
    r"\boráculo\b",
    r"\boracle\b",
    r"\bBFT\s*Local\b",
]


def check_ast_nesting(filepath: str) -> List[Dict[str, Any]]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except SyntaxError:
        return [{"type": "SyntaxError", "line": 0}]
    except Exception as e:
        return [{"type": "ASTReadError", "details": str(e)}]

    class NestingVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.max_depth = 0
            self.current_depth = 0
            self.violations = []

        def generic_visit(self, node) -> None:
            increases_depth = isinstance(
                node,
                (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            )
            if increases_depth:
                self.current_depth += 1
                if self.current_depth > 4:
                    self.violations.append(
                        {"type": "NestingViolation", "depth": self.current_depth, "line": getattr(node, "lineno", 0)}
                    )

            super().generic_visit(node)

            if increases_depth:
                self.current_depth -= 1

    visitor = NestingVisitor()
    visitor.visit(tree)
    return visitor.violations


def scan_file(filepath: str) -> Dict[str, Any]:
    issues = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()
    except Exception as e:
        return {"file": filepath, "error": f"Failed to read: {e}"}

    # Check mythological terms
    for term in MYTHOLOGICAL_TERMS:
        regex = re.compile(term, re.IGNORECASE)
        for i, line in enumerate(lines):
            if regex.search(line):
                issues.append({"type": "MythologicalTerm", "term": term, "line": i + 1, "content": line.strip()})

    # Check headers (very basic heuristic)
    if filepath.endswith(".py") or filepath.endswith(".rs"):
        if not any("BABYLON-60" in line for line in lines[:10]):
            issues.append(
                {"type": "MissingHeader", "line": 1, "details": "No BABYLON-60 header found in first 10 lines."}
            )

    # Check AST Nesting for python
    if filepath.endswith(".py"):
        ast_issues = check_ast_nesting(filepath)
        issues.extend(ast_issues)

    if issues:
        return {"file": filepath, "issues": issues}
    return {}


def main() -> None:
    report = []
    ignore_dirs = {".git", ".venv", "__pycache__", "target", ".pytest_cache", ".ruff_cache", "scratch"}

    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in TARGET_EXTENSIONS:
                filepath = os.path.join(root, file)
                result = scan_file(filepath)
                if result:
                    report.append(result)

    scratch_dir = os.path.join(REPO_ROOT, "scratch")
    os.makedirs(scratch_dir, exist_ok=True)
    report_path = os.path.join(scratch_dir, "audit_report.json")

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Audit complete. Found {len(report)} files with issues.")
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
