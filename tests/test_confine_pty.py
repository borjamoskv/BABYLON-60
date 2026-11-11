"""``babylon60 run`` and the user's terminal: a private pseudo-terminal in between, real ptys throughout.

A pseudo-terminal pair plays the user's terminal: the test reads its master as a
terminal emulator would and types into it. A "user shell" (a separate process)
leads a session that owns that terminal and runs the real CLI
(``python -m babylon60.cli.main_dispatcher run ...``) as a foreground job in a
process group of its own, as an interactive shell does: it hands the job the
terminal, waits for it (stops included), takes the terminal back and can then
read what the user typed afterwards.

Every guarantee is paired with a control that runs the same probe as the job
without ``babylon60 run`` and shows the effect there; a control without the
effect fails the test on Linux and skips it elsewhere (not falsifiable).

Set BABYLON60_REQUIRE_LANDLOCK=1 (CI) to fail instead of skipping when Landlock is missing.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
import fcntl
import json
import os
from pathlib import Path
import secrets
import select
import shlex
import signal
import stat
import struct
import subprocess
import sys
import termios
import threading
import time
import tty
from typing import Any

import pytest

from babylon60.confine import launcher
from babylon60.confine.launcher import Launch, interpreter, spawn
from babylon60.confine.policy import default_homes

ROOT = Path(__file__).absolute().parents[1]
LINUX = sys.platform.startswith("linux")
REQUIRED = os.environ.get("BABYLON60_REQUIRE_LANDLOCK") == "1"
needs_backend = pytest.mark.skipif(
    launcher.backend() == "none" and not (LINUX and REQUIRED), reason="no confinement backend here"
)
linux_only = pytest.mark.skipif(
    not LINUX,
    reason="macOS has no subreaper: a descendant that leaves the agent's process group outlives the session "
    "(declared limit); Linux ends every descendant",
)

# The user's shell: owns the terminal, runs the job in the foreground and records how it ended.
SHELL = r"""
import fcntl, json, os, signal, subprocess, sys, termios, time
cfg = json.loads(sys.argv[1])
here = cfg["dir"]


def mark(name, payload):
    path = os.path.join(here, name)
    with open(path + ".tmp", "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    os.replace(path + ".tmp", path)


def wait_for(name):
    deadline = time.monotonic() + 120
    while not os.path.exists(os.path.join(here, name)):
        if time.monotonic() > deadline:
            raise SystemExit("user shell: no " + name)
        time.sleep(0.01)


def foreground(pgrp):
    # A job-control shell ignores SIGTTOU; blocking it has the same effect and exec does not inherit it here.
    signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTTOU})
    try:
        os.tcsetpgrp(terminal, pgrp)
    finally:
        signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTTOU})


def modes():
    mode = termios.tcgetattr(terminal)
    return {"icanon": bool(mode[3] & termios.ICANON), "echo": bool(mode[3] & termios.ECHO),
            "isig": bool(mode[3] & termios.ISIG), "opost": bool(mode[1] & termios.OPOST)}


terminal = os.dup(0)
fcntl.ioctl(terminal, termios.TIOCSCTTY, 0)
shell = os.getpgrp()


def enter_job():
    os.setpgid(0, 0)
    foreground(os.getpgrp())


streams = {}
for name, mode in (("stdin", "rb"), ("stdout", "wb"), ("stderr", "wb")):
    if cfg.get(name):
        streams[name] = open(cfg[name], mode)
job = subprocess.Popen(cfg["job"], cwd=cfg["cwd"], env=cfg["env"], preexec_fn=enter_job, **streams)
foreground(job.pid)
mark("job", {"pid": job.pid})
stops = []
while True:
    _, status = os.waitpid(job.pid, os.WUNTRACED)
    if not os.WIFSTOPPED(status):
        break
    foreground(shell)
    stops.append({"signal": os.WSTOPSIG(status), "modes": modes()})
    mark(f"stopped-{len(stops)}", stops[-1])
    wait_for(f"fg-{len(stops)}")
    foreground(job.pid)
    os.killpg(job.pid, signal.SIGCONT)
job.returncode = os.waitstatus_to_exitcode(status)
foreground(shell)
result = {"exit": job.returncode, "stops": stops, "modes": modes()}
mark("done", result)
if cfg.get("read_typed"):
    wait_for("typed")
    time.sleep(cfg["settle"])  # anything still waiting for the user's input has had its chance
    foreground(shell)  # as a shell does before it reads the next command
    os.set_blocking(terminal, False)
    typed = b""
    try:
        while chunk := os.read(terminal, 4096):
            typed += chunk
    except OSError:
        pass
    result["typed"] = typed.decode("latin-1")
