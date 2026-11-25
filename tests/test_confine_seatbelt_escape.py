# ruff: noqa: F401
"""macOS Seatbelt: what ``(allow default)`` leaves open besides files (review round 3, MACOS-1..15).

Rendering tests run everywhere and check the rules a fix adds; on the current renderer they fail,
which is the static half of each finding. Behaviour tests run only on macOS (the macos-15 CI job,
BABYLON60_REQUIRE_SEATBELT=1). Each one first runs its attempt WITHOUT confinement and skips when
that control has no effect on the machine (no GUI session, no TCC grant, no Developer Tools
access...), so a pass is never vacuous; the confined attempt must then have no effect. Before the
fix a failing behaviour test reproduces the finding; after it, the same test confirms the closure.
Each one asserts on the effect (a file, the mount table, launchd's environment), never on a tool's
exit status. A test that changes state outside its tmp_path (a mount, an attached image, launchd's
environment, a LaunchServices registration) undoes it in a finally block, whatever the assertions did.

The tests revised after the review of AX-210 (lsopen, launchctl setenv, defaults read, screencapture and
the display probe, hdiutil, since AX-225 Apple Events and lldb, and since AX-226 launchd jobs, cfprefsd
writes, the pasteboard and setuid modes, which until then confined through ``box.run`` without checking
that the tool ran) launch the confined attempt as `run` launches the agent (``_as_run``: a new session, a
private TMPDIR and the variables `run` points into it) and, through ``_closed``, count an absent effect
only when the trampoline reported the exec (status ok); a launcher timeout makes them skip with the
reason, never pass. Apple Events also need osascript's own run-time error. Tests that measure through
PROBE (``_probe``) need its report, which it prints once its action is done; since AX-225 a launcher
timeout before it makes them skip with the reason too.

Positive controls measure what the denials cost: what agents run every day (a listing of their own
processes, git, a venv, clang with modules, swift, brew, lldb on their own build) must still work
confined; headless Chrome is a declared limit (below). Each runs unconfined first, with the variables `run` sets in a TMPDIR of its own,
and skips when that fails; confined, a failure carries the command's stderr and the control's.

A declared limit is an xfail with raises=DeclaredLimit that only its exact measured shape satisfies, and
in that shape ``_declared_limit`` makes the XFAIL carry what this run measured, on the -rx line and in
the JUnit, instead of the marker's fixed reason. It is strict once measured, so that XPASS(strict) fails
the test should the limit go; the kern.proc one, still a deduction, is not strict yet. The POSIX
shared-memory xfail predates this pattern: with neither strict nor raises, any failure is its XFAIL, so
its XFAIL at f3242c4 measures no shape. The exploratory Chrome variant (CHROME_EXPLORATORY) is no
declared limit: an xfail with neither, so that it is never red. At f3242c4 (macos-15, named in its
JUnit): executing /bin/ps (setuid root) answered EPERM under `run`'s profile and under one of only
(allow default), so the sandbox itself refuses it; that every setuid or setgid program is refused rests
on an Apple forum report (forbidden-exec-sugid). Headless Chrome died by a signal confined, with its own
sandbox and without it (both FAILED there, before they were declared limits).

Every payload that runs outside the sandbox reads only the decoy key of the test's own disposable
HOME and writes it to a marker file outside the grants; nothing here reads real credentials.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
import contextlib
import json
import os
from pathlib import Path
import plistlib
import re
import secrets
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any, NamedTuple, NoReturn

import pytest

from babylon60.confine import cli, launcher, seatbelt
from babylon60.confine.journal import ConfineJournal, JournalError
from babylon60.confine.policy import PRESETS, Policy, account_home, build_policy, default_homes
from test_confine_seatbelt import DATA, DENIED, TMP, Box, _matches, _paths, _regexes, _rule, _synthetic, macos

ROOT = Path(__file__).absolute().parents[1]

# ---------------------------------------------------------------- rendering (every platform)

USER_DIR = "/private/var/folders/xy/abc123"
SHARED = ("/private/tmp", "/private/var/tmp", "/Volumes", USER_DIR)
SERVICES_ACTING_OUTSIDE = (
    "com.apple.pasteboard.1",
    "com.apple.GSSCred",
    "com.apple.CoreSimulator.CoreSimulatorService",
    "com.apple.DiskArbitration.diskarbitrationd",
    # INV_C5_COMPUTER_USE_TRUST_GATEWAY (docs/03_guides/agent_contracts.md) names these four.
    "com.apple.windowserver.active",
    "com.apple.accessibility.AXServer",
    "com.apple.coreservices.appleevents",
    "com.apple.tsm.portname",
)
TASK_PORTS = "(when (defined? 'mach-priv-task-port) (deny mach-priv-task-port))"
OWN_TASK_PORTS = "(when (defined? 'mach-priv-task-port) (allow mach-priv-task-port (target same-sandbox)))"


def test_services_that_start_code_outside_the_sandbox_are_denied() -> None:
    """MACOS-1..3, 5, 11: `open`, osascript, launchctl, mounts and synthetic input reach past every file rule."""
    lines = seatbelt.render_profile(_synthetic()).splitlines()
    for operation in ("lsopen", "appleevent-send", "job-creation", "hid-control", "file-mount", "file-unmount"):
        assert f"(deny {operation})" in lines, f"{operation} is allowed by (allow default)"


def test_other_processes_can_be_neither_signalled_nor_read() -> None:
    """MACOS-4, MACOS-6, MACOS-11: only processes of this sandbox (the agent and its children) stay reachable."""
    lines = seatbelt.render_profile(_synthetic()).splitlines()
    assert lines.index("(deny signal)") < lines.index("(allow signal (target self) (target same-sandbox))")
    assert lines.index("(deny process-info*)") < lines.index(
        "(allow process-info* (target self) (target same-sandbox))"
    )
    assert '(deny sysctl-read (sysctl-name-prefix "kern.procargs"))' in lines
    assert lines.index(TASK_PORTS) < lines.index(OWN_TASK_PORTS), "the agent's own builds must stay debuggable"
    # "(target others)" leaves the caller's own process group open (MACOS-4): no process rule may use it.
    assert not [line for line in lines if "(target others)" in line]


def test_preferences_are_not_written_through_cfprefsd() -> None:
    """MACOS-7: cfprefsd writes ~/Library/Preferences for its caller, past every file-write rule."""
    assert "(deny user-preference-write)" in seatbelt.render_profile(_synthetic()).splitlines()


def test_credential_and_spawning_services_are_not_looked_up() -> None:
    """MACOS-8, MACOS-9, MACOS-11: the pasteboard (unless clipboard=True), Kerberos, CoreSimulator, DiskArbitration,
    and the window server, accessibility, Apple Event and text input services of INV_C5_COMPUTER_USE_TRUST_GATEWAY.
    """
    closed = seatbelt.render_profile(_synthetic()).splitlines()
    names = set(_paths(next(line for line in closed if line.startswith("(deny mach-lookup")), "global-name"))
    assert set(SERVICES_ACTING_OUTSIDE) <= names
    opened = seatbelt.render_profile(_synthetic(), clipboard=True).splitlines()
    assert "com.apple.pasteboard.1" not in "\n".join(opened)
    unchanged = [line for line in closed if not line.startswith("(deny mach-lookup")]
    assert unchanged == [line for line in opened if not line.startswith("(deny mach-lookup")]


def test_shared_places_outside_the_homes_are_read_denied_and_grants_come_back() -> None:
    """MACOS-10: /private/tmp, /private/var/tmp, /Volumes and the per-user /private/var/folders directory."""
    lines = seatbelt.render_profile(_synthetic(), shared_roots=SHARED).splitlines()
    denied = set(_paths(lines[2], "subpath"))
    assert {*SHARED, *(DATA + root for root in SHARED)} <= denied
    assert "/private/var/folders" not in denied and "/private" not in denied
    assert _matches(_regexes(lines[2]), USER_DIR.upper() + "/T/babylon60-run-other/note.txt")
    granted = _rule(lines, f'(allow file-read* file-write* file-link file-clone (subpath "{TMP}")')
    assert granted > 2, "the private TMPDIR, inside the per-user directory, is allowed after the deny"


# ---------------------------------------------------------------- behaviour (macOS)

PROBE = r"""
import ctypes, errno, json, mmap, os, signal, subprocess, sys

