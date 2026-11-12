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


def _probe(box: Box, action: str, *args: object, confined: bool = True, new_session: bool = False) -> dict:
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
            return json.loads(line)
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


# Ask CoreGraphics for an image of the main display, in this process, with no file involved: one JSON
# line once the symbols resolve ("loaded"), one more if the calls return ("returned").
DISPLAY_PROBE = r"""
import ctypes, json
graphics = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
try:
    main_display, create_image = graphics.CGMainDisplayID, graphics.CGDisplayCreateImage
    release = graphics.CGImageRelease
except AttributeError as exc:
    print(json.dumps({"stage": "missing", "error": str(exc)}), flush=True)
    raise SystemExit(0)
main_display.restype = ctypes.c_uint32
create_image.argtypes, create_image.restype = [ctypes.c_uint32], ctypes.c_void_p
release.argtypes, release.restype = [ctypes.c_void_p], None
print(json.dumps({"stage": "loaded"}), flush=True)
display = main_display()
image = create_image(display)
print(json.dumps({"stage": "returned", "display": display, "image": bool(image)}), flush=True)
if image:
    release(image)
"""


def _display_stages(result: launcher.Result) -> dict[str, dict[str, Any]]:
    stages: dict[str, dict[str, Any]] = {}
    for line in result.stdout.decode("utf-8", "replace").splitlines():
        with contextlib.suppress(ValueError):
            report = json.loads(line)
            if isinstance(report, dict) and isinstance(report.get("stage"), str):
                stages[report["stage"]] = report
    return stages


@macos
def test_the_window_server_gives_the_sandbox_no_image_of_the_display(box: Box) -> None:
    """The window server's part in test_the_screen_cannot_be_captured, measured in-process.

    DISPLAY_PROBE calls CGMainDisplayID and CGDisplayCreateImage. The control, launched as the confined
    attempt (``_as_run``, no policy), must get an image (non-NULL); confined, the probe must reach the
    calls and get none (NULL, or no return at all). Unlike screencapture, the probe writes no file: the
    image would stay in memory, so what withholds it is inside CoreGraphics' calls, where the window
    server answers. Which rule of the profile causes it (the com.apple.windowserver.active lookup, or
    another, such as a file CoreGraphics needs to read) is not isolated here.
    """
    argv = [launcher.interpreter(), "-I", "-S", "-c", DISPLAY_PROBE]
    control = _control_as_run(box, argv, "the display probe", timeout=60)
    stages = _display_stages(control)
    if not stages.get("returned", {}).get("image"):
        pytest.skip(
            "CGDisplayCreateImage gives no image of the display here even unconfined (no window server "
            f"session, no Screen Recording grant or no such symbol): {stages} {_stderr(control)!r}"
        )
    confined = _as_run(box, argv, timeout=60)
    stages = _display_stages(confined)
    finding = "INV_C5_COMPUTER_USE_TRUST_GATEWAY: the window server gave the confined process an image of the display"
    _closed(confined, bool(stages.get("returned", {}).get("image")), finding, "the display probe")
    if "loaded" not in stages:
        pytest.skip(
            "the confined probe never reached CGMainDisplayID, so the absent image says nothing about the "
            f"window server: {stages} {_stderr(confined)!r}"
        )


# MACOS-10 ----------------------------------------------------------------------------------------


@macos
def test_files_of_other_programs_outside_the_homes_are_not_readable(box: Box) -> None:
    """MACOS-10: the shared places the profile read-denies, each measured with the same probe unconfined first.

    Decoy files the runner user writes (mode 0600, removed in finally): another session's private
    TMPDIR in the per-user directory, /private/tmp and /private/var/tmp (both world-writable and
    sticky). /Volumes, where the user plants no file, has its own test below.
    """
    canary = f"B60-CANARY-{secrets.token_hex(8)}"
    user_temp = os.confstr(65537)  # _CS_DARWIN_USER_TEMP_DIR, where `run` creates every session's private TMPDIR
    sibling = Path(tempfile.mkdtemp(prefix="babylon60-run-", dir=user_temp))  # another session's private TMPDIR
    shared = Path(tempfile.mkdtemp(prefix="b60-", dir="/private/tmp"))  # e.g. MIT Kerberos FILE: caches, tool logs
    var_tmp = Path(tempfile.mkdtemp(prefix="b60-", dir="/private/var/tmp"))  # world-writable and sticky, as /tmp
    try:
        for path in (sibling / "note.txt", shared / f"krb5cc_{os.getuid()}", var_tmp / "note.txt"):
            path.write_text(canary)
            path.chmod(0o600)
            assert _probe(box, "read", path, confined=False)["data"] == canary.encode().hex()
            report = _probe(box, "read", path)
            assert report["result"] in DENIED and not report["data"], f"MACOS-10: {path} is readable from the sandbox"
    finally:
        for directory in (sibling, shared, var_tmp):
            shutil.rmtree(directory, ignore_errors=True)


@macos
def test_mounted_volumes_are_not_listed_from_the_sandbox(box: Box) -> None:
    """MACOS-10: /Volumes, read-denied by the profile, where mounted disks, shares and backups appear.

    The runner user has no file of its own to plant there, so the effect is the listing: the same
    probe lists /Volumes unconfined (the test skips if it cannot) and must be denied, with no names,
    confined. Apart from the file test above, so that a control without effect here does not hide
    what that one measured.
    """
    control = _probe(box, "listdir", "/Volumes", confined=False)
    if control["result"] != "ok":
        pytest.skip(f"/Volumes cannot be listed here even unconfined: {control}")
    report = _probe(box, "listdir", "/Volumes")
    assert report["result"] in DENIED and not report["data"], f"MACOS-10: /Volumes is listed from the sandbox: {report}"


# MACOS-11 ---------------------------------------------------------------------------------------

# An attach that interrupts sleep() only shortens one of its 120 sleeps, so it outlives the attaches and
# still ends by itself within about ten minutes if nothing kills it (the probe kills its own child, the
# test kills the victim in finally).
SLEEPER = b"#include <unistd.h>\nint main(void){for(int i=0;i<120;i++)sleep(5);}\n"
# Per attach inside DEBUG_PROBE. The first attach of the job may meet a cold lldb, and the -q logs give no
# durations; at f3747db the same attaches had 180 s (the victim, unconfined) and 150 s (an own child).
LLDB_SECONDS = 120
# The launcher's timeout for a DEBUG_PROBE with a victim, the same for every control and attempt: two
# attaches and the probe's own start.
DEBUG_LAUNCH_SECONDS = 2 * LLDB_SECONDS + 60


def _debug_tools() -> tuple[str, str]:
    lldb, cc = shutil.which("lldb", path="/usr/bin"), shutil.which("cc", path="/usr/bin")
    if lldb is None or cc is None:
        pytest.skip("no lldb or no C compiler (Xcode or the Command Line Tools)")
    return lldb, cc


def _build(cc: str, program: Path) -> None:
    built = subprocess.run([cc, "-x", "c", "-", "-o", str(program)], input=SLEEPER, capture_output=True, timeout=300)
    if built.returncode or not program.is_file():
        pytest.skip(f"cc cannot build a program here: {built.stderr[-2000:]!r}")


# Run as the agent: start a child from ``program``, attach lldb to it and call getpid() inside it, then
# end it. Given a pid and an expression, attach lldb to that process too and evaluate the expression
# there. Each attach is bounded (seconds); the child's descriptors are /dev/null, so nothing it leaves
# behind holds the launcher's pipes. The own child's lldb output sits at the top level of the report,
# the other process's under "outside".
DEBUG_PROBE = r"""
import json, subprocess, sys
lldb, program, seconds, *outside = sys.argv[1:]

def attach(pid, expression):
    try:
        done = subprocess.run(
            [lldb, "--batch", "-p", str(pid), "-o", expression, "-o", "process detach"],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=float(seconds),
        )
    except subprocess.TimeoutExpired:
        return {"timeout": float(seconds)}
    return {
        "stdout": done.stdout.decode("utf-8", "replace")[-4000:],
        "stderr": done.stderr.decode("utf-8", "replace")[-4000:],
    }

child = subprocess.Popen([program], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
report = {"pid": child.pid}
try:
    report.update(attach(child.pid, "expr (int)getpid()"))
finally:
    child.kill()
    child.wait()
if outside:
    report["outside"] = attach(int(outside[0]), outside[1])
print(json.dumps(report), flush=True)
"""


def _evaluated_in_child(report: dict[str, Any]) -> bool:
    """lldb printed ``(int) $N = <pid>``: getpid() ran inside the child it attached to."""
    pid, stdout = report.get("pid"), str(report.get("stdout", ""))
    return isinstance(pid, int) and re.search(rf"\(int\) \$\d+ = {pid}\b", stdout) is not None


def _lldb_finished(report: dict[str, Any], where: str) -> None:
    """An attach that did not finish inside the probe leaves the comparison inconclusive: skip with the reason."""
    for target, entry in (("its own child", report), ("the process outside", report.get("outside") or {})):
        if isinstance(entry, dict) and entry.get("timeout"):
            pytest.skip(
                f"lldb did not finish attaching to {target} in {entry['timeout']:.0f} s ({where}); inconclusive"
            )