mark("result", result)
"""


class Screen(threading.Thread):
    """Reads the user's terminal on the master side, as a terminal emulator would, until it closes."""

    def __init__(self, master: int) -> None:
        super().__init__(daemon=True)
        self.master = master
        self.data = bytearray()
        self.lock = threading.Lock()
        self.halt = threading.Event()

    def run(self) -> None:
        while not self.halt.is_set():
            try:
                ready, _, _ = select.select([self.master], [], [], 0.05)
                chunk = os.read(self.master, 1 << 16) if ready else None
            except OSError:  # EIO once nobody holds the slave (Linux)
                return
            if chunk == b"":
                return
            if chunk:
                with self.lock:
                    self.data += chunk

    def text(self) -> bytes:
        with self.lock:
            return bytes(self.data)

    def wait_for(self, needle: bytes, timeout: float = 60) -> None:
        deadline = time.monotonic() + timeout
        while needle not in self.text():
            assert time.monotonic() < deadline, f"no {needle!r} on the screen: {self.text()[-400:]!r}"
            time.sleep(0.01)


Interact = Callable[[Screen, int, Path], None]  # (screen, user terminal master, shell's directory)


@dataclass
class Session:
    result: dict[str, Any]
    screen: bytes


@dataclass
class Box:
    home: Path
    ws: Path
    journal: Path
    tmp: Path

    def env(self) -> dict[str, str]:
        return {**os.environ, "HOME": str(self.home), "PYTHONPATH": str(ROOT / "01_KISH_ENGINE"), "LC_ALL": "C"}

    def cli(self, *argv: str) -> list[str]:
        """``babylon60 run -- argv``."""
        run = [sys.executable, "-m", "babylon60.cli.main_dispatcher", "run", "--allow-root"]
        return [*run, "--journal", str(self.journal), "--", *argv]

    def run_without_terminal(self, *argv: str) -> subprocess.CompletedProcess[bytes]:
        """``babylon60 run`` with stdin, stdout and stderr off any terminal."""
        return subprocess.run(
            self.cli(*argv),
            env=self.env(),
            cwd=str(self.ws),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=180,
        )

    def journal_entries(self, kind: str) -> list[dict[str, Any]]:
        log = subprocess.run(
            [sys.executable, "-m", "babylon60.cli.main_dispatcher", "log", "--journal", str(self.journal), "--json"],
            env=self.env(),
            capture_output=True,
            text=True,
            timeout=60,
        )
        return [entry["body"] for entry in json.loads(log.stdout)["entries"] if entry["kind"] == kind]

    def session(
        self,
        job: list[str] | Callable[[str, int], list[str]],
        interact: Interact | None = None,
        *,
        raw: bool = False,
        size: tuple[int, int] = (24, 80),
        read_typed: bool = False,
        settle: float = 1.0,
        **redirects: str,
    ) -> Session:
        """Run ``job`` in the foreground of a fresh user terminal while ``interact`` plays the user.

        ``job`` may be built from the user's terminal (its path and device number).
        ``redirects``: files for the job's stdin, stdout or stderr instead of the terminal.
        """
        here = self.tmp / f"shell-{secrets.token_hex(4)}"
        here.mkdir()
        master, slave = os.openpty()
        screen = Screen(master)
        shell: subprocess.Popen[bytes] | None = None
        try:
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", size[0], size[1], 0, 0))
            if raw:
                tty.setraw(slave)
            argv = job(os.ttyname(slave), os.fstat(slave).st_rdev) if callable(job) else job
            cfg = {"dir": str(here), "job": argv, "cwd": str(self.ws), "env": self.env(), "settle": settle}
            cfg.update(read_typed=read_typed, **redirects)
            screen.start()
            shell = subprocess.Popen(
                [sys.executable, "-c", SHELL, json.dumps(cfg)],
                stdin=slave,
                stdout=slave,
                stderr=slave,
                start_new_session=True,
            )
            os.close(slave)
            slave = -1
            if interact is not None:
                interact(screen, master, here)
            shell.wait(timeout=180)
            assert shell.returncode == 0, screen.text()[-2000:]
        finally:
            if shell is not None and shell.poll() is None:
                shell.kill()
                shell.wait()
                _kill_group(here / "job")
            screen.halt.set()
            screen.join(timeout=10)
            for fd in (master, slave):
                if fd >= 0:
                    os.close(fd)
        return Session(json.loads((here / "result").read_text(encoding="utf-8")), screen.text())


def _kill_group(marker: Path) -> None:
    """On failure only: end a job the user shell started."""
    try:
        os.killpg(json.loads(marker.read_text())["pid"], signal.SIGKILL)
    except (OSError, ValueError):
        pass


@pytest.fixture
def box(tmp_path: Path) -> Iterator[Box]:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    (home / ".ssh" / "id_rsa").write_text("B60-CANARY-pty\n")
    ws = tmp_path / "ws"
    ws.mkdir()
    shells = tmp_path / "shells"
    shells.mkdir()
    yield Box(home, ws, tmp_path / "state" / "journal.db", shells)


def _python(source: str, *args: str) -> list[str]:
    return [interpreter(), "-I", "-S", "-c", source, *args]


def _wait_for_file(path: Path, timeout: float = 60) -> None:
    deadline = time.monotonic() + timeout
    while not path.exists():
        assert time.monotonic() < deadline, f"no {path}"
        time.sleep(0.01)


