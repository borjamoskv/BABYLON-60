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
from pathlib import Path
import sysconfig
from typing import TypedDict, Literal

from blake3 import blake3


_MAX_STREAM_BYTES = 2 * 1024 * 1024
_MAX_RESULT_TEXT_BYTES = 1024 * 1024
_READ_CHUNK_BYTES = 8192


class SecurityError(Exception):
    pass


class ScittResult(TypedDict):
    """Untrusted worker observations; status is neither authority nor attestation."""
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
        forbidden = [a.name for a in node.names if a.name.split(".")[0] not in allowed_imports]
        if forbidden:
            raise SecurityError(f"Importacion no permitida: {forbidden[0]}")

    if isinstance(node, ast.ImportFrom) and (not node.module or node.module.split(".")[0] not in allowed_imports):
        raise SecurityError(f"Importacion no permitida: {node.module}")


def validate_ast_markov_blanket(source_code: str) -> tuple[bool, str]:
    """
    Screen known AST patterns; acceptance is not permission or OS isolation.
    Implements RULE_AST_REFLECT_01 for string constants used in reflections.
    """
    if len(source_code.encode("utf-8")) > 1024 * 1024:
        raise SecurityError("Source exceeds the 1 MiB static-screening limit")
    reflection_funcs = {
        "getattr",
        "setattr",
        "delattr",
        "__getattribute__",
        "eval",
        "exec",
        "compile",
        "__import__",
        "open",
        "input",
    }
    allowed_imports = {"numpy", "networkx", "typing"}

    try:
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            _check_ast_node(node, reflection_funcs, allowed_imports)

        ast_hash = blake3(ast.dump(tree).encode("utf-8")).hexdigest()
        return True, ast_hash
    except SecurityError:
        raise
    except SyntaxError as e:
        raise SecurityError(f"Syntax error (safe): {e}")


# Legacy alias for backwards compatibility
validate_ast_sandbox = validate_ast_markov_blanket