@macos
def test_processes_outside_the_sandbox_cannot_be_debugged(box: Box) -> None:
    """MACOS-11: lldb inside the sandbox runs no code in a process outside it.

    AX-219 loosened the profile once, with (allow mach-priv-task-port (target same-sandbox)); this test
    measures what that leaves closed. The victim is a program built with cc on the spot, without the
    hardened runtime like most dev builds, started outside the sandbox. In one session DEBUG_PROBE
    first attaches lldb to its own child and evaluates getpid() there, then attaches to the victim and
    evaluates an expression that copies the decoy key to a marker. Controls run the same probe,
    launched alike (``_control_as_run``), against the same victim, before and after the confined
    attempt, and each must leave its marker; confined, the getpid() must still work (lldb reached the
    task port of a process in the sandbox) and the marker must not appear. The control after the
    attempt shows the victim could still be debugged then, so what tells the attaches apart is
    whether the target is in the sandbox. A launcher timeout, an attach that does not finish or a
    control without effect is inconclusive: a skip with the reason.
    """
    lldb, cc = _debug_tools()
    program = box.ws / "sleeper"  # in the workspace: the confined probe starts its own child from it
    _build(cc, program)
    victim = subprocess.Popen(
        [str(program)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:

        def probe(marker: Path) -> list[str]:
            expression = f'expr (int)system("{_copy_key(box, marker)}")'
            argv = [lldb, str(program), str(LLDB_SECONDS), str(victim.pid), expression]
            return [launcher.interpreter(), "-I", "-S", "-c", DEBUG_PROBE, *argv]

        def control(when: str) -> None:
            marker = box.root / f"debug-{secrets.token_hex(4)}"
            result = _control_as_run(box, probe(marker), "the lldb probe", timeout=DEBUG_LAUNCH_SECONDS)
            report = _last_json(result)
            _lldb_finished(report, f"unconfined, {when}")
            if not _evaluated_in_child(report) or not _escaped(box, marker):
                pytest.skip(f"lldb cannot debug its own child or the victim unconfined, {when}: {report}")
            if victim.poll() is not None:
                pytest.skip(f"the victim ended (status {victim.returncode}) after the control's attach, {when}")

        control("before the confined attempt")
        marker = box.root / f"debug-{secrets.token_hex(4)}"
        confined = _as_run(box, probe(marker), timeout=DEBUG_LAUNCH_SECONDS)
        escaped, ended = _escaped(box, marker), victim.poll()
        finding = (
            "MACOS-11: lldb in the sandbox ran code in, or ended, a process outside it "
            f"(key copied: {escaped}, victim status: {ended}); stdout: {confined.stdout[-2000:]!r}"
        )
        _closed(confined, escaped or ended is not None, finding, "the lldb probe")
        report = _last_json(confined)
        _lldb_finished(report, "confined")
        assert _evaluated_in_child(report), (
            "MACOS-11: lldb in the sandbox cannot debug the probe's own child either, so the closed attach "
            f"to the victim says nothing about whether the target is in the sandbox: {report}"
        )
        control("after the confined attempt")  # the victim still takes an attach: the sandbox closed this one
    finally:
        victim.kill()
        victim.wait()


@macos
def test_the_agent_can_still_debug_its_own_builds(box: Box) -> None:
    """MACOS-11 positive control: task ports are allowed back for the sandbox's own processes.

    Started as `run` starts the agent, lldb attaches to a child the confined process started from a
    program built with cc in the workspace, and calls getpid() inside it. The control is launched the
    same way without a policy.
    """
    lldb, cc = _debug_tools()
    program = box.ws / "own-build"
    _build(cc, program)
    argv = [launcher.interpreter(), "-I", "-S", "-c", DEBUG_PROBE, lldb, str(program), str(LLDB_SECONDS)]
    control = _last_json(_control_as_run(box, argv, "the lldb probe", timeout=240))
    _lldb_finished(control, "unconfined")
    if not _evaluated_in_child(control):
        pytest.skip(f"lldb cannot attach to its own child here even unconfined (Developer Tools access): {control}")
    confined = _as_run(box, argv, timeout=240)
    if confined.status.get("timeout"):
        pytest.skip(
            f"the lldb probe did not finish within the launcher's timeout, confined; inconclusive: {_stderr(confined)!r}"
        )
    assert confined.status.get("ok"), f"the lldb probe never ran: {confined.status} {_stderr(confined)!r}"
    report = _last_json(confined)
    _lldb_finished(report, "confined")
    assert _evaluated_in_child(report), f"MACOS-11: the confined agent cannot debug a program it started: {report}"


# MACOS-5 ---------------------------------------------------------------------------------------

HDIUTIL = "/usr/bin/hdiutil"
MOUNTED = "B60-MOUNTED"  # the file the disk image carries
HOMEBREW_PREFIXES = ("/opt/homebrew", "/usr/local")


def _inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("/") + "/")


def _directory_outside_every_rule(box: Box) -> Path:
    """A fresh directory the user owns on a Homebrew prefix: outside every deny root and every grant but /opt or /usr.

    It stands for /opt/homebrew/bin (on PATH, owned by the user, readable from the sandbox). Never under
    /opt/homebrew/var or /usr/local/var, which the profile read-denies.
    """
    deny_roots = [os.path.realpath(root) for root in ("/Users", *box.policy.homes, *seatbelt.shared_read_roots())]
    granted = [os.path.realpath(g.path) for g in box.policy.grants if g.origin != "system"]
    reasons: list[str] = []
    for prefix in HOMEBREW_PREFIXES:
        try:
            path = Path(tempfile.mkdtemp(prefix="b60-mount-", dir=prefix))
        except OSError as exc:
            reasons.append(f"{prefix}: {exc.strerror or exc}")
            continue
        real = os.path.realpath(path)
        covered = [root for root in (*deny_roots, *granted) if _inside(real, root)]
        if not covered:
            return path
        shutil.rmtree(path, ignore_errors=True)
        reasons.append(f"{real} falls under {covered}")
    pytest.skip("the runner user cannot create a directory outside the deny roots: " + "; ".join(reasons))


def _mount_table_names(target: Path) -> bool:
    """getfsstat(2) through /sbin/mount names ``target``, or its device differs from its parent's."""
    done = _quietly(["/sbin/mount"], 60)
    real = os.path.realpath(target)
    listed = done is not None and f" on {real} (".encode() in done.stdout
    return listed or os.path.ismount(real)


def _shows(target: Path, content: str, timeout: float) -> bool:
    """The image's file is visible in ``target``, to this unconfined process."""
    deadline = time.monotonic() + timeout
    while True:
        with contextlib.suppress(OSError):
            if (target / MOUNTED).read_text() == content:
                return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.25)


def _same_file(path: str, other: Path) -> bool:
    try:
        return os.path.samefile(path, other)
    except OSError:
        return os.path.realpath(path) == os.path.realpath(other)


def _detach_everything_from(image: Path, target: Path) -> None:
    """Detach each device attached from ``image`` (by the control or the confined attempt), then ``target``."""
    listing = _quietly([HDIUTIL, "info", "-plist"], 60)
    try:
        images = plistlib.loads(listing.stdout).get("images", []) if listing is not None else []
    except Exception:  # no plist to read: the mount-point fallback below still runs
        images = []
    for entry in images:
        if not _same_file(str(entry.get("image-path", "")), image):
            continue
        for entity in entry.get("system-entities", []):
            if entity.get("dev-entry"):
                _quietly([HDIUTIL, "detach", "-force", str(entity["dev-entry"])], 120)
    if _mount_table_names(target):
        _quietly([HDIUTIL, "detach", "-force", str(target)], 120)


@macos
def test_a_disk_image_cannot_be_mounted_over_a_directory_outside_the_grants(box: Box) -> None:
    """MACOS-5: ``target`` is a fresh directory the user owns on a Homebrew prefix, as /opt/homebrew/bin is.

    At 48a4593 the target sat inside the per-user /private/var/folders directory, which the profile
    read-denies, and only hdiutil's exit status failed: the mount had not happened. Here the target is
    outside every deny root, and the confined attempt mounted nothing at f3242c4 (passed, named in its
    JUnit). The effect is the image's file in ``target`` and the mount table naming it.
    """
    payload = box.root / "payload"
    payload.mkdir()
    content = f"B60-MOUNTED-{secrets.token_hex(8)}"
    (payload / MOUNTED).write_text(content)
    image = box.ws / "tools.dmg"  # an agent can as well download one: the network is open
    made = _quietly([HDIUTIL, "create", "-quiet", "-srcfolder", str(payload), "-format", "UDZO", str(image)], 300)
    if made is None or made.returncode or not image.is_file():
        pytest.skip(f"hdiutil cannot create images here: {made.stderr if made else b'timed out'!r}")
    target = _directory_outside_every_rule(box)
    attach = [HDIUTIL, "attach", "-nobrowse", "-mountpoint", str(target), str(image)]
    try:
        try:
            control = _bounded(attach, timeout=180, env=box.env, cwd=box.ws)
            if not _shows(target, content, timeout=20):
                pytest.skip(f"hdiutil does not mount over a user-owned directory here even unconfined: {control}")
            assert _mount_table_names(target), f"the control shows the image in {target}; the mount table misses it"
        finally:
            _detach_everything_from(image, target)
        assert not _mount_table_names(target), f"the control's image is still attached over {target}"
        confined = _as_run(box, attach, timeout=180)
        shown, listed = _shows(target, content, timeout=5), _mount_table_names(target)
        finding = (
            f"MACOS-5: the confined process mounted an image over {target} (file shown: {shown}, "
            f"mount table: {listed}); hdiutil stdout: {confined.stdout[-2000:]!r}"
        )
        _closed(confined, shown or listed, finding, "hdiutil attach")
    finally:
        _detach_everything_from(image, target)
        if not _mount_table_names(target):
            shutil.rmtree(target, ignore_errors=True)


# MACOS-12 ---------------------------------------------------------------------------------------


