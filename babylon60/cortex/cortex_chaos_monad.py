# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import ast
import asyncio
import sys
import json
import os
import signal
import hashlib
from typing import TypedDict, Literal


class SecurityError(Exception):
    pass


class ScittResult(TypedDict):
    status: Literal["Success", "Falsified", "Timeout_Entropy_Death", "SecurityError", "RuntimeError", "ByzantineFault"]
    stdout: str
    error: str
    scitt_receipt: dict[str, str]


def _check_ast_node(node: ast.AST, reflection_funcs: set[str], allowed_imports: set[str]) -> None:
    forbidden_attrs = {"sys", "modules", "os", "subprocess", "popen", "system", "eval", "exec"}

    # 1. Block Dunder Attributes and Forbidden Introspection Attributes
    if isinstance(node, ast.Attribute) and isinstance(node.attr, str):
        if node.attr.startswith("__") and node.attr.endswith("__"):
            raise SecurityError(f"Acceso a atributo dunder prohibido: {node.attr}")
        if node.attr in forbidden_attrs:
            raise SecurityError(f"Acceso a atributo prohibido: {node.attr}")

    # 2. Block direct call to reflection functions
    if isinstance(node, ast.Name) and (node.id in reflection_funcs or node.id in forbidden_attrs):
        raise SecurityError(f"Llamada a funcion prohibida: {node.id}")

    # 3. RULE_AST_REFLECT_01: Block string literals containing dunders, reflection func names, or OS escape keywords
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        val = node.value
        is_forbidden_dunder = val.startswith("__") and val.endswith("__") and val != "__main__"
        if is_forbidden_dunder or val in reflection_funcs or val in forbidden_attrs:
            raise SecurityError(f"Constante literal prohibida: {val}")

    # 4. Block imports except whitelist
    if isinstance(node, ast.Import):
        forbidden = [a.name for a in node.names if a.name.split('.')[0] not in allowed_imports]
        if forbidden:
            raise SecurityError(f"Importacion no permitida: {forbidden[0]}")

    if isinstance(node, ast.ImportFrom) and (not node.module or node.module.split('.')[0] not in allowed_imports):
        raise SecurityError(f"Importacion no permitida: {node.module}")


def validate_ast_sandbox(source_code: str) -> tuple[bool, str]:
    """
    Evaluates AST for forbidden introspection and memory escapes.
    Implements RULE_AST_REFLECT_01: Validates string constants used in reflections.
    """
    reflection_funcs = {
        "getattr", "setattr", "delattr", "__getattribute__",
        "eval", "exec", "compile", "__import__", "open", "input",
    }
    allowed_imports = {"numpy", "networkx", "typing"}

    try:
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            _check_ast_node(node, reflection_funcs, allowed_imports)

        ast_hash = hashlib.sha256(ast.dump(tree).encode("utf-8")).hexdigest()
        return True, ast_hash
    except SecurityError:
        raise
    except SyntaxError as e:
        raise SecurityError(f"Syntax error (safe): {e}")


_SUBPROCESS_WRAPPER = """
import sys
import json
from io import StringIO
import contextlib
import resource

# Thermodynamic Valve: Memory Constraint (50 MB)
# macOS may ignore RLIMIT_RSS, so we use RLIMIT_AS (Address Space)
MAX_MEM = 50 * 1024 * 1024
try:
    resource.setrlimit(resource.RLIMIT_AS, (MAX_MEM, MAX_MEM))
except Exception:
    pass

class BoundedStringIO(StringIO):
    def __init__(self, max_bytes=1024 * 1024):
        super().__init__()
        self.max_bytes = max_bytes
        self.written = 0

    def write(self, s):
        self.written += len(s.encode('utf-8'))
        if self.written > self.max_bytes:
            raise RuntimeError("SecurityError: STDOUT Buffer Overflow (Limit: 1 MB)")
        return super().write(s)

code = sys.stdin.read()

# Stripped down builtins for strict isolation
# Removed: getattr, hasattr, issubclass, exec, eval, open, etc. Added safe __import__.
def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    allowed_imports = {"numpy", "networkx", "typing"}
    base_name = name.split('.')[0]
    if base_name not in allowed_imports:
        raise ImportError(f"SecurityError: Import of '{name}' is forbidden by CORTEX Sandbox")
    return __import__(name, globals, locals, fromlist, level)

safe_builtins = {
    '__import__': _safe_import,
    'abs': abs, 'all': all, 'any': any, 'ascii': ascii, 'bin': bin,
    'bool': bool, 'bytearray': bytearray, 'bytes': bytes, 'chr': chr,
    'complex': complex, 'dict': dict, 'dir': dir, 'divmod': divmod,
    'enumerate': enumerate, 'filter': filter, 'float': float, 'format': format,
    'frozenset': frozenset,
    'hash': hash, 'hex': hex, 'id': id, 'int': int, 'isinstance': isinstance,
    'iter': iter, 'len': len, 'list': list,
    'map': map, 'max': max, 'min': min, 'next': next, 'object': object,
    'oct': oct, 'ord': ord, 'pow': pow, 'print': print, 'range': range,
    'repr': repr, 'reversed': reversed, 'round': round, 'set': set,
    'slice': slice, 'sorted': sorted, 'str': str, 'sum': sum, 'tuple': tuple,
    'type': type, 'zip': zip
}
# Execute within a restricted global scope (La Monada Estricta)
env = {"__builtins__": safe_builtins, "__name__": "__main__"}

stdout_capture = BoundedStringIO()

try:
    with contextlib.redirect_stdout(stdout_capture):
        exec(code, env, env)
    result = {"status": "Success", "stdout": stdout_capture.getvalue(), "error": ""}
except MemoryError as e:
    result = {"status": "SecurityError", "stdout": stdout_capture.getvalue(), "error": "MemoryError: Thermodynamic Limit Exceeded"}
except Exception as e:
    result = {"status": "RuntimeError", "stdout": stdout_capture.getvalue(), "error": str(e)}

print("---JSON_OUTPUT_MARKER---")
print(json.dumps(result))
"""


