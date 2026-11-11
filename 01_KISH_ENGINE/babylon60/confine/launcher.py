"""Start a command through the confinement trampoline and read what it applied."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import IO, TYPE_CHECKING, Any

from babylon60.confine.policy import MIN_LANDLOCK_ABI, Policy

if TYPE_CHECKING:
    from babylon60.confine.terminal_proxy import PrivateTerminal

EXIT_REFUSED = 126
TRAMPOLINE = Path(__file__).with_name("_landlock_exec.py")
LINUX = sys.platform.startswith("linux")
PR_SET_CHILD_SUBREAPER = 36
LEFTOVER_GRACE = 1.0  # seconds between SIGTERM and SIGKILL for what the agent leaves behind
LEFTOVER_PATIENCE = 5.0  # then at most this long for SIGKILL to take effect


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
    clipboard: bool = False  # macOS: allow the pasteboard (`run --allow-clipboard`: pasting images into an agent)
    new_session: bool = False  # trampoline starts a new session: no controlling terminal, or ``private_tty``
    acquire_ctty: bool = False  # test hook: stdin becomes the controlling terminal before confinement
    # With new_session: (target descriptor among 0-2, st_rdev) of the private pseudo-terminal slave the launcher
    # passed there; it becomes the controlling terminal and the target runs under a monitor (_landlock_exec.py).
    private_tty: tuple[int, int] | None = None
    default_signals: tuple[str, ...] = ()  # signals the launcher ignores only for itself: SIG_DFL for the target


def session_launch(argv: list[str], policy: Policy, *, unix_sockets: bool = False) -> Launch:
    """The confinement layers of ``babylon60 run``, as the demo and the tests apply them.

    seccomp on Linux; on macOS, where Seatbelt does not filter ioctls, a new
    session without a controlling terminal. ``run_launch`` adds what ``run``
    itself does with the terminal on every platform.
    """
    return Launch(
        argv,
        policy,
        seccomp=sys.platform.startswith("linux"),
        unix_sockets=unix_sockets,
        new_session=sys.platform == "darwin",
    )


def run_launch(
    argv: list[str],
    policy: Policy,
    *,
    unix_sockets: bool = False,
    private_tty: tuple[int, int] | None = None,
    clipboard: bool = False,
) -> Launch:
    """How ``babylon60 run`` starts the agent: ``session_launch`` in a new session, on every platform.

    The agent's controlling terminal is the private pseudo-terminal the launcher
    allocated (``private_tty``, see ``terminal_proxy``), or it has none: it never
    holds the user's terminal.
    """
    launch = session_launch(argv, policy, unix_sockets=unix_sockets)
    launch.new_session, launch.private_tty, launch.clipboard = True, private_tty, clipboard
    return launch


FORWARDED_SIGNALS = ("SIGINT", "SIGTERM", "SIGHUP", "SIGQUIT", "SIGWINCH")


def ignored_signals() -> frozenset[int]:
    """Signals inherited as ignored (``nohup``, a background job): left alone; the target keeps them ignored."""
    names = (*FORWARDED_SIGNALS, "SIGTSTP")
    return frozenset(
        getattr(signal, name) for name in names if signal.getsignal(getattr(signal, name)) == signal.SIG_IGN
    )


@contextmanager
def forward_signals(process: subprocess.Popen[Any], *, ignored: Iterable[int] = ()) -> Iterator[None]:
    """Relay terminal signals to a target started with ``new_session`` and no terminal (``run`` without a tty).

    Such a target leads its own session and process group, so the terminal no
    longer signals it: Ctrl-C, Ctrl-\\, hangups and window resizes reach only this
    launcher. While the context is active, SIGINT, SIGTERM, SIGHUP, SIGQUIT and
    SIGWINCH go to the target's whole process group. SIGTSTP stops that group
    with SIGSTOP (the kernel discards SIGTSTP in an orphaned process group, which
    the target's group is) and then stops this launcher, so the shell gets the
    terminal back; SIGCONT continues the group. Signals in ``ignored`` (see
    ``ignored_signals``) keep their disposition. Previous handlers come back on exit.
    With a terminal, ``terminal_proxy.relay`` does this job.
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
    for signum in ignored:
        handlers.pop(signum, None)
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
    if launch.private_tty is not None and (not launch.new_session or launch.acquire_ctty):
        raise ValueError("private_tty needs new_session and excludes acquire_ctty")
    cfg: dict[str, Any] = {
        "status_fd": status_fd,
        "argv": launch.argv,
        "drop_caps": launch.drop_caps,
        "landlock": False,
        "seccomp": launch.seccomp,
        "unix_sockets": launch.unix_sockets,
        "new_session": launch.new_session,
        "acquire_ctty": launch.acquire_ctty,
        "default_signals": list(launch.default_signals),
    }
    if launch.private_tty is not None:
        fd, rdev = launch.private_tty
        cfg["private_tty"] = {"fd": fd, "rdev": rdev}
    prefix: list[str] = []
    if launch.policy is not None:
        if sys.platform.startswith("linux"):
            abi = landlock_abi()
            if abi < 1:
                raise ConfinementUnavailable("Landlock is not available in this kernel")
            handled, scoped, rules = launch.policy.landlock_rules(abi)
            cfg.update(landlock=True, abi=abi, min_abi=launch.min_abi, handled_fs=handled, scoped=scoped, rules=rules)
        elif sys.platform == "darwin":
            from babylon60.confine.seatbelt import SANDBOX_EXEC, available, render_profile, shared_read_roots

            if not available():
                raise ConfinementUnavailable("sandbox-exec is not available")
            profile = render_profile(
                launch.policy,
                unix_sockets=launch.unix_sockets,
                clipboard=launch.clipboard,
                shared_roots=shared_read_roots(),
            )
            prefix = [SANDBOX_EXEC, "-p", profile]
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
    stdin: int | None = None,
) -> Result:
    """``stdin``: a descriptor for the target's standard input, such as a pty slave with ``acquire_ctty``."""
    if stdin is not None and stdin_data is not None:
        raise ValueError("Pass stdin or stdin_data, not both")
    if stdin is None:
        stdin = subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL
    process, status = spawn(launch, env=env, cwd=cwd, stdin=stdin)
    try:
        stdout, stderr = process.communicate(stdin_data, timeout=timeout)
    except subprocess.TimeoutExpired:
        _end(process, launch)
        stdout, stderr = process.communicate()
        status = {**status, "timeout": True}
    return Result(process.returncode, stdout, stderr, status)


