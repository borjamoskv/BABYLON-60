"""Seccomp rules for what Landlock does not mediate: keyrings, System V IPC, setuid modes, datagram pairs.

Every refusal runs next to an unconfined control with the same probe, so a rule
that blocks nothing (or a kernel that lacks the feature) fails or skips the test
instead of passing it. Ordinary development work must keep running confined.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import shutil
import sys
from typing import Any

import pytest

from babylon60.confine import launcher
from babylon60.confine.launcher import Launch, interpreter, interpreter_prefix, landlock_abi
from babylon60.confine.policy import MIN_LANDLOCK_ABI, build_policy, default_homes

LINUX = sys.platform.startswith("linux")
REQUIRED = os.environ.get("BABYLON60_REQUIRE_LANDLOCK") == "1"
SUPPORTED = LINUX and platform.machine() in ("x86_64", "aarch64")
pytestmark = pytest.mark.skipif(
    not SUPPORTED or not (landlock_abi() >= MIN_LANDLOCK_ABI or REQUIRED),
    reason="seccomp filter: Linux x86_64/aarch64 with Landlock only",
)
NR = {
    "x86_64": {"keyctl": 250, "add_key": 248, "openat2": 437},
    "aarch64": {"keyctl": 219, "add_key": 217, "openat2": 437},
}.get(platform.machine(), {})

PROBE = r"""
import ctypes, errno, json, os, socket, stat, sys
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
nr = json.loads(sys.argv[1])
out = {}
def errname():
    return errno.errorcode.get(ctypes.get_errno(), str(ctypes.get_errno()))
def attempt(name, fn):
    try:
        value = fn()
        out[name] = "ok" if value is None or value >= 0 else errname()
    except OSError as exc:
        out[name] = errno.errorcode.get(exc.errno, str(exc.errno))
# keyctl(KEYCTL_GET_KEYRING_ID, KEY_SPEC_PROCESS_KEYRING, create=1); add_key("user", ..., KEY_SPEC_PROCESS_KEYRING)
attempt("keyctl", lambda: libc.syscall(nr["keyctl"], 0, -2, 1))
attempt("add_key", lambda: libc.syscall(nr["add_key"], b"user", b"b60-probe", b"x", 1, -2))
# System V shared memory, semaphores and message queues
IPC_PRIVATE, IPC_CREAT, IPC_RMID = 0, 0o1000, 0
libc.shmget.restype = libc.semget.restype = libc.msgget.restype = ctypes.c_int
def sysv(get, ctl, *args):
    ident = get(IPC_PRIVATE, *args)
    if ident < 0:
        raise OSError(ctypes.get_errno(), "get")
    ctl(ident, *([0, IPC_RMID] if ctl is libc.semctl else [IPC_RMID]), None)
attempt("shmget", lambda: sysv(libc.shmget, libc.shmctl, 4096, IPC_CREAT | 0o600))
attempt("semget", lambda: sysv(libc.semget, libc.semctl, 1, IPC_CREAT | 0o600))
attempt("msgget", lambda: sysv(libc.msgget, libc.msgctl, IPC_CREAT | 0o600))
# setuid and setgid modes on files the process owns
open("tool", "w").close()
attempt("chmod_755", lambda: os.chmod("tool", 0o755))
attempt("chmod_4755", lambda: os.chmod("tool", 0o4755))
attempt("chmod_2755", lambda: os.chmod("tool", 0o2755))
attempt("open_creat_6755", lambda: os.close(os.open("tool-created", os.O_CREAT | os.O_WRONLY, 0o6755)))
attempt("mknod_4644", lambda: os.mknod("tool-node", stat.S_IFREG | 0o4644))
out["tool_mode"] = oct(os.stat("tool").st_mode & 0o7777)
# openat2(AT_FDCWD, ".", {flags=O_RDONLY}, sizeof(struct open_how))
how = (ctypes.c_uint64 * 3)(0, 0, 0)
def openat2():
    fd = libc.syscall(nr["openat2"], -100, b".", ctypes.byref(how), ctypes.sizeof(how))
    if fd >= 0:
        os.close(fd)
    return fd
attempt("openat2", openat2)
# Unix socket pairs by type
for name, kind in (("stream", socket.SOCK_STREAM), ("seqpacket", socket.SOCK_SEQPACKET),
                   ("dgram", socket.SOCK_DGRAM), ("raw", socket.SOCK_RAW),
                   ("stream_cloexec", socket.SOCK_STREAM | socket.SOCK_CLOEXEC | socket.SOCK_NONBLOCK)):
    attempt("pair_" + name, lambda kind=kind: [s.close() for s in socket.socketpair(socket.AF_UNIX, kind)] and None)