def kill(pid):
    os.kill(int(pid), signal.SIGTERM)

def own_child():
    child = subprocess.Popen(["/bin/sleep", "30"])
    os.kill(child.pid, signal.SIGTERM)
    return str(child.wait()).encode()

def procargs(pid):
    libc = ctypes.CDLL(None, use_errno=True)
    mib = (ctypes.c_int * 3)(1, 49, int(pid))  # CTL_KERN, KERN_PROCARGS2
    size = ctypes.c_size_t(os.sysconf("SC_ARG_MAX"))
    buffer = ctypes.create_string_buffer(size.value)
    if libc.sysctl(mib, ctypes.c_uint(3), buffer, ctypes.byref(size), None, ctypes.c_size_t(0)) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))
    return buffer.raw[: size.value]

def lookup(name):
    libc = ctypes.CDLL(None)
    port = ctypes.c_uint32(0)
    bootstrap = ctypes.c_uint32.in_dll(libc, "bootstrap_port")
    return str(libc.bootstrap_look_up(bootstrap, name.encode(), ctypes.byref(port))).encode()

def shm_read(name):
    import _posixshmem
    fd = _posixshmem.shm_open(name, os.O_RDONLY, mode=0o600)
    try:
        size = os.fstat(fd).st_size
        with mmap.mmap(fd, size, prot=mmap.PROT_READ) as view:
            return view[:size]
    finally:
        os.close(fd)

def stat(path):
    os.stat(path)

def read(path):
    with open(path, "rb") as handle:
        return handle.read(4096)

def listdir(path):
    return "\n".join(sorted(os.listdir(path))).encode()

report = {"result": "ok", "data": ""}
try:
    data = globals()[sys.argv[1]](*sys.argv[2:])
    report["data"] = (data or b"").hex()
except OSError as exc:
    report["result"] = errno.errorcode.get(exc.errno or 0, "E%s" % exc.errno)
print(json.dumps(report), flush=True)
"""

# Run as the agent by `babylon60 run`: look for a withheld variable in the exec-time environment
# (KERN_PROCARGS2) of its parent and grandparent, outside the sandbox. Only the name is searched
# for in argv-free form, so the launcher's own command line cannot produce a false positive.
LAUNCHER_PROBE = r"""
import ctypes, os
libc = ctypes.CDLL(None, use_errno=True)

def procargs(pid):
    mib = (ctypes.c_int * 3)(1, 49, pid)
    size = ctypes.c_size_t(os.sysconf("SC_ARG_MAX"))
    buffer = ctypes.create_string_buffer(size.value)
    if libc.sysctl(mib, ctypes.c_uint(3), buffer, ctypes.byref(size), None, ctypes.c_size_t(0)) != 0:
        return b""
    return buffer.raw[: size.value]

# The launcher is this process's parent: run re-executes itself without the withheld variables.
if b"B60_PROBE_TOKEN=B60-CANARY-" in procargs(os.getppid()):
    print("FOUND", os.getppid(), flush=True)