# --- what a session leaves behind ------------------------------------------------------------------


def become_subreaper(enable: bool = True) -> bool:
    """Linux: orphaned descendants are reparented to this process, not to init (``PR_SET_CHILD_SUBREAPER``).

    ``end_descendants`` then reaches everything the session started, double-forked
    and ``setsid`` daemons included. Returns whether the attribute is now set.
    """
    if not LINUX:
        return False
    libc = ctypes.CDLL(None, use_errno=True)
    return libc.prctl(PR_SET_CHILD_SUBREAPER, int(enable), 0, 0, 0) == 0 and enable


def wait_reaping(process: subprocess.Popen[Any]) -> int:
    """Wait for ``process``; meanwhile reap the orphans a subreaper inherits, so none piles up as a zombie."""
    while process.returncode is None:
        try:
            pid, status = os.waitpid(-1, 0)
        except ChildProcessError:
            return process.wait()
        if pid == process.pid:
            process.returncode = os.waitstatus_to_exitcode(status)
    return process.returncode


def reap(process: subprocess.Popen[Any] | None = None) -> None:
    """Reap every child that has exited, recording the status of ``process`` if it is one of them."""
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        if pid == 0:
            return
        if process is not None and pid == process.pid and process.returncode is None:
            process.returncode = os.waitstatus_to_exitcode(status)


def _proc_stat(pid: int) -> tuple[int, int, str] | None:
    """(parent pid, start time, state) from ``/proc/<pid>/stat``; None once the process is gone."""
    try:
        with open(f"/proc/{pid}/stat", "rb") as handle:
            fields = handle.read().rsplit(b")", 1)[1].split()
        return int(fields[1]), int(fields[19]), fields[0].decode("ascii", "replace")
    except (OSError, IndexError, ValueError):
        return None


def descendants() -> dict[int, int]:
    """Linux: the living descendants of this process, ``{pid: start time}``."""
    table: dict[int, tuple[int, int, str]] = {}
    for name in os.listdir("/proc"):
        entry = _proc_stat(int(name)) if name.isdigit() else None
        if entry is not None:
            table[int(name)] = entry
    children: dict[int, list[int]] = {}
    for pid, (ppid, _start, _state) in table.items():
        children.setdefault(ppid, []).append(pid)
    found: dict[int, int] = {}
    pending = list(children.get(os.getpid(), ()))
    while pending:
        pid = pending.pop()
        _ppid, start, state = table[pid]
        if state != "Z":
            found[pid] = start
        pending.extend(children.get(pid, ()))
    return found