print(json.dumps(out))
"""

WORK = r"""
import json, multiprocessing, os, subprocess, sys
out = {}
os.makedirs("pkg", exist_ok=True)
with open("pkg/run.sh", "w") as handle:
    handle.write("#!/bin/sh\necho ran\n")
os.chmod("pkg/run.sh", 0o755)
out["exec_script"] = subprocess.run(["./pkg/run.sh"], capture_output=True, text=True).stdout.strip()
def square(x):
    return x * x
if __name__ == "__main__":
    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(2) as pool:
        out["pool"] = pool.map(square, [1, 2, 3])
    lock = ctx.Lock()
    with lock:
        out["lock"] = True
    a, b = ctx.Pipe()
    a.send("ping")
    out["pipe"] = b.recv()
    git = sys.argv[1]
    if git:
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid", "HOME": os.getcwd()}
        steps = [[git, "init", "-q", "repo"], [git, "-C", "repo", "add", "-A"],
                 [git, "-C", "repo", "commit", "-q", "--allow-empty", "-m", "x"]]
        out["git"] = [subprocess.run(step, env=env, capture_output=True).returncode for step in steps]
    print(json.dumps(out))
"""


@pytest.fixture
def box(tmp_path: Path) -> dict[str, Any]:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    ws = tmp_path / "ws"
    ws.mkdir()
    tmp = tmp_path / "tmp"
    tmp.mkdir(mode=0o700)
    policy = build_policy(ws, homes=[str(home), *default_homes()], runtime=[interpreter_prefix()], private_tmp=str(tmp))
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "TMPDIR": str(tmp), "LC_ALL": "C"}
    return {"ws": ws, "policy": policy, "env": env}


def _probe(box: dict[str, Any], source: str, *args: str, confined: bool, unix_sockets: bool = False) -> dict[str, Any]:
    argv = [interpreter(), "-I", "-S", "-c", source, *args]
    launch = Launch(argv, box["policy"], seccomp=True, unix_sockets=unix_sockets) if confined else Launch(argv, None)
    workdir = box["ws"] / ("confined" if confined else "control") / ("unix" if unix_sockets else "default")
    workdir.mkdir(parents=True, exist_ok=True)
    result = launcher.run(launch, env=box["env"], cwd=str(workdir), timeout=120)
    assert result.status.get("ok"), result.status
    lines = result.stdout.decode().strip().splitlines()
    assert lines, result.stderr.decode()
    return json.loads(lines[-1])


def test_status_reports_every_rule(box: dict[str, Any]) -> None:
    result = launcher.run(Launch(["/bin/true"], box["policy"], seccomp=True), env=box["env"], cwd=str(box["ws"]))
    for rule in ("keyrings", "sysv_ipc", "openat2", "setid_modes", "socketpair_dgram"):
        assert rule in result.status["seccomp"], result.status


def test_keyrings_sysv_ipc_setid_modes_and_datagram_pairs_are_refused(box: dict[str, Any]) -> None:
    control = _probe(box, PROBE, json.dumps(NR), confined=False)
    confined = _probe(box, PROBE, json.dumps(NR), confined=True)
    # Controls: the kernel offers each feature to this user without the filter.
    for name in ("keyctl", "add_key", "shmget", "semget", "msgget", "chmod_4755", "pair_dgram"):
        if control[name] != "ok":
            pytest.skip(f"{name} unavailable without the filter here: {control}")
    for name in ("keyctl", "add_key", "shmget", "semget", "msgget"):
        assert confined[name] == "EPERM", (name, confined)
    for name in ("chmod_4755", "chmod_2755", "open_creat_6755", "mknod_4644"):
        assert confined[name] == "EPERM", (name, confined)
    assert confined["chmod_755"] == "ok" and confined["tool_mode"] == "0o755", confined
    assert confined["openat2"] == "ENOSYS" and control["openat2"] in ("ok", "ENOSYS"), (control, confined)
    assert confined["pair_dgram"] == confined["pair_raw"] == "EPERM", confined
    for name in ("pair_stream", "pair_seqpacket", "pair_stream_cloexec"):
        assert confined[name] == "ok", (name, confined)


def test_unix_sockets_flag_keeps_datagram_pairs_but_not_the_rest(box: dict[str, Any]) -> None:
    confined = _probe(box, PROBE, json.dumps(NR), confined=True, unix_sockets=True)
    assert confined["pair_dgram"] == "ok", confined
    assert confined["keyctl"] == confined["shmget"] == confined["chmod_4755"] == "EPERM", confined


def test_ordinary_development_work_still_runs(box: dict[str, Any]) -> None:
    git = shutil.which("git") or ""
    report = _probe(box, WORK, git, confined=True)
    assert report["exec_script"] == "ran" and report["pool"] == [1, 4, 9], report
    assert report["lock"] is True and report["pipe"] == "ping", report
    if git:
        assert report["git"] == [0, 0, 0], report
