"""Generated MCP execution under measured macOS Seatbelt confinement.

AST filtering is not isolation. Each invocation verifies the actual OS policy
with a trusted probe before dispatch. Unsupported platforms fail closed.
"""

import asyncio
import concurrent.futures
import ctypes
import json
import math
import os
from pathlib import Path
import signal
import socket
import stat
import sys
import tempfile
import time

from blake3 import blake3

from .mcp_deductive_engine import McpCandidateContract

SANDBOX_EXEC = "/usr/bin/sandbox-exec"
MAX_BYTES = 1024 * 1024
MAX_TIMEOUT = 30.0

# This trusted bootstrap sets hard resource limits before loading generated code.
_BOOTSTRAP = """import resource, sys
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_CPU, (int(sys.argv[2]), int(sys.argv[2])))
resource.setrlimit(resource.RLIMIT_FSIZE, (1048576, 1048576))
resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
p = sys.argv[1]
with open(p, 'rb') as source:
    code = source.read(1048577)
if len(code) > 1048576:
    raise ValueError('script too large')
exec(compile(code, p, 'exec'), {'__name__': '__main__', '__file__': p})
"""


def _failure(reason: str, code: str = "OS_ISOLATION_UNAVAILABLE") -> dict[str, object]:
    return {"status": "ERROR", "is_valid": False, "error_code": code, "reason": reason, "latency_ms": 0.0}


def _literal(path: str) -> str:
    # JSON escaping is also valid for these SBPL string literals; disallow control
    # characters rather than admitting ambiguous profile source.
    if any(ord(char) < 32 for char in path):
        raise ValueError("Control character in sandbox path")
    return json.dumps(path, ensure_ascii=False)


def _runtime() -> tuple[str, str]:
    if sys.platform != "darwin" or not os.path.isfile(SANDBOX_EXEC):
        raise RuntimeError("No supported OS confinement backend: macOS Seatbelt is required")
    base = os.path.realpath(sys.base_prefix)
    # Framework launchers spawn Python.app; select that actual executable so the
    # policy never needs process-fork just to start the interpreter.
    framework_binary = os.path.join(base, "Resources/Python.app/Contents/MacOS/Python")
    executable = framework_binary if os.path.isfile(framework_binary) else os.path.realpath(sys.executable)
    if not os.path.isfile(executable):
        raise RuntimeError("Python runtime executable unavailable")
    if base in ("/", "/Users", os.path.expanduser("~")):
        raise RuntimeError("Refusing an overbroad Python runtime root")
    return executable, base


def _profile(executable: str, base: str, code_dir: str, work_dir: str) -> str:
    parents = sorted({str(parent) for path in (executable, base, code_dir, work_dir) for parent in Path(path).parents})
    metadata = " ".join(f"(literal {_literal(path)})" for path in parents)
    readable = (base, "/usr/lib", "/System/Library", code_dir, work_dir)
    reads = " ".join(f"(subpath {_literal(path)})" for path in readable)
    # No process-fork, network, Mach services, HID, Apple Events, or write grants
    # outside the private work directory. Deny site-packages within the runtime.
    site_packages = os.path.join(
        base, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages"
    )
    return (
        "(version 1) (deny default)\n"
        "(allow sysctl-read)\n"
        f"(allow file-read-metadata {metadata})\n"
        f"(allow process-exec (literal {_literal(executable)}))\n"
        f'(allow file-read* (literal "/") (literal "/dev/null") (literal "/dev/urandom") {reads})\n'
        f"(deny file-read* (subpath {_literal(site_packages)}))\n"
        f"(allow file-write* (subpath {_literal(work_dir)}))\n"
    )


def _read_script(path: str) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_BYTES:
            raise ValueError("MCP source must be a regular file of at most 1 MiB")
        with os.fdopen(fd, "rb", closefd=False) as source:
            data = source.read(MAX_BYTES + 1)
        after = os.fstat(fd)
        if len(data) > MAX_BYTES or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValueError("MCP source changed while reading")
        return data
    finally:
        os.close(fd)


class _RusageInfo(ctypes.Structure):
    # Darwin SDK sys/resource.h rusage_info_v0, queried in the supervising parent.
    _fields_ = [("uuid", ctypes.c_uint8 * 16)] + [
        (name, ctypes.c_uint64)
        for name in (
            "user_time",
            "system_time",
            "pkg_idle_wkups",
            "interrupt_wkups",
            "pageins",
            "wired_size",
            "resident_size",
            "phys_footprint",
            "proc_start_abstime",
            "proc_exit_abstime",
        )
    ]


