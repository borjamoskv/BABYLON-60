#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import ast
import os


class DepthVisitor(ast.NodeVisitor):
    def __init__(self):
        self.max_depth = 0
        self.current_depth = 0

    def visit(self, node):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.FunctionDef, ast.ClassDef)):
            self.current_depth += 1
            if self.current_depth > self.max_depth:
                self.max_depth = self.current_depth
            super().generic_visit(node)
            self.current_depth -= 1
        else:
            super().generic_visit(node)


def check_file(path):
    with open(path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=path)
        except Exception:
            return
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            visitor = DepthVisitor()
            # Start at 0 for the function body since the function itself is depth 1
            visitor.current_depth = 0
            for child in node.body:
                visitor.visit(child)
            if visitor.max_depth > 4:
                print(f"{path}: Function {node.name} has depth {visitor.max_depth}")


for root_dir in ["babylon60", "scripts"]:
    if not os.path.exists(root_dir):
        continue
    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            if f.endswith(".py"):
                check_file(os.path.join(dirpath, f))