def _alive(pid: int) -> bool:
    """Whether ``pid`` exists and is not a zombie (/proc on Linux, ``ps`` elsewhere)."""
    if LINUX:
        try:
            with open(f"/proc/{pid}/stat", encoding="ascii") as handle:
                return handle.read().rsplit(")", 1)[1].split()[0] != "Z"
        except FileNotFoundError:
            return False
    state = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    return state not in ("", "Z")


def _state(pid: int) -> str:
    if LINUX:
        with open(f"/proc/{pid}/stat", encoding="ascii") as handle:
            return handle.read().rsplit(")", 1)[1].split()[0]
    return subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()[:1]


def _control_holds(holds: bool, what: str) -> None:
    """A control without its effect: a broken test on Linux, not falsifiable elsewhere."""
    if not holds:
        if LINUX:
            pytest.fail(f"control: {what}")
        pytest.skip(f"not falsifiable here: {what}")


def _after_done(then: Callable[[int, Path], None] | None = None) -> Interact:
    """Once the job has ended: optionally type something, then let the shell read its terminal."""

    def interact(_screen: Screen, master: int, here: Path) -> None:
        _wait_for_file(here / "done")
        if then is not None:
            then(master, here)
        (here / "typed").touch()

    return interact


# --- a process left behind never reads what the user types after run --------------------------------

# The agent forks a reader and exits at once. The reader ignores SIGTERM and SIGHUP, waits until the
# shell has its terminal back, prints a fake sudo prompt and reads the next line typed: "tcsetpgrp"
# first makes its group the terminal's foreground group; "setsid" leaves the session and reads the
# terminal descriptor it inherited (stderr, which stays a terminal even when stdin is redirected).
LINGER = r"""
import os, select, signal, sys, time
log_path, mode = sys.argv[1], sys.argv[2]
if os.fork() == 0:
    with open(log_path + ".pid", "w") as handle:
        handle.write(str(os.getpid()))
    for name in ("SIGTERM", "SIGHUP", "SIGTTOU", "SIGTTIN"):
        signal.signal(getattr(signal, name), signal.SIG_IGN)
    if mode == "setsid":
        os.setsid()
    time.sleep(0.8)
    with open(log_path, "w") as log:
        try:
            if mode == "tcsetpgrp":
                fd = os.open("/dev/tty", os.O_RDWR)
                os.tcsetpgrp(fd, os.getpgrp())
            else:
                fd = 2
            os.write(fd, b"\r\n[sudo] password for user: ")
            ready = select.select([fd], [], [], 8)[0]
            log.write("read: %r\n" % (os.read(fd, 200) if ready else b"<nothing>"))
        except OSError as exc:
            log.write("failed: %s\n" % exc)
    os._exit(0)
print("agent exits", flush=True)
"""


def _reader_log(log: Path) -> str:
    """What the reader got, once it has finished or is gone."""
    pidfile = Path(str(log) + ".pid")
    _wait_for_file(pidfile, timeout=30)
    pid = int(pidfile.read_text())
    deadline = time.monotonic() + 15
    while _alive(pid) and time.monotonic() < deadline:
        time.sleep(0.02)
    return log.read_text() if log.exists() else "<no log: ended before it read>"


@needs_backend
@pytest.mark.parametrize("mode", ["tcsetpgrp", "setsid"])
def test_a_process_left_behind_never_reads_what_the_user_types_after_run(box: Box, mode: str) -> None:
    secret = f"hunter2-{secrets.token_hex(4)}".encode()

    def type_secret(master: int, _here: Path) -> None:
        time.sleep(1.5)  # a reader left behind has armed itself by now (it waits 0.8 s)
        os.write(master, secret + b"\r")

    control_log = box.ws / "control.log"
    control = box.session(_python(LINGER, str(control_log), mode), _after_done(type_secret), read_typed=True)
    got = _reader_log(control_log)
    _control_holds(secret in got.encode(), f"the {mode} reader did not get the line without babylon60: {got}")
    assert secret not in control.result["typed"].encode()

    confined_log = box.ws / "confined.log"
    job = box.cli(*_python(LINGER, str(confined_log), mode))
    confined = box.session(job, _after_done(type_secret), read_typed=True)
    got = _reader_log(confined_log)
    assert confined.result["exit"] == 0, confined.screen
    assert secret not in got.encode(), got
    assert secret in confined.result["typed"].encode(), confined.result  # the line reached the user's shell
    assert confined.result["modes"]["icanon"] and confined.result["modes"]["echo"], confined.result