_SUBPROCESS_WRAPPER = """
import sys
import json
from io import StringIO
import contextlib
import resource
import logging

# Thermodynamic Valve: Memory Constraint (50 MB)
# macOS restricts RLIMIT_AS differently from Linux, handle gracefully per platform
MAX_MEM = 50 * 1024 * 1024
try:
    if sys.platform != "darwin":
        resource.setrlimit(resource.RLIMIT_AS, (MAX_MEM, MAX_MEM))
    else:
        try:
            resource.setrlimit(resource.RLIMIT_DATA, (MAX_MEM, MAX_MEM))
        except (ValueError, OSError, AttributeError) as _err:
            sys.stderr.write(f"C5-INFO: Darwin RLIMIT_DATA: {_err}\\n")
except (ValueError, OSError, AttributeError) as _err:
    sys.stderr.write(f"C5-INFO: RLIMIT_AS: {_err}\\n")

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

# Additional syntax restrictions; the OS profile is the isolation boundary.
# Removed: getattr, hasattr, issubclass, exec, eval, open, etc. Added safe __import__.
def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    allowed_imports = {"numpy", "networkx", "typing"}
    base_name = name.split('.')[0]
    if base_name not in allowed_imports:
        raise ImportError(f"SecurityError: Import of '{name}' is forbidden by CORTEX Markov Blanket")
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
# Execute only after the parent has required operating-system confinement.
env = {"__builtins__": safe_builtins, "__name__": "__main__"}

stdout_capture = BoundedStringIO()

# [FRENTE-032] AST Confinement Gate: Pre-screen AST for prohibited dunder traversal
# before entering exec(). Rejects __class__, __subclasses__, __bases__, __mro__, etc.
import ast as _ast
_tree = _ast.parse(code)
_prohibited_attrs = {"__class__", "__subclasses__", "__bases__", "__mro__", "__globals__", "__code__"}
for _node in _ast.walk(_tree):
    if isinstance(_node, _ast.Attribute) and (_node.attr in _prohibited_attrs or _node.attr.startswith("_")):
        raise PermissionError(f"SecurityError: Prohibited attribute '{_node.attr}' blocked by CORTEX AST Gate")

try:
    with contextlib.redirect_stdout(stdout_capture):
        exec(code, env, env)
    result = {"status": "Success", "stdout": stdout_capture.getvalue(), "error": ""}
except MemoryError as e:
    result = {"status": "SecurityError", "stdout": stdout_capture.getvalue(), "error": "MemoryError: Thermodynamic Limit Exceeded"}
except Exception as e:
    result = {"status": "RuntimeError", "stdout": stdout_capture.getvalue(), "error": str(e)}

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


class _OutputLimitExceeded(Exception):
    pass


async def _read_bounded(stream: asyncio.StreamReader) -> bytes:
    """Enforce the raw byte budget outside the arbitrary-code worker."""
    output = bytearray()
    while True:
        chunk = await stream.read(min(_READ_CHUNK_BYTES, _MAX_STREAM_BYTES - len(output) + 1))
        if not chunk:
            return bytes(output)
        if len(output) + len(chunk) > _MAX_STREAM_BYTES:
            raise _OutputLimitExceeded
        output.extend(chunk)


async def _feed_source(stream: asyncio.StreamWriter, source: bytes) -> None:
    try:
        stream.write(source)
        await stream.drain()
    except (BrokenPipeError, ConnectionResetError):
        pass
    finally:
        stream.close()


async def _collect_bounded(process: asyncio.subprocess.Process, source: bytes) -> bytes:
    if process.stdin is None or process.stdout is None or process.stderr is None:
        raise RuntimeError("Execution streams are unavailable")
    stdout_task = asyncio.create_task(_read_bounded(process.stdout))
    tasks = [
        asyncio.create_task(_feed_source(process.stdin, source)),
        stdout_task,
        asyncio.create_task(_read_bounded(process.stderr)),
        asyncio.create_task(process.wait()),
    ]
    try:
        await asyncio.gather(*tasks)
        return stdout_task.result()
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def _discard_stream(stream: asyncio.StreamReader | None) -> None:
    if stream is not None:
        while await stream.read(_READ_CHUNK_BYTES):
            pass


async def _stop_and_reap(process: asyncio.subprocess.Process) -> None:
    if process.returncode is None:
        _purge_zombies(process)
    # Drain without retaining bytes: a paused pipe can otherwise prevent wait()
    # from completing after SIGKILL. All bounded readers have been cancelled.
    await asyncio.gather(
        _discard_stream(process.stdout), _discard_stream(process.stderr), process.wait(),
        return_exceptions=True,
    )


async def _finish_reaping(process: asyncio.subprocess.Process) -> None:
    cleanup = asyncio.create_task(_stop_and_reap(process))
    cancelled = False
    while not cleanup.done():
        try:
            await asyncio.shield(cleanup)
        except asyncio.CancelledError:
            cancelled = True
    cleanup.result()
    if cancelled:
        raise asyncio.CancelledError


def _sandbox_command() -> list[str]:
    """Build the supported read-only Darwin runtime, with no fallback.

    File metadata is visible, but file contents are restricted to the Python
    runtime and installed packages. The profile grants no writes, network,
    process forks, desktop access or arbitrary program execution.
    """
    sandbox = Path("/usr/bin/sandbox-exec")
    if sys.platform != "darwin" or not sandbox.is_file() or not os.access(sandbox, os.X_OK):
        raise SecurityError("No verified OS confinement backend is available on this platform")
    runtime = os.path.realpath(sys.base_prefix)
    framework_python = Path(runtime) / "Resources/Python.app/Contents/MacOS/Python"
    if not framework_python.is_file():
        raise SecurityError("No verified OS confinement backend is available for this Python runtime")
    executable = str(framework_python)
    packages = sorted({os.path.realpath(sysconfig.get_path(key)) for key in ("purelib", "platlib")})
    runtime_paths = sorted({
        runtime, *packages,
        "/System/Library", "/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld",
        "/usr/lib", "/usr/share",
    })
    # Never turn an unusual Python installation into broad host access.
    forbidden_roots = {
        "/", "/Users", "/System", "/System/Volumes", "/System/Volumes/Data", "/usr", "/usr/local",
        "/opt", "/opt/homebrew", "/opt/homebrew/Cellar", "/Library", "/Library/Frameworks", str(Path.home()),
    }
    home = os.path.realpath(str(Path.home()))
    home_aliases = {home, "/System/Volumes/Data" + home}
    if any(
        path in forbidden_roots or not os.path.isabs(path)
        or any(os.path.commonpath((path, user_home)) == path for user_home in home_aliases)
        for path in runtime_paths
    ):
        raise SecurityError("Python runtime paths cannot provide bounded OS confinement")
    profile = (
        "(version 1)(deny default)"
        f"(allow process-exec (literal {json.dumps(executable)}))"
        "(allow sysctl-read)(allow file-read-metadata)"
        "(allow file-read* "
        + "".join(f"(subpath {json.dumps(path)})" for path in runtime_paths)
        + '(literal "/")(literal "/dev/random")(literal "/dev/urandom"))'
    )
    # -S prevents site hooks before confinement; these package directories are
    # the exact read-only directories admitted by the OS profile above.
    wrapper = f"import sys\nsys.path.extend({packages!r})\n" + _SUBPROCESS_WRAPPER
    return [str(sandbox), "-p", profile, executable, "-I", "-S", "-B", "-c", wrapper]


async def run_chaos_monad(
    source_code: str, frontier_tick: str = "GENESIS_TICK", timeout_ms: int = 1000, use_seatbelt: bool = True
) -> ScittResult:
    """Execute only in the supported OS sandbox; deny every unsafe fallback.

    Darwin supports a read-only Python runtime. Other platforms and unavailable
    providers fail closed. ``frontier_tick`` is retained for compatibility; this
    function issues no cryptographic signature or SCITT attestation. Worker
    status and text remain untrusted data, even after schema validation.
    Each raw stream is capped at 2 MiB; decoded stdout/error at 1 MiB each.
    """
    try:
        validate_ast_markov_blanket(source_code)
        if use_seatbelt is not True:
            raise SecurityError("OS confinement is mandatory; unconfined execution is disabled")
        if not isinstance(timeout_ms, int) or not 1 <= timeout_ms <= 60_000:
            raise SecurityError("Execution timeout must be between 1 and 60000 milliseconds")
        cmd = _sandbox_command()
    except SecurityError as e:
        return {"status": "SecurityError", "stdout": "", "error": str(e), "scitt_receipt": {}}

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={}, cwd="/",
            start_new_session=True,
            limit=64 * 1024,
        )
    except OSError:
        return {"status": "SecurityError", "stdout": "", "error": "OS confinement failed to start", "scitt_receipt": {}}

    try:
        try:
            stdout_bytes = await asyncio.wait_for(
                _collect_bounded(process, source_code.encode("utf-8")), timeout=timeout_ms / 1000.0
            )
        except _OutputLimitExceeded:
            return {
                "status": "RuntimeError", "stdout": "",
                "error": "Execution output exceeded parent byte budget", "scitt_receipt": {},
            }
        except asyncio.TimeoutError:
            return {
                "status": "Timeout_Entropy_Death",
                "stdout": "",
                "error": "Execution exceeded timeout",
                "scitt_receipt": {},
            }
    finally:
        await _finish_reaping(process)

    if process.returncode != 0:
        return {"status": "SecurityError", "stdout": "", "error": "OS-confined runtime did not complete", "scitt_receipt": {}}
    try:
        parsed = json.loads(stdout_bytes.decode("utf-8"))
        if not isinstance(parsed, dict) or set(parsed) != {"status", "stdout", "error"}:
            raise ValueError("Invalid execution response")
        if parsed["status"] not in {"Success", "RuntimeError", "SecurityError"}:
            raise ValueError("Invalid execution response")
        if not isinstance(parsed.get("stdout"), str) or not isinstance(parsed.get("error"), str):
            raise ValueError("Invalid execution response")
        if any(len(parsed[key].encode("utf-8")) > _MAX_RESULT_TEXT_BYTES for key in ("stdout", "error")):
            return {
                "status": "RuntimeError", "stdout": "",
                "error": "Execution output exceeded parent byte budget", "scitt_receipt": {},
            }
        if parsed["status"] == "Success" and parsed["error"]:
            raise ValueError("Invalid execution response")
        return {"status": parsed["status"], "stdout": parsed["stdout"], "error": parsed["error"], "scitt_receipt": {}}
    except (ValueError, TypeError, RecursionError):
        return {"status": "RuntimeError", "stdout": "", "error": "Invalid OS-confined execution response", "scitt_receipt": {}}
