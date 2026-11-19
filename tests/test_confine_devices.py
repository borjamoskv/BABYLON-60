"""Terminals, /tmp and device files: real Landlock, real pseudo-terminals.

The default policy grants no other terminal of the user (/dev/pts) and no shared
/tmp. The session's own terminals are granted one by one (``ttys``) and
``allow_ptys`` grants all of /dev/pts. Every confined run has an unconfined
control showing that the same operation succeeds without the policy, so a
denial is not vacuous.

Landlock tests run on Linux only; set BABYLON60_REQUIRE_LANDLOCK=1 (CI) to fail
instead of skipping when Landlock is missing. Policy and ``session_ttys`` tests
need only POSIX pseudo-terminals.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
import json
import os
from pathlib import Path
import secrets
import select
import stat
import subprocess
import sys
import tempfile
from typing import Any

import pytest

from babylon60.confine import launcher
from babylon60.confine.policy import MIN_LANDLOCK_ABI, PTYS_WARNING, Policy, account_home, build_policy

ROOT = Path(__file__).absolute().parents[1]
LINUX = sys.platform.startswith("linux")
ABI = launcher.landlock_abi()
REQUIRED = os.environ.get("BABYLON60_REQUIRE_LANDLOCK") == "1"
needs_landlock = pytest.mark.skipif(
    not LINUX or (ABI < MIN_LANDLOCK_ABI and not REQUIRED),
    reason=f"Landlock ABI {ABI} < {MIN_LANDLOCK_ABI} or not Linux; set BABYLON60_REQUIRE_LANDLOCK=1 to fail instead",
)

OpenPty = Callable[[], tuple[int, int, str]]  # -> (master, slave, slave path)

# Runs inside the sandbox (python -I -S -B): one JSON line, {label: result or errno name}.
PROBE = r'''
import errno, fcntl, json, os, select, struct, sys, termios

TIOCSPTLCK, TIOCGPTPEER = 0x40045431, 0x5441


def unlocked_master():
    master = os.open("/dev/ptmx", os.O_RDWR | os.O_NOCTTY)
    fcntl.ioctl(master, TIOCSPTLCK, struct.pack("i", 0))
    return master


def op_open(arg):
    os.close(os.open(arg, os.O_RDWR | os.O_NOCTTY))
    return "ok"


def op_read(arg):
    with open(arg, encoding="utf-8") as handle:
        return handle.read()


def op_create(arg):
    os.close(os.open(arg, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
    return "ok"


def op_list(arg):
    os.listdir(arg)
    return "ok"


def op_spy(arg):
    """pts_victim.py: a fake prompt on another terminal, then what the user types there."""
    fd = os.open(arg, os.O_RDWR | os.O_NOCTTY)
    try:
        os.write(fd, b"\r\n[sudo] password for user: ")
        if not select.select([fd], [], [], 5)[0]:
            return "TIMEOUT"
        return os.read(fd, 100).decode()
    finally:
        os.close(fd)


def op_openpty(arg):
    master, slave = os.openpty()
    os.write(slave, b"ping\n")
    return "ok" if b"ping" in os.read(master, 64) else "no data"


def op_ptmx_peer(arg):
    master = unlocked_master()
    os.close(fcntl.ioctl(master, TIOCGPTPEER, os.O_RDWR | os.O_NOCTTY))
    return "ok"


def op_ctty_from_ptmx(arg):
    master = unlocked_master()
    fcntl.ioctl(master, termios.TIOCSCTTY, 0)
    tty = os.open("/dev/tty", os.O_RDWR)
    os.write(master, b"typed\n")
    return "ok" if os.read(tty, 64) == b"typed\n" else "no data"


def op_ttyname0(arg):
    name = os.ttyname(0)
    fd = os.open(name, os.O_RDWR | os.O_NOCTTY)
    try:
        termios.tcgetattr(fd)
    finally:
        os.close(fd)
    return name


def op_own_ctty(arg):
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)
    tty = os.open("/dev/tty", os.O_RDWR)
    os.write(tty, arg.encode())
    return "ok"


def op_dev_tty(arg):
    os.close(os.open("/dev/tty", os.O_RDWR))
    return "ok"


def op_dev_null(arg):
    with open("/dev/null", "r+b", buffering=0) as handle:
        handle.write(b"x")
        return "ok" if handle.read() == b"" else "data"


def op_mp_lock(arg):
    import multiprocessing

    with multiprocessing.Lock():
        return "ok"


results = {}
for label, name, arg in json.loads(sys.argv[1]):
    try:
        results[label] = globals()["op_" + name](arg)
    except OSError as exc:
        results[label] = errno.errorcode.get(exc.errno or 0, str(exc.errno))
print(json.dumps(results))
'''


@dataclass
class Box:
    home: Path
    ws: Path
    env: dict[str, str]

    def policy(self, **kwargs: Any) -> Policy:
        kwargs.setdefault("homes", [str(self.home)])
        return build_policy(self.ws, runtime=[launcher.interpreter_prefix()], **kwargs)

    def probe(
        self, policy: Policy | None, ops: list[list[str]], *, stdin: int | None = None, new_session: bool = True
    ) -> dict[str, str]:
        """Run PROBE as ``babylon60 run`` starts an agent, or unconfined when ``policy`` is None.

        A new session by default: no controlling terminal is inherited from whoever runs pytest.
        """
        argv = [launcher.interpreter(), "-I", "-S", "-B", "-c", PROBE, json.dumps(ops)]
        launch = launcher.Launch(argv, None) if policy is None else launcher.session_launch(argv, policy)
        process, status = launcher.spawn(
            launch,
            env=self.env,
            cwd=str(self.ws),
            stdin=subprocess.DEVNULL if stdin is None else stdin,
            start_new_session=new_session,
        )
        stdout, stderr = process.communicate(timeout=60)
        assert status.get("ok"), status
        assert process.returncode == 0, stderr.decode("utf-8", "replace")
        return json.loads(stdout.decode().splitlines()[-1])


@pytest.fixture
def box(tmp_path: Path) -> Box:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    ws = tmp_path / "ws"
    ws.mkdir()
    return Box(home, ws, {"PATH": "/usr/bin:/bin", "HOME": str(home), "LC_ALL": "C"})


@pytest.fixture
def ptys() -> Iterator[OpenPty]:
    """Open real pseudo-terminal pairs on demand; all are closed after the test."""
    fds: list[int] = []

    def open_pair() -> tuple[int, int, str]:
        master, slave = os.openpty()
        fds.extend((master, slave))
        return master, slave, os.ttyname(slave)

    yield open_pair
    for fd in fds:
        os.close(fd)


def _drain(fd: int) -> bytes:
    data = b""
    while select.select([fd], [], [], 0.2)[0]:
        chunk = os.read(fd, 4096)
        if not chunk:
            break
        data += chunk
    return data


def _session_ttys_in_child(**stdio: Any) -> list[str]:
    code = "import json; from babylon60.confine.terminals import session_ttys; print(json.dumps(session_ttys()))"
    env = {**os.environ, "PYTHONPATH": str(ROOT / "01_KISH_ENGINE")}
    done = subprocess.run(
        [sys.executable, "-c", code], stdout=subprocess.PIPE, env=env, timeout=60, check=True, **stdio
    )
    return json.loads(done.stdout)


# Policy: what is granted, on every platform.


def test_default_policy_grants_no_other_terminal_and_no_shared_tmp(box: Box) -> None:
    policy = box.policy(homes=[account_home()])
    grants = {g.path: g for g in policy.grants}
    assert "/tmp" not in grants
    assert not any(path == "/dev/pts" or path.startswith("/dev/pts/") for path in grants)
    for device in ("/dev/null", "/dev/tty", "/dev/ptmx"):
        if os.path.exists(device) and not os.path.islink(device):
            assert (grants[device].access, grants[device].origin) == ("dev", "system")
    if os.path.isdir("/dev/shm"):
        assert grants["/dev/shm"].access == "rw"
    assert not policy.allow_ptys and PTYS_WARNING not in policy.warnings


def test_ttys_grant_exactly_the_named_terminals(box: Box, tmp_path: Path, ptys: OpenPty) -> None:
    _master, _slave, name = ptys()
    regular = tmp_path / "not-a-tty"
    regular.write_text("x")
    missing = tmp_path / "missing-tty"
    policy = box.policy(ttys=[name, str(regular), str(missing)])
    grant = next(g for g in policy.grants if g.path == name)
    assert (grant.access, grant.origin, grant.is_dir) == ("dev", "tty", False)
    assert f"{regular}: not a terminal device under /dev" in policy.skipped
    assert str(missing) in policy.skipped
    assert {str(regular), str(missing)}.isdisjoint(g.path for g in policy.grants)


def test_terminal_device_outside_dev_is_refused(box: Box, tmp_path: Path) -> None:
    node = tmp_path / "tty-elsewhere"
    try:
        os.mknod(node, stat.S_IFCHR | 0o600, os.stat("/dev/null").st_rdev)
    except PermissionError:
        pytest.skip("creating a device node needs CAP_MKNOD")
    policy = box.policy(ttys=[str(node)])
    assert f"{node}: not a terminal device under /dev" in policy.skipped
    assert str(node) not in {g.path for g in policy.grants}


def test_allow_ptys_grants_dev_pts_and_warns(box: Box) -> None:
    policy = box.policy(allow_ptys=True)
    assert policy.allow_ptys and PTYS_WARNING in policy.warnings
    assert policy.digest() != box.policy().digest()
    if os.path.isdir("/dev/pts"):
        grant = next(g for g in policy.grants if g.path == "/dev/pts")
        assert (grant.access, grant.origin, grant.is_dir) == ("dev", "ptys", True)


def test_session_ttys_names_the_terminals_of_stdio(ptys: OpenPty) -> None:
    _ma, slave_a, name_a = ptys()
    _mb, slave_b, name_b = ptys()
    assert _session_ttys_in_child(stdin=slave_a, stderr=slave_a) == [name_a]
    assert _session_ttys_in_child(stdin=slave_a, stderr=slave_b) == [name_a, name_b]
    assert _session_ttys_in_child(stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == []


# Landlock: what a confined process can actually open.


@needs_landlock
def test_another_terminal_can_be_neither_read_nor_written(box: Box, ptys: OpenPty) -> None:
    """pts_victim.py: a fake sudo prompt on another tab of the user and the line typed there."""
    master, slave, victim = ptys()
    typed = f"hunter2-{secrets.token_hex(4)}\n"
    ops = [["spy", "spy", victim]]

    os.write(master, typed.encode())  # the user types in the other tab; the line waits for a reader
    assert box.probe(None, ops) == {"spy": typed}
    assert b"[sudo] password" in _drain(master)

    os.write(master, typed.encode())
    assert box.probe(box.policy(), ops) == {"spy": "EACCES"}
    assert b"[sudo] password" not in _drain(master)
    assert _drain(slave) == typed.encode()  # still unread: the confined process never got it


@needs_landlock
def test_session_tty_is_reopened_and_another_terminal_is_not(box: Box, ptys: OpenPty) -> None:
    _own_master, own_slave, own = ptys()
    _other_master, _other_slave, other = ptys()
    ops = [["own", "ttyname0", ""], ["other", "open", other]]
    assert box.probe(None, ops, stdin=own_slave) == {"own": own, "other": "ok"}
    assert box.probe(box.policy(), ops, stdin=own_slave) == {"own": "EACCES", "other": "EACCES"}
    assert box.probe(box.policy(ttys=[own]), ops, stdin=own_slave) == {"own": own, "other": "EACCES"}


@needs_landlock
def test_allow_ptys_reaches_other_terminals_and_creates_ptys(box: Box, ptys: OpenPty) -> None:
    _master, _slave, other = ptys()
    ops = [["other", "open", other], ["openpty", "openpty", ""], ["peer", "ptmx_peer", ""]]
    assert box.probe(box.policy(allow_ptys=True), ops) == {"other": "ok", "openpty": "ok", "peer": "ok"}
    assert box.probe(box.policy(), ops) == {"other": "EACCES", "openpty": "EACCES", "peer": "EACCES"}


@needs_landlock
def test_ptmx_without_dev_pts_reaches_no_existing_terminal(box: Box, ptys: OpenPty) -> None:
    """/dev/ptmx stays granted: opening it only allocates a new pair, whose slave is in /dev/pts.

    TIOCGPTPEER opens the slave through Landlock's file_open on its devpts path, like
    the path-based fallback of glibc's openpty, so both fail with EACCES. Declared
    limit: a session leader can still make the new slave its controlling terminal
    (TIOCSCTTY on the master) and open it as /dev/tty; that is a terminal of its own,
    and another terminal stays out of reach.
    """
    _master, _slave, victim = ptys()
    ops = [
        ["ptmx", "open", "/dev/ptmx"],
        ["peer", "ptmx_peer", ""],
        ["openpty", "openpty", ""],
        ["own_new_pty", "ctty_from_ptmx", ""],
        ["victim", "open", victim],
    ]
    expected = {"ptmx": "ok", "peer": "EACCES", "openpty": "EACCES", "own_new_pty": "ok", "victim": "EACCES"}
    assert box.probe(box.policy(), ops) == expected


@needs_landlock
def test_tmp_is_not_granted_but_the_private_tmp_is(box: Box, tmp_path: Path) -> None:
    private = tmp_path / "private-tmp"
    private.mkdir(mode=0o700)
    token = secrets.token_hex(8)
    created = f"/tmp/b60-devices-{token}"
    handle, canary = tempfile.mkstemp(prefix="krb5cc_b60test_", dir="/tmp")  # like a Kerberos cache
    try:
        os.write(handle, token.encode())
        os.close(handle)
        # The account home is outside /tmp: before this change such a policy granted /tmp read-write.
        policy = box.policy(homes=[account_home()], private_tmp=str(private))
        assert "/tmp" not in {g.path for g in policy.grants}
        ops = [
            ["read", "read", canary],
            ["create", "create", created],
            ["list", "list", "/tmp"],
            ["private", "create", str(private / "scratch")],
            ["semaphore", "mp_lock", ""],
        ]
        assert box.probe(None, ops) == {"read": token, "create": "ok", "list": "ok", "private": "ok", "semaphore": "ok"}
        os.unlink(created)
        os.unlink(private / "scratch")
        confined = box.probe(policy, ops)
        assert confined == {"read": "EACCES", "create": "EACCES", "list": "EACCES", "private": "ok", "semaphore": "ok"}
        assert not os.path.exists(created)
    finally:
        for path in (canary, created):
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass


@needs_landlock
def test_dev_null_and_dev_tty_behave_as_without_confinement(box: Box, ptys: OpenPty) -> None:
    ops = [["null", "dev_null", ""], ["tty", "dev_tty", ""]]
    assert box.probe(box.policy(), ops) == box.probe(None, ops) == {"null": "ok", "tty": "ENXIO"}
    master, slave, _name = ptys()
    marker = f"b60-own-terminal-{secrets.token_hex(4)}"
    # The controlling terminal stays reachable through /dev/tty without any /dev/pts grant.
    assert box.probe(box.policy(), [["ctty", "own_ctty", marker]], stdin=slave) == {"ctty": "ok"}
    assert marker.encode() in _drain(master)
