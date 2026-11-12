"""Linux Landlock trampoline: refusal paths, privilege drop and descriptor hygiene.

Set BABYLON60_REQUIRE_LANDLOCK=1 (CI) to turn a missing Landlock into a failure
instead of a skip, so a silent skip cannot pass for coverage.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from babylon60.confine import launcher
from babylon60.confine.launcher import Launch, interpreter_prefix, landlock_abi, run, spawn
from babylon60.confine.policy import MIN_LANDLOCK_ABI, build_policy

ABI = landlock_abi()
REQUIRED = os.environ.get("BABYLON60_REQUIRE_LANDLOCK") == "1"
pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux") or (ABI < MIN_LANDLOCK_ABI and not REQUIRED),
    reason=f"Landlock ABI {ABI} < {MIN_LANDLOCK_ABI}; set BABYLON60_REQUIRE_LANDLOCK=1 to fail instead",
)


def test_landlock_is_available_when_required() -> None:
    print(f"landlock_abi={ABI}")
    assert ABI >= MIN_LANDLOCK_ABI


@pytest.fixture
def box(tmp_path: Path) -> dict[str, object]:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    key = home / ".ssh" / "id_rsa"
    key.write_text("BABYLON60-CANARY landlock-test\n")
    ws = tmp_path / "ws"
    ws.mkdir()
    policy = build_policy(ws, homes=[str(home)], runtime=[interpreter_prefix()])
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "LC_ALL": "C"}
    return {"home": home, "key": key, "ws": ws, "policy": policy, "env": env}


def _run(box: dict[str, object], argv: list[str], **kwargs: object) -> launcher.Result:
    launch = Launch(argv, box["policy"], **kwargs)  # type: ignore[arg-type]
    return run(launch, env=box["env"], cwd=str(box["ws"]))  # type: ignore[arg-type]


def test_home_is_denied_and_workspace_is_writable(box: dict[str, object]) -> None:
    denied = _run(box, ["/bin/cat", str(box["key"])])
    assert denied.returncode == 1 and b"Permission denied" in denied.stderr
    assert denied.stdout == b""
    written = _run(box, ["/bin/sh", "-c", "echo ok > out.txt && cat out.txt"])
    assert written.returncode == 0 and written.stdout == b"ok\n"
    assert denied.status["ok"] and denied.status["landlock_abi"] == ABI
    assert denied.status["no_new_privs"] == 1


def test_control_run_reads_the_canary(box: dict[str, object]) -> None:
    result = run(Launch(["/bin/cat", str(box["key"])], None), env=box["env"], cwd=str(box["ws"]))  # type: ignore[arg-type]
    assert result.returncode == 0 and b"BABYLON60-CANARY" in result.stdout


def test_capabilities_are_empty_after_the_trampoline(box: dict[str, object]) -> None:
    result = _run(box, ["/bin/true"])
    assert result.returncode == 0
    caps = result.status["caps"]
    assert caps["CapEff"] == caps["CapPrm"] == caps["CapAmb"] == "0" * 16
    assert result.status["no_new_privs"] == 1
    if os.geteuid() == 0:
        # Root held capabilities: the trampoline must also empty the bounding set.
        assert result.status["caps_dropped"] is True and caps["CapBnd"] == "0" * 16
    else:
        # Nothing to drop; NO_NEW_PRIVS already blocks gaining privileges through exec.
        assert result.status["caps_dropped"] is False


def test_insufficient_abi_refuses_before_exec(box: dict[str, object]) -> None:
    marker = Path(str(box["ws"])) / "ran"
    result = _run(box, ["/bin/sh", "-c", f"touch {marker}"], min_abi=99)
    assert result.returncode == launcher.EXIT_REFUSED
    assert not result.status["ok"] and "below the required" in result.status["error"]
    assert not marker.exists()


def test_grant_replaced_after_check_is_refused(box: dict[str, object]) -> None:
    ws = Path(str(box["ws"]))
    ws.rename(ws.with_name("ws-moved"))
    ws.mkdir()
    result = _run(box, ["/bin/true"])
    assert result.returncode == launcher.EXIT_REFUSED
    assert "changed after it was checked" in result.status["error"]


def test_leaked_descriptor_does_not_reach_the_target(box: dict[str, object]) -> None:
    leaked = os.open(str(box["key"]), os.O_RDONLY)
    os.set_inheritable(leaked, True)
    read_fd, write_fd = os.pipe()
    probe = f"import os\ntry:\n    print(os.read({leaked}, 64))\nexcept OSError as e:\n    print('EBADF' if e.errno == 9 else e)"
    launch = Launch([launcher.interpreter(), "-I", "-S", "-c", probe], box["policy"])  # type: ignore[arg-type]
    try:
        command = launcher._command(launch, write_fd)
        process = subprocess.Popen(
            command,
            env=box["env"],
            cwd=str(box["ws"]),
            stdout=subprocess.PIPE,
            pass_fds=(write_fd, leaked),  # type: ignore[arg-type]
        )
    finally:
        os.close(write_fd)
        os.close(leaked)
    with os.fdopen(read_fd, "rb") as status_pipe:
        assert b'"ok": true' in status_pipe.read()
    stdout, _ = process.communicate(timeout=30)
    assert process.returncode == 0
    assert stdout.strip() == b"EBADF"


def _tiocsti_probe() -> str:
    return (
        "import fcntl, os, termios\n"
        "fcntl.ioctl(0, termios.TIOCSCTTY, 0)\n"
        "try:\n"
        "    fcntl.ioctl(0, termios.TIOCSTI, b'x')\n"
        "    print('INJECTED')\n"
        "except OSError as e:\n"
        "    print('errno', e.errno)\n"
    )


def _run_on_pty(box: dict[str, object], seccomp: bool, policy: object) -> bytes:
    master, slave = os.openpty()
    try:
        launch = Launch([launcher.interpreter(), "-I", "-S", "-c", _tiocsti_probe()], policy, seccomp=seccomp)  # type: ignore[arg-type]
        process, status = spawn(launch, env=box["env"], cwd=str(box["ws"]), stdin=slave, start_new_session=True)  # type: ignore[arg-type]
        stdout, _ = process.communicate(timeout=30)
        assert status["ok"], status
        return stdout
    finally:
        os.close(master)
        os.close(slave)


def test_seccomp_blocks_terminal_injection(box: dict[str, object]) -> None:
    legacy = Path("/proc/sys/dev/tty/legacy_tiocsti")
    if legacy.exists() and legacy.read_text().strip() != "1":
        pytest.skip("TIOCSTI is already disabled by the kernel (dev.tty.legacy_tiocsti=0)")
    control = _run_on_pty(box, seccomp=False, policy=None)
    if control.strip() != b"INJECTED":
        pytest.skip(f"TIOCSTI unavailable without the filter here: {control!r}")
    confined = _run_on_pty(box, seccomp=True, policy=box["policy"])
    assert confined.strip() == b"errno 1"


def test_relative_target_is_rejected(box: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="absolute path"):
        _run(box, ["cat", "x"])


def test_interpreter_is_not_a_virtualenv_shim() -> None:
    assert os.path.realpath(launcher.interpreter()) == launcher.interpreter()
    assert shutil.which(launcher.interpreter())
