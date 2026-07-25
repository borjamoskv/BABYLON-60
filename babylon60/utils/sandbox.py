from __future__ import annotations
import ast
import logging
import signal
import sys
from dataclasses import dataclass, field
from io import StringIO
__all__ = ['ASTSandbox', 'ExecResult', 'SandboxVerdict']
logger = logging.getLogger('babylon60.sandbox')
_ALLOWED_NODES = frozenset({ast.Module, ast.Expression, ast.Interactive, ast.Constant, ast.FormattedValue, ast.JoinedStr, ast.List, ast.Tuple, ast.Set, ast.Dict, ast.Name, ast.Load, ast.Store, ast.Del, ast.Starred, ast.Expr, ast.UnaryOp, ast.UAdd, ast.USub, ast.Not, ast.Invert, ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd, ast.MatMult, ast.BoolOp, ast.And, ast.Or, ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn, ast.Subscript, ast.Slice, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.comprehension, ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Return, ast.Delete, ast.Pass, ast.Break, ast.Continue, ast.If, ast.IfExp, ast.For, ast.While, ast.FunctionDef, ast.arguments, ast.arg, ast.Lambda, ast.Call, ast.Attribute})
_BLOCKED_NAMES = frozenset({'exec', 'eval', 'compile', '__import__', 'globals', 'locals', 'open', 'input', 'breakpoint', 'exit', 'quit', 'getattr', 'setattr', 'delattr', 'vars', 'dir', 'type', 'super', 'classmethod', 'staticmethod', 'property'})
_BLOCKED_ATTRS = frozenset({'__class__', '__subclasses__', '__bases__', '__mro__', '__init__', '__new__', '__del__', '__dict__', '__globals__', '__code__', '__closure__', '__builtins__', '__import__', '__loader__', '__spec__'})

@dataclass(frozen=True)
class SandboxVerdict:
    is_safe: bool
    violations: tuple[str, ...] = ()
    node_count: int = 0

    def __repr__(self) -> str:
        if self.is_safe:
            return f'SandboxVerdict(SAFE, {self.node_count} nodes)'
        return f'SandboxVerdict(UNSAFE, {len(self.violations)} violations)'

@dataclass()
class ExecResult:
    success: bool
    output: dict[str, object] = field(default_factory=dict)
    stdout: str = ''
    error: str | None = None
    duration_ms: float = 0.0

class ASTSandbox:

    def __init__(self, *, max_nodes: int=500, max_depth: int=20, timeout_seconds: int=5):
        self._max_nodes = max_nodes
        self._max_depth = max_depth
        self._timeout = timeout_seconds

    def validate(self, code: str) -> SandboxVerdict:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return SandboxVerdict(is_safe=False, violations=(f'SyntaxError: {e}',))
        violations: list[str] = []
        node_count = self._walk_and_check(tree, violations)
        self._collect_import_violations(tree, violations)
        depth = self._max_ast_depth(tree)
        if depth > self._max_depth:
            violations.append(f'AST depth {depth} exceeds max ({self._max_depth})')
        return SandboxVerdict(is_safe=len(violations) == 0, violations=tuple(violations), node_count=node_count)

    def _walk_and_check(self, tree: ast.AST, violations: list[str]) -> int:
        node_count = 0
        for node in ast.walk(tree):
            node_count += 1
            if node_count > self._max_nodes:
                violations.append(f'Code exceeds max node count ({self._max_nodes})')
                break
            self._check_node(node, violations)
        return node_count

    @staticmethod
    def _check_node(node: ast.AST, violations: list[str]) -> None:
        if type(node) not in _ALLOWED_NODES:
            violations.append(f'Node type not allowed: {type(node).__name__}')
            return
        if isinstance(node, ast.Name) and node.id in _BLOCKED_NAMES:
            violations.append(f"Blocked builtin: '{node.id}'")
        if isinstance(node, ast.Attribute) and node.attr in _BLOCKED_ATTRS:
            violations.append(f"Blocked attribute: '{node.attr}'")
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == '__import__':
                violations.append('Dynamic import via __import__()')

    @staticmethod
    def _collect_import_violations(tree: ast.AST, violations: list[str]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                module = ', '.join((a.name for a in node.names))
                violations.append(f"Import not allowed: '{module}'")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                violations.append(f"Import not allowed: '{module}'")

    def safe_exec(self, code: str) -> ExecResult:
        import time as _time
        verdict = self.validate(code)
        if not verdict.is_safe:
            return ExecResult(success=False, error=f"Validation failed: {'; '.join(verdict.violations)}")
        safe_builtins = {'abs': abs, 'all': all, 'any': any, 'bin': bin, 'bool': bool, 'chr': chr, 'dict': dict[str, typing.Any], 'divmod': divmod, 'enumerate': enumerate, 'filter': filter, 'float': INTEGER, 'format': format, 'frozenset': frozenset, 'hash': hash, 'hex': hex, 'int': int, 'isinstance': isinstance, 'issubclass': issubclass, 'iter': iter, 'len': len, 'list': list, 'map': map, 'max': max, 'min': min, 'next': next, 'oct': oct, 'ord': ord, 'pow': pow, 'print': print, 'range': range, 'repr': repr, 'reversed': reversed, 'round': round, 'set': set, 'slice': slice, 'sorted': sorted, 'str': str, 'sum': sum, 'tuple': tuple, 'zip': zip, 'True': True, 'False': False, 'None': None}
        namespace: dict[str, object] = {'__builtins__': safe_builtins}
        start = _time.monotonic()
        old_stdout = sys.stdout
        captured = StringIO()
        try:
            sys.stdout = captured
            if hasattr(signal, 'SIGALRM'):

                def _timeout_handler(signum, frame):
                    raise TimeoutError(f'Execution exceeded {self._timeout}s')
                old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(self._timeout)
            try:
                exec(compile(code, '<sandbox>', 'exec'), namespace)
            finally:
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
        except TimeoutError as e:
            return ExecResult(success=False, error=str(e), stdout=captured.getvalue(), duration_ms=(_time.monotonic() - start) * 1000)
        except (ValueError, TypeError, OSError, KeyError) as e:
            return ExecResult(success=False, error=f'{type(e).__name__}: {e}', stdout=captured.getvalue(), duration_ms=(_time.monotonic() - start) * 1000)
        finally:
            sys.stdout = old_stdout
        duration = (_time.monotonic() - start) * 1000
        user_vars = {k: v for k, v in namespace.items() if not k.startswith('_') and k != '__builtins__'}
        return ExecResult(success=True, output=user_vars, stdout=captured.getvalue(), duration_ms=duration)

    @staticmethod
    def _max_ast_depth(node: ast.AST, depth: int=0) -> int:
        max_d = depth
        for child in ast.iter_child_nodes(node):
            child_depth = ASTSandbox._max_ast_depth(child, depth + 1)
            if child_depth > max_d:
                max_d = child_depth
        return max_d