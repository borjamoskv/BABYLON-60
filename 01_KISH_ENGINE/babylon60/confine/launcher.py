"""Start a command through the confinement trampoline and read what it applied."""

from __future__ import annotations

from dataclasses import dataclass, field
import ctypes
import json
import os
from pathlib import Path
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
        process.kill()
        stdout, stderr = process.communicate()
        status = {**status, "timeout": True}
    return Result(process.returncode, stdout, stderr, status)