def _signal(pid: int, start: int, signum: int) -> None:
    """Signal ``pid`` only while it is the process that started at ``start``: through a pidfd, never a reused pid."""
    try:
        handle: int | None = os.pidfd_open(pid)
    except OSError:
        handle = None  # gone, or a kernel without pidfd: the start time still guards most of the window
    try:
        entry = _proc_stat(pid)
        if entry is None or entry[1] != start:
            return
        if handle is not None:
            signal.pidfd_send_signal(handle, signum)
        else:
            os.kill(pid, signum)
    except OSError:
        pass
    finally:
        if handle is not None:
            os.close(handle)


def end_descendants(
    process: subprocess.Popen[Any] | None = None, *, grace: float = LEFTOVER_GRACE, patience: float = LEFTOVER_PATIENCE
) -> int:
    """Linux, as a subreaper: end every remaining descendant and reap it; return how many were running.

    SIGTERM (and SIGCONT, for stopped ones) first, then SIGKILL for whatever is
    left after ``grace`` seconds, until none remains or ``patience`` runs out.
    """
    if not LINUX:
        return 0
    reap(process)
    found = descendants()
    seen = dict(found)
    for pid, start in found.items():
        _signal(pid, start, signal.SIGTERM)
        _signal(pid, start, signal.SIGCONT)
    deadline = time.monotonic() + grace
    while found and time.monotonic() < deadline:
        time.sleep(0.02)
        reap(process)
        found = descendants()
        seen.update(found)
    deadline = time.monotonic() + patience
    while found and time.monotonic() < deadline:
        for pid, start in found.items():
            _signal(pid, start, signal.SIGKILL)
        time.sleep(0.01)
        reap(process)
        found = descendants()
        seen.update(found)
    reap(process)
    return len(seen)


def end_process_group(pgid: int, *, grace: float = LEFTOVER_GRACE) -> None:
    """Without a subreaper (macOS): SIGTERM the group ``pgid``, SIGKILL it if anything is left after ``grace``."""
    try:
        os.killpg(pgid, signal.SIGTERM)
        os.killpg(pgid, signal.SIGCONT)
    except OSError:
        return
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        try:
            os.killpg(pgid, 0)
        except OSError:
            return
        time.sleep(0.02)
    try:
        os.killpg(pgid, signal.SIGKILL)
    except OSError:
        pass


def end_session(process: subprocess.Popen[Any], agent_pgid: int | None) -> int | None:
    """End what the agent left running once its session is over; return how many (Linux) or None.

    Linux: every descendant, found through the subreaper. macOS has no
    subreaper: the agent's process group (and the monitor, if it still runs)
    is ended, and a descendant that left that group (``setsid``, ``setpgid``)
    survives the session, still confined (declared limit).
    """
    if LINUX:
        count: int | None = end_descendants(process)
    else:
        count = None
        groups = [agent_pgid] if agent_pgid else []
        if process.poll() is None:
            groups.append(process.pid)  # not reaped yet, so its process group id cannot have been reused
        for group in groups:
            end_process_group(group)
    if process.returncode is None:
        try:
            process.wait(timeout=LEFTOVER_PATIENCE)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    return count


@dataclass
class Session:
    returncode: int  # the agent's, as Popen reports it (-n: killed by signal n)
    ended_by: int | None  # SIGTERM or SIGHUP sent to the launcher ended the session early
    leftovers: int | None  # descendants still running when it ended (Linux), all ended; None elsewhere

    @property
    def exit_code(self) -> int:
        """What ``run`` exits with: the agent's code, or 128 + n for signal n, as a shell reports it."""
        if self.ended_by:
            return 128 + self.ended_by
        return self.returncode if self.returncode >= 0 else 128 - self.returncode


def supervise(
    process: subprocess.Popen[Any],
    status: dict[str, Any],
    terminal: PrivateTerminal | None,
    *,
    ignored: Iterable[int] = (),
) -> Session:
    """Wait for the agent's session started by ``spawn``, then end everything it left behind.

    With a terminal, relay it through the private one (``terminal_proxy.relay``)
    and hang that up when the session ends; without one, relay signals to the
    agent's group (``forward_signals``). Either way ``end_session`` has ended the
    agent's leftovers before this returns, so nothing the agent started can
    change files after the caller's after-session checks.
    """
    from babylon60.confine import terminal_proxy

    ended_by: int | None = None
    agent_pgid = status.get("pid")
    try:
        if terminal is not None:
            ended_by = terminal_proxy.relay(process, terminal, agent_pgid=agent_pgid, ignored=ignored)
        else:
            with forward_signals(process, ignored=ignored):
                wait_reaping(process)
    finally:
        if terminal is not None:
            terminal.close()  # the slave hangs up: a process left behind holds a dead terminal
        leftovers = end_session(process, agent_pgid)
    returncode = process.returncode
    assert returncode is not None
    return Session(returncode, ended_by, leftovers)
