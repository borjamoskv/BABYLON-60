"""Start a command through the confinement trampoline and read what it applied."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from typing import IO, Any

from babylon60.confine.policy import MIN_LANDLOCK_ABI, Policy

EXIT_REFUSED = 126
TRAMPOLINE = Path(__file__).with_name("_landlock_exec.py")


class ConfinementUnavailable(RuntimeError):
    """No supported OS confinement backend on this machine."""


def landlock_abi() -> int:
    """Landlock ABI exposed by the running kernel, or 0 when absent."""
    if not sys.platform.startswith("linux"):
        return 0
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    abi = libc.syscall(444, None, ctypes.c_size_t(0), ctypes.c_uint32(1))
    return int(abi) if abi > 0 else 0


def backend() -> str:
    if sys.platform.startswith("linux"):
        return "landlock" if landlock_abi() >= MIN_LANDLOCK_ABI else "none"
    if sys.platform == "darwin":
        from babylon60.confine.seatbelt import available

        return "seatbelt" if available() else "none"
    return "none"


def interpreter() -> str:
    """The base interpreter, outside any virtual environment."""
    return os.path.realpath(getattr(sys, "_base_executable", None) or sys.executable)


def interpreter_prefix() -> str:
    return os.path.realpath(sys.base_prefix)


@dataclass
class Launch:
    argv: list[str]
    policy: Policy | None  # None runs the same trampoline without restrictions (control)
    seccomp: bool = False
    drop_caps: bool = True
    min_abi: int = MIN_LANDLOCK_ABI
    unix_sockets: bool = False  # with seccomp (Linux) or Seatbelt (macOS), allow Unix domain sockets
    new_session: bool = False  # trampoline drops the controlling terminal (setsid) before exec
    acquire_ctty: bool = False  # test hook: stdin becomes the controlling terminal before confinement


def session_launch(argv: list[str], policy: Policy, *, unix_sockets: bool = False) -> Launch:
    """How ``babylon60 run`` and the demo start a confined target, on every platform."""
    return Launch(
        argv,
        policy,
        seccomp=sys.platform.startswith("linux"),
        unix_sockets=unix_sockets,
        new_session=sys.platform == "darwin",
    )


FORWARDED_SIGNALS = ("SIGINT", "SIGTERM", "SIGHUP", "SIGQUIT", "SIGWINCH")


@contextmanager
def forward_signals(process: subprocess.Popen[Any]) -> Iterator[None]:
    """Relay terminal signals to a target started with ``new_session``.

    Such a target leads its own session and process group, so the terminal no
    longer signals it: Ctrl-C, Ctrl-\\, hangups and window resizes reach only this
    launcher. While the context is active, SIGINT, SIGTERM, SIGHUP, SIGQUIT and
    SIGWINCH go to the target's whole process group. SIGTSTP stops that group
    with SIGSTOP (the kernel discards SIGTSTP in an orphaned process group, which
    the target's group is) and then stops this launcher, so the shell gets the
    terminal back; SIGCONT continues the group. Previous handlers come back on exit.
    """

    def send(signum: int) -> None:
        if process.returncode is not None:
            return  # reaped: its process group id may already belong to someone else
        try:
            os.killpg(process.pid, signum)
        except (ProcessLookupError, PermissionError):
            pass  # raising here would abort process.wait() and orphan the agent

    def relay(signum: int, _frame: object) -> None:
        send(signum)

    def suspend(_signum: int, _frame: object) -> None:
        send(signal.SIGSTOP)
        signal.signal(signal.SIGTSTP, signal.SIG_DFL)
        try:
            os.kill(os.getpid(), signal.SIGTSTP)  # stops here until SIGCONT, unless our own group is orphaned
        finally:
            signal.signal(signal.SIGTSTP, suspend)
        send(signal.SIGCONT)

    def resume(_signum: int, _frame: object) -> None:
        send(signal.SIGCONT)

    handlers: dict[int, Callable[[int, Any], None]] = {
        getattr(signal, name): relay for name in FORWARDED_SIGNALS if hasattr(signal, name)
    }
    handlers[signal.SIGTSTP] = suspend
    handlers[signal.SIGCONT] = resume
    previous: dict[int, Any] = {}
    try:
        for signum, handler in handlers.items():
            previous[signum] = signal.signal(signum, handler)
        yield
    finally:
        for signum, old in previous.items():
            signal.signal(signum, signal.SIG_DFL if old is None else old)


# Test hook ``acquire_ctty``: the target inherits the user's terminal. Like the user's shell, this
# holder leads a new session that owns the terminal on fd 0 and runs the trampoline as an ordinary
# member, so the target can neither lead the session nor take the terminal back after leaving it.
# It closes its copy of the status pipe, ends the target on SIGTERM/SIGINT/SIGHUP and exits as it does.
CTTY_HOLDER = r"""
import fcntl, json, os, signal, sys, termios
status_fd, command, holder = int(sys.argv[1]), sys.argv[2:], os.getpid()
def refuse(message):
    os.write(status_fd, (json.dumps({"ok": False, "error": "acquire_ctty: " + message}) + "\n").encode())
    os._exit(126)
try:
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)
except OSError as exc:
    refuse("fd 0 cannot become the controlling terminal: " + str(exc.strerror))