print("DONE", flush=True)
"""


@pytest.fixture
def box(tmp_path: Path) -> Box:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    key = home / ".ssh" / "id_rsa"
    key.write_text(f"B60-CANARY-{secrets.token_hex(8)}\n")
    ws = tmp_path / "ws"
    ws.mkdir()
    policy = build_policy(ws, homes=[str(home), *default_homes()], runtime=[launcher.interpreter_prefix()])
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "LC_ALL": "C"}
    return Box(tmp_path, home, key, ws, policy, env)


def _probe(box: Box, action: str, *args: object, confined: bool = True, new_session: bool = False) -> dict[str, Any]:
    """The same probe under the box's policy, or without confinement (``confined=False``, the control).

    PROBE prints its report once its action is done. With a report, the trampoline must have exec'd
    it (status ok). Without one, a launcher timeout (60 s) leaves the measurement inconclusive, a skip
    with the reason; any other missing report fails the test.
    """
    argv = [launcher.interpreter(), "-I", "-S", "-B", "-c", PROBE, action, *map(str, args)]
    launch = launcher.Launch(argv, box.policy if confined else None, new_session=new_session)
    result = launcher.run(launch, env=box.env, cwd=str(box.ws))
    stderr = result.stderr.decode("utf-8", "replace")
    for line in reversed(result.stdout.decode("utf-8", "replace").splitlines()):
        with contextlib.suppress(ValueError):
            report = json.loads(line)
            if isinstance(report, dict):
                assert result.status.get("ok"), (result.status, stderr)
                return report
    if result.status.get("timeout"):
        where = "confined" if confined else "unconfined"
        pytest.skip(
            f"the probe ({action}) did not report within the launcher's timeout, {where}; "
            f"inconclusive: {stderr[-2000:]!r}"
        )
    assert result.status.get("ok"), (result.status, stderr)
    raise AssertionError(stderr)


def _appeared(path: Path, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists() and path.stat().st_size:
            return True
        time.sleep(0.2)
    return False


def _escaped(box: Box, marker: Path) -> bool:
    """The payload outside the sandbox copied the decoy key into ``marker``."""
    return _appeared(marker) and marker.read_bytes() == box.key.read_bytes()


def _script_app(bundle: Path, script: str) -> Path:
    """An app whose executable is a shell script, with no Dock icon: what an agent can write in its workspace."""
    (bundle / "Contents" / "MacOS").mkdir(parents=True)
    info = {
        "CFBundleExecutable": "probe",
        "CFBundleIdentifier": f"org.babylon60.probe.{secrets.token_hex(4)}",
        "CFBundleName": "B60Probe",
        "CFBundlePackageType": "APPL",
        "LSUIElement": True,
    }
    (bundle / "Contents" / "Info.plist").write_bytes(plistlib.dumps(info))
    executable = bundle / "Contents" / "MacOS" / "probe"
    executable.write_text(script)
    executable.chmod(0o755)
    return bundle


def _copy_key(box: Box, marker: Path) -> str:
    return f"/bin/cat '{box.key}' > '{marker}'"


def _bounded(
    argv: list[str], *, timeout: float, env: dict[str, str] | None = None, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run ``argv`` in a process group of its own; past ``timeout``, end the group (SIGTERM, then SIGKILL).

    The run never hangs the job: `babylon60 run` forwards SIGTERM to the agent's session and ends it.
    """
    process = subprocess.Popen(
        argv,
        env=env,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        errors="replace",
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        stdout = stderr = ""
        for ending in (signal.SIGTERM, signal.SIGKILL):
            with contextlib.suppress(OSError):
                os.killpg(process.pid, ending)
            try:
                stdout, stderr = process.communicate(timeout=30)
                break
            except subprocess.TimeoutExpired:
                continue
        else:  # something outside the group still holds the pipes
            for pipe in (process.stdout, process.stderr):
                if pipe is not None:
                    pipe.close()
            process.wait()
        stderr += f"\n[ended after {timeout:.0f} s without finishing]"
    return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)