def _purge_zombies(process: asyncio.subprocess.Process) -> None:
    """Purge process group to prevent zombies (INV_C5_CHAOS_MONAD)."""
    if sys.platform != "win32":
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            try:
                process.kill()
            except (ProcessLookupError, OSError):
                pass
    else:
        process.kill()


async def run_chaos_monad(source_code: str, frontier_tick: str = "GENESIS_TICK", timeout_ms: int = 1000, use_seatbelt: bool = False) -> ScittResult:
    """
    Executes dynamic code in a strict subprocess sandbox.
    Returns a strict Monad Result to protect the core from entropy.
    """
    try:
        is_valid, ast_hash = validate_ast_sandbox(source_code)
    except SecurityError as e:
        return {"status": "SecurityError", "stdout": "", "error": str(e), "scitt_receipt": {}}

    # Spawn subprocess
    cmd = [sys.executable, "-I", "-c", _SUBPROCESS_WRAPPER]
    if use_seatbelt and sys.platform == "darwin":
        cmd = [
            "sandbox-exec",
            "-p",
            '(version 1)(deny default)(allow file-read* (subpath "/System"))(allow file-read* (subpath "/Library"))(allow file-read* (subpath "/usr/lib"))',
        ] + cmd

    kwargs = {}
    if sys.platform != "win32":
        kwargs["start_new_session"] = True

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={},
        **kwargs,
    )

    try:
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(input=source_code.encode("utf-8")), timeout=timeout_ms / 1000.0
            )
        except asyncio.TimeoutError:
            # Turing-Sandbox Chaos Isolation (La Sandbox Aislado)
            _purge_zombies(process)
            return {"status": "Timeout_Entropy_Death", "stdout": "", "error": "Execution exceeded timeout", "scitt_receipt": {}}
    finally:
        # Guarantee no zombie processes or runaway processes remain
        if process.returncode is None:
            _purge_zombies(process)
            try:
                await process.wait()
            except (ProcessLookupError, OSError, asyncio.CancelledError):
                pass

    stdout_str = stdout_bytes.decode("utf-8")
    stderr_str = stderr_bytes.decode("utf-8")

    def generate_receipt(final_status: str, out_text: str) -> dict[str, str]:
        # Emula la firma COSE Sign1 (SCITT) anclando el AST y la frontera
        payload = f"{frontier_tick}|{ast_hash}|{final_status}|{len(out_text)}"
        signature = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return {
            "frontier_tick": frontier_tick,
            "ast_hash": ast_hash,
            "signature": signature
        }

    if "---JSON_OUTPUT_MARKER---" in stdout_str:
        parts = stdout_str.split("---JSON_OUTPUT_MARKER---")
        try:
            parsed = json.loads(parts[1].strip())
            status = parsed.get("status", "RuntimeError")
            error_str = parsed.get("error", "")
            
            # Defensa Bizantina: Interceptamos AssertionError del código ejecutado
            if "AssertionError" in error_str or "AssertionError" in stderr_str:
                status = "Falsified"
                
            receipt = generate_receipt(status, parsed.get("stdout", ""))
            return {
                "status": status,
                "stdout": parsed.get("stdout", ""),
                "error": error_str,
                "scitt_receipt": receipt
            }
        except json.JSONDecodeError:
            return {"status": "RuntimeError", "stdout": parts[0], "error": "Failed to decode JSON", "scitt_receipt": {}}

    return {"status": "RuntimeError", "stdout": stdout_str, "error": stderr_str, "scitt_receipt": {}}
