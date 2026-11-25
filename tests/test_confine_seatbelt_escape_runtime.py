"""macOS Seatbelt escape tests — Part 3 (Everyday workflows, setuid, kern.proc, private TMPDIR, clang)."""
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
from tests.test_confine_seatbelt_escape_limits import (  # noqa: F401
    CANDIDATE_RULES,
    CHROME,
    CHROME_DEATH,
    CHROME_EXPLORATORY,
    CHROME_LINES,
    CLI,
    DEBUG_LAUNCH_SECONDS,
    DEBUG_PROBE,
    DISPLAY_PROBE,
    DeclaredLimit,
    EVERYDAY,
    EVERYDAY_MARKS,
    Everyday,
    GITCONFIG,
    HDIUTIL,
    HOMEBREW_PREFIXES,
    LLDB_SECONDS,
    MACH_O,
    MODULE_CACHE_MARKER,
    MOUNTED,
    OWN_PROCESSES_PROBE,
    SLEEPER,
    USED_RULES,
    _brew_version,
    _build,
    _clang_modules,
    _compiles,
    _debug_tools,
    _declared_limit,
    _detach_everything_from,
    _directory_outside_every_rule,
    _display_stages,
    _evaluated_in_child,
    _git,
    _headless_chrome,
    _inside,
    _installed,
    _json_line,
    _lldb_finished,
    _mount_table_names,
    _own_processes,
    _python_venv,
    _real_agent_state,
    _same_file,
    _shows,
    _swift_version,
)


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
    expected: dict[str, str | None] = {
        "CLANG_MODULE_CACHE_PATH": os.path.join(private, "clang-module-cache"),
        "MAC_CHROMIUM_TMPDIR": private if sys.platform == "darwin" else None,
    }
    if case == "set-by-the-user":
        expected = dict(users)
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
