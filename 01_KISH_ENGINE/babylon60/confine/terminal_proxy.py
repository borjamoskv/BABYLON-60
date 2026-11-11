"""A private pseudo-terminal between the user's terminal and a confined agent.

When any of descriptors 0-2 of ``babylon60 run`` is a terminal, the agent gets
no descriptor to that terminal and never has it as its controlling terminal.
``PrivateTerminal.open`` allocates a pseudo-terminal pair with the user's modes
and window size. The agent's terminal descriptors (only those that were
terminals; pipes and files pass through unchanged) become the slave, which the
trampoline makes the controlling terminal of the agent's new session
(``Launch.private_tty``). ``relay`` then carries bytes between the user's
terminal and the master, as sudo's ``use_pty`` and ``script(1)`` do:

* while this process has the user's terminal in the foreground, that terminal
  is in raw mode: Ctrl-C, Ctrl-Z, Ctrl-D and every other byte reach the private
  terminal, whose line discipline, with the user's own modes, echoes, edits
  lines and signals the agent's foreground process group. Output processing
  (``ONLCR``) happens there too, once, so the user's terminal receives the same
  bytes as without the relay. The user's modes come back on every way out,
  exceptions and handled signals included (SIGKILL cannot be handled);
* with standard input redirected from a file or a device (stdout or stderr on
  the terminal), the user's terminal is still read, so a ``/dev/tty`` prompt
  such as an ssh passphrase works, but raw mode keeps ISIG: Ctrl-C, Ctrl-Z and
  Ctrl-\\ signal this job and this process relays them. In a pipeline (standard
  input or output a pipe or a socket) the terminal is neither read nor put in
  raw mode, as sudo does: another process of the job, a pager for instance,
  may be using it; output and keyboard signals are still relayed;
* the window size is pushed when the session starts, on SIGWINCH and on SIGCONT;
* when the agent stops (Ctrl-Z), its queued output is shown, the user's modes
  are restored and this process stops itself with SIGTSTP, so the shell gets
  its terminal back; once continued it re-enters raw mode (in the foreground),
  pushes the window size and continues the agent;
* SIGINT, SIGQUIT and SIGTSTP sent to this process go to the private terminal's
  foreground group; SIGTERM and SIGHUP end the session;
* when the agent exits, the output it left queued is drained; the caller then
  closes the master, so the slave hangs up: whatever the agent left behind
  holds a dead terminal, never the user's, and nothing typed afterwards reaches it.

Signals this process inherited as ignored (``launcher.ignored_signals``) are
neither relayed nor acted upon. ``relay`` must run in the main thread.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import errno
import fcntl
import os
import select
import signal
import stat
import subprocess
import termios
import time
from typing import Any

from babylon60.confine.terminals import STDIO, session_ttys

CHUNK = 1 << 14
BACKLOG = 1 << 18  # bytes held for one side before reading from the other pauses
DRAIN_SECONDS = 2.0  # reading what an exited agent left queued stops after this long (a leftover may keep writing)
FORWARDED = ("SIGINT", "SIGQUIT", "SIGTSTP")
ENDING = ("SIGTERM", "SIGHUP")
WATCHED = ("SIGCHLD", "SIGWINCH", "SIGCONT")
GONE = (errno.EIO, errno.ENXIO, errno.EBADF, errno.EPIPE, errno.ENOTTY)  # a hung-up or revoked terminal
ACCESS_MODE = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
WINSIZE = b"\0" * 8  # struct winsize: rows, columns, x and y pixels


def terminal_descriptors() -> tuple[int, ...]:
    """Which of descriptors 0-2 are terminals."""
    return tuple(fd for fd in STDIO if os.isatty(fd))


def _model(stdio: tuple[int, ...]) -> int:
    """The user's terminal descriptor the private terminal copies: the output terminal, else standard input."""
    return next(fd for fd in (1, 2, 0) if fd in stdio)


def _copy_size(source: int, target: int) -> None:
    try:
        fcntl.ioctl(target, termios.TIOCSWINSZ, fcntl.ioctl(source, termios.TIOCGWINSZ, WINSIZE))
    except OSError:
        pass