# The launcher's pieces without the teardown of leftovers (macOS has no subreaper; on Linux run also
# ends them): "private" relays through the private terminal and hangs it up; the control hands the
# agent the user's terminal in a detached session, which is what run did before.
NO_TEARDOWN = r"""
import json, sys
from babylon60.confine import launcher
from babylon60.confine.policy import build_policy
from babylon60.confine.terminal_proxy import PrivateTerminal, relay
cfg = json.loads(sys.argv[1])
terminal = PrivateTerminal.open() if cfg["private"] else None
ttys = terminal.ttys if terminal else []
policy = build_policy(cfg["ws"], homes=cfg["homes"], runtime=[launcher.interpreter_prefix()], ttys=ttys)
launch = launcher.run_launch(cfg["argv"], policy, private_tty=terminal.private_tty if terminal else None)
stdin, stdout, stderr = terminal.agent_stdio() if terminal else (None, None, None)
process, status = launcher.spawn(launch, env=cfg["env"], cwd=cfg["ws"], stdin=stdin, stdout=stdout, stderr=stderr)
assert status.get("ok"), status
if terminal:
    relay(process, terminal, agent_pgid=status.get("pid"))
    terminal.close()
else:
    process.wait()
"""


@needs_backend
def test_the_hangup_alone_cuts_off_a_reader_left_behind(box: Box) -> None:
    """A reader that keeps the agent's terminal descriptor, with no teardown: it holds a dead terminal."""
    secret = f"hunter2-{secrets.token_hex(4)}".encode()

    def type_secret(master: int, _here: Path) -> None:
        time.sleep(1.5)
        os.write(master, secret + b"\r")

    def attempt(private: bool, log: Path) -> tuple[Session, str]:
        cfg = {
            "private": private,
            "ws": str(box.ws),
            "homes": [str(box.home), *default_homes()],
            "argv": _python(LINGER, str(log), "setsid"),
            "env": {"PATH": "/usr/bin:/bin", "HOME": str(box.home), "LC_ALL": "C"},
        }
        job = [sys.executable, "-c", NO_TEARDOWN, json.dumps(cfg)]
        return box.session(job, _after_done(type_secret), read_typed=True), _reader_log(log)

    control, got = attempt(False, box.ws / "control.log")
    _control_holds(secret in got.encode(), f"the reader did not get the line through the user's terminal: {got}")
    confined, got = attempt(True, box.ws / "private.log")
    assert confined.result["exit"] == 0, confined.screen
    assert secret not in got.encode() and got.startswith(("failed:", "read: b''")), got
    assert secret in confined.result["typed"].encode(), confined.result


# --- /dev/tty is the private terminal; TIOCSTI never reaches the user's input ------------------------

TERMINAL_PROBE = r"""
import errno, fcntl, json, os, struct, sys, termios
out_path, user_rdev, user_name, marker = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
def attempt(fn):
    try:
        return fn()
    except OSError as exc:
        return errno.errorcode.get(exc.errno, str(exc.errno))
def device(fd):  # the terminal behind a descriptor, also through /dev/tty (Linux TIOCGDEV)
    raw = struct.unpack("I", fcntl.ioctl(fd, 0x80045432, b"\0" * 4))[0]
    return [os.major(raw), os.minor(raw)]
out = {"user": [os.major(user_rdev), os.minor(user_rdev)], "stdio": {}}
for fd in (0, 1, 2):
    if os.isatty(fd):
        out["stdio"][str(fd)] = [os.major(os.fstat(fd).st_rdev), os.minor(os.fstat(fd).st_rdev)]
def ctty():
    fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
    try:
        out["dev_tty"] = device(fd) if sys.platform.startswith("linux") else "open"
        for byte in marker.encode() + b"\n":
            fcntl.ioctl(fd, termios.TIOCSTI, bytes([byte]))
        return "injected"
    finally:
        os.close(fd)
out["tiocsti"] = attempt(ctty)
out["open_user_terminal"] = attempt(lambda: os.close(os.open(user_name, os.O_RDWR | os.O_NOCTTY)) or "ok")
own = next(fd for fd in (1, 2, 0) if os.isatty(fd))
out["reopen_own"] = attempt(lambda: os.close(os.open(os.ttyname(own), os.O_RDWR | os.O_NOCTTY)) or "ok")
with open(out_path, "w") as handle:
    json.dump(out, handle)
"""


