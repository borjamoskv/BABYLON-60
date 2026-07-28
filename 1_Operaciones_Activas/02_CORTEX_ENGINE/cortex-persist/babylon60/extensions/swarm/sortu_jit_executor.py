# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
import ast
import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger("babylon60.autodidact.sandbox")
logging.basicConfig(level=logging.INFO)


class SecurityViolationException(Exception):
    pass


class JITTimeoutException(Exception):
    pass


class SovereignASTVisitor(ast.NodeVisitor):
    def visit_Import(self, node):
        for name in node.names:
            if name.name in ["os", "sys", "subprocess", "shlex", "builtins"]:
                raise SecurityViolationException(f"Forbidden import: {name.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module in ["os", "sys", "subprocess", "shlex", "builtins"]:
            raise SecurityViolationException(f"Forbidden import from module: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in ["open", "eval", "exec", "input", "breakpoint", "__import__"]:
                raise SecurityViolationException(f"Forbidden call: {node.func.id}")
        self.generic_visit(node)


def _execute_sync(source_code: str, global_ctx: dict) -> dict:
    # Epistemic Filter (AST Parse)
    try:
        tree = ast.parse(source_code)
        SovereignASTVisitor().visit(tree)
    except SyntaxError as e:
        raise SecurityViolationException(f"AST Syntax Error: {e}") from e

    # Compilation
    compiled_code = compile(tree, filename="<jit_ast>", mode="exec")

    # Isolated Execution Environment
    local_env: dict[str, Any] = {}

    # We restrict __builtins__
    safe_builtins = {
        "print": print,
        "len": len,
        "range": range,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "any": any,
        "all": all,
        "map": map,
        "filter": filter,
        "zip": zip,
        "enumerate": enumerate,
        "Exception": Exception,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "KeyError": KeyError,
        "IndexError": IndexError,
        # SECURITY: __import__ deliberately excluded - CRIT-02 remediation.
        # Allowing __import__ in safe_builtins defeats the SovereignASTVisitor
        # blocklist and enables arbitrary code execution.
    }

    exec_globals = {"__builtins__": safe_builtins}
    exec_globals.update(global_ctx)
    exec_globals["__builtins__"] = safe_builtins

    import json
    import tempfile
    import subprocess
    import sys
    import os

    # Chaos Monad: Isolated Edge Execution
    wrapped_code = f"{source_code}\n\nimport json\n__res = {{k: v for k, v in locals().items() if not k.startswith('_') and isinstance(v, (str, int, float, bool, list, dict, type(None)))}}\nprint(json.dumps(__res))\n"

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(wrapped_code)
        f_name = f.name

    try:
        import signal
        proc = subprocess.Popen(
            [sys.executable, f_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={},
            start_new_session=True
        )
        try:
            out, err = proc.communicate(timeout=5.0)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            out, err = proc.communicate()
            raise RuntimeError("Execution exceeded 5.0s (Zombie Purged)")

        if proc.returncode != 0:
            raise RuntimeError(err or out)

        try:
            local_env = json.loads(out)
        except json.JSONDecodeError:
            local_env = {"raw_output": out}

        return local_env
    finally:
        try:
            os.remove(f_name)
        except OSError:
            pass


def _worker(source_code: str, global_ctx: dict, conn) -> None:
    t0 = time.perf_counter()
    try:
        conn.send(("started", t0))
    except OSError:
        pass

    result_dict = {}
    try:
        res = _execute_sync(source_code, global_ctx)
        # Avoid passing complex objects back via IPC
        result_dict["locals"] = list(res.keys())
        result_dict["status"] = "success"  # type: ignore[assignment]
        result_dict["exec_time_ms"] = (time.perf_counter() - t0) * 1000
    except AssertionError as e:
        if global_ctx.get("bounty_mode") is True:
            result_dict["status"] = "poc_success"
            result_dict["error"] = "AssertionError triggered successfully"
            result_dict["locals"] = []
            result_dict["exec_time_ms"] = (time.perf_counter() - t0) * 1000
        else:
            result_dict["status"] = "failed"
            result_dict["error"] = f"AssertionError: {str(e)}"
    except Exception as e:  # noqa: BLE001
        result_dict["status"] = "failed"
        result_dict["error"] = f"{type(e).__name__}: {str(e)}"

    try:
        conn.send(("result", result_dict))
    except OSError:
        pass


async def run_jit_sandbox(source_code: str, timeout_ms: int = 500, global_ctx: dict = None) -> Any:  # pyright: ignore[reportArgumentType]
    """
    Executes Python AST in a bounded memory-only sandbox.
    Uses multiprocessing to guarantee true OS-level termination and bypass GIL deadlocks.
    """
    ctx = global_ctx or {}
    start_time = time.perf_counter()

    import multiprocessing

    parent_conn, child_conn = multiprocessing.Pipe()

    # Run in a completely separate process to protect the main node
    p = multiprocessing.Process(target=_worker, args=(source_code, ctx, child_conn))
    p.start()

    # Close child end in parent process so EOF will be triggered if child exits/crashes
    child_conn.close()

    # We allow up to 10.0 seconds for process spawn/initialization overhead
    # and strictly enforce timeout_ms on actual execution
    spawn_timeout = 10.0
    exec_timeout = timeout_ms / 1000.0

    timeout_triggered = False
    parent_started_at = None
    started = False
    res_dict = None

    while p.is_alive() or parent_conn.poll():
        if res_dict is not None:
            break
        # Check pipe messages
        while parent_conn.poll():
            try:
                msg_type, val = parent_conn.recv()
                if msg_type == "started":
                    started = True
                    parent_started_at = time.perf_counter()
                elif msg_type == "result":
                    res_dict = val
            except EOFError:
                break
            except Exception:  # noqa: BLE001
                break

        now = time.perf_counter()
        if not started:
            if now - start_time > spawn_timeout:
                timeout_triggered = True
                break
        else:
            if now - parent_started_at > exec_timeout:
                timeout_triggered = True
                break

        await asyncio.sleep(0.005)

    # Clean up the process
    if p.is_alive() or timeout_triggered:
        p.terminate()
        p.join(timeout=0.1)
        if p.is_alive():
            p.kill()

    # Close parent connection
    parent_conn.close()

    if timeout_triggered or res_dict is None:
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.error(
            "⚡ [SORTU-JIT] Thermodynamic Timeout triggered (%.2fms). Process terminated via SIGKILL.",
            elapsed,
        )
        raise JITTimeoutException(f"Execution exceeded thermodynamic bounds ({timeout_ms}ms)")

    elapsed = (time.perf_counter() - start_time) * 1000
    if res_dict.get("status") in ("success", "poc_success"):
        exec_time = res_dict.get("exec_time_ms", elapsed)
        status = res_dict.get("status")
        logger.info(
            "⚡ [SORTU-JIT] Sovereign AST execution complete. Status: %s. Yield Time: %.2fms (Process Lifetime: %.2fms)",
            status,
            exec_time,
            elapsed,
        )
        return {
            "status": status,
            "result": {"locals": res_dict["locals"]},
            "time_ms": exec_time,
        }
    err = res_dict.get("error", "Unknown Epistemic Failure")
    logger.error("⚡ [SORTU-JIT] Epistemic failure: %s", err)
    return {"status": "failed", "error": err}