# Predates raises=DeclaredLimit: any failure, a missing report of _probe's included, is an XFAIL here, so
# its XFAIL (f3242c4) measures no shape; giving it one is left to a later batch.
@macos
@pytest.mark.xfail(
    strict=False, reason="declared limit: POSIX shared memory stays readable on macOS, as /dev/shm on Linux"
)
def test_shared_memory_of_other_processes_is_not_readable(box: Box) -> None:
    from multiprocessing import shared_memory

    canary = f"B60-CANARY-{secrets.token_hex(8)}".encode()
    segment = shared_memory.SharedMemory(name=f"b60{secrets.token_hex(4)}", create=True, size=4096)
    try:
        segment.buf[: len(canary)] = canary
        name = "/" + segment.name.lstrip("/")
        if canary.hex() not in _probe(box, "shm_read", name, confined=False)["data"]:
            pytest.skip("POSIX shared memory of a sibling process is not readable here even unconfined")
        assert canary.hex() not in _probe(box, "shm_read", name)["data"], (
            "MACOS-12: shared memory read from the sandbox"
        )
    finally:
        segment.close()
        segment.unlink()


# MACOS-13 ---------------------------------------------------------------------------------------


class DeclaredLimit(AssertionError):
    """The failure a declared limit predicts. Any other failure of the same test stays a failure."""


def _declared_limit(request: pytest.FixtureRequest, message: str) -> NoReturn:
    """End a test in the measured shape of its declared limit: XFAIL with ``message`` as the reason.

    The test's marker (xfail, raises=DeclaredLimit) makes any other exception a failure and, when
    strict, a pass too (XPASS(strict)); but the XFAIL it gives a raised DeclaredLimit shows only the
    marker's fixed reason, on the -rx line and in the JUnit. pytest.xfail shows ``message``, what this
    run measured. Without that marker, ``message`` fails the test as a DeclaredLimit, and so it does
    under ``pytest --runxfail``, which makes pytest.xfail return instead of raising.
    """
    marker = request.node.get_closest_marker("xfail")
    if marker is None or marker.kwargs.get("raises") is not DeclaredLimit:
        raise DeclaredLimit(message)
    pytest.xfail(message)
    raise DeclaredLimit(message)  # reached only under --runxfail: the limit is there, so the test fails


@macos
@pytest.mark.xfail(
    strict=True,
    raises=DeclaredLimit,
    reason="declared limit (macOS): inside a denied directory the error tells which names exist "
    "(ENOENT for a missing name, EPERM or EACCES for an existing one); their contents stay unreadable",
)
def test_denied_paths_do_not_tell_which_names_exist(box: Box, request: pytest.FixtureRequest) -> None:
    """MACOS-13: XFAILED in the CI of 48a4593, d594608, ae39991, f3747db and f3242c4. Strict: should it pass,
    the limit is gone.

    None of those runs records which errno the key got. Only the declared shape ends in
    ``_declared_limit`` (ENOENT for the missing name, EPERM or EACCES for the key), so an XFAIL
    certifies it, and since AX-226 its line names both answers; any other pair fails with both values.
    """
    missing = box.home / ".ssh" / f"absent-{secrets.token_hex(4)}"
    control = _probe(box, "stat", missing, confined=False)["result"]
    if control != "ENOENT":
        pytest.skip(f"stat of a missing name answers {control} here even unconfined")
    present, absent = _probe(box, "stat", box.key)["result"], _probe(box, "stat", missing)["result"]
    assert present in DENIED, f"L1: stat of the protected key answered {present} inside the sandbox"
    read = _probe(box, "read", box.key)
    assert read["result"] in DENIED and not read["data"], f"the protected key is readable: {read}"
    if absent == "ENOENT" and present in DENIED:
        _declared_limit(
            request,
            f"declared limit (macOS) MACOS-13: stat answers {present} for the key and ENOENT for a missing name, "
            "inside a denied directory; reading the key answers "
            f"{read['result']}",
        )
    assert absent == present, f"MACOS-13: stat answers {present} for the key and {absent} for a missing name"


# MACOS-14 and the names a fix relies on ----------------------------------------------------------


@macos
def test_the_fcntl_rule_is_not_skipped_silently() -> None:
    """(when (defined? 'system-fcntl) ...) is a no-op where the operation is unknown; prove the branch is taken."""
    hosts = '(deny file-read* (literal "/private/etc/hosts"))'
    probe = f"(version 1)\n(allow default)\n(when (defined? 'system-fcntl) {hosts})\n"
    done = subprocess.run(
        [seatbelt.SANDBOX_EXEC, "-p", probe, "/bin/cat", "/etc/hosts"], capture_output=True, timeout=30
    )
    assert done.returncode != 0, (
        "MACOS-14: system-fcntl is undefined, so F_MAKECOMPRESSED/F_TRANSFEREXTENTS stay allowed"
    )


USED_RULES = (
    "(deny lsopen)",
    "(deny appleevent-send)",
    "(deny job-creation)",
    "(deny hid-control)",
    "(deny file-mount)",
    "(deny file-unmount)",
    "(deny signal)\n(allow signal (target self) (target same-sandbox))",
    "(deny process-info*)\n(allow process-info* (target self) (target same-sandbox))",
    '(deny sysctl-read (sysctl-name-prefix "kern.procargs"))',
    f"{TASK_PORTS}\n{OWN_TASK_PORTS}",
    "(deny user-preference-write)",
    '(deny mach-lookup (global-name "com.apple.pasteboard.1"))',
    '(when (defined? \'file-write-setugid) (deny file-write-setugid (subpath "/")))',
    "(deny system-fcntl (fcntl-command 80 110))",
)
CANDIDATE_RULES = (
    "(deny mach-priv-task-port)",
    "(deny file-write-setugid)",
    "(deny signal)\n(allow signal (target self) (target children))",
    '(deny user-preference-read)\n(allow user-preference-read (preference-domain "kCFPreferencesAnyApplication"))',
    '(deny ipc-posix-shm-read-data ipc-posix-shm-write-data (ipc-posix-name-regex "^/b60"))',
    '(deny file-test-existence (subpath "/private/var/empty"))',
)


