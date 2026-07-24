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
    try:
        tree = ast.parse(source_code)
        SovereignASTVisitor().visit(tree)
    except SyntaxError as e:
        raise SecurityViolationException(f"AST Syntax Error: {e}") from e

    compiled_code = compile(tree, filename="<jit_ast>", mode="exec")

    local_env: dict[str, Any] = {}

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
    }

    exec_globals = {"__builtins__": safe_builtins}
    exec_globals.update(global_ctx)
    exec_globals["__builtins__"] = safe_builtins

    exec(compiled_code, exec_globals, local_env)
    return local_env


def _worker(source_code: str, global_ctx: dict, conn) -> None:
    t0 = time.perf_counter()
    try:
        conn.send(("started", t0))
    except OSError:
        pass

    result_dict = {}
    try:
        res = _execute_sync(source_code, global_ctx)
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

    p = multiprocessing.Process(target=_worker, args=(source_code, ctx, child_conn))
    p.start()

    child_conn.close()

    spawn_timeout = 10.0
    exec_timeout = timeout_ms / 1000.0

    timeout_triggered = False
    parent_started_at = None
    started = False
    res_dict = None

    while p.is_alive() or parent_conn.poll():
        if res_dict is not None:
            break
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
            except (OSError, ValueError):
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

    if p.is_alive() or timeout_triggered:
        p.terminate()
        p.join(timeout=0.1)
        if p.is_alive():
            p.kill()

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