@needs_backend
@pytest.mark.parametrize("stdin", ["terminal", "devnull"])
def test_dev_tty_is_the_private_terminal_and_tiocsti_stays_inside(box: Box, stdin: str) -> None:
    """With stdin on the terminal, and redirected (``< /dev/null``) with stdout and stderr still on it."""
    redirects = {"stdin": os.devnull} if stdin == "devnull" else {}
    marker = f"B60-INJECTED-{secrets.token_hex(4)}"

    def attempt(name: str, wrap: Callable[[list[str]], list[str]]) -> tuple[Session, dict[str, Any]]:
        report = box.ws / f"{name}.json"

        def job(user: str, rdev: int) -> list[str]:
            return wrap(_python(TERMINAL_PROBE, str(report), str(rdev), user, marker))

        session = box.session(job, _after_done(), read_typed=True, settle=0.3, **redirects)
        return session, json.loads(report.read_text())

    control, seen = attempt("control", lambda argv: argv)
    if LINUX:
        assert seen["dev_tty"] == seen["user"], seen  # without babylon60, /dev/tty is the user's terminal
    assert seen["open_user_terminal"] == "ok", seen
    injects = marker in control.result["typed"]  # TIOCSTI may be disabled by the kernel: then not falsifiable

    confined, report = attempt("confined", lambda argv: box.cli(*argv))
    assert confined.result["exit"] == 0, confined.screen
    assert marker not in confined.result["typed"], confined.result  # nothing reached the user's input
    assert report["stdio"] and all(dev != report["user"] for dev in report["stdio"].values()), report
    assert ("0" in report["stdio"]) == (stdin == "terminal"), report  # a redirected stdin passes through
    if LINUX:
        assert report["dev_tty"] != report["user"] and report["dev_tty"] in report["stdio"].values(), report
        assert report["tiocsti"] == "EPERM", report  # seccomp; the private terminal would only reach the agent
        assert report["open_user_terminal"] == "EACCES", report
    else:
        assert report["open_user_terminal"] in ("EPERM", "EACCES"), report
    assert report["reopen_own"] == "ok", report  # the private slave is granted by path, not the user's terminal
    start = box.journal_entries("run_start")[-1]
    assert start["terminal"] == "private" and start["new_session"] is True, start
    if not injects:
        pytest.skip(f"TIOCSTI does not inject here even without babylon60 ({seen['tiocsti']}); /dev/tty checked")


# --- nothing the agent starts outlives the session (Linux) --------------------------------------------

DAEMONIZE = r"""
import os, signal, sys, time
pidfile = sys.argv[1]
if os.fork() == 0:
    os.setsid()
    if os.fork() == 0:
        for name in ("SIGTERM", "SIGHUP", "SIGINT"):
            signal.signal(getattr(signal, name), signal.SIG_IGN)
        with open(pidfile + ".tmp", "w") as handle:
            handle.write(str(os.getpid()))
        os.replace(pidfile + ".tmp", pidfile)
        time.sleep(60)
    os._exit(0)
deadline = time.monotonic() + 30
while not os.path.exists(pidfile) and time.monotonic() < deadline:
    time.sleep(0.01)
"""


@linux_only
@needs_backend
@pytest.mark.parametrize("terminal", [True, False], ids=["terminal", "no-terminal"])
def test_a_double_forked_setsid_daemon_is_ended_with_the_session(box: Box, terminal: bool) -> None:
    control_pid = box.ws / "control.pid"
    subprocess.run(_python(DAEMONIZE, str(control_pid)), timeout=60, check=True)
    daemon = int(control_pid.read_text())
    try:
        _control_holds(_alive(daemon), "the daemon did not outlive its parent without babylon60")
    finally:
        os.kill(daemon, signal.SIGKILL)

    pidfile = box.ws / "daemon.pid"
    probe = _python(DAEMONIZE, str(pidfile))
    if terminal:
        assert box.session(box.cli(*probe)).result["exit"] == 0
    else:
        done = box.run_without_terminal(*probe)
        assert done.returncode == 0, done.stderr
    daemon = int(pidfile.read_text())
    assert not _alive(daemon), f"daemon {daemon} outlived babylon60 run"
    end = box.journal_entries("run_end")[-1]
    assert end["leftovers"] >= 1 and end["exit_code"] == 0, end


# The round-2 review's t_delay.sh and t_meta.sh: a write made by a process the agent left behind, after
# the agent exited, used to land after run's hook and metadata checks. Now nothing the agent started
# runs by then. The writer ignores SIGHUP: with a terminal, the kernel would otherwise end it already
# when the private terminal's session leader exits, and the teardown would not be what is tested.
DELAYED = {
    "hook": "(trap '' HUP; sleep 1.5; printf '#!/bin/sh\\necho PWNED\\n' > .git/hooks/pre-commit;"
    " chmod +x .git/hooks/pre-commit) </dev/null >/dev/null 2>&1 & echo agent exits",
    "chmod": '(trap \'\' HUP; sleep 1.5; chmod 755 "$HOME/.ssh"; chmod 644 "$HOME/.ssh/id_rsa")'
    " </dev/null >/dev/null 2>&1 & echo agent exits",
}


def _delayed_effect(box: Box, kind: str) -> bool:
    if kind == "hook":
        return (box.ws / ".git" / "hooks" / "pre-commit").exists()
    modes = (
        stat.S_IMODE(os.stat(box.home / ".ssh").st_mode),
        stat.S_IMODE(os.stat(box.home / ".ssh" / "id_rsa").st_mode),
    )
    return modes != (0o700, 0o600)


