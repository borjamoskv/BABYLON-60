import ast
import inspect
from typing import Any, Callable
from proof_kernel.canonicalizer import hash_evidence
from proof_kernel.crdt import CRDTMap

class ASTRule:

    def __init__(self, func: Callable[[CRDTMap], CRDTMap]):
        self.name = func.__name__
        try:
            import textwrap
            source = inspect.getsource(func)
            source = textwrap.dedent(source)
        except (TypeError, OSError):
            source = f'def {self.name}(state):\n    pass'
        self.ast_tree = ast.parse(source)
        from proof_kernel.canonical_ast import canonicalize_ast
        self.canonical_schema = canonicalize_ast(self.ast_tree)
        self.ast_node_count = len(list(ast.walk(self.ast_tree)))
        self.ruleset_hash = hash_evidence({'version': 'C5-REAL-AST-V1', 'ast_schema': self.canonical_schema})
        self._audit_purity()
        code_obj = compile(self.ast_tree, filename='<ast>', mode='exec')
        namespace: dict[str, Any] = {'CRDTMap': CRDTMap}
        exec(code_obj, namespace)
        self.executable = namespace[self.name]

    def _audit_purity(self) -> None:
        banned_calls = {'eval', 'exec', 'open', 'print', 'input', '__import__', 'getattr', 'setattr', 'delattr', 'globals', 'locals', 'compile'}
        for node in ast.walk(self.ast_tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                raise ValueError('Ω166 Violated: Imports are prohibited in pure inference rules.')
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in banned_calls:
                    raise ValueError(f"Ω166 Violated: Call to impure function '{node.func.id}' is prohibited.")

    def execute(self, state: CRDTMap) -> CRDTMap:
        result: CRDTMap = self.executable(state)
        return result

    def get_hash(self) -> str:
        return self.ruleset_hash