def raw_mode(mode: list[Any], *, keyboard_signals: bool = False) -> list[Any]:
    """``cfmakeraw`` (``tty.cfmakeraw`` is 3.12+): no input or output processing, no echo, one byte at a time.

    ``keyboard_signals`` keeps ISIG, so Ctrl-C, Ctrl-Z and Ctrl-\\ still signal this process's job.
    """
    raw = [*mode[:6], list(mode[6])]
    raw[0] &= ~(
        termios.IGNBRK
        | termios.BRKINT
        | termios.PARMRK
        | termios.ISTRIP
        | termios.INLCR
        | termios.IGNCR
        | termios.ICRNL
        | termios.IXON
    )
    raw[1] &= ~termios.OPOST
    raw[2] = (raw[2] & ~(termios.CSIZE | termios.PARENB)) | termios.CS8
    raw[3] &= ~(
        termios.ECHO | termios.ECHONL | termios.ICANON | termios.IEXTEN | (0 if keyboard_signals else termios.ISIG)
    )
    raw[6][termios.VMIN] = 1
    raw[6][termios.VTIME] = 0
    return raw


@dataclass
class PrivateTerminal:
    master: int
    slave: int
    rdev: int
    stdio: tuple[int, ...]  # this process's descriptors among 0-2 that are terminals: the agent gets the slave there
    name: str | None  # path of the slave beneath /dev, granted so that the agent can reopen its own terminal

    @classmethod
    def open(cls) -> PrivateTerminal | None:
        """A pseudo-terminal with the modes and window size of the user's terminal; None when 0-2 hold none."""
        stdio = terminal_descriptors()
        if not stdio:
            return None
        master, slave = os.openpty()
        try:
            model = _model(stdio)
            try:
                termios.tcsetattr(slave, termios.TCSANOW, termios.tcgetattr(model))
            except termios.error:
                pass
            _copy_size(model, master)
            names = session_ttys((slave,))
            return cls(master, slave, os.fstat(slave).st_rdev, stdio, names[0] if names else None)
        except BaseException:
            os.close(master)
            os.close(slave)
            raise

    @property
    def private_tty(self) -> tuple[int, int]:
        """``Launch.private_tty``: the agent's descriptor that becomes its controlling terminal, and the device."""
        return self.stdio[0], self.rdev

    @property
    def ttys(self) -> list[str]:
        """``build_policy(ttys=...)``: the slave alone, never the user's terminal."""
        return [self.name] if self.name else []

    def agent_stdio(self) -> tuple[int | None, int | None, int | None]:
        """``spawn``'s stdin, stdout and stderr: the slave where this process has a terminal, else inherited."""
        stdin, stdout, stderr = (self.slave if fd in self.stdio else None for fd in STDIO)
        return stdin, stdout, stderr

    def close(self) -> None:
        """Close both ends (idempotent): the slave hangs up for every process still holding it."""
        for fd in (self.master, self.slave):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
        self.master = self.slave = -1


def _usable(fd: int, access: int) -> tuple[int | None, bool]:
    """``fd`` itself when it was opened with ``access`` (or read-write), else the same terminal reopened by
    name with ``access`` (only if the name leads to the same device); the flag says it was opened here."""
    if fcntl.fcntl(fd, fcntl.F_GETFL) & ACCESS_MODE in (access, os.O_RDWR):
        return fd, False
    try:
        reopened = os.open(os.ttyname(fd), access | os.O_NOCTTY | os.O_CLOEXEC)
    except OSError:
        return None, False
    if os.fstat(reopened).st_rdev == os.fstat(fd).st_rdev:
        return reopened, True
    os.close(reopened)
    return None, False


def _writer(stdio: tuple[int, ...]) -> tuple[int | None, bool]:
    """Where the private terminal's output goes: the user's output terminal, else standard input's terminal
    (echo and ``/dev/tty`` prompts, such as a passphrase)."""
    for fd in (1, 2):
        if fd in stdio:
            return fd, False
    return _usable(0, os.O_WRONLY)


def _reader(stdio: tuple[int, ...]) -> tuple[int | None, bool]:
    """The user's terminal as input: standard input, else the output terminal, as sudo's ``use_pty`` reads it.

    With standard input redirected, what the agent reads from ``/dev/tty`` (a
    passphrase prompt) still comes from the user's keyboard. In a pipeline
    (standard input or output a pipe or a socket), as sudo does, the terminal is
    neither read nor put in raw mode: another process of the job, such as a pager
    (``run -- git log | less``), may be using it.
    """
    for fd in (0, 1):
        try:
            mode = os.fstat(fd).st_mode
        except OSError:
            continue
        if stat.S_ISFIFO(mode) or stat.S_ISSOCK(mode):
            return None, False
    if 0 in stdio:
        return 0, False
    return _usable(next(fd for fd in (1, 2) if fd in stdio), os.O_RDONLY)


