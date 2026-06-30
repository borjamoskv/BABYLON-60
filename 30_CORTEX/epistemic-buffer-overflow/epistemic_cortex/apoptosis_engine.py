# [C5-REAL] Ontological Apoptosis / Code Compactor
# Author: borjamoskv
# Estilo: Sin comillas simples (exclusivo comillas dobles)

from __future__ import annotations
import ast

class ApoptosisOntologicaEngine:
    """
    Simulates the Macrófago (AGENTE-OMEGA) logic.
    Strips dead code branches, empty functions, and unreferenced definitions
    from Python code to shrink the total LOC and reduce system entropy.
    """
    def __init__(self) -> None:
        pass

    def run_apoptosis(self, source_code: str) -> str:
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return source_code

        transformer = ApoptosisTransformer()
        pruned_tree = transformer.visit(tree)
        ast.fix_missing_locations(pruned_tree)

        # Generate source back from AST
        # (In python < 3.9, we fallback to simple AST prints if unparse is missing)
        try:
            return ast.unparse(pruned_tree)
        except AttributeError:
            return source_code

class ApoptosisTransformer(ast.NodeTransformer):
    """AST transformer that removes unreferenced structures."""
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef | None:
        # Apoptosis rules:
        # 1. Remove if the function has only a 'pass' or docstring with no actual code
        body = [stmt for stmt in node.body if not isinstance(stmt, (ast.Pass, ast.Expr))]
        if not body:
            # Apoptosis triggered: dead function purged
            return None
        
        # 2. Visit child elements
        self.generic_visit(node)
        return node

    def visit_If(self, node: ast.If) -> ast.If | None:
        # Simplify conditions like: 'if False:'
        if isinstance(node.test, ast.Constant) and node.test.value is False:
            return None
        self.generic_visit(node)
        return node