@needs_backend
@pytest.mark.parametrize("terminal", [True, False], ids=["terminal", "no-terminal"])
@pytest.mark.parametrize("kind", ["hook", "chmod"])
def test_a_delayed_write_by_a_process_left_behind_never_happens(box: Box, kind: str, terminal: bool) -> None:
    (box.ws / ".git" / "hooks").mkdir(parents=True)
    (box.ws / ".git" / "config").write_text("[core]\n\tbare = false\n")
    (box.home / ".ssh").chmod(0o700)
    (box.home / ".ssh" / "id_rsa").chmod(0o600)

    subprocess.run(["/bin/sh", "-c", DELAYED[kind]], cwd=str(box.ws), env=box.env(), timeout=60, check=True)
    deadline = time.monotonic() + 10
    while not _delayed_effect(box, kind) and time.monotonic() < deadline:
        time.sleep(0.05)
    _control_holds(_delayed_effect(box, kind), f"the delayed {kind} did not happen without babylon60")
    (box.ws / ".git" / "hooks" / "pre-commit").unlink(missing_ok=True)
    (box.home / ".ssh").chmod(0o700)
    (box.home / ".ssh" / "id_rsa").chmod(0o600)

    if terminal:
        assert box.session(box.cli("/bin/sh", "-c", DELAYED[kind])).result["exit"] == 0
    else:
        done = box.run_without_terminal("/bin/sh", "-c", DELAYED[kind])
        assert done.returncode == 0, done.stderr
    time.sleep(3)  # well past the moment the write would have happened
    assert not _delayed_effect(box, kind)
    end = box.journal_entries("run_end")[-1]
    assert end["hooks_changed"] == [] and end["metadata_changed"] == [], end
    if LINUX:
        assert end["leftovers"] >= 1, end


# --- fidelity ---------------------------------------------------------------------------------------


@needs_backend
def test_binary_output_is_relayed_byte_for_byte(box: Box) -> None:
    """1 MiB of random bytes through a raw user terminal: the private terminal copies raw mode, no byte changes."""
    data = secrets.token_bytes(1 << 20)
    (box.ws / "random.bin").write_bytes(data)
    session = box.session(box.cli("/bin/cat", "random.bin"), raw=True)
    assert session.result["exit"] == 0
    assert len(session.screen) == len(data) and session.screen == data


@needs_backend
def test_cooked_output_is_what_the_terminal_shows_without_babylon60(box: Box) -> None:
    """Output processing (ONLCR) happens once, in the private terminal with the user's modes."""
    data = secrets.token_bytes(1 << 18) + b"last line\n"
    (box.ws / "random.bin").write_bytes(data)
    control = box.session(["/bin/cat", "random.bin"])
    confined = box.session(box.cli("/bin/cat", "random.bin"))
    assert control.result["exit"] == confined.result["exit"] == 0
    assert control.screen.endswith(b"last line\r\n") and confined.screen == control.screen
    assert confined.result["modes"] == control.result["modes"]  # the user's modes are back after the session


@needs_backend
@pytest.mark.parametrize(
    ("script", "code", "recorded"), [("exit 0", 0, 0), ("exit 3", 3, 3), ("kill -TERM $$", 143, -15)]
)
@pytest.mark.parametrize("terminal", [True, False], ids=["terminal", "no-terminal"])
def test_exit_status_is_propagated(box: Box, terminal: bool, script: str, code: int, recorded: int) -> None:
    if terminal:
        assert box.session(box.cli("/bin/sh", "-c", script)).result["exit"] == code
    else:
        assert box.run_without_terminal("/bin/sh", "-c", script).returncode == code
    assert box.journal_entries("run_end")[-1]["exit_code"] == recorded


WINDOW_AGENT = r"""
import fcntl, signal, struct, termios, time
def size():
    rows, cols, _x, _y = struct.unpack("HHHH", fcntl.ioctl(1, termios.TIOCGWINSZ, b"\0" * 8))
    return f"{rows}x{cols}"
got = []
signal.signal(signal.SIGWINCH, lambda *_: got.append(size()))
print("SIZE", size(), flush=True)
deadline = time.monotonic() + 60
while not got and time.monotonic() < deadline:
    time.sleep(0.02)
print("RESIZED", got[0] if got else "never", flush=True)
"""


@needs_backend
def test_window_size_is_copied_and_follows_resizes(box: Box) -> None:
    def resize(screen: Screen, master: int, _here: Path) -> None:
        screen.wait_for(b"SIZE 31x97")
        fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 120, 0, 0))  # SIGWINCH to the job

    session = box.session(box.cli(*_python(WINDOW_AGENT)), resize, size=(31, 97))
    assert session.result["exit"] == 0 and b"RESIZED 40x120" in session.screen, session.screen


# --- signals and job control ------------------------------------------------------------------------

SLEEPER = "echo READY; exec sleep 60"


@needs_backend
def test_ctrl_c_interrupts_the_agent(box: Box) -> None:
    """A byte in raw mode; the private terminal's line discipline signals the agent (which does not ignore it)."""

    def interrupt(screen: Screen, master: int, _here: Path) -> None:
        screen.wait_for(b"READY")
        os.write(master, b"\x03")

    session = box.session(box.cli("/bin/sh", "-c", SLEEPER), interrupt)
    assert session.result["exit"] == 128 + signal.SIGINT, session.screen
    assert box.journal_entries("run_end")[-1]["exit_code"] == -signal.SIGINT