class _Relay:
    def __init__(
        self, process: subprocess.Popen[Any], terminal: PrivateTerminal, agent_pgid: int | None, ignored: Iterable[int]
    ) -> None:
        self.process = process  # the trampoline: the monitor that leads the agent's session
        self.terminal = terminal
        self.agent_pgid = agent_pgid if agent_pgid and agent_pgid > 0 else process.pid
        self.ignored = frozenset(ignored)
        self.output, self.own_output = _writer(terminal.stdio)
        self.input, self.own_input = _reader(terminal.stdio)
        # stdin redirected: in raw mode, the keyboard's signals keep signalling this process's job.
        self.keyboard_signals = 0 not in terminal.stdio
        self.model = _model(terminal.stdio)
        self.saved: list[Any] | None = None  # the user's modes while raw mode is on
        self.to_agent = bytearray()
        self.to_user = bytearray()
        self.input_open = self.input is not None
        self.output_open = self.output is not None
        self.master_open = True
        self.pending: list[int] = []
        self.ended_by: int | None = None

    def run(self) -> None:
        wake_read, wake_write = os.pipe()
        previous: dict[int, Any] = {}
        old_wakeup = -1
        try:
            for fd in (wake_read, wake_write, self.terminal.master):
                os.set_blocking(fd, False)
            old_wakeup = signal.set_wakeup_fd(wake_write, warn_on_full_buffer=False)
            for name in (*FORWARDED, *ENDING, *WATCHED):
                signum = getattr(signal, name)
                if name in WATCHED or signum not in self.ignored:
                    previous[signum] = signal.signal(signum, self._record)
            self._resume()
            while self.process.returncode is None and self.ended_by is None:
                self._step(wake_read)
            if self.ended_by is None:
                self._drain(time.monotonic() + DRAIN_SECONDS)
        finally:
            self._cooked()
            for signum, handler in previous.items():
                signal.signal(signum, signal.SIG_DFL if handler is None else handler)
            signal.set_wakeup_fd(old_wakeup)
            os.close(wake_read)
            os.close(wake_write)
            for opened, own in ((self.output, self.own_output), (self.input, self.own_input)):
                if own and opened is not None:
                    os.close(opened)

    def _record(self, signum: int, _frame: object) -> None:
        self.pending.append(signum)

    def _step(self, wake_read: int) -> None:
        self._reap()
        self._dispatch()
        if self.process.returncode is not None or self.ended_by is not None:
            return
        master = self.terminal.master
        foreground = self._foreground()
        if foreground and self.saved is None:
            self._raw()
        readers = [wake_read]
        if self.master_open and len(self.to_user) < BACKLOG:
            readers.append(master)
        if self.input is not None and self.input_open and foreground and len(self.to_agent) < BACKLOG:
            readers.append(self.input)
        writers = []
        if self.output is not None and self.output_open and self.to_user:
            writers.append(self.output)
        if self.master_open and self.to_agent:
            writers.append(master)
        readable, writable, _ = select.select(readers, writers, [], 1.0)
        if wake_read in readable:
            try:
                while os.read(wake_read, 512):
                    pass
            except BlockingIOError:
                pass
        if master in readable:
            self._from_agent()
        self._reap()
        if self.process.returncode is not None:
            return  # nothing read from the user from now on goes to an agent that is gone
        if self.input is not None and self.input in readable:
            self._from_user()
        if master in writable:
            self._to_agent()
        if self.output is not None and self.output in writable:
            self._to_user()

    def _dispatch(self) -> None:
        while self.pending:
            signum = self.pending.pop(0)
            if signum == signal.SIGWINCH:
                _copy_size(self.model, self.terminal.master)
            elif signum == signal.SIGCONT:
                self._resume()
            elif signum in (signal.SIGTERM, signal.SIGHUP):
                self.ended_by = signum
            elif signum in (signal.SIGINT, signal.SIGQUIT, signal.SIGTSTP):
                self._forward(signum)

    def _forward(self, signum: int) -> None:
        """Signal the private terminal's foreground group, as the key would; else the agent's own group."""
        group = self.agent_pgid
        try:
            foreground = os.tcgetpgrp(self.terminal.master)  # Linux answers on the master; macOS does not
            if foreground > 0 and os.getsid(foreground) == self.process.pid:
                group = foreground
        except OSError:
            pass
        try:
            os.killpg(group, signum)
        except OSError:
            pass

    def _reap(self) -> None:
        while self.process.returncode is None:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG | os.WUNTRACED)
            except ChildProcessError:
                return
            if pid == 0:
                return
            if pid != self.process.pid:
                continue  # an orphan reparented to this subreaper: reaped
            if os.WIFSTOPPED(status):
                self._suspend()
            else:
                self.process.returncode = os.waitstatus_to_exitcode(status)

    def _suspend(self) -> None:
        """The agent stopped (Ctrl-Z): show its last output, give the shell its terminal back and stop likewise."""
        self._drain(time.monotonic() + 0.5)
        self._cooked()
        if signal.SIGTSTP not in self.ignored:
            handler = signal.signal(signal.SIGTSTP, signal.SIG_DFL)
            try:
                os.kill(os.getpid(), signal.SIGTSTP)  # returns once continued; at once if this group is orphaned
            finally:
                signal.signal(signal.SIGTSTP, handler)
        self._resume()
        try:
            os.kill(self.process.pid, signal.SIGCONT)  # the monitor continues the agent's group
        except ProcessLookupError:
            pass

    def _resume(self) -> None:
        if self._foreground():
            self._raw()
        _copy_size(self.model, self.terminal.master)

    def _foreground(self) -> bool:
        """Whether this process may use the user's terminal as input: it is in its foreground group."""
        if self.input is None:
            return False
        try:
            return os.tcgetpgrp(self.input) == os.getpgrp()
        except OSError:
            return True  # not this process's controlling terminal: job control does not apply to it

    def _raw(self) -> None:
        if self.input is None:
            return
        try:
            if self.saved is None:
                self.saved = termios.tcgetattr(self.input)
            termios.tcsetattr(self.input, termios.TCSANOW, raw_mode(self.saved, keyboard_signals=self.keyboard_signals))
        except (termios.error, OSError):
            self.saved = None

    def _cooked(self) -> None:
        """The user's modes back, also from the background: SIGTTOU is blocked meanwhile."""
        if self.saved is None or self.input is None:
            return
        saved, self.saved = self.saved, None
        mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTTOU})
        try:
            termios.tcsetattr(self.input, termios.TCSADRAIN, saved)
        except (termios.error, OSError):
            pass
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, mask)

    def _from_agent(self) -> None:
        try:
            data = os.read(self.terminal.master, CHUNK)
        except BlockingIOError:
            return
        except OSError as exc:
            if exc.errno not in GONE:
                raise
            data = b""
        if not data:  # the slave was revoked (macOS, when the monitor exits); never while this process holds it
            self.master_open = False
        elif self.output_open:
            self.to_user += data

    def _from_user(self) -> None:
        assert self.input is not None
        try:
            data = os.read(self.input, CHUNK)
        except BlockingIOError:
            return
        except OSError as exc:
            if exc.errno not in GONE:
                raise
            data = b""
        if data:
            self.to_agent += data
            return
        self.input_open = False  # the user's terminal hung up: end of input for the agent
        try:
            mode = termios.tcgetattr(self.terminal.slave)
        except termios.error:
            return
        if mode[3] & termios.ICANON:
            eof = mode[6][termios.VEOF]
            self.to_agent += eof if isinstance(eof, bytes) else bytes([eof])

    def _to_agent(self) -> None:
        try:
            written = os.write(self.terminal.master, self.to_agent[:CHUNK])
        except BlockingIOError:
            return
        except OSError as exc:
            if exc.errno not in GONE:
                raise
            self.master_open = False
            self.to_agent.clear()
            return
        del self.to_agent[:written]

    def _to_user(self) -> None:
        assert self.output is not None
        try:
            written = os.write(self.output, self.to_user[:CHUNK])
        except BlockingIOError:
            return
        except OSError as exc:
            if exc.errno not in GONE:
                raise
            self.output_open = False  # the user's terminal is gone: what the agent prints is dropped
            self.to_user.clear()
            return
        del self.to_user[:written]

    def _drain(self, deadline: float) -> None:
        """Read what the agent left queued in the private terminal and write it out, until ``deadline``."""
        while self.master_open and time.monotonic() < deadline:
            before = len(self.to_user)
            self._from_agent()
            if len(self.to_user) == before:
                break  # nothing more queued (or the output is gone)
            self._flush(deadline)
        self._flush(deadline)

    def _flush(self, deadline: float) -> None:
        while self.output is not None and self.output_open and self.to_user and time.monotonic() < deadline:
            select.select([], [self.output], [], max(0.0, deadline - time.monotonic()))
            self._to_user()


def relay(
    process: subprocess.Popen[Any],
    terminal: PrivateTerminal,
    *,
    agent_pgid: int | None = None,
    ignored: Iterable[int] = (),
) -> int | None:
    """Relay the user's terminal until the agent's session ends; return SIGTERM or SIGHUP if one ended it.

    ``process`` is the trampoline, which monitors the agent's session (its exit
    status, the agent's, lands in ``process.returncode``); ``agent_pgid`` is the
    agent's process group, reported by the trampoline. When a signal ends the
    session early the agent may still run: the caller closes ``terminal``, which
    hangs it up, and ends what is left (``launcher.end_session``).
    """
    session = _Relay(process, terminal, agent_pgid, ignored)
    session.run()
    return session.ended_by