child = os.fork()
if child == 0:
    try:
        if sys.platform.startswith("linux"):
            import ctypes
            ctypes.CDLL(None).prctl(1, 9)  # PR_SET_PDEATHSIG, SIGKILL: never outlive the holder
            if os.getppid() != holder:
                os._exit(126)
        os.execv(command[0], command)
    except OSError as exc:
        refuse(str(exc))
os.close(status_fd)
def end_target(_signum, _frame):
    for kill in (os.killpg, os.kill):  # its own group after new_session, otherwise the child alone
        try:
            kill(child, signal.SIGKILL)
        except OSError:
            pass
for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
    signal.signal(signum, end_target)
code = os.waitstatus_to_exitcode(os.waitpid(child, 0)[1])
if code < 0:
    try:
        signal.signal(-code, signal.SIG_DFL)
    except (OSError, ValueError):
        pass
    os.kill(holder, -code)
os._exit(code if code >= 0 else 128 - code)
"""


def _end(process: subprocess.Popen[bytes], launch: Launch) -> None:
    """Kill a target that ran out of time; with ``acquire_ctty`` its session holder ends it first."""
    if launch.acquire_ctty:
        try:
            os.killpg(process.pid, signal.SIGTERM)  # the holder, and the target unless it left the group
            process.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            pass
    process.kill()


@dataclass
class Result:
    returncode: int
    stdout: bytes
    stderr: bytes
    status: dict[str, Any] = field(default_factory=dict)


def _command(launch: Launch, status_fd: int) -> list[str]:
    if not launch.argv or not os.path.isabs(launch.argv[0]):
        raise ValueError("The target command must be an absolute path")
    cfg: dict[str, Any] = {
        "status_fd": status_fd,
        "argv": launch.argv,
        "drop_caps": launch.drop_caps,
        "landlock": False,
        "seccomp": launch.seccomp,
        "unix_sockets": launch.unix_sockets,
        "new_session": launch.new_session,
        "acquire_ctty": launch.acquire_ctty,
    }
    prefix: list[str] = []
    if launch.policy is not None:
        if sys.platform.startswith("linux"):
            abi = landlock_abi()
            if abi < 1:
                raise ConfinementUnavailable("Landlock is not available in this kernel")
            handled, scoped, rules = launch.policy.landlock_rules(abi)
            cfg.update(landlock=True, abi=abi, min_abi=launch.min_abi, handled_fs=handled, scoped=scoped, rules=rules)
        elif sys.platform == "darwin":
            from babylon60.confine.seatbelt import SANDBOX_EXEC, available, render_profile

            if not available():
                raise ConfinementUnavailable("sandbox-exec is not available")
            prefix = [SANDBOX_EXEC, "-p", render_profile(launch.policy, unix_sockets=launch.unix_sockets)]
        else:
            raise ConfinementUnavailable(f"No confinement backend for {sys.platform}")
    return [*prefix, interpreter(), "-I", "-S", "-B", "-c", TRAMPOLINE.read_text(encoding="utf-8"), json.dumps(cfg)]


def spawn(
    launch: Launch,
    *,
    env: dict[str, str],
    cwd: str,
    stdin: int | IO[Any] | None = subprocess.DEVNULL,
    stdout: int | IO[Any] | None = subprocess.PIPE,
    stderr: int | IO[Any] | None = subprocess.PIPE,
    start_new_session: bool = False,
) -> tuple[subprocess.Popen[bytes], dict[str, Any]]:
    """Start the trampoline and wait until it has exec'd the target or refused."""
    read_fd, write_fd = os.pipe()
    try:
        command = _command(launch, write_fd)
        if launch.acquire_ctty:  # test hook: the session holder owns the terminal; the trampoline is its child
            command = [interpreter(), "-I", "-S", "-B", "-c", CTTY_HOLDER, str(write_fd), *command]
        process = subprocess.Popen(
            command,
            env=env,
            cwd=cwd,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            pass_fds=(write_fd,),
            close_fds=True,
            start_new_session=start_new_session or launch.acquire_ctty,
        )
    except BaseException:
        os.close(read_fd)
        raise
    finally:
        os.close(write_fd)
    with os.fdopen(read_fd, "rb") as status_pipe:
        lines = status_pipe.read().decode("utf-8", "replace").splitlines()
    status: dict[str, Any] = {"ok": False, "error": "trampoline ended without reporting"}
    for line in lines:
        try:
            status = json.loads(line)
        except ValueError:
            continue
    return process, status


def run(
    launch: Launch,
    *,
    env: dict[str, str],
    cwd: str,
    stdin_data: bytes | None = None,
    timeout: float | None = 60,
) -> Result:
    process, status = spawn(
        launch, env=env, cwd=cwd, stdin=subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL
    )
    try:
        stdout, stderr = process.communicate(stdin_data, timeout=timeout)
    except subprocess.TimeoutExpired:
        _end(process, launch)
        stdout, stderr = process.communicate()
        status = {**status, "timeout": True}
    return Result(process.returncode, stdout, stderr, status)
