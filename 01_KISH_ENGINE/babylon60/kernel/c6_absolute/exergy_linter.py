#!/usr/bin/env python3
"""
EXERGY LINTER (Reality Level: #C6-ABSOLUTE)
Evaluates codebases for thermodynamic exergy (E_x) vs anergy (A) via AST inspection.

Formula:
  E_x = 1.0 - (Comments / TotalLines) - (AnergyPenalty / TotalLines) + (Guards / TotalLines)
  Bounds: clamped between 0.0 and 1.0.
"""

import ast
import re
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

ANERGY_TERMS = ["TODO", "FIXME", "pass", "placeholder", "print(", "sleep("]


class ExergyVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.guards_count: int = 0

    def visit_Assert(self, node: ast.Assert) -> None:
        self.guards_count += 1
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.guards_count += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.returns:
            self.guards_count += 1
        for arg in node.args.args:
            if arg.annotation:
                self.guards_count += 1
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if node.returns:
            self.guards_count += 1
        for arg in node.args.args:
            if arg.annotation:
                self.guards_count += 1
        self.generic_visit(node)


def analyze_source(source: str, filepath: str = "<unknown>") -> Optional[Dict[str, Any]]:
    lines = source.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return None

    comments = sum(1 for line in lines if line.strip().startswith("#"))
    anergy_count = sum(
        1
        for line in lines
        for term in ANERGY_TERMS
        if (re.search(r"\b" + term + r"\b", line) if term.isalpha() else term in line)
    )

    try:
        parsed_ast = ast.parse(source)
        visitor = ExergyVisitor()
        visitor.visit(parsed_ast)
        guards = visitor.guards_count
        syntax_penalty = 0
    except SyntaxError:
        guards = 0
        syntax_penalty = 10

    effective_anergy = anergy_count + syntax_penalty
    comment_ratio = comments / total_lines
    anergy_ratio = effective_anergy / total_lines
    guards_ratio = guards / total_lines

    raw_score = 1.0 - comment_ratio - anergy_ratio + guards_ratio
    clamped_score = round(max(0.0, min(1.0, raw_score)), 4)

    return {
        "filepath": filepath,
        "filename": os.path.basename(filepath),
        "total_lines": total_lines,
        "comments": comments,
        "anergy_count": anergy_count,
        "guards": guards,
        "syntax_error": syntax_penalty > 0,
        "exergy_score": clamped_score,
        "status": "EXERGIC" if clamped_score >= 0.75 else ("TRANSITIONAL" if clamped_score >= 0.40 else "ANERGIC"),
    }


def analyze_file(filepath: str) -> Optional[Dict[str, Any]]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception:
        return None
    return analyze_source(source, filepath)


def scan_directory(target_dir: str, exclude_dirs: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    if exclude_dirs is None:
        exclude_dirs = [".git", ".agents", "venv", ".venv", "__pycache__", "node_modules"]

    results: List[Dict[str, Any]] = []
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                res = analyze_file(full_path)
                if res is not None:
                    results.append(res)
    return results


def print_table(results: List[Dict[str, Any]], sort_by_score: bool = True) -> None:
    if not results:
        print("[!] No python files evaluated.")
        return

    if sort_by_score:
        results = sorted(results, key=lambda x: x["exergy_score"], reverse=True)

    header = (
        f"{'FILENAME':<35} | {'LINES':<6} | {'COMM':<5} | {'ANERGY':<6} | {'GUARDS':<6} | {'EXERGY':<7} | {'STATUS'}"
    )
    print("=" * len(header))
    print(header)
    print("=" * len(header))

    total_exergy = 0.0
    for r in results:
        total_exergy += r["exergy_score"]
        fn = r["filename"] if len(r["filename"]) <= 35 else r["filename"][:32] + "..."
        print(
            f"{fn:<35} | {r['total_lines']:<6} | {r['comments']:<5} | {r['anergy_count']:<6} | {r['guards']:<6} | {r['exergy_score']:<7.4f} | {r['status']}"
        )

    print("=" * len(header))
    mean_exergy = total_exergy / len(results)
    print(f"TOTAL ANALYZED: {len(results)} files | MEAN EXERGY: {mean_exergy:.4f} | REALITY LEVEL: #C6-ABSOLUTE")


def main() -> None:
    parser = argparse.ArgumentParser(description="Exergy Linter (C6-ABSOLUTE): AST-level thermodynamic auditing.")
    parser.add_argument("path", nargs="?", default=".", help="File or directory path to audit.")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format.")
    parser.add_argument("--min-score", type=float, default=0.0, help="Filter out files below minimum exergy score.")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"[!] Path does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    if target.is_file():
        res = analyze_file(str(target))
        results = [res] if res else []
    else:
        results = scan_directory(str(target))

    if args.min_score > 0.0:
        results = [r for r in results if r["exergy_score"] >= args.min_score]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_table(results)


if __name__ == "__main__":
    main()
