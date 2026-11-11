"""Terminal injection and Unix-socket escape from a confined agent, with real syscalls.

* seccomp (Linux x86_64/aarch64): ``TIOCSTI``/``TIOCLINUX``, ``socket(AF_UNIX)``
  (unless allowed), io_uring and foreign or x32 syscalls return EPERM.
* ``new_session`` (the macOS defence, also exercised on Linux): the target starts
  without a controlling terminal.
* ``forward_signals``: terminal signals still reach a target that left the session.

Each blocking assertion is paired with a control that shows the same probe
succeeds without the protection, otherwise the test is skipped as not falsifiable
here. Signal tests drive a separate launcher process, as the terminal would.

Set BABYLON60_REQUIRE_LANDLOCK=1 (CI) to fail instead of skipping when Landlock is missing.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
import errno
import json
import os
from pathlib import Path
import platform
import signal
import socket
import subprocess
import sys
import time
import tty
from typing import Any

import pytest

from babylon60.confine import launcher
from babylon60.confine.launcher import Launch, interpreter, interpreter_prefix, landlock_abi, spawn
from babylon60.confine.policy import MIN_LANDLOCK_ABI, build_policy, default_homes

ROOT = Path(__file__).absolute().parents[1]
LINUX = sys.platform.startswith("linux")
REQUIRED = os.environ.get("BABYLON60_REQUIRE_LANDLOCK") == "1"
BACKEND = launcher.backend() != "none"
NR_SOCKET = {"x86_64": 41, "aarch64": 198}.get(platform.machine())
NR_IOCTL = {"x86_64": 16, "aarch64": 29}.get(platform.machine())
SECCOMP = LINUX and NR_SOCKET is not None
needs_backend = pytest.mark.skipif(not (BACKEND or (LINUX and REQUIRED)), reason="no confinement backend here")
needs_seccomp = pytest.mark.skipif(
    not SECCOMP or not (landlock_abi() >= MIN_LANDLOCK_ABI or REQUIRED),
    reason="seccomp filter: Linux x86_64/aarch64 with Landlock only",
)
DEFAULT_RULES = ["foreign_arch", "tiocsti", "tioclinux", "af_unix", "io_uring"]


@pytest.fixture
def box(tmp_path: Path) -> dict[str, Any]:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    (home / ".ssh" / "id_rsa").write_text("B60-CANARY-terminal\n")
    ws = tmp_path / "ws"
    ws.mkdir()
    policy = build_policy(ws, homes=[str(home), *default_homes()], runtime=[interpreter_prefix()])
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "LC_ALL": "C"}
    return {"home": home, "ws": ws, "policy": policy, "env": env, "journal": tmp_path / "state" / "journal.db"}


def _python(source: str, *args: str) -> list[str]:
    return [interpreter(), "-I", "-S", "-c", source, *args]


def _run(box: dict[str, Any], argv: list[str], **kwargs: Any) -> launcher.Result:
    return launcher.run(Launch(argv, box["policy"], **kwargs), env=box["env"], cwd=str(box["ws"]))


def _report(result: launcher.Result) -> dict[str, Any]:
    assert result.status.get("ok"), result.status
    lines = result.stdout.decode().strip().splitlines()
    assert lines, result.stderr.decode()
    return json.loads(lines[-1])


def _cli_env() -> dict[str, str]:
    return {**os.environ, "PYTHONPATH": str(ROOT / "01_KISH_ENGINE")}


def _cli_run(box: dict[str, Any], *options: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "babylon60.cli.main_dispatcher",
        "run",
        "--allow-root",
        "--journal",
        str(box["journal"]),
        *options,
        "--",
    ]


def _wait_for(condition: Callable[[], bool], what: str, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    while not condition():
        assert time.monotonic() < deadline, f"timed out waiting for {what}"
        time.sleep(0.02)


@contextmanager
def _terminal() -> Iterator[int]:
    """A pseudo-terminal in raw mode, so any injected byte is readable at once; yields the user side."""
    master, slave = os.openpty()
    try:
        tty.setraw(slave)
        yield slave
    finally:
        os.close(slave)
        os.close(master)


def _pending(fd: int) -> bytes:
    """Bytes waiting in a terminal's input queue: what the user's shell would read and run next."""
    chunks = []
    os.set_blocking(fd, False)
    try:
        while chunk := os.read(fd, 4096):
            chunks.append(chunk)
    except BlockingIOError:
        pass
    finally:
        os.set_blocking(fd, True)
    return b"".join(chunks)


# --- seccomp: status ----------------------------------------------------------------------------


@needs_seccomp
def test_seccomp_reports_each_rule_it_applied(box: dict[str, Any]) -> None:
    default = _run(box, ["/bin/true"], seccomp=True)
    assert default.returncode == 0 and default.status["seccomp"] == DEFAULT_RULES
    allowed = _run(box, ["/bin/true"], seccomp=True, unix_sockets=True)
    assert allowed.returncode == 0 and allowed.status["seccomp"] == [r for r in DEFAULT_RULES if r != "af_unix"]
    launch = launcher.session_launch(["/bin/true"], box["policy"])
    assert (launch.seccomp, launch.unix_sockets, launch.new_session) == (True, False, False)


# --- terminal injection -------------------------------------------------------------------------

INJECT = r"""
import fcntl, os, termios
try:
    fd = os.open("/dev/tty", os.O_RDWR)
    for ch in b"echo INJECTED-BY-AGENT\n":
        fcntl.ioctl(fd, termios.TIOCSTI, bytes([ch]))
    print("TIOCSTI ok")
