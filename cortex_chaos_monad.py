import ast
import asyncio
import sys
import tempfile
import json
import os
from typing import TypedDict, Literal

class SecurityError(Exception):
    pass

class MonadResult(TypedDict):
    status: Literal["Success", "Timeout_Entropy_Death", "SecurityError", "RuntimeError"]
    stdout: str
    error: str

def validate_ast_sandbox(source_code: str) -> bool:
    """
    Evaluates AST for forbidden introspection and memory escapes.
    Implements RULE_AST_REFLECT_01: Validates string constants used in reflections.
    """
    try:
        tree = ast.parse(source_code)
        
        reflection_funcs = {"getattr", "setattr", "delattr", "__getattribute__", "eval", "exec", "compile", "__import__"}
        
        for node in ast.walk(tree):
            # 1. Block Dunder Attributes (Direct access)
            if isinstance(node, ast.Attribute):
                if isinstance(node.attr, str) and node.attr.startswith("__") and node.attr.endswith("__"):
                    raise SecurityError(f"Acceso a atributo dunder prohibido: {node.attr}")
            
            # 2. Block direct call to reflection functions
            if isinstance(node, ast.Name) and node.id in reflection_funcs:
                raise SecurityError(f"Llamada a funcion de introspeccion prohibida: {node.id}")
            
            # 3. RULE_AST_REFLECT_01: Block string literals containing dunders or reflection func names
            if isinstance(node, ast.Constant):
                if isinstance(node.value, str):
                    if node.value.startswith("__") and node.value.endswith("__"):
                        raise SecurityError(f"Constante literal con patron dunder prohibida: {node.value}")
                    if node.value in reflection_funcs:
                        raise SecurityError(f"Constante literal con nombre de introspeccion prohibida: {node.value}")
                        
            # 4. Block f-strings containing dunders or reflections (Constant parts)
            # F-strings evaluate to ast.JoinedStr with ast.Constant parts and ast.FormattedValue parts
            if isinstance(node, ast.JoinedStr):
                # The constants inside f-strings are caught by the ast.Constant check above,
                # but let's be extra safe and evaluate concatenated string if possible.
                pass
                
            # 5. Block imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                raise SecurityError("Importacion no permitida en entorno sandboxed")
                
        return True
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
# Removed: getattr, hasattr, issubclass, exec, eval, open, etc.
safe_builtins = {
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
env = {"__builtins__": safe_builtins}

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

async def run_chaos_monad(source_code: str, timeout_ms: int = 1000, use_seatbelt: bool = False) -> MonadResult:
    """
    Executes dynamic code in a strict subprocess sandbox.
    Returns a strict Monad Result to protect the core from entropy.
    """
    try:
        validate_ast_sandbox(source_code)
    except SecurityError as e:
        return {"status": "SecurityError", "stdout": "", "error": str(e)}

    # Spawn subprocess
    cmd = [sys.executable, "-I", "-c", _SUBPROCESS_WRAPPER]
    if use_seatbelt and sys.platform == "darwin":
        cmd = [
            "sandbox-exec", "-p",
            "(version 1)(deny default)(allow file-read* (subpath \"/System\"))(allow file-read* (subpath \"/Library\"))(allow file-read* (subpath \"/usr/lib\"))"
        ] + cmd

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(input=source_code.encode("utf-8")), 
            timeout=timeout_ms / 1000.0
        )
    except asyncio.TimeoutError:
        # Thermodynamic Valve: Kill runaway processes
        process.kill()
        return {"status": "Timeout_Entropy_Death", "stdout": "", "error": "Execution exceeded timeout"}

    stdout_str = stdout_bytes.decode("utf-8")
    
    if "---JSON_OUTPUT_MARKER---" in stdout_str:
        parts = stdout_str.split("---JSON_OUTPUT_MARKER---")
        try:
            return json.loads(parts[1].strip())
        except json.JSONDecodeError:
            return {"status": "RuntimeError", "stdout": parts[0], "error": "Failed to decode JSON from subprocess"}
    
    stderr_str = stderr_bytes.decode("utf-8")
    return {"status": "RuntimeError", "stdout": stdout_str, "error": stderr_str}