def _resident_bytes(pid: int) -> int:
    library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    query = library.proc_pid_rusage
    query.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
    query.restype = ctypes.c_int
    usage = _RusageInfo()
    if query(pid, 0, ctypes.byref(usage)) != 0:
        raise OSError(ctypes.get_errno(), "Cannot measure confined process memory")
    return int(usage.resident_size)


async def _run_confined(
    script: Path,
    executable: str,
    profile: str,
    work: Path,
    timeout: float,
    stdin: bytes = b"",
    *,
    max_memory_bytes: int = 256 * 1024 * 1024,
    max_output_bytes: int = MAX_BYTES,
    max_input_bytes: int = MAX_BYTES,
) -> tuple[int, bytes, bytes]:
    """Supervise one process group with bounded pipes and sampled RSS.

    Callers must establish and probe the OS policy before dispatching user code.
    The RSS cutoff is sampled; it is not a kernel hard memory quota.
    """
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or not 0 < timeout <= MAX_TIMEOUT
    ):
        raise ValueError("Invalid confined process timeout")
    for label, value, lower, upper in (
        ("memory", max_memory_bytes, 32 * 1024 * 1024, 1024 * 1024 * 1024),
        ("output", max_output_bytes, 1, 8 * MAX_BYTES),
        ("input", max_input_bytes, 1, 8 * MAX_BYTES),
    ):
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError(f"Invalid confined process {label} budget")
    if not isinstance(stdin, bytes) or len(stdin) > max_input_bytes:
        raise ValueError("Confined process input exceeds byte limit")
    process = await asyncio.create_subprocess_exec(
        SANDBOX_EXEC,
        "-p",
        profile,
        executable,
        "-I",
        "-S",
        "-B",
        "-X",
        "utf8",
        "-c",
        _BOOTSTRAP,
        str(script),
        str(max(1, math.ceil(timeout))),
        cwd=str(work),
        env={"HOME": str(work), "TMPDIR": str(work), "LANG": "C", "LC_ALL": "C"},
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        close_fds=True,
        start_new_session=True,
        limit=min(65_536, max_output_bytes + 1),
    )

    async def read_bounded(stream: asyncio.StreamReader | None) -> bytes:
        if stream is None:
            raise RuntimeError("Missing subprocess pipe")
        data = bytearray()
        while len(data) <= max_output_bytes:
            chunk = await stream.read(min(65_536, max_output_bytes + 1 - len(data)))
            if not chunk:
                return bytes(data)
            data.extend(chunk)
        raise ValueError(f"Confined process output exceeds {max_output_bytes} byte limit")

    async def feed() -> None:
        if process.stdin is None:
            raise RuntimeError("Missing subprocess stdin")
        try:
            process.stdin.write(stdin)
            await process.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            process.stdin.close()

    async def monitor_memory() -> None:
        # macOS does not enforce RLIMIT_AS/DATA. This is a sampled RSS cutoff,
        # not a kernel hard memory quota; CPU/output/file limits remain hard.
        while process.returncode is None:
            try:
                if _resident_bytes(process.pid) > max_memory_bytes:
                    raise ValueError(f"Confined process resident memory exceeds {max_memory_bytes} byte cutoff")
            except OSError:
                try:
                    await asyncio.wait_for(asyncio.shield(process.wait()), 0.05)
                except asyncio.TimeoutError as exc:
                    raise RuntimeError("OS memory supervision unavailable") from exc
                return
            await asyncio.sleep(0.05)

    tasks = (
        asyncio.create_task(feed()),
        asyncio.create_task(read_bounded(process.stdout)),
        asyncio.create_task(read_bounded(process.stderr)),
        asyncio.create_task(process.wait()),
        asyncio.create_task(monitor_memory()),
    )
    try:
        _, out, err, returncode, _ = await asyncio.wait_for(asyncio.gather(*tasks), timeout)
        return returncode, out, err
    finally:

        async def cleanup() -> None:
            # A successful/reaped leader can leave live descendants in its group.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            # Cancel the in-flight wait/reads before opening a second wait().
            # asyncio only wakes Process.wait() from connection_lost, and that
            # callback does not run until every pipe transport is closed. A
            # cancelled reader leaves stdout/stderr open, so the reaper hangs
            # even after SIGKILL.
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            transport = getattr(process, "_transport", None)
            if transport is not None:
                for fd in (0, 1, 2):
                    pipe = transport.get_pipe_transport(fd)
                    if pipe is not None and not pipe.is_closing():
                        pipe.close()
            if process.returncode is None:
                await process.wait()

        reaping = asyncio.create_task(cleanup())
        cancelled = False
        while not reaping.done():
            try:
                await asyncio.shield(reaping)
            except asyncio.CancelledError:
                cancelled = True
        reaping.result()
        if cancelled:
            raise asyncio.CancelledError


