# ============================================================================
# BABYLON-60 AST Grader
# █ AST_GRADER | Code Structure & Proof Tree Verification
# ============================================================================

from __future__ import annotations

import ast
from typing import Any, Dict

__all__ = ["ASTGrader"]


class ASTGrader:
    """
    Evaluates AST correctness and compliance for generated code / student proofs.
    """

    def grade(self, source_code: str) -> Dict[str, Any]:
        try:
            parsed = ast.parse(source_code)
            return {"valid": True, "syntax_error": None, "nodes_count": len(list(ast.walk(parsed)))}
        except SyntaxError as e:
            return {"valid": False, "syntax_error": str(e), "nodes_count": 0}