except OSError as exc:
    print("TIOCSTI failed", exc.errno)
"""

# A minimal user shell: owns the terminal on fd 0, runs one command with stdin from
# /dev/null (the reviewer's `echo | babylon60 run ...`), then reads what it would run next.
USER_SHELL = r"""
import fcntl, json, os, subprocess, sys, termios
fcntl.ioctl(0, termios.TIOCSCTTY, 0)
done = subprocess.run(sys.argv[2:], stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
os.set_blocking(0, False)
try:
    pending = os.read(0, 4096)
except BlockingIOError:
    pending = b""
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump({"returncode": done.returncode, "stdout": done.stdout.decode(), "stderr": done.stderr.decode(),
               "pending": pending.decode("latin-1")}, handle)
"""


def _in_user_shell(box: dict[str, Any], command: list[str], name: str) -> dict[str, Any]:
    result = box["ws"].parent / f"{name}.json"
    with _terminal() as user_tty:
        subprocess.run(
            [sys.executable, "-c", USER_SHELL, str(result), *command],
            stdin=user_tty,
            stdout=subprocess.DEVNULL,
            env={**_cli_env(), "HOME": str(box["home"])},
            cwd=str(box["ws"]),
            start_new_session=True,
            timeout=180,
            check=True,
        )
    return json.loads(result.read_text(encoding="utf-8"))


@needs_backend
def test_run_cli_keeps_injected_input_out_of_the_user_terminal(box: dict[str, Any]) -> None:
    """The reviewer's scenario: stdin redirected, but /dev/tty still reaches the user's terminal."""
    control = _in_user_shell(box, _python(INJECT), "control")
    if control["pending"] != "echo INJECTED-BY-AGENT\n":
        pytest.skip(f"TIOCSTI does not inject here even without babylon60: {control}")
    confined = _in_user_shell(box, [*_cli_run(box), *_python(INJECT)], "confined")
    assert confined["pending"] == "", confined
    assert confined["returncode"] == 0 and "TIOCSTI failed" in confined["stdout"], confined


TIOCSTI_PROBE = r"""
import ctypes, errno, fcntl, json, sys, termios
out = {}
try:
    fcntl.ioctl(0, termios.TIOCSTI, b"A")
    out["tiocsti"] = "ok"
except OSError as exc:
    out["tiocsti"] = errno.errorcode[exc.errno]
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
byte = ctypes.c_char(b"B")  # the kernel truncates the request to 32 bits; high bits must not evade the filter
result = libc.syscall(int(sys.argv[1]), 0, ctypes.c_ulong(termios.TIOCSTI | (1 << 32)), ctypes.byref(byte))
out["tiocsti_high_bits"] = "ok" if result == 0 else errno.errorcode[ctypes.get_errno()]
print(json.dumps(out))
"""


@needs_seccomp
def test_seccomp_refuses_tiocsti_on_the_controlling_terminal(box: dict[str, Any]) -> None:
    def attempt(**kwargs: Any) -> tuple[dict[str, Any], bytes]:
        with _terminal() as user_tty:
            launch = Launch(_python(TIOCSTI_PROBE, str(NR_IOCTL)), box["policy"], acquire_ctty=True, **kwargs)
            process, status = spawn(launch, env=box["env"], cwd=str(box["ws"]), stdin=user_tty)
            stdout, stderr = process.communicate(timeout=60)
            assert status.get("ok") and status.get("acquire_ctty"), status
            return json.loads(stdout), _pending(user_tty)

    report, pending = attempt(seccomp=False)
    if pending != b"AB":
        pytest.skip(f"TIOCSTI does not inject here without the filter: {report}")
    report, pending = attempt(seccomp=True)
    assert report == {"tiocsti": "EPERM", "tiocsti_high_bits": "EPERM"} and pending == b""


FOREIGN_ARCH_PROBE = r"""
import ctypes, errno, mmap, os
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
x32 = libc.syscall(0x40000000 | 39)  # x32 getpid
x32 = "pid" if x32 == os.getpid() else errno.errorcode[ctypes.get_errno()]
code = mmap.mmap(-1, mmap.PAGESIZE, prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
code.write(b"\xb8\x14\x00\x00\x00\xcd\x80\xc3")  # mov eax, 20 (i386 getpid); int 0x80; ret
i386 = ctypes.CFUNCTYPE(ctypes.c_int)(ctypes.addressof(ctypes.c_char.from_buffer(code)))()
print("x32", x32, "i386", "pid" if i386 == os.getpid() else i386)
"""


@needs_seccomp
@pytest.mark.skipif(platform.machine() != "x86_64", reason="x32 and i386 entry points exist on x86_64 only")
def test_seccomp_refuses_foreign_and_x32_syscalls(box: dict[str, Any]) -> None:
    control = _run(box, _python(FOREIGN_ARCH_PROBE))
    if control.returncode != 0 or b"i386 pid" not in control.stdout:
        pytest.skip(f"no i386 syscall entry here: {control.stdout!r} {control.stderr[-200:]!r}")
    confined = _run(box, _python(FOREIGN_ARCH_PROBE), seccomp=True)
    assert confined.returncode == 0
    assert confined.stdout.split() == [b"x32", b"EPERM", b"i386", f"-{errno.EPERM}".encode()]


# --- Unix sockets and io_uring ------------------------------------------------------------------

SOCKET_PROBE = r"""
import ctypes, errno, json, socket, sys
def attempt(fn):
    try:
        fn()
        return "ok"
    except OSError as exc:
        return errno.errorcode.get(exc.errno, str(exc.errno))
out = {kind: attempt(lambda kind=kind: socket.socket(socket.AF_UNIX, getattr(socket, kind)).close())
       for kind in ("SOCK_STREAM", "SOCK_DGRAM", "SOCK_SEQPACKET")}
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
# The kernel reads the domain as an int: high bits must not slip AF_UNIX past the filter.
fd = libc.syscall(int(sys.argv[1]), ctypes.c_long(socket.AF_UNIX | (1 << 32)), socket.SOCK_STREAM, 0)
out["raw_high_bits"] = "ok" if fd >= 0 else errno.errorcode[ctypes.get_errno()]
print(json.dumps(out))
"""


@needs_seccomp
def test_unix_socket_creation_is_refused(box: dict[str, Any]) -> None:
    kinds = ("SOCK_STREAM", "SOCK_DGRAM", "SOCK_SEQPACKET", "raw_high_bits")
    control = _report(_run(box, _python(SOCKET_PROBE, str(NR_SOCKET))))  # Landlock alone allows them
    assert control == dict.fromkeys(kinds, "ok")
    confined = _report(_run(box, _python(SOCKET_PROBE, str(NR_SOCKET)), seccomp=True))
    assert confined == dict.fromkeys(kinds, "EPERM")


CONNECT_PROBE = r"""
import errno, json, socket, sys
try:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(sys.argv[1])
        client.sendall(b"agent-was-here")
    print(json.dumps({"result": "connected"}))
except OSError as exc:
    print(json.dumps({"result": errno.errorcode.get(exc.errno, str(exc.errno))}))
"""


@contextmanager
def _agent_socket(box: dict[str, Any]) -> Iterator[tuple[socket.socket, str]]:
    """An unconfined service on a socket path inside the denied home, like ssh-agent or tmux."""
    path = str(box["home"] / "agent.sock")
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server.bind(path)
        server.listen(4)
        server.setblocking(False)
        yield server, path
    finally:
        server.close()


def _received(server: socket.socket) -> bytes | None:
    """What a client sent, or None when nobody connected (connections wait in the backlog)."""
    try:
        peer, _ = server.accept()
    except BlockingIOError:
        return None
    with peer:
        peer.settimeout(10)
        return peer.recv(64)


@needs_seccomp
def test_unix_socket_service_is_unreachable_unless_allowed(box: dict[str, Any]) -> None:
    with _agent_socket(box) as (server, path):
        blocked = _report(_run(box, _python(CONNECT_PROBE, path), seccomp=True))
        assert blocked == {"result": "EPERM"} and _received(server) is None
        allowed = _report(_run(box, _python(CONNECT_PROBE, path), seccomp=True, unix_sockets=True))
        assert allowed == {"result": "connected"} and _received(server) == b"agent-was-here"


@needs_seccomp
def test_run_cli_blocks_unix_sockets_unless_allowed(box: dict[str, Any]) -> None:
    def cli(*options: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [*_cli_run(box, *options), *_python(CONNECT_PROBE, path)],
            env={**_cli_env(), "HOME": str(box["home"])},
            cwd=str(box["ws"]),
            capture_output=True,
            text=True,
            timeout=180,
        )

    with _agent_socket(box) as (server, path):
        blocked = cli()
        assert blocked.returncode == 0 and json.loads(blocked.stdout) == {"result": "EPERM"}, blocked.stderr
        assert _received(server) is None
        allowed = cli("--allow-unix-sockets")
        assert allowed.returncode == 0 and json.loads(allowed.stdout) == {"result": "connected"}, allowed.stderr
        assert _received(server) == b"agent-was-here"
    log = subprocess.run(
        [sys.executable, "-m", "babylon60.cli.main_dispatcher", "log", "--journal", str(box["journal"]), "--json"],
        env=_cli_env(),
        capture_output=True,
        text=True,
        timeout=60,
    )
    starts = [e["body"] for e in json.loads(log.stdout)["entries"] if e["kind"] == "run_start"]
    assert [(s["seccomp"], s["unix_sockets"]) for s in starts] == [(True, False), (True, True)]


COMPAT_PROBE = r"""
import asyncio, json, os, pwd, socket, subprocess
out = {}
left, right = socket.socketpair()
left.sendall(b"pair")
out["socketpair"] = right.recv(4).decode()
with socket.socket() as server:
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    with socket.create_connection(server.getsockname(), timeout=5) as client:
        peer, _ = server.accept()
        with peer:
            client.sendall(b"tcp")
            out["tcp"] = peer.recv(3).decode()
async def child():
    proc = await asyncio.create_subprocess_exec("/bin/echo", "asyncio", stdout=asyncio.subprocess.PIPE)
    return (await proc.communicate())[0].decode().strip()
out["asyncio"] = asyncio.run(child())
done = subprocess.run(["/bin/echo", "subprocess"], capture_output=True, check=True)
out["subprocess"] = done.stdout.decode().strip()
out["passwd"] = pwd.getpwuid(os.getuid()).pw_name  # glibc tries nscd over AF_UNIX first, then files
out["hosts"] = socket.getaddrinfo("localhost", 80, type=socket.SOCK_STREAM)[0][4][0]
print(json.dumps(out))
"""


@needs_seccomp
def test_ordinary_ipc_and_name_lookups_still_work(box: dict[str, Any]) -> None:
    import pwd

    report = _report(_run(box, _python(COMPAT_PROBE), seccomp=True))
    assert report["socketpair"] == "pair" and report["tcp"] == "tcp"
    assert report["asyncio"] == "asyncio" and report["subprocess"] == "subprocess"
    assert report["passwd"] == pwd.getpwuid(os.getuid()).pw_name
    assert report["hosts"] in ("127.0.0.1", "::1")


IO_URING_PROBE = r"""
import ctypes, errno, json, os
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
def call(*args):
    result = libc.syscall(*args)
    if result < 0:
        return errno.errorcode[ctypes.get_errno()]
    if args[0] == 425:
        os.close(result)
    return "ok"
params = ctypes.create_string_buffer(120)  # struct io_uring_params
print(json.dumps({"setup": call(425, 8, params), "enter": call(426, -1, 0, 0, 0, None, 0),
                  "register": call(427, -1, 0, None, 0)}))
"""


@needs_seccomp
def test_io_uring_is_refused_even_with_unix_sockets(box: dict[str, Any]) -> None:
    control = _report(_run(box, _python(IO_URING_PROBE)))
    if control["setup"] != "ok":
        pytest.skip(f"io_uring is unavailable here: {control}")
    assert control["enter"] != "EPERM" and control["register"] != "EPERM"
    for unix_sockets in (False, True):
        confined = _report(_run(box, _python(IO_URING_PROBE), seccomp=True, unix_sockets=unix_sockets))
        assert confined == {"setup": "EPERM", "enter": "EPERM", "register": "EPERM"}


@needs_backend
def test_target_gets_default_signal_dispositions(box: dict[str, Any]) -> None:
    """Python ignores SIGPIPE at startup; the target must not inherit that (`yes | head`)."""
    result = _run(box, ["/bin/sh", "-c", "yes | head -n 1"])
    assert result.returncode == 0 and result.stdout == b"y\n" and result.stderr == b""


# --- new_session --------------------------------------------------------------------------------

CTTY_PROBE = r"""
import errno, fcntl, json, os, termios
def attempt(fn):
    try:
        fn()
        return "ok"
    except OSError as exc:
        return errno.errorcode.get(exc.errno, str(exc.errno))
out = {"dev_tty": attempt(lambda: os.close(os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY))),
       "session_leader": os.getsid(0) == os.getpid()}
out["tiocsctty"] = attempt(lambda: fcntl.ioctl(0, termios.TIOCSCTTY, 0)) if os.environ.get("B60_REACQUIRE") else "skipped"
out["tiocsti"] = attempt(lambda: fcntl.ioctl(0, termios.TIOCSTI, b"X"))
print(json.dumps(out))
"""
NO_TERMINAL = ("EPERM", "EACCES", "EIO")  # Linux: not the controlling terminal; macOS: EACCES; EIO: legacy off


def _on_terminal(box: dict[str, Any], argv: list[str], **kwargs: Any) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    """Run ``argv`` with the ``acquire_ctty`` hook: a session holder owns the terminal, as the user's shell does."""
    with _terminal() as user_tty:
        launch = Launch(argv, box["policy"], acquire_ctty=True, **kwargs)
        process, status = spawn(launch, env={**box["env"], "B60_REACQUIRE": "1"}, cwd=str(box["ws"]), stdin=user_tty)
        stdout, _ = process.communicate(timeout=60)
        report = json.loads(stdout) if status.get("ok") else {}
        return status, report, _pending(user_tty)


@needs_backend
def test_new_session_target_cannot_reach_the_inherited_terminal(box: dict[str, Any]) -> None:
    """``acquire_ctty`` then ``new_session``: the macOS defence, on any platform."""
    status, control, pending = _on_terminal(box, _python(CTTY_PROBE))
    assert status.get("ok") and status.get("acquire_ctty") is True, status
    assert control["dev_tty"] == "ok" and not control["session_leader"], control
    if pending != b"X":
        pytest.skip(f"TIOCSTI does not inject here without new_session: {control}")
    status, report, pending = _on_terminal(box, _python(CTTY_PROBE), new_session=True)
    assert status.get("ok") and status.get("new_session") is True, status
    assert report["session_leader"] and report["dev_tty"] == "ENXIO", report
    # The terminal still belongs to the holder's session: it cannot be taken back.
    assert report["tiocsctty"] == "EPERM" and report["tiocsti"] in NO_TERMINAL and pending == b"", report


@needs_backend
def test_acquire_ctty_refuses_without_a_terminal(box: dict[str, Any]) -> None:
    launch = Launch(["/bin/true"], box["policy"], acquire_ctty=True)
    process, status = spawn(launch, env=box["env"], cwd=str(box["ws"]), stdin=subprocess.DEVNULL)
    process.communicate(timeout=60)
    assert process.returncode == launcher.EXIT_REFUSED
    assert not status["ok"] and status["error"].startswith("acquire_ctty: fd 0 cannot become"), status


def _gone(pid: int) -> bool:
    if LINUX:
        try:
            with open(f"/proc/{pid}/stat", encoding="ascii") as handle:
                return handle.read().rsplit(")", 1)[1].split()[0] == "Z"
        except FileNotFoundError:
            return True
    state = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    return state in ("", "Z")


@needs_backend
@pytest.mark.parametrize("new_session", [False, True])
def test_acquire_ctty_timeout_ends_the_target(box: dict[str, Any], new_session: bool) -> None:
    pidfile = box["ws"] / "target.pid"
    sleeper = "import os, sys, time\nopen(sys.argv[1], 'w').write(str(os.getpid()))\ntime.sleep(120)"
    with _terminal() as user_tty:
        launch = Launch(_python(sleeper, str(pidfile)), box["policy"], acquire_ctty=True, new_session=new_session)
        process, status = spawn(launch, env=box["env"], cwd=str(box["ws"]), stdin=user_tty)
        try:
            assert status.get("ok"), status
            _wait_for(lambda: pidfile.exists() and pidfile.stat().st_size > 0, "the target")
            target = int(pidfile.read_text())
            launcher._end(process, launch)  # what launcher.run does when the timeout expires
            process.communicate(timeout=30)
            _wait_for(lambda: _gone(target), "the target to end with its session holder")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


# The user's shell owns the terminal and starts the trampoline as its own process group leader, so
# setsid() fails and the trampoline falls back to releasing the terminal with TIOCNOTTY.
SHELL_GROUP_LEADER = r"""
import fcntl, json, os, subprocess, sys, termios
from babylon60.confine import launcher
from babylon60.confine.policy import build_policy
cfg = json.loads(sys.argv[1])
fcntl.ioctl(0, termios.TIOCSCTTY, 0)
policy = build_policy(cfg["ws"], homes=cfg["homes"], runtime=[launcher.interpreter_prefix()])
read_fd, write_fd = os.pipe()
command = launcher._command(launcher.Launch(cfg["argv"], policy, new_session=True), write_fd)
process = subprocess.Popen(command, env=cfg["env"], cwd=cfg["ws"], stdout=subprocess.PIPE, pass_fds=(write_fd,),
                           process_group=0)
os.close(write_fd)
with os.fdopen(read_fd, "rb") as pipe:
    status = json.loads(pipe.read().decode().splitlines()[-1])
stdout, _ = process.communicate(timeout=60)
os.set_blocking(0, False)
try:
    pending = os.read(0, 4096)
except BlockingIOError:
    pending = b""
with open(cfg["result"], "w", encoding="utf-8") as handle:
    json.dump({"status": status, "stdout": stdout.decode(), "pending": pending.decode("latin-1")}, handle)
"""


@needs_backend
def test_new_session_releases_the_terminal_when_setsid_fails(box: dict[str, Any]) -> None:
    result = box["ws"].parent / "group-leader.json"
    cfg = {
        "ws": str(box["ws"]),
        "homes": [str(box["home"]), *default_homes()],
        "argv": _python(CTTY_PROBE),
        "env": {**box["env"], "B60_REACQUIRE": "1"},
        "result": str(result),
    }
    with _terminal() as user_tty:
        subprocess.run(
            [sys.executable, "-c", SHELL_GROUP_LEADER, json.dumps(cfg)],
            stdin=user_tty,
            env=_cli_env(),
            start_new_session=True,
            timeout=120,
            check=True,
        )
    outcome = json.loads(result.read_text(encoding="utf-8"))
    assert outcome["status"].get("ok") and outcome["status"].get("new_session") is True, outcome
    report = json.loads(outcome["stdout"])
    # Still a member of the user's session (setsid failed), but without the terminal.
    assert not report["session_leader"] and report["dev_tty"] == "ENXIO", report
    assert report["tiocsctty"] == "EPERM" and report["tiocsti"] in NO_TERMINAL, report
    assert outcome["pending"] == "", outcome


# --- forward_signals ----------------------------------------------------------------------------

SIGNAL_AGENT = r"""
import json, os, signal, sys, time
ws = sys.argv[1]
wanted = (signal.SIGINT, signal.SIGWINCH)
def mark(name, text=""):
    with open(os.path.join(ws, name + ".tmp"), "w") as handle:
        handle.write(text)
    os.replace(os.path.join(ws, name + ".tmp"), os.path.join(ws, name))
for signum in wanted:
    signal.signal(signum, lambda signum, _frame: mark(f"got-{os.getpid()}-{signum}"))
child = os.fork()  # stays in the agent's process group: forwarding must reach the whole group
mark(f"ready-{os.getpid()}", json.dumps({"sid": os.getsid(0), "pgid": os.getpgid(0)}))
def got_all():
    return all(os.path.exists(os.path.join(ws, f"got-{os.getpid()}-{signum}")) for signum in wanted)
deadline = time.monotonic() + 60
while not got_all() and time.monotonic() < deadline:
    time.sleep(0.02)
if child:
    os.waitpid(child, 0)
os._exit(0 if got_all() else 3)
"""

# A launcher as `babylon60 run` uses it: spawn with new_session, relay signals while waiting.
FORWARD_DRIVER = r"""
import json, os, signal, subprocess, sys
from babylon60.confine import launcher
from babylon60.confine.policy import build_policy
cfg = json.loads(sys.argv[1])
names = ("SIGINT", "SIGTERM", "SIGHUP", "SIGQUIT", "SIGWINCH", "SIGTSTP", "SIGCONT")
before = {name: signal.getsignal(getattr(signal, name)) for name in names}
policy = build_policy(cfg["ws"], homes=cfg["homes"], runtime=[launcher.interpreter_prefix()])
process, status = launcher.spawn(launcher.Launch(cfg["argv"], policy, new_session=True), env=cfg["env"],
                                 cwd=cfg["ws"], stdin=subprocess.DEVNULL, stdout=None, stderr=None)
with launcher.forward_signals(process):
    with open(cfg["marker"] + ".tmp", "w", encoding="utf-8") as handle:
        json.dump({"status": status, "pid": process.pid, "sid": os.getsid(0)}, handle)
    os.replace(cfg["marker"] + ".tmp", cfg["marker"])
    code = process.wait()
after = {name: signal.getsignal(getattr(signal, name)) for name in names}
print(json.dumps({"exit": code, "restored": before == after}), flush=True)
"""


def _start_driver(box: dict[str, Any], argv: list[str], **popen: Any) -> tuple[subprocess.Popen[str], dict[str, Any]]:
    marker = box["ws"].parent / "driver.json"
    cfg = {
        "ws": str(box["ws"]),
        "homes": [str(box["home"]), *default_homes()],
        "argv": argv,
        "env": box["env"],
        "marker": str(marker),
    }
    driver = subprocess.Popen(
        [sys.executable, "-c", FORWARD_DRIVER, json.dumps(cfg)],
        env=_cli_env(),
        stdout=subprocess.PIPE,
        text=True,
        **popen,
    )
    try:
        _wait_for(lambda: marker.exists() and marker.stat().st_size > 0, "the launcher to start relaying")
        started = json.loads(marker.read_text(encoding="utf-8"))
        assert started["status"].get("ok") and started["status"].get("new_session") is True, started
    except BaseException:
        driver.kill()
        driver.wait()
        raise
    return driver, started


def _relay_until_received(box: dict[str, Any], launcher_pid: int) -> dict[int, dict[str, int]]:
    """Signal the launcher, as the terminal would, until both agent processes report both signals."""
    ws = box["ws"]
    _wait_for(lambda: len(list(ws.glob("ready-[0-9]*[0-9]"))) == 2, "both agent processes")
    agents = {int(p.name.split("-")[1]): json.loads(p.read_text()) for p in ws.glob("ready-[0-9]*[0-9]")}
    wanted = [ws / f"got-{pid}-{int(sig)}" for pid in agents for sig in (signal.SIGINT, signal.SIGWINCH)]

    def delivered() -> bool:
        if all(path.exists() for path in wanted):
            return True
        os.kill(launcher_pid, signal.SIGINT)
        os.kill(launcher_pid, signal.SIGWINCH)
        time.sleep(0.2)
        return False

    _wait_for(delivered, "SIGINT and SIGWINCH in every agent process")
    return agents


def _stop_driver(driver: subprocess.Popen[str], agent: int) -> None:
    """On failure only: end a launcher still running and its agent's group (not yet reaped)."""
    if driver.poll() is None:
        driver.kill()
        driver.wait()
        try:
            os.killpg(agent, signal.SIGKILL)
        except ProcessLookupError:
            pass


@needs_backend
def test_forward_signals_relays_sigint_and_sigwinch_to_the_agent_group(box: dict[str, Any]) -> None:
    driver, started = _start_driver(box, _python(SIGNAL_AGENT, str(box["ws"])))
    leader = started["pid"]
    try:
        agents = _relay_until_received(box, driver.pid)
        stdout, _ = driver.communicate(timeout=60)
    finally:
        _stop_driver(driver, leader)
    # The agent leads its own session, outside the launcher's (terminal) session; its child shares the group.
    assert leader in agents and started["sid"] != leader
    assert all(info == {"sid": leader, "pgid": leader} for info in agents.values()), agents
    assert json.loads(stdout) == {"exit": 0, "restored": True}


def _state(pid: int) -> str:
    if LINUX:
        with open(f"/proc/{pid}/stat", encoding="ascii") as handle:
            return handle.read().rsplit(")", 1)[1].split()[0]
    return subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()[:1]


@needs_backend
def test_forward_signals_suspends_and_resumes_the_agent_group(box: dict[str, Any]) -> None:
    sleeper = _python("import sys, time\nopen(sys.argv[1] + '/ready-1', 'w').close()\ntime.sleep(120)", str(box["ws"]))
    # Own process group in this session, like a shell job: SIGTSTP can stop it.
    driver, started = _start_driver(box, sleeper, process_group=0)
    agent = started["pid"]
    try:
        _wait_for(lambda: (box["ws"] / "ready-1").exists(), "the agent")
        os.kill(driver.pid, signal.SIGTSTP)

        def launcher_stopped() -> bool:
            pid, status = os.waitpid(driver.pid, os.WNOHANG | os.WUNTRACED)
            assert pid == 0 or os.WIFSTOPPED(status), status
            return pid != 0

        _wait_for(launcher_stopped, "the launcher to stop itself")
        _wait_for(lambda: _state(agent) == "T", "the agent group to stop")
        os.kill(driver.pid, signal.SIGCONT)
        _wait_for(lambda: _state(agent) != "T", "the agent group to continue")
        os.kill(driver.pid, signal.SIGTERM)  # relayed: the agent ends, the launcher reports it
        stdout, _ = driver.communicate(timeout=60)
    finally:
        _stop_driver(driver, agent)
    assert json.loads(stdout) == {"exit": -signal.SIGTERM, "restored": True}


# `babylon60 run` as on macOS (new_session), exercised on any platform by setting the flag.
CLI_NEW_SESSION = r"""
import sys
from babylon60.confine import launcher
plain = launcher.session_launch
def session_launch(argv, policy, *, unix_sockets=False):
    launch = plain(argv, policy, unix_sockets=unix_sockets)
    launch.new_session = True
    return launch
launcher.session_launch = session_launch
from babylon60.cli.main_dispatcher import main
sys.argv = ["babylon60", *sys.argv[1:]]
main()
"""


@needs_backend
def test_run_cli_relays_signals_to_a_new_session_agent(box: dict[str, Any]) -> None:
    command = [*_cli_run(box)[3:], *_python(SIGNAL_AGENT, str(box["ws"]))]
    driver = subprocess.Popen(
        [sys.executable, "-c", CLI_NEW_SESSION, *command],
        env={**_cli_env(), "HOME": str(box["home"])},
        cwd=str(box["ws"]),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _relay_until_received(box, driver.pid)
        stdout, stderr = driver.communicate(timeout=60)
    finally:
        if driver.poll() is None:
            driver.kill()
            driver.wait()
    assert driver.returncode == 0, stderr
    log = subprocess.run(
        [sys.executable, "-m", "babylon60.cli.main_dispatcher", "log", "--journal", str(box["journal"]), "--json"],
        env=_cli_env(),
        capture_output=True,
        text=True,
        timeout=60,
    )
    entries = json.loads(log.stdout)["entries"]
    assert [e["kind"] for e in entries] == ["run_start", "run_end"]
    assert entries[0]["body"]["new_session"] is True and entries[1]["body"]["exit_code"] == 0