def _probe_source(canary: Path, outside_write: Path, work: Path, executable: str, tcp_port: int, unix_path: str) -> str:
    return f"""import errno, json, os, socket, subprocess, sys
from pathlib import Path
results = {{}}
def denied(name, operation):
    try:
        operation()
    except OSError as exc:
        results[name] = exc.errno in (errno.EPERM, errno.EACCES)
    else:
        results[name] = False
canary = Path({str(canary)!r})
work = Path({str(work)!r})
denied('read_outside', lambda: canary.read_bytes())
denied('write_outside', lambda: Path({str(outside_write)!r}).write_text('escape'))
link = work / 'outside-link'
link.symlink_to(canary)
denied('symlink_read', lambda: link.read_bytes())
def tcp_connect():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(1)
        client.connect(('127.0.0.1', {tcp_port!r}))
def unix_connect():
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(1)
        client.connect({unix_path!r})
def udp_send():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.sendto(b'probe', ('127.0.0.1', {tcp_port!r}))
denied('network_tcp', tcp_connect)
denied('network_unix', unix_connect)
denied('network_udp', udp_send)
marker = work / 'spawned'
command = [{executable!r}, '-I', '-S', '-c', "from pathlib import Path; Path(" + repr(str(marker)) + ").write_text('child')"]
denied('subprocess', lambda: subprocess.run(command, check=False, timeout=1))
def spawn():
    pid = os.posix_spawn(command[0], command, {{}})
    os.waitpid(pid, 0)
denied('posix_spawn', spawn)
def fork():
    pid = os.fork()
    if pid == 0:
        marker.write_text('fork')
        os._exit(0)
    os.waitpid(pid, 0)
denied('fork', fork)
(work / 'positive').write_text('allowed')
results['write_private'] = (work / 'positive').read_text() == 'allowed'
print(json.dumps(results), flush=True)
"""