@needs_backend
def test_ctrl_c_reaches_the_agent_when_stdin_is_redirected(box: Box) -> None:
    """stdin is not the terminal, so it stays in cooked mode: the key signals run, which relays it."""

    def interrupt(screen: Screen, master: int, _here: Path) -> None:
        screen.wait_for(b"READY")
        os.write(master, b"\x03")

    session = box.session(box.cli("/bin/sh", "-c", SLEEPER), interrupt, stdin=os.devnull)
    assert session.result["exit"] == 128 + signal.SIGINT, session.screen


PROMPT_AGENT = r"""
import os
fd = os.open("/dev/tty", os.O_RDWR)
os.write(fd, b"Passphrase: ")
line = b""
while not line.endswith(b"\n"):
    chunk = os.read(fd, 100)
    if not chunk:
        break
    line += chunk
print("got", line.strip().decode(), flush=True)
"""


@needs_backend
def test_a_dev_tty_prompt_reads_the_user_terminal_when_stdin_is_redirected(box: Box) -> None:
    """Like ssh asking for a passphrase under ``cmd < /dev/null``: the user's keyboard still answers it."""

    def answer(screen: Screen, master: int, _here: Path) -> None:
        screen.wait_for(b"Passphrase: ")
        os.write(master, b"s3cret\r")

    session = box.session(box.cli(*_python(PROMPT_AGENT)), answer, stdin=os.devnull)
    assert session.result["exit"] == 0 and b"got s3cret\r\n" in session.screen, session.screen


@needs_backend
def test_in_a_pipeline_run_leaves_the_terminal_to_the_rest_of_the_job(box: Box) -> None:
    """``run -- cmd | less``: neither raw mode nor reading, so a pager downstream keeps the terminal.

    Contrast: alone in its job, run puts the terminal in raw mode and relays what is typed to the agent.
    """
    agent = box.cli("/bin/sh", "-c", "echo READY >&2; sleep 1; echo out")

    def attempt(job: list[str]) -> tuple[Session, bool]:
        seen: dict[str, bool] = {}

        def type_ahead(screen: Screen, master: int, here: Path) -> None:
            screen.wait_for(b"READY")
            seen["canonical"] = bool(termios.tcgetattr(master)[3] & termios.ICANON)  # the user's terminal modes
            os.write(master, b"typed-ahead\r")
            _wait_for_file(here / "done")
            (here / "typed").touch()

        session = box.session(job, type_ahead, read_typed=True, settle=0.3)
        return session, seen["canonical"]

    alone, canonical = attempt(agent)
    assert alone.result["exit"] == 0 and not canonical and "typed-ahead" not in alone.result["typed"], alone
    piped, canonical = attempt(["/bin/sh", "-c", f"{shlex.join(agent)} | cat"])
    assert piped.result["exit"] == 0 and b"out\r\n" in piped.screen, piped.screen
    assert canonical and "typed-ahead" in piped.result["typed"], piped.result


JOB_AGENT = r"""
import os, sys
with open(sys.argv[1], "w") as handle:
    handle.write(str(os.getpid()))
print("READY", flush=True)
for line in sys.stdin:
    if line.strip() == "quit":
        break
    print("got:", line.strip(), flush=True)
"""


@needs_backend
def test_ctrl_z_stops_the_session_and_fg_resumes_it(box: Box) -> None:
    pidfile = box.ws / "agent.pid"
    seen: dict[str, Any] = {}

    def suspend_and_resume(screen: Screen, master: int, here: Path) -> None:
        screen.wait_for(b"READY")
        os.write(master, b"\x1a")  # Ctrl-Z
        _wait_for_file(here / "stopped-1")
        agent = int(pidfile.read_text())
        seen["agent_state"] = _state(agent)
        (here / "fg-1").touch()  # the shell's `fg`
        deadline = time.monotonic() + 30
        while _state(agent) == "T":
            assert time.monotonic() < deadline, "the agent was not continued"
            time.sleep(0.02)
        os.write(master, b"after\r")
        screen.wait_for(b"got: after")
        os.write(master, b"quit\r")

    session = box.session(box.cli(*_python(JOB_AGENT, str(pidfile))), suspend_and_resume)
    assert session.result["exit"] == 0, session.screen
    [stop] = session.result["stops"]
    assert stop["signal"] == signal.SIGTSTP and seen["agent_state"] == "T", (stop, seen)
    assert stop["modes"]["icanon"] and stop["modes"]["echo"], stop  # the user's modes while stopped


@needs_backend
def test_sigterm_to_run_ends_the_session_and_restores_the_terminal(box: Box) -> None:
    pidfile = box.ws / "agent.pid"

    def terminate(screen: Screen, _master: int, here: Path) -> None:
        screen.wait_for(b"READY")
        os.kill(json.loads((here / "job").read_text())["pid"], signal.SIGTERM)

    session = box.session(box.cli("/bin/sh", "-c", f"echo $$ > {pidfile}; {SLEEPER}"), terminate)
    assert session.result["exit"] == 128 + signal.SIGTERM, session.screen
    assert session.result["modes"]["icanon"] and session.result["modes"]["echo"], session.result
    assert not _alive(int(pidfile.read_text()))
    assert box.journal_entries("run_end")[-1]["ended_by"] == "SIGTERM"