def _quietly(argv: list[str], timeout: float) -> subprocess.CompletedProcess[bytes] | None:
    """Clean-up and setup commands: None when they time out, so a finally block always completes."""
    try:
        return subprocess.run(argv, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None


def _as_run(
    box: Box, argv: list[str], *, confined: bool = True, timeout: float = 240, stdin_data: bytes | None = None
) -> launcher.Result:
    """``argv`` started as `babylon60 run` starts the agent (``run_launch``: a new session, a private TMPDIR).

    The environment is the box's plus what `run` adds: TMPDIR and the variables it points into the
    private TMPDIR (``cli.private_tmp_environment``: clang's module cache, and Chrome's temporary
    directory on macOS). ``confined=False`` is the control: the same trampoline, session, TMPDIR and
    environment, no policy. ``stdin_data`` is the command's standard input (otherwise /dev/null).
    """
    private_tmp = Path(tempfile.mkdtemp(prefix="tmp-", dir=box.root))
    env = {**box.env, **cli.private_tmp_environment(box.env, str(private_tmp))}
    if confined:
        launch = launcher.run_launch(argv, box.policy_with(private_tmp=str(private_tmp)))
    else:
        launch = launcher.Launch(argv, None, new_session=True)
    result = launcher.run(launch, env=env, cwd=str(box.ws), timeout=timeout, stdin_data=stdin_data)
    if result.status.get("timeout") and isinstance(result.status.get("pid"), int):
        # The launcher killed only the target, which led its own session and process group: end what it left.
        with contextlib.suppress(OSError):
            os.killpg(result.status["pid"], signal.SIGKILL)
    return result


def _last_json(result: launcher.Result) -> dict[str, Any]:
    """The JSON report a payload prints last, or what the launcher said when there is none."""
    for line in reversed(result.stdout.decode("utf-8", "replace").splitlines()):
        try:
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                return parsed
        except ValueError:
            continue
    return {"status": result.status, "stderr": result.stderr.decode("utf-8", "replace")[-2000:]}


def _stderr(result: launcher.Result) -> str:
    return result.stderr.decode("utf-8", "replace")[-2000:]


def _control_as_run(
    box: Box, argv: list[str], what: str, *, timeout: float = 120, stdin_data: bytes | None = None
) -> launcher.Result:
    """The unconfined control, launched as the confined attempt will be: ``_as_run`` without a policy.

    Only the policy then tells the two apart. A timeout leaves nothing to compare (skip with the reason);
    an exec the trampoline refused without any policy is a broken harness (failure).
    """
    result = _as_run(box, argv, confined=False, timeout=timeout, stdin_data=stdin_data)
    stderr = _stderr(result)
    if result.status.get("timeout"):
        pytest.skip(f"{what} did not finish in {timeout:.0f} s even unconfined; nothing to compare: {stderr!r}")
    assert result.status.get("ok"), f"{what}: the unconfined trampoline did not exec it ({result.status}): {stderr!r}"
    return result


def _closed(result: launcher.Result, effect: bool, finding: str, what: str) -> None:
    """The confined attempt (``result``) had no effect, and that absence counts.

    An effect fails the test whatever the launcher reports, so neither a timeout nor a refused exec
    can hide one. Without an effect, the trampoline must have exec'd ``what`` (status ok), or the
    absence would be vacuous; a launcher timeout leaves it inconclusive: a skip with the reason, never
    a pass.
    """
    stderr = _stderr(result)
    assert not effect, f"{finding} (launcher status: {result.status}; stderr: {stderr!r})"
    if result.status.get("timeout"):
        pytest.skip(f"{what} did not finish within the launcher's timeout, confined; inconclusive: {stderr!r}")
    assert result.status.get("ok"), f"{what} never ran: the trampoline did not exec it ({result.status}): {stderr!r}"


# MACOS-1 ----------------------------------------------------------------------------------------


LSREGISTER = "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
# Everything allowed but LaunchServices opens: what "(deny lsopen)" stops on its own.
LSOPEN_ONLY = "(version 1)\n(allow default)\n(deny lsopen)\n"


@pytest.fixture
def opened_app(box: Box) -> Iterator[tuple[list[str], Path]]:
    """`open` of an app in the workspace that copies the decoy key to a marker, and that marker.

    The control has already started it, launched as the confined attempt will be (``_as_run``, no
    policy); without that effect the test skips. LaunchServices registers the app when it opens it:
    the registration is removed in finally.
    """
    marker = box.root / f"lsopen-{secrets.token_hex(4)}"
    app = _script_app(box.ws / "B60Probe.app", f"#!/bin/sh\n{_copy_key(box, marker)}\n")
    argv = ["/usr/bin/open", "-g", "-n", str(app)]
    try:
        control = _control_as_run(box, argv, "open", timeout=60)
        if not _escaped(box, marker):
            pytest.skip(f"LaunchServices does not launch apps in this session even unconfined: {_stderr(control)!r}")
        marker.unlink()
        yield argv, marker
    finally:
        if os.path.exists(LSREGISTER):
            _quietly([LSREGISTER, "-u", str(app)], 60)


@macos
@pytest.mark.parametrize("profile", ["run-profile", "lsopen-only"])
def test_launch_services_cannot_start_code_outside_the_sandbox(
    box: Box, opened_app: tuple[list[str], Path], profile: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MACOS-1: an app that `open` starts runs outside the sandbox, so the app must not start.

    ``run-profile`` is the profile `run` renders. ``lsopen-only`` has the patched renderer return
    LSOPEN_ONLY, where nothing but "(deny lsopen)" is denied: a closure there is that rule's alone.
    The app reads the key outside the sandbox, so no file rule is involved either way.
    """
    argv, marker = opened_app
    rendered: list[str] = []
    if profile == "lsopen-only":

        def lsopen_only(policy: Policy, **options: Any) -> str:
            rendered.append(profile)
            return LSOPEN_ONLY

        monkeypatch.setattr(seatbelt, "render_profile", lsopen_only)
    confined = _as_run(box, argv, timeout=60)
    if profile == "lsopen-only":
        assert rendered == [profile], "the launcher did not render this profile through seatbelt.render_profile"
    finding = f"MACOS-1: an app opened from inside the sandbox read the protected key outside it ({profile})"
    _closed(confined, _escaped(box, marker), finding, "open")


@macos
def test_without_deny_lsopen_the_profile_lets_open_start_an_app(
    box: Box, opened_app: tuple[list[str], Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Negative control for MACOS-1: the profile `run` renders, minus its "(deny lsopen)" line.

    A pass is an escape under that weakened profile: nothing else in it (Apple Events, the window
    server and Apple Event lookups, the file-write fallback over the per-user directory) stops `open`,
    so "(deny lsopen)" is what closes MACOS-1. If the app does not start, the test skips and says so:
    another rule is in the way too, and this test does not isolate which.
    """
    argv, marker = opened_app
    render = seatbelt.render_profile
    removed: list[bool] = []

    def without_lsopen(policy: Policy, **options: Any) -> str:
        lines = render(policy, **options).splitlines()
        removed.append("(deny lsopen)" in lines)
        return "\n".join(line for line in lines if line != "(deny lsopen)") + "\n"

    monkeypatch.setattr(seatbelt, "render_profile", without_lsopen)
    weakened = _as_run(box, argv, timeout=60)
    assert removed == [True], "the launcher did not render the profile through seatbelt.render_profile"
    if weakened.status.get("timeout"):
        pytest.skip(f"open did not finish within the launcher's timeout; inconclusive: {_stderr(weakened)!r}")
    assert weakened.status.get("ok"), f"open never ran: {weakened.status} {_stderr(weakened)!r}"
    if not _escaped(box, marker):
        pytest.skip(
            "without (deny lsopen) the rest of the profile still keeps open from starting the app: another rule "
            f"is in the way too; stderr: {_stderr(weakened)!r}"
        )


# MACOS-2 ----------------------------------------------------------------------------------------


# osascript reached run time and the event failed there: AppleScript's "execution error", or one of the
# codes a refused or undeliverable event gives (errAEEventNotPermitted, procNotFound, errAEPrivilegeError).
# A "syntax error" is a compile-time error, before any event is sent.
APPLE_EVENT_REFUSALS = ("execution error", "(-1743)", "(-600)", "(-10004)")


@macos
@pytest.mark.parametrize("target", ["Finder", "Terminal"])
def test_apple_events_cannot_make_another_app_run_code(box: Box, target: str, request: pytest.FixtureRequest) -> None:
    """MACOS-2: an Apple Event makes another app run code for the sender, outside the sandbox.

    Control and attempt are launched alike (``_as_run``: a new session, a private TMPDIR, the decoy
    HOME), so only the policy tells them apart. The control skips on its own timeout of 90 s (likely
    a consent dialog nobody answers in the CI, inferred: [Terminal]'s control timed out so at
    f3242c4, named in its JUnit, while [Finder] passed) or when it has no effect. Confined, an effect fails, and through ``_closed``
    a launcher timeout skips and osascript must have been exec'd. The absent effect counts only when
    osascript reached run time and the event failed there: a non-zero exit with an AppleScript
    execution error or a refusal code (APPLE_EVENT_REFUSALS) in its stderr; otherwise the test skips
    with that stderr. On a pass, the confined stderr is the JUnit property "osascript_confined_stderr".
    """
    marker = box.root / f"appleevent-{secrets.token_hex(4)}"
    app: Path | None = None
    if target == "Finder":
        app = _script_app(box.ws / "B60Probe.app", f"#!/bin/sh\n{_copy_key(box, marker)}\n")
        script = f'tell application "Finder" to open (POSIX file "{app}")'
    else:
        script = f'tell application "Terminal" to do script "{_copy_key(box, marker)}; exit"'
    argv = ["/usr/bin/osascript", "-e", script]
    try:
        control = _control_as_run(box, argv, f"osascript to {target}", timeout=90)
        if control.returncode != 0 or not _escaped(box, marker):
            pytest.skip(f"Apple Events to {target} are not authorized here even unconfined: {_stderr(control)!r}")
        marker.unlink()
        confined = _as_run(box, argv, timeout=90)
        stderr = _stderr(confined)
        request.node.user_properties.append(("osascript_confined_stderr", stderr))
        finding = f"MACOS-2: {target} ran code for the confined process, outside the sandbox"
        _closed(confined, _escaped(box, marker), finding, "osascript")
        if confined.returncode == 0 or not any(refusal in stderr for refusal in APPLE_EVENT_REFUSALS):
            pytest.skip(
                f"osascript to {target} exited {confined.returncode} confined without an execution error, so it "
                f"may never have sent the event; the absent effect is inconclusive: {stderr!r}"
            )
    finally:
        if app is not None and os.path.exists(LSREGISTER):  # Finder registered it with LaunchServices
            _quietly([LSREGISTER, "-u", str(app)], 60)


# MACOS-3 ----------------------------------------------------------------------------------------


def _launchctl(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["/bin/launchctl", *args], capture_output=True, timeout=30)


@macos
@pytest.mark.parametrize("how", ["submit", "bootstrap"])
def test_launchd_jobs_cannot_be_created(box: Box, how: str) -> None:
    """MACOS-3: launchd starts a job outside the sandbox; `launchctl submit` or `bootstrap` must create none.

    The job copies the decoy key to a marker. Control and attempt are launched alike
    (``_control_as_run``, ``_as_run``), so only the policy tells them apart; the control must leave
    its marker or the test skips. Confined, an effect fails, and through ``_closed`` launchctl must
    have been exec'd. Until AX-226 the confined attempt ran through ``box.run`` and the test passed
    without checking that. Each job is removed in finally.
    """
    domains = [f"gui/{os.getuid()}", f"user/{os.getuid()}"]

    def job() -> tuple[list[str], Path, str, str | None]:
        marker = box.root / f"launchd-{secrets.token_hex(4)}"
        label = f"org.babylon60.probe.{secrets.token_hex(4)}"
        command = [
            "/bin/sh",
            "-c",
            f"{_copy_key(box, marker)}; sleep 600",
        ]  # the sleep keeps launchd from respawning it
        if how == "submit":
            return ["/bin/launchctl", "submit", "-l", label, "--", *command], marker, label, None
        plist = box.ws / f"{label}.plist"
        plist.write_bytes(plistlib.dumps({"Label": label, "ProgramArguments": command, "RunAtLoad": True}))
        domain = next((d for d in domains if _launchctl("print", d).returncode == 0), domains[-1])
        return ["/bin/launchctl", "bootstrap", domain, str(plist)], marker, label, domain

    def remove(label: str, domain: str | None) -> None:
        _launchctl("remove", label) if domain is None else _launchctl("bootout", f"{domain}/{label}")

    argv, marker, label, domain = job()
    try:
        control = _control_as_run(box, argv, f"launchctl {how}", timeout=60)
        if not _escaped(box, marker):
            pytest.skip(f"launchctl {how} does not start jobs here even unconfined: {_stderr(control)!r}")
    finally:
        remove(label, domain)
    argv, marker, label, domain = job()
    try:
        confined = _as_run(box, argv, timeout=60)
        finding = f"MACOS-3: launchctl {how} from inside the sandbox ran a job outside it"
        _closed(confined, _escaped(box, marker), finding, f"launchctl {how}")
    finally:
        remove(label, domain)


def _launchd_env(name: str) -> str:
    done = _launchctl("getenv", name)
    return done.stdout.decode("utf-8", "replace").strip()


@macos
def test_launchd_environment_cannot_be_changed(box: Box) -> None:
    """MACOS-3: `launchctl setenv` sets a variable for every program launchd starts later, outside the sandbox.

    No job is created, so "(deny job-creation)" may not cover it; this measures it. The control's
    setenv is launched as the confined one (``_as_run``); getenv and unsetenv run unconfined.
    """
    name = f"B60_PROBE_{secrets.token_hex(4).upper()}"
    control_value, canary = f"B60-CONTROL-{secrets.token_hex(8)}", f"B60-CANARY-{secrets.token_hex(8)}"
    try:
        control = _control_as_run(box, ["/bin/launchctl", "setenv", name, control_value], "launchctl setenv")
        works = _launchd_env(name) == control_value
        _launchctl("unsetenv", name)
        if not works or _launchd_env(name):
            pytest.skip(
                "launchctl setenv, getenv and unsetenv do not work in this session even unconfined: "
                f"{_stderr(control)!r}"
            )
        attempt = _as_run(box, ["/bin/launchctl", "setenv", name, canary], timeout=60)
        finding = f"MACOS-3: the confined process set {name} for the programs launchd starts later"
        _closed(attempt, canary in _launchd_env(name), finding, "launchctl setenv")
    finally:
        _launchctl("unsetenv", name)


# MACOS-4 ----------------------------------------------------------------------------------------


def _victim(where: str, victim: str, canary: str) -> tuple[list[str], dict[str, str]]:
    """A process outside the sandbox holding ``canary`` in its exec-time environment or arguments."""
    env = {"PATH": "/usr/bin:/bin"}
    if victim == "interpreter":
        argv = [launcher.interpreter(), "-I", "-S", "-c", "import time; time.sleep(120)"]
    else:  # a platform binary: /bin/sleep takes no extra arguments, /bin/sh keeps them in its own argv
        # "; exit 0" keeps the shell from exec'ing sleep in its place, which would drop the extra argument.
        argv = ["/bin/sleep", "120"] if where == "environment" else ["/bin/sh", "-c", "sleep 120; exit 0", "sh"]
    if where == "environment":
        env["B60_PROBE_TOKEN"] = canary
    else:
        argv.append(f"--api-token={canary}")
    return argv, env


@macos
@pytest.mark.parametrize("session", ["same-process-group", "new-session"])
@pytest.mark.parametrize("victim", ["interpreter", "platform-binary"])
@pytest.mark.parametrize("where", ["environment", "arguments"])
def test_other_processes_exec_strings_are_not_readable(box: Box, where: str, victim: str, session: str) -> None:
    """MACOS-4: KERN_PROCARGS2 (`ps -E`) of a process outside the sandbox, as V22 and L6 measure it.

    ``run`` starts the agent in a new session; the probe also runs in the victim's process group,
    which "(target others)" alone did not cover. XNU leaves out the environment of restricted
    targets (entitlements, setuid), so a plain interpreter is tried as well as a platform binary.
    """
    canary = f"B60-CANARY-{secrets.token_hex(8)}"
    argv, env = _victim(where, victim, canary)
    process = subprocess.Popen(argv, env=env)
    try:
        control = _probe(box, "procargs", process.pid, confined=False)
        if canary.encode() not in bytes.fromhex(control["data"]):
            pytest.skip(f"KERN_PROCARGS2 omits the {where} of {argv[0]} even unconfined ({control['result']})")
        report = _probe(box, "procargs", process.pid, new_session=session == "new-session")
        assert canary.encode() not in bytes.fromhex(report["data"]), (
            f"MACOS-4: the confined process read the {where} of a process outside the sandbox ({session})"
        )
        assert report["result"] in ("EPERM", "EACCES"), report  # denied, not merely empty
    finally:
        process.kill()
        process.wait()


@macos
def test_run_withheld_credentials_stay_out_of_reach(tmp_path: Path) -> None:
    """`run` withholds B60_PROBE_TOKEN from the agent; its own exec-time environment must not hand it back."""
    canary = f"B60-CANARY-{secrets.token_hex(8)}"
    home, ws = tmp_path / "home", tmp_path / "ws"
    home.mkdir()
    ws.mkdir()
    probe = ws / "probe.py"
    probe.write_text(LAUNCHER_PROBE)
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(home),
        "LC_ALL": "C",
        "PYTHONPATH": str(ROOT / "01_KISH_ENGINE"),
        "B60_PROBE_TOKEN": canary,
    }
    agent = [launcher.interpreter(), "-I", "-S", str(probe)]
    parent = [launcher.interpreter(), "-I", "-S", "-c", "import subprocess, sys; subprocess.run(sys.argv[1:])"]
    control = subprocess.run([*parent, *agent], env=env, cwd=ws, capture_output=True, text=True, timeout=60)
    if "FOUND" not in control.stdout:
        pytest.skip(f"a parent's environment is not readable here even unconfined: {control.stdout!r}")
    done = subprocess.run(
        [
            sys.executable,
            "-P",
            "-m",
            "babylon60.cli.main_dispatcher",
            "run",
            "--journal",
            str(tmp_path / "j.db"),
            "--",
            *agent,
        ],
        env=env,
        cwd=ws,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert "B60_PROBE_TOKEN" in done.stderr and "DONE" in done.stdout, (done.stdout, done.stderr)
    assert "FOUND" not in done.stdout, (
        "MACOS-4: the agent read a variable `run` withheld, from the launcher's environment"
    )


# MACOS-6 ----------------------------------------------------------------------------------------


@macos
def test_processes_outside_the_sandbox_cannot_be_signalled(box: Box) -> None:
    control_victim = subprocess.Popen(["/bin/sleep", "120"])
    victim = subprocess.Popen(["/bin/sleep", "120"])
    try:
        assert _probe(box, "kill", control_victim.pid, confined=False)["result"] == "ok"
        assert control_victim.wait(timeout=10) == -15
        try:
            report = _probe(box, "kill", victim.pid)
        except pytest.skip.Exception:  # no report within the launcher's timeout: an ended victim still fails
            time.sleep(0.5)
            assert victim.poll() is None, f"MACOS-6: the confined process ended {victim.pid}"
            raise
        time.sleep(0.5)
        assert victim.poll() is None and report["result"] in DENIED, f"MACOS-6: the confined process ended {victim.pid}"
        assert _probe(box, "own_child")["result"] == "ok", "the agent must still end its own children"
    finally:
        for process in (control_victim, victim):
            process.kill()
            process.wait()


@macos
def test_the_agent_cannot_end_its_launcher(tmp_path: Path) -> None:
    """SIGKILL to `babylon60 run` skips run_end, the persistence and metadata comparison and the teardown."""
    home, ws = tmp_path / "home", tmp_path / "ws"
    home.mkdir()
    ws.mkdir()
    journal = tmp_path / "j.db"
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "LC_ALL": "C", "PYTHONPATH": str(ROOT / "01_KISH_ENGINE")}
    script = "import os, signal; os.kill(os.getppid(), signal.SIGKILL)"
    parent = "import subprocess, sys; subprocess.run(sys.argv[1:]); print('parent survived')"
    agent = [launcher.interpreter(), "-I", "-S", "-c", script]
    control = subprocess.run(
        [launcher.interpreter(), "-I", "-S", "-c", parent, *agent], capture_output=True, timeout=60
    )
    assert control.returncode == -9, "control: without confinement a child can SIGKILL its parent"
    cli = [sys.executable, "-P", "-m", "babylon60.cli.main_dispatcher"]
    done = subprocess.run(
        [*cli, "run", "--journal", str(journal), "--", *agent],
        env=env,
        cwd=ws,
        capture_output=True,
        timeout=180,
    )
    log = subprocess.run([*cli, "log", "--journal", str(journal), "--json"], env=env, capture_output=True, timeout=60)
    kinds = [entry["kind"] for entry in json.loads(log.stdout)["entries"]]
    assert done.returncode != -9 and "run_end" in kinds, f"MACOS-6: the agent killed its launcher ({kinds})"


# MACOS-7 ----------------------------------------------------------------------------------------

DEFAULTS = "/usr/bin/defaults"


def _defaults(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([DEFAULTS, *args], capture_output=True, text=True, timeout=30)


@macos
def test_preferences_are_not_a_way_to_write_outside_the_grants(box: Box) -> None:
    """MACOS-7: cfprefsd writes ~/Library/Preferences for a `defaults write`, outside every grant.

    Control and attempt are launched alike (``_control_as_run``, ``_as_run``), so only the policy tells
    them apart; each write is read back with the test's own environment (in the read test below, which
    passed at f3242c4, `defaults` with the decoy HOME read what this environment wrote, so cfprefsd
    does not follow $HOME: inferred). The control's value must come back or the test skips.
    Confined, an effect fails, and through ``_closed`` `defaults` must have been exec'd. Until AX-226
    the confined write ran through ``box.run`` and the test passed without checking that.
    """
    domain = f"org.babylon60.probe.{secrets.token_hex(4)}"
    control_value, canary = f"B60-CONTROL-{secrets.token_hex(8)}", f"B60-CANARY-{secrets.token_hex(8)}"
    try:
        control = _control_as_run(box, [DEFAULTS, "write", domain, "control", control_value], "defaults write")
        if _defaults("read", domain, "control").stdout.strip() != control_value:
            pytest.skip(
                "defaults write, launched as the agent is but unconfined, does not reach cfprefsd here: "
                f"{_stderr(control)!r}"
            )
        confined = _as_run(box, [DEFAULTS, "write", domain, "planted", canary], timeout=60)
        finding = f"MACOS-7: cfprefsd wrote ~/Library/Preferences/{domain}.plist for the confined process"
        _closed(confined, canary in _defaults("read", domain, "planted").stdout, finding, "defaults write")
    finally:
        _defaults("delete", domain)


@macos
def test_preferences_of_other_programs_are_not_readable(box: Box) -> None:
    """MACOS-7: it XPASSED, marked xfail, in the CI of 48a4593, d594608 and ae39991.

    Only user-preference-write is denied, yet the confined `defaults read` got nothing. Why (cfprefsd
    applying the caller's file rules to the plist in the denied home, or something else) is not measured.
    Those runs compared an unconfined read with the test's own environment against a confined one with
    the decoy HOME and nothing else; here the control read is launched as the confined one
    (``_as_run``, same environment), so only the policy differs.
    """
    domain = f"org.babylon60.probe.{secrets.token_hex(4)}"
    canary = f"B60-CANARY-{secrets.token_hex(8)}"
    argv = [DEFAULTS, "read", domain, "token"]
    try:
        if _defaults("write", domain, "token", canary).returncode:
            pytest.skip("cfprefsd does not serve this session")
        control = _control_as_run(box, argv, "defaults read")
        if canary.encode() not in control.stdout:
            plain = canary in _defaults("read", domain, "token").stdout  # with the test's own environment
            pytest.skip(
                "defaults read, launched as the agent is but unconfined, does not see the value written here "
                f"(a read with the test's own environment does: {plain}); nothing to compare: {_stderr(control)!r}"
            )
        confined = _as_run(box, argv, timeout=60)
        finding = "MACOS-7: cfprefsd read a home plist for the confined process"
        _closed(confined, canary.encode() in confined.stdout, finding, "defaults read")
    finally:
        _defaults("delete", domain)


# MACOS-8 ----------------------------------------------------------------------------------------


def _pasted() -> bytes:
    """What the user would paste now, read with the test's own environment."""
    return subprocess.run(["/usr/bin/pbpaste"], capture_output=True, timeout=30).stdout


@macos
def test_the_pasteboard_is_neither_readable_nor_writable(box: Box) -> None:
    """MACOS-8: pbpaste reads and pbcopy replaces what the user pastes next, through the pasteboard server.

    Each command is launched as `run` launches the agent (``_as_run``) after a control launched alike
    without a policy (``_control_as_run``) that must have its effect, or the test skips. pbcopy is
    exec'd itself, with the text on its standard input, so that the exec ``_closed`` requires is its
    own. Until AX-226 the confined commands ran through ``box.run`` (pbcopy behind /bin/sh) and the test
    passed without checking that they ran. What the user had copied is put back in finally.
    """
    canary = f"B60-CANARY-{secrets.token_hex(8)}"
    previous = _pasted()
    try:
        copied = subprocess.run(["/usr/bin/pbcopy"], input=canary.encode(), capture_output=True, timeout=30)
        control = _control_as_run(box, ["/usr/bin/pbpaste"], "pbpaste", timeout=60)
        if copied.returncode or canary.encode() not in control.stdout:
            pytest.skip(
                f"pbcopy exited {copied.returncode} unconfined, and pbpaste launched as the agent is but unconfined "
                "does not read what it copied (a read with the test's own environment does: "
                f"{canary.encode() in _pasted()}): {_stderr(control)!r}"
            )
        confined = _as_run(box, ["/usr/bin/pbpaste"], timeout=60)
        _closed(
            confined, canary.encode() in confined.stdout, "MACOS-8: the confined process read the clipboard", "pbpaste"
        )
        copied_by_control = f"B60-PASTE-{secrets.token_hex(8)}"
        control = _control_as_run(box, ["/usr/bin/pbcopy"], "pbcopy", timeout=60, stdin_data=copied_by_control.encode())
        if copied_by_control.encode() not in _pasted():
            pytest.skip(
                f"pbcopy, launched as the agent is but unconfined, does not replace the clipboard: {_stderr(control)!r}"
            )
        planted = f"B60-PASTE-{secrets.token_hex(8)}"
        confined = _as_run(box, ["/usr/bin/pbcopy"], timeout=60, stdin_data=planted.encode())
        finding = "MACOS-8: the confined process replaced what the user pastes next"
        _closed(confined, planted.encode() in _pasted(), finding, "pbcopy")
    finally:
        subprocess.run(["/usr/bin/pbcopy"], input=previous, capture_output=True, timeout=30)


# MACOS-9, MACOS-11 ------------------------------------------------------------------------------


@macos
@pytest.mark.parametrize("service", SERVICES_ACTING_OUTSIDE)
def test_services_that_act_outside_the_sandbox_are_not_reachable(box: Box, service: str) -> None:
    control = bytes.fromhex(_probe(box, "lookup", service, confined=False)["data"])
    if control != b"0":
        pytest.skip(f"{service} is not registered in this session (bootstrap_look_up returned {control.decode()})")
    report = bytes.fromhex(_probe(box, "lookup", service)["data"])
    assert report != b"0", f"MACOS-9/11: {service} is reachable from inside the sandbox"


SCREENCAPTURE = "/usr/sbin/screencapture"
PNG = b"\x89PNG\r\n\x1a\n"


def _png(path: Path) -> bool:
    try:
        with open(path, "rb") as handle:
            return handle.read(len(PNG)) == PNG
    except OSError:
        return False


@macos
def test_the_screen_cannot_be_captured(box: Box) -> None:
    """INV_C5_COMPUTER_USE_TRUST_GATEWAY: no screenshot of the user's windows from inside the sandbox.

    The image goes to the workspace, which the confined process may write. Control and attempt are
    launched alike (``_as_run``: a new session and a private TMPDIR each may write), so the TMPDIR is
    not what tells them apart; other files screencapture may need are not ruled out here. The test
    after this one measures the window server's part in-process, where the probe writes no file.
    """
    if not os.path.exists(SCREENCAPTURE):
        pytest.skip(f"no {SCREENCAPTURE}")
    shot = box.ws / "shot.png"
    argv = [SCREENCAPTURE, "-x", str(shot)]
    control = _control_as_run(box, argv, "screencapture", timeout=60)
    if not _png(shot):
        pytest.skip(
            "screencapture produces no image here even unconfined (no window server session or no Screen "
            f"Recording grant), so there is nothing to compare: {_stderr(control)!r}"
        )
    shot.unlink()
    confined = _as_run(box, argv, timeout=60)
    _closed(confined, _png(shot), "the confined process captured the screen", "screencapture")