class McpSandboxValidator:
    """Execute only after fresh OS confinement probes; never fall back to bare Python.

    The original source is retained. A descriptor-pinned copy is executed in a
    private directory and always removed by the parent, regardless of detonate.
    """

    async def _execute(
        self, script_path: str, candidate: McpCandidateContract, arguments: dict[str, object] | None, timeout: float
    ) -> dict[str, object]:
        started = time.monotonic()
        try:
            if not math.isfinite(timeout) or not 0 < timeout <= MAX_TIMEOUT:
                return _failure("Timeout must be finite and in (0, 30] seconds", "INVALID_REQUEST")
            executable, base = _runtime()
            source = _read_script(script_path)
            digest = blake3(source).hexdigest()
            with (
                tempfile.TemporaryDirectory(prefix="babylon60_mcp_") as raw_root,
                tempfile.TemporaryDirectory(prefix="babylon60_canary_") as raw_outside,
            ):
                root = Path(os.path.realpath(raw_root))
                outside = Path(os.path.realpath(raw_outside))
                work, code = root / "work", root / "code"
                work.mkdir(mode=0o700)
                code.mkdir(mode=0o700)
                script = code / "candidate.py"
                script.write_bytes(source)
                script.chmod(0o400)
                if blake3(script.read_bytes()).hexdigest() != digest:
                    raise ValueError("Pinned source digest mismatch")
                canary, escaped = outside / "canary", outside / "escaped"
                canary.write_bytes(os.urandom(32))
                original_canary = canary.read_bytes()
                probe = code / "probe.py"
                # Parent-owned loopback/Unix listeners provide reachable targets;
                # ECONNREFUSED is not accepted as proof of a network denial.
                with (
                    socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp,
                    socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as unix,
                ):
                    tcp.bind(("127.0.0.1", 0))
                    tcp.listen(1)
                    unix_path = str(outside / "sock")
                    unix.bind(unix_path)
                    unix.listen(1)
                    probe.write_text(_probe_source(canary, escaped, work, executable, tcp.getsockname()[1], unix_path))
                    probe.chmod(0o400)
                    profile = _profile(executable, base, str(code), str(work))
                    rc, out, err = await _run_confined(probe, executable, profile, work, min(timeout, 5.0))
                    expected = {
                        "read_outside",
                        "write_outside",
                        "symlink_read",
                        "network_tcp",
                        "network_unix",
                        "network_udp",
                        "subprocess",
                        "posix_spawn",
                        "fork",
                        "write_private",
                    }
                    try:
                        evidence = json.loads(out)
                    except (ValueError, UnicodeDecodeError):
                        evidence = {}
                    if (
                        rc != 0
                        or not isinstance(evidence, dict)
                        or set(evidence) != expected
                        or not all(value is True for value in evidence.values())
                    ):
                        return _failure(
                            f"OS confinement probe failed (exit {rc}, checks {evidence}): {err[:512].decode('utf-8', errors='replace')}"
                        )
                    for listener in (tcp, unix):
                        listener.setblocking(False)
                        try:
                            connection, _ = listener.accept()
                        except BlockingIOError:
                            pass
                        else:
                            connection.close()
                            return _failure("Independent network witness observed a connection")
                if canary.read_bytes() != original_canary or escaped.exists() or (work / "spawned").exists():
                    return _failure("Independent confinement witness failed")
                requests = [
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "Babylon60", "version": "1"},
                        },
                    },
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                ]
                if arguments is not None:
                    requests.append(
                        {
                            "jsonrpc": "2.0",
                            "id": 3,
                            "method": "tools/call",
                            "params": {"name": candidate.tool_name, "arguments": arguments},
                        }
                    )
                stdin = b"".join(json.dumps(request).encode() + b"\n" for request in requests)
                if len(stdin) > MAX_BYTES:
                    return _failure("MCP request exceeds 1 MiB", "INVALID_REQUEST")
                rc, out, err = await _run_confined(script, executable, profile, work, timeout, stdin)
                if rc != 0:
                    return _failure(
                        f"Confined MCP exited {rc}: {err[:512].decode('utf-8', errors='replace')}", "EXECUTION_FAILED"
                    )
                responses = [json.loads(line) for line in out.splitlines()]
                if len(responses) != len(requests) or any(
                    not isinstance(response, dict)
                    or response.get("jsonrpc") != "2.0"
                    or response.get("id") != request["id"]
                    or "error" in response
                    for request, response in zip(requests, responses)
                ):
                    return _failure("Invalid MCP protocol response", "PROTOCOL_ERROR")
                tools = responses[1].get("result", {}).get("tools", [])
                names = [tool.get("name") for tool in tools]
                if candidate.tool_name not in names:
                    return _failure("Expected MCP tool is absent", "PROTOCOL_ERROR")
                result: dict[str, object] = {
                    "status": "SUCCESS",
                    "is_valid": True,
                    "server_name": candidate.server_name,
                    "tool_name": candidate.tool_name,
                    "target_tool": candidate.tool_name,
                    "tools_found": names,
                    "code_hash": digest,
                    "isolation_backend": "macos-seatbelt",
                    "isolation_evidence": evidence,
                    "latency_ms": (time.monotonic() - started) * 1000,
                }
                if arguments is not None:
                    call = responses[2].get("result", {})
                    if call.get("isError", False):
                        return _failure("Confined tool reported an error", "TOOL_ERROR")
                    result["tool_output"] = json.loads(call["content"][0]["text"])
                return result
        except asyncio.TimeoutError:
            return _failure("Confined MCP timed out and was killed", "TIMEOUT")
        except (OSError, ValueError, RuntimeError, KeyError, TypeError, AttributeError, IndexError) as exc:
            return _failure(str(exc))

    async def validate_mcp_server(
        self, script_path: str, candidate: McpCandidateContract, timeout_seconds: float = 5.0
    ) -> dict[str, object]:
        return await self._execute(script_path, candidate, None, timeout_seconds)

    async def execute_and_detonate_mcp(
        self,
        script_path: str,
        candidate: McpCandidateContract,
        call_arguments: dict[str, object],
        timeout_seconds: float = 5.0,
        detonate: bool = True,
    ) -> dict[str, object]:
        return await self._execute(script_path, candidate, call_arguments, timeout_seconds)

    def execute_and_detonate_mcp_sync(
        self,
        script_path: str,
        candidate: McpCandidateContract,
        call_arguments: dict[str, object],
        timeout_seconds: float = 5.0,
        detonate: bool = True,
    ) -> dict[str, object]:
        def run() -> dict[str, object]:
            return asyncio.run(
                self.execute_and_detonate_mcp(script_path, candidate, call_arguments, timeout_seconds, detonate)
            )

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return run()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(run).result()