@needs_backend
def test_end_of_input_reaches_the_agent(box: Box) -> None:
    def type_then_eof(screen: Screen, master: int, _here: Path) -> None:
        screen.wait_for(b"READY")
        os.write(master, b"hello\r")
        screen.wait_for(b"hello\r\nhello\r\n")  # the private terminal's echo, then cat's copy
        os.write(master, b"\x04")  # Ctrl-D at the start of a line

    session = box.session(box.cli("/bin/sh", "-c", "echo READY; exec cat"), type_then_eof)
    assert session.result["exit"] == 0, session.screen
    lines = box.tmp / "lines.txt"
    lines.write_bytes(b"line one\nline two\n")
    piped = box.session(box.cli("/bin/cat"), stdin=str(lines))  # a file on stdin passes through unchanged
    assert piped.result["exit"] == 0 and piped.screen == b"line one\r\nline two\r\n", piped.screen


# --- without a terminal -------------------------------------------------------------------------------

NO_TERMINAL_PROBE = r"""
import errno, json, os, signal, sys
def attempt(fn):
    try:
        return fn()
    except OSError as exc:
        return errno.errorcode.get(exc.errno, str(exc.errno))
out = {"dev_tty": attempt(lambda: os.close(os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)) or "ok"),
       "session_leader": os.getsid(0) == os.getpid(),
       "sigint_ignored": signal.getsignal(signal.SIGINT) is signal.SIG_IGN,
       "terminals": [fd for fd in (0, 1, 2) if os.isatty(fd)]}
with open(sys.argv[1], "w") as handle:
    json.dump(out, handle)
"""


@needs_backend
def test_without_a_terminal_the_agent_has_no_controlling_terminal(box: Box) -> None:
    """stdin, stdout and stderr redirected while run itself still has the user's terminal as controlling terminal."""
    redirects = {"stdin": os.devnull, "stdout": str(box.tmp / "out.txt"), "stderr": str(box.tmp / "err.txt")}
    control_report = box.ws / "control.json"
    box.session(_python(NO_TERMINAL_PROBE, str(control_report)), **redirects)
    control = json.loads(control_report.read_text())
    _control_holds(control["dev_tty"] == "ok", f"/dev/tty is not the user's terminal without babylon60: {control}")

    report_path = box.ws / "confined.json"
    session = box.session(box.cli(*_python(NO_TERMINAL_PROBE, str(report_path))), **redirects)
    report = json.loads(report_path.read_text())
    assert session.result["exit"] == 0, (box.tmp / "err.txt").read_text()
    assert report == {"dev_tty": "ENXIO", "session_leader": True, "sigint_ignored": False, "terminals": []}, report
    assert box.journal_entries("run_start")[-1]["terminal"] == "none"


# --- the trampoline verifies the private terminal and fails closed --------------------------------------

PRIVATE_PROBE = r"""
import json, os
fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
print(json.dumps({"pid": os.getpid(), "sid": os.getsid(0), "pgid": os.getpgrp(), "foreground": os.tcgetpgrp(fd)}))
"""


@needs_backend
def test_the_trampoline_refuses_a_private_terminal_it_cannot_verify(box: Box) -> None:
    pairs = [os.openpty() for _ in range(2)]
    try:
        (_ma, slave_a), (_mb, slave_b) = pairs
        rdev_a, rdev_b = os.fstat(slave_a).st_rdev, os.fstat(slave_b).st_rdev
        env, cwd = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, str(box.ws)

        def start(private_tty: tuple[int, int], **stdio: Any) -> tuple[subprocess.Popen[bytes], dict[str, Any]]:
            launch = Launch(_python(PRIVATE_PROBE), None, new_session=True, private_tty=private_tty)
            return spawn(launch, env=env, cwd=cwd, **stdio)

        process, status = start((0, rdev_b), stdin=slave_a)
        process.communicate(timeout=60)
        assert process.returncode == 126 and "not the launcher's pseudo-terminal" in status["error"], status
        process, status = start((0, rdev_a), stdin=slave_a, stderr=slave_b)
        process.communicate(timeout=60)
        assert process.returncode == 126 and "descriptor 2 is a terminal other than" in status["error"], status
        with pytest.raises(ValueError, match="private_tty needs new_session"):
            launcher._command(Launch(["/bin/true"], None, private_tty=(0, rdev_a)), 3)

        process, status = start((0, rdev_a), stdin=slave_a)
        stdout, _ = process.communicate(timeout=60)
        seen = json.loads(stdout)
        assert status["ok"] and status["terminal"] == "private" and status["pid"] == seen["pid"], status
        # The target runs under the monitor, which leads the session; the target's group is in the foreground.
        assert seen["sid"] == process.pid != seen["pid"] and seen["foreground"] == seen["pgid"] == seen["pid"], seen
    finally:
        for pair in pairs:
            for fd in pair:
                os.close(fd)
