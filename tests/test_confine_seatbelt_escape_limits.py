"""macOS Seatbelt escape tests — Part 2 (WindowServer, volumes, lldb, hdiutil, shm, limits, profile rules)."""
# ruff: noqa: F401, F811

from __future__ import annotations

from collections.abc import Callable, Iterator
import contextlib
from dataclasses import dataclass
import json
import os
from pathlib import Path
import plistlib
import re
import secrets
import shlex
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import textwrap
import time
from typing import Any, NamedTuple, NoReturn

import pytest

from babylon60.confine import cli, demo, gitconfig, launcher, policy as policy_mod, seatbelt
from babylon60.confine.journal import ConfineJournal, JournalError
from babylon60.confine.policy import PRESETS, Policy, account_home, build_policy, default_homes
from test_confine_seatbelt import DATA, DENIED, TMP, Box, _matches, _paths, _regexes, _rule, _synthetic, macos
from tests.test_confine_seatbelt_escape import (  # noqa: F401
    APPLE_EVENT_REFUSALS,
    DEFAULTS,
    LAUNCHER_PROBE,
    LSOPEN_ONLY,
    LSREGISTER,
    OWN_TASK_PORTS,
    PNG,
    PROBE,
    ROOT,
    SCREENCAPTURE,
    SERVICES_ACTING_OUTSIDE,
    SHARED,
    TASK_PORTS,
    USER_DIR,
    _appeared,
    _as_run,
    _bounded,
    _closed,
    _control_as_run,
    _copy_key,
    _defaults,
    _escaped,
    _last_json,
    _launchctl,
    _launchd_env,
    _pasted,
    _png,
    _probe,
    _quietly,
    _script_app,
    _stderr,
    _victim,
    box,
    opened_app,
)


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
        assert segment.buf is not None
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
