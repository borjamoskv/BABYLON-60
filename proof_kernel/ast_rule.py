import ast
import inspect
from typing import Callable
from proof_kernel.canonicalizer import hash_evidence
from proof_kernel.crdt import CRDTMap

class ASTRule:
    """
    Ω165 / Ω166 Reversible Ledger & Referential Transparency
    Wraps a python function into a serializable, cryptographically bound AST representation.
    """
    def __init__(self, func: Callable[[CRDTMap], CRDTMap]):
        self.name = func.__name__
        try:
            import textwrap
            source = inspect.getsource(func)
            source = textwrap.dedent(source)
        except (TypeError, OSError):
            source = f"def {self.name}(state):\n    pass"
            
        self.ast_tree = ast.parse(source)
        self.ast_dump = ast.dump(self.ast_tree)
        self.ruleset_hash = hash_evidence({"ast": self.ast_dump})
        
        # Compile it back into an executable object to verify we can run it
        code_obj = compile(self.ast_tree, filename="<ast>", mode="exec")
        namespace = {}
        exec(code_obj, namespace)
        self.executable = namespace[self.name]

    def execute(self, state: CRDTMap) -> CRDTMap:
        return self.executable(state)

    def get_hash(self) -> str:
        return self.ruleset_hash