def _compiles(rules: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [seatbelt.SANDBOX_EXEC, "-p", f"(version 1)\n(allow default)\n{rules}\n", "/usr/bin/true"],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_every_used_rule_is_in_the_profile() -> None:
    lines = seatbelt.render_profile(_synthetic()).splitlines()
    for rules in USED_RULES:
        for rule in rules.splitlines():
            assert rule in lines or rule.startswith("(deny mach-lookup") or rule.startswith("(deny system-fcntl"), rule


@macos
@pytest.mark.parametrize("rules", USED_RULES)
def test_each_rule_of_the_profile_is_known_to_sandbox_exec(rules: str) -> None:
    """sandbox-exec rejects a whole profile over one unknown operation or filter: check each one alone."""
    done = _compiles(rules)
    assert done.returncode == 0, done.stderr


@macos
@pytest.mark.parametrize("rules", CANDIDATE_RULES)
def test_candidate_rules_report_whether_sandbox_exec_knows_them(rules: str) -> None:
    """Not in the profile: the -rs summary records which ones this macOS accepts, for a later round."""
    done = _compiles(rules)
    if done.returncode != 0:
        pytest.skip(f"not accepted here: {done.stderr.strip()[:200]}")


@macos
@pytest.mark.parametrize("mode", [0o4755, 0o2755])
def test_setuid_and_setgid_modes_are_denied(box: Box, mode: int) -> None:
    """The macOS side of the seccomp setid rule: no setuid program left behind in the workspace.

    The same chmod probe runs as a control launched alike without a policy (``_control_as_run``), on a
    file of its own, which must get the mode or the test skips, and then as `run` runs the agent
    (``_as_run``). Confined, the bit must not be set, the trampoline must have exec'd the probe
    (``_closed``) and the probe must report how its chmod ended. Until AX-226 the attempt ran through
    ``box.run`` and the test passed without checking that the probe ran.
    """

    def chmod_probe(tool: Path) -> list[str]:
        tool.write_text("#!/bin/sh\nexec /bin/sh\n")
        script = (
            "import errno, os\n"
            f"try:\n    os.chmod({str(tool)!r}, {mode})\n    print('chmod: ok', flush=True)\n"
            "except OSError as exc:\n    print('chmod:', errno.errorcode.get(exc.errno, exc.errno), flush=True)\n"
        )
        return [launcher.interpreter(), "-I", "-S", "-c", script]

    control_tool = box.ws / f"control-{mode:o}"
    control = _control_as_run(box, chmod_probe(control_tool), "the chmod probe", timeout=60)
    if not os.stat(control_tool).st_mode & 0o6000:
        pytest.skip(f"mode {mode:o} does not stick even unconfined: {control.stdout!r} {_stderr(control)!r}")
    tool = box.ws / f"tool-{mode:o}"
    confined = _as_run(box, chmod_probe(tool), timeout=60)
    finding = f"the confined process set a setuid or setgid bit (mode {os.stat(tool).st_mode:o})"
    _closed(confined, bool(os.stat(tool).st_mode & 0o6000), finding, "the chmod probe")
    assert confined.stdout.startswith(b"chmod: "), f"the chmod probe did not report: {_stderr(confined)!r}"


# Positive controls: what agents run every day -----------------------------------------------------

# -P: with the workspace as the working directory, `run` refuses a launcher that imports from it.
CLI = [sys.executable, "-P", "-m", "babylon60.cli.main_dispatcher"]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MACH_O = (b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf")  # MH_MAGIC_64, in either byte order
# A small ~/.gitconfig, as most users have: an identity and no credential.
GITCONFIG = "[user]\n\tname = B60 Decoy\n\temail = decoy@b60.invalid\n"
MODULE_CACHE_MARKER = "B60-MODULE-CACHE-IN-TMPDIR"


class Everyday(NamedTuple):
    """A command prepared in one workspace, and how `run` starts it."""

    argv: list[str]
    worked: Callable[[subprocess.CompletedProcess[str]], bool]  # whether it had its effect
    timeout: float  # seconds
    options: tuple[str, ...] = ()  # `run` options before "--"


def _installed(*candidates: str) -> str:
    found = next((path for path in candidates if os.path.exists(path)), None)
    if found is None:
        pytest.skip(f"not installed here: {' or '.join(candidates)}")
    return found


def _json_line(text: str) -> dict[str, Any]:
    """The last line of ``text`` that is a JSON object, or an empty dict."""
    for line in reversed(text.splitlines()):
        with contextlib.suppress(ValueError):
            report = json.loads(line)
            if isinstance(report, dict):
                return report
    return {}


# Run as the agent: start a child, then list this process group with sysctl(KERN_PROC_PGRP), as `ps -g`
# does, without ps (setuid root; its exec answered EPERM through `run` at f3747db: see
# test_a_setuid_program_runs_inside_the_sandbox). Only this group is asked for, no other process; XNU's
# kern.proc handler makes no process-info check (bsd/kern/kern_sysctl.c, sysctl_prochandle) and the
# profile denies only kern.procargs* among sysctl reads. kinfo_proc (sys/sysctl.h) is 648 bytes on
# 64-bit macOS: p_pid at 40, p_comm (17 bytes) at 243, e_ppid at 560. The control checks this layout:
# the process itself must appear with its own parent.
OWN_PROCESSES_PROBE = r"""
import ctypes, json, os, struct, subprocess
KINFO, PID, COMM, PPID = 648, 40, 243, 560
libc = ctypes.CDLL(None, use_errno=True)
child = subprocess.Popen(["/bin/sleep", "30"], stdin=subprocess.DEVNULL)
report = {"pid": os.getpid(), "ppid": os.getppid(), "child": child.pid, "pgid": os.getpgrp()}
try:
    mib = (ctypes.c_int * 4)(1, 14, 2, os.getpgrp())  # CTL_KERN, KERN_PROC, KERN_PROC_PGRP, this group
    size = ctypes.c_size_t(0)
    if libc.sysctl(mib, ctypes.c_uint(4), None, ctypes.byref(size), None, ctypes.c_size_t(0)) != 0:
        raise OSError(ctypes.get_errno(), "sysctl(KERN_PROC_PGRP) size")
    buffer = ctypes.create_string_buffer(size.value + 8 * KINFO)
    size = ctypes.c_size_t(len(buffer))
    if libc.sysctl(mib, ctypes.c_uint(4), buffer, ctypes.byref(size), None, ctypes.c_size_t(0)) != 0:
        raise OSError(ctypes.get_errno(), "sysctl(KERN_PROC_PGRP)")
    raw = buffer.raw[: size.value]
    report["bytes"] = size.value
    report["listed"] = [
        [
            struct.unpack_from("<i", raw, offset + PID)[0],
            struct.unpack_from("<i", raw, offset + PPID)[0],
            raw[offset + COMM : offset + COMM + 17].split(b"\0")[0].decode("utf-8", "replace"),
        ]
        for offset in range(0, len(raw) - KINFO + 1, KINFO)
    ]
except OSError as exc:
    report["error"] = "%s: %s" % (exc.errno, exc.strerror)
finally:
    child.kill()
    child.wait()
print(json.dumps(report), flush=True)
"""


def _own_processes(ws: Path, env: dict[str, str]) -> Everyday:
    """The agent lists its own processes without ps: its process group, through sysctl (OWN_PROCESSES_PROBE).

    The effect: the listing names the probe with its parent and the probe's child, /bin/sleep, with
    the probe as parent. Under `run` the agent leads a session and a process group of its own, as
    the control does here (``_bounded`` starts a new session).
    """

    def listed(done: subprocess.CompletedProcess[str]) -> bool:
        report = _json_line(done.stdout)
        rows = {tuple(row) for row in report.get("listed", []) if isinstance(row, list) and len(row) == 3}
        pid, ppid, child = report.get("pid"), report.get("ppid"), report.get("child")
        itself = any(row[:2] == (pid, ppid) for row in rows)
        return isinstance(pid, int) and report.get("bytes", 0) % 648 == 0 and itself and (child, pid, "sleep") in rows

    return Everyday([launcher.interpreter(), "-I", "-S", "-c", OWN_PROCESSES_PROBE], listed, 120)


def _real_agent_state() -> str | None:
    """A path ``--preset claude-code`` would grant read-write from this account's real home, if one exists."""
    home = account_home()
    return next((home + item[1:] for item in PRESETS["claude-code"]["write"] if os.path.lexists(home + item[1:])), None)


def _git(*candidates: str, gitconfig: bool = False) -> Callable[[Path, dict[str, str]], Everyday]:
    """git init and an empty commit; the effect is the commit with its author.

    Without ``gitconfig`` the decoy HOME has no ~/.gitconfig and the identity is the workspace's own
    (.git/config). With it, the HOME has GITCONFIG (user.name and user.email, no credential), the
    commit takes its author from there, so the effect also shows that git read the file, and `run`
    gets --preset claude-code. Without a grant git cannot read ~/.gitconfig and stops (measured on
    Linux: "fatal: unknown error occurred while reading the configuration files"). The presets grant it
    read-only (AX-207/217); both -gitconfig variants passed confined in the CI of f3242c4, named in its
    JUnit. They skip where the preset would grant this account's real
    agent state to the test.
    """

    def prepare(ws: Path, env: dict[str, str]) -> Everyday:
        git = _installed(*candidates)
        quoted = shlex.quote(git)
        if gitconfig:
            reached = _real_agent_state()
            if reached:
                pytest.skip(f"--preset claude-code would grant this account's real agent state ({reached}) to the test")
            (Path(env["HOME"]) / ".gitconfig").write_text(GITCONFIG)
            identity, author = "", "B60 Decoy"
        else:
            identity = f"{quoted} config user.name 'B60 Probe' && {quoted} config user.email probe@b60.invalid && "
            author = "B60 Probe"
        script = f"{quoted} init -q && {identity}{quoted} commit -q --allow-empty -m b60-probe"

        def committed(done: subprocess.CompletedProcess[str]) -> bool:
            log = subprocess.run(
                [git, "-C", str(ws), "log", "-1", "--format=%an%n%s"],
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            return log.stdout.splitlines() == [author, "b60-probe"]

        options = ("--preset", "claude-code") if gitconfig else ()
        return Everyday(["/bin/sh", "-c", script], committed, 120, options)

    return prepare


def _python_venv(ws: Path, env: dict[str, str]) -> Everyday:
    venv = ws / "venv"

    def created(done: subprocess.CompletedProcess[str]) -> bool:
        python = venv / "bin" / "python"
        if not (venv / "pyvenv.cfg").is_file() or not python.exists():
            return False
        check = subprocess.run(
            [str(python), "-I", "-c", "import sys, pip; print(sys.prefix != sys.base_prefix)"],
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return check.stdout.strip() == "True"

    return Everyday([_installed("/usr/bin/python3"), "-m", "venv", str(venv)], created, 300)


def _clang_modules(*, cache_in_tmpdir: bool = False) -> Callable[[Path, dict[str, str]], Everyday]:
    """clang -fmodules with @import Foundation.

    clang's module cache defaults to the per-user cache directory, read-denied by the profile and
    write-denied by its base. The user documentation names only -fmodules-cache-path to move it; the
    driver also reads CLANG_MODULE_CACHE_PATH (LLVM review D126678), which that documentation leaves
    out. In the CI of f3747db the plain variant failed confined ("unable to open output file
    .../C/clang/ModuleCache/...") and ``cache_in_tmpdir`` passed (inferred then from the -q log). Since
    then `run` sets CLANG_MODULE_CACHE_PATH in the private TMPDIR when the user's environment does not
    (cli.private_tmp_environment): the plain variant measures that default, and ``cache_in_tmpdir``
    still sets $TMPDIR/clang-modules itself and requires a cache there. Both passed confined in the CI
    of f3242c4, named in its JUnit: Apple clang honours the variable, `run`'s value included, and
    xcrun's warning that it cannot write its cache in the denied T directory is not fatal. The per-user
    cache directory stays denied: a module cache the agent could write there would be loaded by the
    user's own unconfined builds.

    The control gets `run`'s CLANG_MODULE_CACHE_PATH too, in its own TMPDIR (see the test), so both
    sides build with the same variable; ``cache_in_tmpdir`` overrides it on both sides alike.
    """

    def prepare(ws: Path, env: dict[str, str]) -> Everyday:
        build = [_installed("/usr/bin/clang"), "-fmodules", "-c", "probe.m", "-o", "probe.o"]
        (ws / "probe.m").write_text('@import Foundation; int b60_probe(void) { return (int)[@"B60" length]; }\n')
        argv = build
        if cache_in_tmpdir:
            script = (
                'CLANG_MODULE_CACHE_PATH="$TMPDIR/clang-modules"; export CLANG_MODULE_CACHE_PATH; '
                f"{shlex.join(build)} || exit; "
                'if [ -n "$(ls -A "$CLANG_MODULE_CACHE_PATH" 2>/dev/null)" ]; '
                f"then echo {MODULE_CACHE_MARKER}; "
                'else echo "no module cache in $CLANG_MODULE_CACHE_PATH: clang ignored the variable" >&2; fi'
            )
            argv = ["/bin/sh", "-c", script]

        def compiled(done: subprocess.CompletedProcess[str]) -> bool:
            with contextlib.suppress(OSError):
                built = (ws / "probe.o").read_bytes()[:4] in MACH_O
                return built and (not cache_in_tmpdir or MODULE_CACHE_MARKER in done.stdout.split())
            return False

        return Everyday(argv, compiled, 420)

    return prepare


def _swift_version(ws: Path, env: dict[str, str]) -> Everyday:
    swift = _installed("/usr/bin/swift")
    return Everyday([swift, "--version"], lambda done: "Swift version" in done.stdout + done.stderr, 120)


def _brew_version(ws: Path, env: dict[str, str]) -> Everyday:
    """brew lives in a prefix whose var/ the profile read-denies (Homebrew's service data)."""
    brew = _installed("/opt/homebrew/bin/brew", "/usr/local/bin/brew")
    return Everyday([brew, "--version"], lambda done: done.stdout.startswith("Homebrew "), 120)


def _headless_chrome(
    *, own_sandbox: bool = True, disable_gpu: bool = True
) -> Callable[[Path, dict[str, str]], Everyday]:
    """INV_C5_COMPUTER_USE_TRUST_GATEWAY denies the window server lookup: headless Chrome must do without it.

    The effect: the page's marker in --dump-dom's output. In the CI of f3747db Chrome aborted confined
    (exit 21) after "Failed to create socket directory.": its ProcessSingleton creates that directory
    with base::CreateUniqueTempDir, and base::GetTempDir on macOS reads MAC_CHROMIUM_TMPDIR when it is
    not empty and otherwise NSTemporaryDirectory() (Chromium's base/files/file_util_apple.mm). That
    NSTemporaryDirectory() gives the per-user T directory the profile denies, not $TMPDIR, is inferred
    from that failure (the private TMPDIR was writable); Chromium's code shows only the order. `run`
    now sets MAC_CHROMIUM_TMPDIR to the private TMPDIR when unset or empty, and the control gets the
    same variable in its own TMPDIR. Either way the socket's path is longer than sockaddr_un's 104-byte
    sun_path (about 113 bytes under a private TMPDIR in the per-user T directory); on macOS Chromium
    binds it with an oversized sockaddr that takes up to 253 (chrome/browser/process_singleton_posix.cc,
    SetupSockAddr).

    In the CI of f3242c4 (its JUnit) that line was gone, and Chrome died by a signal confined while it
    rendered the page unconfined. [chrome-headless] by SIGTRAP (exit 133), with only three Crashpad
    lines in its stderr: two denied stats of the real ~/Library, not the decoy HOME, and "ReadExactly:
    expected 8, observed 0". At f3747db the same three lines came before the socket directory's, so this
    stderr does not show whether Chrome got that far. [chrome-headless-no-sandbox]
    (``own_sandbox=False``: --no-sandbox, the helpers confined by `run`'s profile alone) did: after
    those lines it started helper processes, which Chrome only launches past that step (Chromium's code:
    the step runs from chrome_main_delegate.cc, whose hooks content runs before BrowserMain), and died
    by SIGSEGV (exit 139) after "XPC error for connection com.apple.backupd.sandbox.xpc: Connection
    invalid", "CVDisplayLinkCreateWithCGDisplay failed. CVReturn: -6670" and "Trying to load the
    allocator multiple times. This is *not* supported.". Why it dies is not measured. That Chrome's own
    sandbox cannot be applied inside `run`'s is a hypothesis, not measured: no "Failed to initialize
    sandbox.", the line a helper prints when it fails there, was captured, and Chrome died without its
    sandbox too. Both are a declared limit (CHROME_DEATH), for which no rule is loosened: the window
    server stays denied, as INV_C5_COMPUTER_USE_TRUST_GATEWAY asks. That this denial is part of what
    keeps the screen from being captured is inferred: test_the_screen_cannot_be_captured and
    test_the_window_server_gives_the_sandbox_no_image_of_the_display passed at f3242c4, under the
    profile as a whole, and which rule closes capture is not isolated. Both ran with --disable-gpu, as
    every Chrome variant has since AX-210; ``disable_gpu=False`` drops it, and nothing else, in the
    exploratory variant.
    """

    def prepare(ws: Path, env: dict[str, str]) -> Everyday:
        chrome = _installed(CHROME)
        marker = f"B60-PAGE-{secrets.token_hex(8)}"
        page = ws / "page.html"
        page.write_text(f"<!doctype html><title>b60</title><p>{marker}</p>\n")
        argv = [
            chrome,
            "--headless=new",
            *(("--disable-gpu",) if disable_gpu else ()),
            "--no-first-run",
            *(() if own_sandbox else ("--no-sandbox",)),
            f"--user-data-dir={ws / 'chrome-profile'}",
            "--dump-dom",
            page.as_uri(),
        ]
        return Everyday(argv, lambda done: marker in done.stdout, 180)

    return prepare


EVERYDAY: dict[str, Callable[[Path, dict[str, str]], Everyday]] = {
    "own-processes-sysctl": _own_processes,
    "git-xcrun-shim": _git("/usr/bin/git"),
    "git-homebrew": _git("/opt/homebrew/bin/git", "/usr/local/bin/git"),
    "git-xcrun-shim-gitconfig": _git("/usr/bin/git", gitconfig=True),
    "git-homebrew-gitconfig": _git("/opt/homebrew/bin/git", "/usr/local/bin/git", gitconfig=True),
    "python-venv": _python_venv,
    "clang-fmodules": _clang_modules(),
    "clang-fmodules-cache-in-tmpdir": _clang_modules(cache_in_tmpdir=True),
    "swift-version": _swift_version,
    "brew-version": _brew_version,
    "chrome-headless": _headless_chrome(),
    "chrome-headless-no-sandbox": _headless_chrome(own_sandbox=False),
    "chrome-headless-no-sandbox-without-disable-gpu": _headless_chrome(own_sandbox=False, disable_gpu=False),
}
# Headless Chrome on macOS, since the CI of f3242c4: a declared limit, and one exploratory variant.
CHROME_DEATH = pytest.mark.xfail(
    strict=True,
    raises=DeclaredLimit,
    reason="declared limit (macOS): headless Chrome dies by a signal under run's profile and renders the page "
    "unconfined (f3242c4: SIGTRAP with its own sandbox, SIGSEGV with --no-sandbox); should it render the page "
    "confined, this XPASS(strict) fails",
)
CHROME_EXPLORATORY = pytest.mark.xfail(
    strict=False,
    reason="exploratory (macOS): [chrome-headless-no-sandbox] without --disable-gpu, nothing else changed; never "
    "red: XPASS if Chrome renders the page confined (in the JUnit, a passed testcase), otherwise XFAIL with what "
    "it did (in the JUnit, skipped of type pytest.xfail), or SKIPPED if its control fails or it times out",
)
EVERYDAY_MARKS = {
    "chrome-headless": CHROME_DEATH,
    "chrome-headless-no-sandbox": CHROME_DEATH,
    "chrome-headless-no-sandbox-without-disable-gpu": CHROME_EXPLORATORY,
}
# Lines of Chrome's stderr that tell its failures apart: the XFAIL line counts each and quotes the first.
CHROME_LINES = {
    "socket directory": "Failed to create socket directory",  # f3747db, before MAC_CHROMIUM_TMPDIR
    "sandbox init": "Failed to initialize sandbox",  # a helper could not apply Chrome's own profile
    "Crashpad": "crashpad",
    "backupd XPC": "com.apple.backupd.sandbox.xpc",
    "CVDisplayLink": "CVDisplayLinkCreateWithCGDisplay failed",
    "allocator": "Trying to load the allocator multiple times",
}


def _everyday_session(root: Path) -> tuple[Path, Path, dict[str, str]]:
    """A decoy HOME, an empty workspace, a TMPDIR of its own and a plain environment.

    The HOME has no ~/.gitconfig unless a -gitconfig git variant writes one. git stops when one exists
    and the agent cannot read it (measured on Linux, git 2.43 under Landlock: "fatal: unknown error
    occurred while reading the configuration files"), so git is measured with and without one.
    """
    home, ws, tmp = root / "home", root / "ws", root / "tmp"
    (home / ".ssh").mkdir(parents=True)
    (home / ".ssh" / "id_rsa").write_text(f"B60-CANARY-{secrets.token_hex(8)}\n")
    ws.mkdir()
    tmp.mkdir(mode=0o700)
    env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(home),
        "LC_ALL": "C",
        "PYTHONPATH": str(ROOT / "01_KISH_ENGINE"),  # for the launcher; the agent receives it too
        **{name: os.environ[name] for name in ("USER", "LOGNAME") if name in os.environ},
    }
    return ws, tmp, env


def _timed_out(done: subprocess.CompletedProcess[str]) -> bool:
    """``_bounded`` ended the command at its timeout."""
    return done.stderr.endswith(" s without finishing]")


def _journal_story(path: Path) -> str:
    """What `run` recorded: run_refused (the trampoline did not exec the command, and why) or run_end."""
    if not path.exists():
        return "no journal"
    try:
        with ConfineJournal(path) as journal:
            entries = journal.entries()
    except JournalError as exc:
        return f"unreadable journal: {exc}"
    story = []
    for entry in entries:
        if entry.kind == "run_refused":
            story.append(f"run_refused ({entry.body.get('error')})")
        elif entry.kind == "run_end":
            story.append(f"run_end (exit code {entry.body.get('exit_code')})")
        else:
            story.append(entry.kind)
    return ", ".join(story) or "no entries"


def _signal_death(done: subprocess.CompletedProcess[str], journal: Path) -> str | None:
    """The signal that ended the command by itself after `run` started it confined, or None.

    `run` journals run_end only once the trampoline reported the exec (a refusal journals run_refused),
    with the agent's exit code as Popen gives it (-n: signal n), and then exits with 128 + n; ended_by
    names a SIGTERM or SIGHUP to `run` that ended the session instead. The shape needs a single run_end
    without ended_by, a negative code and 128 minus it as `run`'s exit status: in the CI of f3242c4,
    -5 and 133 for [chrome-headless], -11 and 139 for [chrome-headless-no-sandbox].
    """
    if not journal.exists():
        return None
    try:
        with ConfineJournal(journal) as opened:
            ends = [entry.body for entry in opened.entries() if entry.kind == "run_end"]
    except JournalError:
        return None
    if len(ends) != 1 or ends[0].get("ended_by"):
        return None
    code = ends[0].get("exit_code")
    if not isinstance(code, int) or code >= 0 or done.returncode != 128 - code:
        return None
    with contextlib.suppress(ValueError):
        return signal.Signals(-code).name
    return f"signal {-code}"


def _lines_named(text: str, named: dict[str, str]) -> str:
    """How many lines of ``text`` contain each of ``named``'s strings, the first such line of each, and the last.

    Each quoted line keeps its last 200 characters (the last line, 300): the message, after the log prefix.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    found = {label: [line for line in lines if needle in line] for label, needle in named.items()}
    counts = ", ".join(f"{label}: {len(matching)}" for label, matching in found.items())
    firsts = "; ".join(f"{label} {matching[0][-200:]!r}" for label, matching in found.items() if matching)
    last = lines[-1][-300:] if lines else ""
    return f"stderr: {len(lines)} lines ({counts}); the first of each: {firsts or 'none'}; the last {last!r}"


@macos
@pytest.mark.parametrize("name", [pytest.param(name, marks=EVERYDAY_MARKS.get(name, ()), id=name) for name in EVERYDAY])
def test_what_agents_run_every_day_works_through_run(tmp_path: Path, name: str, request: pytest.FixtureRequest) -> None:
    """Positive control through the real command line: `babylon60 run --journal <tmp> [options] -- <command>`.

    Decoy HOME, cwd = workspace. The same command first runs unconfined with the environment `run`
    gives the agent: a TMPDIR of its own and the variables `run` points into it
    (``cli.private_tmp_environment``: clang's module cache, and Chrome's temporary directory on
    macOS), so both sides get the same variables, each in its own TMPDIR. The test skips when the
    control fails. Confined, a failure fails the test with the command's stderr, what the journal
    recorded (run_refused when the trampoline did not exec it) and the control's exit and stderr:
    this is what the denials cost. A confined run that ``_bounded`` ends at its timeout is
    inconclusive: a skip with the reason.

    Headless Chrome is a declared limit on macOS (CHROME_DEATH): its measured shape, a death by a
    signal after `run` started it confined (``_signal_death``) while the control rendered the page,
    ends in ``_declared_limit``, whose XFAIL line carries the exit, the signal and, for each kind of
    line that tells Chrome's failures apart (CHROME_LINES), how many its stderr has and the first, plus
    its last line; any other failure fails, and a page rendered confined is an XPASS(strict), which
    fails too. The exploratory variant (CHROME_EXPLORATORY) is never red: XPASS when it renders the
    page, otherwise XFAIL with what it did, or a skip as above. In the JUnit an XPASS that is not
    strict is a passed testcase, and an XFAIL a skipped one of type pytest.xfail.
    """
    ws, tmp, env = _everyday_session(tmp_path / "control")
    control = EVERYDAY[name](ws, env)
    control_env = {**env, **cli.private_tmp_environment(env, str(tmp))}  # what `run` adds, in the control's TMPDIR
    unconfined = _bounded(control.argv, timeout=control.timeout, env=control_env, cwd=ws)
    if not control.worked(unconfined):
        pytest.skip(f"{name} fails here even unconfined (exit {unconfined.returncode}): {unconfined.stderr[-2000:]!r}")
    ws, _tmp, env = _everyday_session(tmp_path / "confined")
    confined = EVERYDAY[name](ws, env)
    journal = tmp_path / "journal.db"
    run = [*CLI, "run", "--journal", str(journal), *confined.options, "--", *confined.argv]
    # `run` creates the agent's private TMPDIR under the session's own, as in a terminal.
    done = _bounded(run, timeout=confined.timeout + 60, env={**env, "TMPDIR": tempfile.gettempdir()}, cwd=ws)
    if confined.worked(done):
        return  # under CHROME_DEATH an XPASS(strict), a failure: the declared limit is gone
    if _timed_out(done):
        pytest.skip(f"{name} did not finish under `babylon60 run`; inconclusive: {done.stderr[-2000:]!r}")
    report = (
        f"{name} fails under `babylon60 run` (exit {done.returncode}; journal: {_journal_story(journal)}); "
        f"stderr: {done.stderr[-4000:]!r}; stdout: {done.stdout[-1000:]!r}; unconfined it worked (exit "
        f"{unconfined.returncode}; stderr: {unconfined.stderr[-1000:]!r})"
    )
    mark = EVERYDAY_MARKS.get(name)
    if mark is not None:  # headless Chrome
        death = _signal_death(done, journal)
        ended = f"died by {death} after `run` started it confined" if death else "did not render the page confined"
        shape = (
            f"{name} {ended} (exit {done.returncode}; journal: {_journal_story(journal)}), while unconfined it "
            f"rendered the page; {_lines_named(done.stderr, CHROME_LINES)}"
        )
        if death and mark is CHROME_DEATH:
            _declared_limit(request, f"declared limit (macOS): {shape}")
        if mark is CHROME_EXPLORATORY:
            pytest.xfail(f"exploratory: {shape}" + ("" if death else f"; stderr tail: {done.stderr[-600:]!r}"))
    raise AssertionError(report)


# Declared limit: setuid programs ------------------------------------------------------------------

PS = "/bin/ps"
# Run as the agent: execute each program given as `<program> -p <this pid> -o pid=`, as ps lists its
# caller, and report how each exec ended (errno) or what it printed.
PS_PROBE = r"""
import errno, json, os, subprocess, sys
report = {"pid": os.getpid()}
for program in sys.argv[1:]:
    try:
        done = subprocess.run(
            [program, "-p", str(os.getpid()), "-o", "pid="],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=60,
        )
    except OSError as exc:
        report[program] = {"errno": errno.errorcode.get(exc.errno or 0, "E%s" % exc.errno)}
    except subprocess.TimeoutExpired:
        report[program] = {"timeout": 60}
    else:
        report[program] = {
            "exit": done.returncode,
            "stdout": done.stdout.decode("utf-8", "replace")[-500:],
            "stderr": done.stderr.decode("utf-8", "replace")[-500:],
        }
print(json.dumps(report), flush=True)
"""


def _listed_itself(report: dict[str, Any], program: str) -> bool:
    """``program`` ran and printed exactly the probe's own pid."""
    entry = report.get(program)
    return (
        isinstance(entry, dict)
        and entry.get("exit") == 0
        and str(entry.get("stdout", "")).split() == [str(report.get("pid"))]
    )


# Nothing but "(allow default)": what the sandbox refuses under it, no rule of a profile decides.
ALLOW_DEFAULT_ONLY = "(version 1)\n(allow default)\n"


@macos
@pytest.mark.parametrize("profile", ["run-profile", "allow-default"])
@pytest.mark.xfail(
    strict=True,
    raises=DeclaredLimit,
    reason="declared limit (macOS): the sandbox itself refuses exec of /bin/ps (setuid root) with EPERM, "
    "whatever run's profile says: [allow-default], under a profile of only (allow default), XFAILed at f3242c4 "
    "as [run-profile] did; other setuid and setgid programs are inferred from a user's report "
    "(forbidden-exec-sugid: developer.apple.com/forums/thread/689303)",
)
def test_a_setuid_program_runs_inside_the_sandbox(
    box: Box, profile: str, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    """At f3747db the CI's [ps-own-pid] failed confined: "/bin/sh: /bin/ps: Operation not permitted".

    /bin/ps is setuid root. No rule of `run`'s profile is about executing programs (it denies writing
    a setuid or setgid mode, file-write-setugid, not running one). In an Apple forum thread a user
    reports the same EPERM for /bin/ps under sandbox-exec, with a profile the post does not show,
    "deny(1) forbidden-exec-sugid" in the log and a copy without the bit running
    (developer.apple.com/forums/thread/689303). ``run-profile`` measures the limit under the profile
    `run` renders; ``allow-default`` has the patched renderer return ALLOW_DEFAULT_ONLY, so a refusal
    there is the sandbox's own, whatever a profile says. In the CI of f3242c4 both XFAILed, named in
    its JUnit: measured, the sandbox itself refuses the exec of /bin/ps. Their XFAIL showed the
    marker's fixed reason, so what the copy without the bit did there is not recorded; since AX-226
    ``_declared_limit`` shows it. Only /bin/ps is measured; that every setuid or setgid program is
    refused rests on that report.

    Only the declared shape ends in ``_declared_limit``: the control, launched as the attempt
    (``_control_as_run``), runs /bin/ps, or the test skips; confined, the trampoline exec'd the probe
    and exec of /bin/ps fails with EPERM. The probe also runs a copy of /bin/ps without the setuid
    bit. When the copy lists its caller unconfined it must do so confined too (then the bit is what
    the sandbox refuses); when it does not even unconfined (a copy of a system program may not run
    elsewhere), the limit is still measured on /bin/ps and the message says so. Should /bin/ps run
    confined, the strict xfail fails: the limit is gone or, with ``allow-default`` alone, a rule of
    `run`'s profile caused it. Any other shape fails with the reports. Agents list their own
    processes without ps: see the own-processes-sysctl positive control, which passed at f3242c4.
    """
    if not os.path.isfile(PS) or not os.stat(PS).st_mode & (stat.S_ISUID | stat.S_ISGID):
        pytest.skip(f"{PS} is not a setuid or setgid program here; nothing to measure")
    copy = box.ws / "ps-without-setuid"
    shutil.copyfile(PS, copy)  # contents only: the copy belongs to the runner user, mode set below
    copy.chmod(0o755)
    argv = [launcher.interpreter(), "-I", "-S", "-c", PS_PROBE, PS, str(copy)]
    control = _last_json(_control_as_run(box, argv, "the ps probe"))
    if not _listed_itself(control, PS):
        pytest.skip(f"{PS} does not list its caller here even unconfined: {control}")
    copy_runs = _listed_itself(control, str(copy))
    rendered: list[str] = []
    if profile == "allow-default":

        def allow_default_only(policy: Policy, **options: Any) -> str:
            rendered.append(profile)
            return ALLOW_DEFAULT_ONLY

        monkeypatch.setattr(seatbelt, "render_profile", allow_default_only)
    confined = _as_run(box, argv, timeout=120)
    if profile == "allow-default":
        assert rendered == [profile], "the launcher did not render this profile through seatbelt.render_profile"
    if confined.status.get("timeout"):
        pytest.skip(
            f"the ps probe did not finish within the launcher's timeout, confined; inconclusive: {_stderr(confined)!r}"
        )
    assert confined.status.get("ok"), f"the ps probe never ran: {confined.status} {_stderr(confined)!r}"
    report = _last_json(confined)
    if _listed_itself(report, PS):
        return  # XPASS(strict): /bin/ps runs inside this sandbox, the declared limit does not hold here
    if copy_runs:
        assert _listed_itself(report, str(copy)), (
            f"the copy of {PS} without the setuid bit does not run confined either, so the bit is not what the "
            f"sandbox refuses ({profile}): confined {report}; control {control}"
        )
    assert report.get(PS) == {"errno": "EPERM"}, (
        f"{PS} failed confined ({profile}), but not with EPERM at exec: confined {report}; control {control}"
    )
    under = "run's profile" if profile == "run-profile" else "a profile of only (allow default)"
    copy_note = (
        "its copy without the bit, owned by the runner user, lists its caller there, as unconfined"
        if copy_runs
        else f"its copy without the bit did not list its caller even unconfined ({control.get(str(copy))}; "
        f"confined: {report.get(str(copy))})"
    )
    _declared_limit(
        request, f"declared limit (macOS): exec of the setuid {PS} answers EPERM under {under}; {copy_note}"
    )


# Declared limit L6: the kern.proc lists --------------------------------------------------------------

# Run as the agent: list every process with sysctl(KERN_PROC_ALL), as `ps -A` does, and report the rows
# (pid, parent, name, user) of this process and of the pids given. kinfo_proc as in OWN_PROCESSES_PROBE,
# plus kp_eproc.e_ucred.cr_uid, the effective uid `ps -o user` shows, at offset 420 by the layout of
# sys/sysctl.h; the control checks the layout: the probe must find itself with its own parent and
# effective uid. A process started between the two calls makes the second one fail with ENOMEM: up to
# three tries, each with room for 64 more.
ALL_PROCESSES_PROBE = r"""
import ctypes, errno, json, os, struct, sys
KINFO, PID, COMM, PPID, UID = 648, 40, 243, 560, 420
libc = ctypes.CDLL(None, use_errno=True)
wanted = {os.getpid(), *map(int, sys.argv[1:])}
report = {"pid": os.getpid(), "ppid": os.getppid(), "uid": os.geteuid()}
mib = (ctypes.c_int * 4)(1, 14, 0, 0)  # CTL_KERN, KERN_PROC, KERN_PROC_ALL
for _ in range(3):
    size = ctypes.c_size_t(0)
    if libc.sysctl(mib, ctypes.c_uint(4), None, ctypes.byref(size), None, ctypes.c_size_t(0)) != 0:
        report["error"] = errno.errorcode.get(ctypes.get_errno(), str(ctypes.get_errno()))
        break
    buffer = ctypes.create_string_buffer(size.value + 64 * KINFO)
    size = ctypes.c_size_t(len(buffer))
    if libc.sysctl(mib, ctypes.c_uint(4), buffer, ctypes.byref(size), None, ctypes.c_size_t(0)) == 0:
        raw = buffer.raw[: size.value]
        rows = [
            [
                struct.unpack_from("<i", raw, offset + PID)[0],
                struct.unpack_from("<i", raw, offset + PPID)[0],
                raw[offset + COMM : offset + COMM + 17].split(b"\0")[0].decode("utf-8", "replace"),
                struct.unpack_from("<I", raw, offset + UID)[0],
            ]
            for offset in range(0, len(raw) - KINFO + 1, KINFO)
        ]
        report.pop("error", None)
        report["count"] = len(rows)
        report["listed"] = [row for row in rows if row[0] in wanted]
        break
    code = ctypes.get_errno()
    report["error"] = errno.errorcode.get(code, str(code))
    if code != errno.ENOMEM:
        break
print(json.dumps(report), flush=True)
"""


def _lists_itself(report: dict[str, Any]) -> bool:
    """The probe's listing names the probe with its own parent and effective uid: the kinfo_proc layout holds."""
    rows = [row for row in report.get("listed", []) if isinstance(row, list) and len(row) == 4]
    return [report.get("pid"), report.get("ppid"), report.get("uid")] in [[row[0], row[1], row[3]] for row in rows]


@macos
@pytest.mark.xfail(
    strict=False,
    raises=DeclaredLimit,
    reason="declared limit L6 (macOS): sysctl(KERN_PROC_ALL) inside the sandbox lists processes outside it (pid, "
    "parent, name, user), deduced from XNU's sysctl_prochandle; XFAIL if it lists the victim, XPASS if not",
)
def test_processes_outside_the_sandbox_are_not_listed_by_kern_proc(box: Box, request: pytest.FixtureRequest) -> None:
    """L6 on macOS: the kern.proc lists, which no rule of the profile denies, outside the sandbox.

    The profile denies process information (process-info*) and kern.procargs* for every process
    outside the sandbox, and reading their arguments and environment was denied confined
    (test_other_processes_exec_strings_are_not_readable: its 8 variants passed at f3242c4). XNU's
    kern.proc handler (bsd/kern/kern_sysctl.c, sysctl_prochandle) makes no per-process check, so
    pid, parent, name and user would still be listed: deduced, NO_VERIFICADO until this test runs.
    The victim is /bin/sleep 600, started by this test outside the sandbox; should it have ended by
    the time the confined probe is done, the test skips. The control, launched as the attempt
    (``_control_as_run``), must list the probe with its parent and effective uid, and the victim with
    this test as parent and this test's effective uid, or the test skips. Confined, the probe must
    have run: a listing that names the victim, all four fields alike, is the declared shape
    (``_declared_limit``, XFAIL); a denial, or a listing that names the probe but not the victim, is a
    pass (XPASS: the deduction is wrong). Non-strict, so neither makes the CI red; any other shape
    fails. Both reports are JUnit properties (kern_proc_control_report, kern_proc_confined_report), so
    an XPASS, a passed testcase there, still records the error or how many processes each listed.
    """
    victim = subprocess.Popen(
        ["/bin/sleep", "600"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    outside = [victim.pid, os.getpid(), "sleep", os.geteuid()]
    argv = [launcher.interpreter(), "-I", "-S", "-c", ALL_PROCESSES_PROBE, str(victim.pid)]
    try:
        control = _last_json(_control_as_run(box, argv, "the kern.proc.all probe", timeout=60))
        request.node.user_properties.append(("kern_proc_control_report", json.dumps(control)[-2000:]))
        if not _lists_itself(control) or outside not in control.get("listed", []):
            pytest.skip(f"sysctl(KERN_PROC_ALL) does not list the probe and the victim here even unconfined: {control}")
        confined = _as_run(box, argv, timeout=60)
        if confined.status.get("timeout"):
            pytest.skip(
                f"the kern.proc.all probe did not finish within the launcher's timeout, confined: {_stderr(confined)!r}"
            )
        assert confined.status.get("ok"), f"the kern.proc.all probe never ran: {confined.status} {_stderr(confined)!r}"
        report = _last_json(confined)
        request.node.user_properties.append(("kern_proc_confined_report", json.dumps(report)[-2000:]))
        if victim.poll() is not None:
            pytest.skip(
                f"the victim ended (exit {victim.returncode}) by the end of the confined probe; inconclusive: {report}"
            )
        assert report.get("pid"), f"the kern.proc.all probe did not report confined: {report}"
        listed = report.get("listed", [])
        if outside in listed:
            _declared_limit(
                request,
                f"declared limit L6 (macOS): sysctl(KERN_PROC_ALL) inside the sandbox lists a process outside it, "
                f"pid {victim.pid}, parent {os.getpid()}, name sleep, user {os.geteuid()}, among "
                f"{report.get('count')} processes (unconfined, the control listed {control.get('count')})",
            )
        assert not any(isinstance(row, list) and row[:1] == [victim.pid] for row in listed), (
            f"the confined probe lists the victim's pid with other fields than the control did ({outside}): {report}"
        )
        assert report.get("error") in DENIED or _lists_itself(report), (
            f"the confined probe was neither denied nor able to list itself: {report}"
        )
    finally:
        victim.kill()
        victim.wait()


# The variables `run` points into the private TMPDIR (every platform) ------------------------------

TMPDIR_VARIABLES = ("TMPDIR", "CLANG_MODULE_CACHE_PATH", "MAC_CHROMIUM_TMPDIR")
REQUIRED_BACKEND = "1" in (os.environ.get("BABYLON60_REQUIRE_LANDLOCK"), os.environ.get("BABYLON60_REQUIRE_SEATBELT"))


def test_run_points_tools_that_ignore_tmpdir_into_the_private_tmpdir() -> None:
    """The CI of f3747db (macos-15), through `run`: clang -fmodules could not write its module cache in the
    per-user C directory, and Chrome could not create its ProcessSingleton socket directory, which it makes
    where base::GetTempDir points (MAC_CHROMIUM_TMPDIR when not empty, else NSTemporaryDirectory(); that
    this gives the per-user T directory and not $TMPDIR is inferred from that failure, with the private
    TMPDIR writable: Chromium's code shows only the order). Both directories stay denied; `run` points
    each tool into the private TMPDIR instead, unless the user's environment names a place of its own.
    """
    tmp = "/private/var/folders/xy/abc123/T/babylon60-run-k3"
    cache = f"{tmp}/clang-module-cache"
    darwin = cli.private_tmp_environment({"PATH": "/usr/bin"}, tmp, platform="darwin")
    assert darwin == {"TMPDIR": tmp, "CLANG_MODULE_CACHE_PATH": cache, "MAC_CHROMIUM_TMPDIR": tmp}
    # Linux: clang's default cache is ~/.cache/clang/ModuleCache, under the denied home; Chromium reads $TMPDIR.
    assert cli.private_tmp_environment({}, tmp, platform="linux") == {"TMPDIR": tmp, "CLANG_MODULE_CACHE_PATH": cache}
    # A value the user set is kept; TMPDIR is always the private one.
    mine = {"TMPDIR": "/var/tmp", "CLANG_MODULE_CACHE_PATH": "/opt/cache", "MAC_CHROMIUM_TMPDIR": "/opt/chrome"}
    assert cli.private_tmp_environment(mine, tmp, platform="darwin") == {"TMPDIR": tmp}
    # Empty: clang reads it as "no module cache" (Driver::getDefaultModuleCachePath), so it stays the user's
    # choice, as unconfined; Chromium ignores it and would fall back to the denied T directory, so `run` sets it.
    empty = {"CLANG_MODULE_CACHE_PATH": "", "MAC_CHROMIUM_TMPDIR": ""}
    assert cli.private_tmp_environment(empty, tmp, platform="darwin") == {"TMPDIR": tmp, "MAC_CHROMIUM_TMPDIR": tmp}
    assert cli.private_tmp_environment(empty, tmp, platform="linux") == {"TMPDIR": tmp}


ENVIRONMENT_PROBE = (
    f"import json, os; print(json.dumps({{name: os.environ.get(name) for name in {TMPDIR_VARIABLES!r}}}))"
)


backend_here = pytest.mark.skipif(
    launcher.backend() == "none" and not REQUIRED_BACKEND,
    reason="no confinement backend here; BABYLON60_REQUIRE_LANDLOCK=1 or BABYLON60_REQUIRE_SEATBELT=1 fails instead",
)


def _run_cli(journal: Path, command: list[str]) -> list[str]:
    """`babylon60 run --journal <journal> -- <command>`; --allow-root only when this process is root."""
    allow_root = ["--allow-root"] if os.geteuid() == 0 else []
    return [*CLI, "run", *allow_root, "--journal", str(journal), "--", *command]


@backend_here
@pytest.mark.parametrize("case", ["unset", "set-by-the-user", "empty"])
def test_the_agent_receives_the_tmpdir_variables_through_run(tmp_path: Path, case: str) -> None:
    """Through the real command line, on this machine's backend (Landlock on Linux, Seatbelt on macOS).

    Started as the positive controls through `run` are (``_bounded``: stdin from /dev/null, so `run`
    takes the path without a terminal, and a process group of its own); a run that does not finish is
    inconclusive: a skip with the reason.
    """
    home, ws = tmp_path / "home", tmp_path / "ws"
    home.mkdir()
    ws.mkdir()
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(home),
        "LC_ALL": "C",
        "PYTHONPATH": str(ROOT / "01_KISH_ENGINE"),
        "TMPDIR": tempfile.gettempdir(),
    }
    users = {
        "unset": {},
        "set-by-the-user": {"CLANG_MODULE_CACHE_PATH": str(ws / "modules"), "MAC_CHROMIUM_TMPDIR": str(ws / "chrome")},
        "empty": {"CLANG_MODULE_CACHE_PATH": "", "MAC_CHROMIUM_TMPDIR": ""},
    }[case]
    env.update(users)
    probe = [launcher.interpreter(), "-I", "-S", "-c", ENVIRONMENT_PROBE]
    done = _bounded(_run_cli(tmp_path / "j.db", probe), timeout=180, env=env, cwd=ws)
    seen = _json_line(done.stdout)
    if not seen and _timed_out(done):
        pytest.skip(f"`babylon60 run` did not finish in 180 s; inconclusive: {done.stderr[-2000:]!r}")
    assert done.returncode == 0 and seen, f"the probe did not report (exit {done.returncode}): {done.stderr[-2000:]!r}"
    private = str(seen["TMPDIR"])
    assert os.path.basename(private).startswith("babylon60-run-") and not os.path.exists(private), seen
    expected = {
        "CLANG_MODULE_CACHE_PATH": os.path.join(private, "clang-module-cache"),
        "MAC_CHROMIUM_TMPDIR": private if sys.platform == "darwin" else None,
    }
    if case == "set-by-the-user":
        expected = users
    elif case == "empty":  # clang reads an empty value as "no cache": the user's; Chromium ignores an empty one
        expected = {"CLANG_MODULE_CACHE_PATH": "", "MAC_CHROMIUM_TMPDIR": private if sys.platform == "darwin" else ""}
    assert {name: seen[name] for name in expected} == expected, seen


# A module of its own, so no SDK is needed: clang builds B60 into its module cache when probe.c includes b60.h.
LOCAL_MODULE = {
    "b60.h": "int b60(void);\n",
    "module.modulemap": 'module B60 {\n  header "b60.h"\n  export *\n}\n',
    "probe.c": '#include "b60.h"\nint probe(void) { return b60(); }\n',
}
OBJECT_MAGIC = (*MACH_O, b"\x7fELF")
PRIVATE_CACHE_MARKER = "B60-MODULE-CACHE-IN-PRIVATE-TMPDIR"


@backend_here
def test_clang_builds_a_module_through_run_with_its_cache_in_the_private_tmpdir(tmp_path: Path) -> None:
    """clang -fmodules on a local module through `babylon60 run`, with the CLANG_MODULE_CACHE_PATH `run` sets.

    The control compiles unconfined, in its own decoy HOME and without the variable: clang's default
    cache (~/.cache/clang/ModuleCache on Linux, the per-user cache directory on macOS). Confined, the
    object must be built, the variable must point inside the agent's TMPDIR with the cache there, and
    the decoy HOME must stay without a cache. Before `run` set the variable, the same build through
    `run` failed on Linux (clang 18.1.3, Landlock): "unable to open output file
    .../.cache/clang/ModuleCache/...".
    """
    clang = shutil.which("clang", path="/usr/bin")
    if clang is None:
        pytest.skip("no /usr/bin/clang here")
    build = [clang, "-fmodules", "-fimplicit-module-maps", "-c", "probe.c", "-o", "probe.o"]

    def session(name: str) -> tuple[Path, dict[str, str]]:
        ws, tmp, env = _everyday_session(tmp_path / name)
        for file, content in LOCAL_MODULE.items():
            (ws / file).write_text(content)
        # The control's TMPDIR is its own; `run` creates the agent's private one under the session's.
        return ws, {**env, "TMPDIR": str(tmp) if name == "control" else tempfile.gettempdir()}

    def built(ws: Path) -> bool:
        with contextlib.suppress(OSError):
            return (ws / "probe.o").read_bytes()[:4] in OBJECT_MAGIC
        return False

    ws, env = session("control")
    control = _bounded(build, timeout=300, env=env, cwd=ws)
    if not built(ws):
        pytest.skip(
            f"clang cannot build a module here even unconfined (exit {control.returncode}): {control.stderr[-2000:]!r}"
        )
    ws, env = session("confined")
    script = (
        f"{shlex.join(build)} || exit; "
        'case "$CLANG_MODULE_CACHE_PATH" in "$TMPDIR"/?*) ;; '
        '*) echo "CLANG_MODULE_CACHE_PATH=$CLANG_MODULE_CACHE_PATH is not inside TMPDIR=$TMPDIR" >&2; exit 3;; esac; '
        f'if [ -n "$(ls -A "$CLANG_MODULE_CACHE_PATH" 2>/dev/null)" ]; then echo {PRIVATE_CACHE_MARKER}; fi'
    )
    journal = tmp_path / "journal.db"
    done = _bounded(_run_cli(journal, ["/bin/sh", "-c", script]), timeout=360, env=env, cwd=ws)
    if not built(ws) and _timed_out(done):
        pytest.skip(f"clang did not finish under `babylon60 run`; inconclusive: {done.stderr[-2000:]!r}")
    assert built(ws) and PRIVATE_CACHE_MARKER in done.stdout.split(), (
        f"clang -fmodules fails under `babylon60 run`, or its cache is not in the private TMPDIR (exit "
        f"{done.returncode}; journal: {_journal_story(journal)}); stderr: {done.stderr[-3000:]!r}"
    )
    home = Path(env["HOME"])
    assert not (home / ".cache").exists(), f"the confined build wrote a cache under the HOME: {list(home.rglob('*'))}"
