"""macOS Seatbelt: what ``(allow default)`` leaves open besides files (review round 3, MACOS-1..15).

Rendering tests run everywhere and check the rules a fix adds; on the current renderer they fail,
which is the static half of each finding. Behaviour tests run only on macOS (the macos-15 CI job,
BABYLON60_REQUIRE_SEATBELT=1). Each one first runs its attempt WITHOUT confinement and skips when
that control has no effect on the machine (no GUI session, no TCC grant, no Developer Tools
access...), so a pass is never vacuous; the confined attempt must then have no effect. Before the
fix a failing behaviour test reproduces the finding; after it, the same test confirms the closure.

Every payload that runs outside the sandbox reads only the decoy key of the test's own disposable
HOME and writes it to a marker file outside the grants; nothing here reads real credentials.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import plistlib
import secrets
import shutil
import subprocess
import sys
import tempfile
import time

import pytest

from babylon60.confine import launcher, seatbelt
from babylon60.confine.policy import build_policy, default_homes
from test_confine_seatbelt import DATA, DENIED, TMP, Box, _matches, _paths, _regexes, _rule, _synthetic, macos

ROOT = Path(__file__).absolute().parents[1]

# ---------------------------------------------------------------- rendering (every platform)

USER_DIR = "/private/var/folders/xy/abc123"
SHARED = ("/private/tmp", "/private/var/tmp", "/Volumes", USER_DIR)
SPAWNING_AND_CREDENTIAL_SERVICES = (
    "com.apple.pasteboard.1",
    "com.apple.GSSCred",
    "com.apple.CoreSimulator.CoreSimulatorService",
    "com.apple.DiskArbitration.diskarbitrationd",
    "com.apple.accessibility.AXServer",
    "com.apple.tsm.portname",
)


def test_services_that_start_code_outside_the_sandbox_are_denied() -> None:
    """MACOS-1..3, 5, 11: `open`, osascript, launchctl, mounts and synthetic input reach past every file rule."""
    lines = seatbelt.render_profile(_synthetic()).splitlines()
    for operation in ("lsopen", "appleevent-send", "job-creation", "hid-control", "file-mount", "file-unmount"):
        assert f"(deny {operation})" in lines, f"{operation} is allowed by (allow default)"


def test_other_processes_can_be_neither_signalled_nor_read() -> None:
    """MACOS-4, MACOS-6, MACOS-12: only processes of this sandbox (the agent's own children) stay reachable."""
    lines = seatbelt.render_profile(_synthetic()).splitlines()
    assert lines.index("(deny signal)") < lines.index("(allow signal (target self) (target same-sandbox))")
    assert lines.index("(deny process-info*)") < lines.index(
        "(allow process-info* (target self) (target same-sandbox))"
    )
    assert '(deny sysctl-read (sysctl-name-prefix "kern.procargs"))' in lines
    assert "(when (defined? 'mach-priv-task-port) (deny mach-priv-task-port))" in lines


def test_preferences_are_not_written_through_cfprefsd() -> None:
    """MACOS-7: cfprefsd writes ~/Library/Preferences for its caller, past every file-write rule."""
    assert "(deny user-preference-write)" in seatbelt.render_profile(_synthetic()).splitlines()


def test_credential_and_spawning_services_are_not_looked_up() -> None:
    """MACOS-8, MACOS-9, MACOS-11: the pasteboard (unless clipboard=True), Kerberos, CoreSimulator, DiskArbitration."""
    closed = seatbelt.render_profile(_synthetic()).splitlines()
    names = set(_paths(next(line for line in closed if line.startswith("(deny mach-lookup")), "global-name"))
    assert set(SPAWNING_AND_CREDENTIAL_SERVICES) <= names
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
    """The same probe under the box's policy, or without confinement (``confined=False``, the control)."""
    argv = [launcher.interpreter(), "-I", "-S", "-B", "-c", PROBE, action, *map(str, args)]
    launch = launcher.Launch(argv, box.policy if confined else None, new_session=new_session)
    result = launcher.run(launch, env=box.env, cwd=str(box.ws))
    assert result.status.get("ok"), (result.status, result.stderr.decode("utf-8", "replace"))
    for line in reversed(result.stdout.decode("utf-8", "replace").splitlines()):
        try:
            return json.loads(line)
        except ValueError:
            continue
    raise AssertionError(result.stderr.decode("utf-8", "replace"))


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


def _control(argv: list[str], timeout: float) -> subprocess.CompletedProcess[bytes]:
    """The unconfined attempt; a consent dialog nobody answers (TCC, Developer Tools) makes it inconclusive."""
    try:
        return subprocess.run(argv, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        pytest.skip(f"{argv[0]} waited for a consent dialog even unconfined; nothing to compare here")


def _copy_key(box: Box, marker: Path) -> str:
    return f"/bin/cat '{box.key}' > '{marker}'"


# MACOS-1 ----------------------------------------------------------------------------------------


@macos
def test_launch_services_cannot_start_code_outside_the_sandbox(box: Box) -> None:
    marker = box.root / f"lsopen-{secrets.token_hex(4)}"
    app = _script_app(box.ws / "B60Probe.app", f"#!/bin/sh\n{_copy_key(box, marker)}\n")
    argv = ["/usr/bin/open", "-g", "-n", str(app)]
    control = _control(argv, 60)
    if control.returncode != 0 or not _escaped(box, marker):
        pytest.skip(f"LaunchServices does not launch apps in this session even unconfined: {control.stderr!r}")
    marker.unlink()
    confined = box.run(argv)
    assert not _escaped(box, marker), "MACOS-1: an app opened from inside the sandbox read the protected key outside it"
    assert confined.returncode != 0, confined.stderr


# MACOS-2 ----------------------------------------------------------------------------------------


@macos
@pytest.mark.parametrize("target", ["Finder", "Terminal"])
def test_apple_events_cannot_make_another_app_run_code(box: Box, target: str) -> None:
    marker = box.root / f"appleevent-{secrets.token_hex(4)}"
    if target == "Finder":
        app = _script_app(box.ws / "B60Probe.app", f"#!/bin/sh\n{_copy_key(box, marker)}\n")
        script = f'tell application "Finder" to open (POSIX file "{app}")'
    else:
        script = f'tell application "Terminal" to do script "{_copy_key(box, marker)}; exit"'
    argv = ["/usr/bin/osascript", "-e", script]
    control = _control(argv, 90)
    if control.returncode != 0 or not _escaped(box, marker):
        pytest.skip(f"Apple Events to {target} are not authorized here even unconfined: {control.stderr!r}")
    marker.unlink()
    box.run(argv)
    assert not _escaped(box, marker), f"MACOS-2: {target} ran code for the confined process, outside the sandbox"


# MACOS-3 ----------------------------------------------------------------------------------------


def _launchctl(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["/bin/launchctl", *args], capture_output=True, timeout=30)


@macos
@pytest.mark.parametrize("how", ["submit", "bootstrap"])
def test_launchd_jobs_cannot_be_created(box: Box, how: str) -> None:
    domains = [f"gui/{os.getuid()}", f"user/{os.getuid()}"]

    def attempt(confined: bool) -> tuple[Path, str, str | None]:
        marker = box.root / f"launchd-{secrets.token_hex(4)}"
        label = f"org.babylon60.probe.{secrets.token_hex(4)}"
        command = [
            "/bin/sh",
            "-c",
            f"{_copy_key(box, marker)}; sleep 600",
        ]  # the sleep keeps launchd from respawning it
        if how == "submit":
            argv, domain = ["/bin/launchctl", "submit", "-l", label, "--", *command], None
        else:
            plist = box.ws / f"{label}.plist"
            plist.write_bytes(plistlib.dumps({"Label": label, "ProgramArguments": command, "RunAtLoad": True}))
            domain = next((d for d in domains if _launchctl("print", d).returncode == 0), domains[-1])
            argv = ["/bin/launchctl", "bootstrap", domain, str(plist)]
        if confined:
            box.run(argv)
        else:
            _control(argv, 30)
        return marker, label, domain

    def remove(label: str, domain: str | None) -> None:
        _launchctl("remove", label) if domain is None else _launchctl("bootout", f"{domain}/{label}")

    marker, label, domain = attempt(confined=False)
    try:
        if not _escaped(box, marker):
            pytest.skip(f"launchctl {how} does not start jobs here even unconfined")
    finally:
        remove(label, domain)
    marker, label, domain = attempt(confined=True)
    try:
        assert not _escaped(box, marker), f"MACOS-3: launchctl {how} from inside the sandbox ran a job outside it"
    finally:
        remove(label, domain)


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
        report = _probe(box, "kill", victim.pid)
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
    cli = [sys.executable, "-m", "babylon60.cli.main_dispatcher"]
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
    domain = f"org.babylon60.probe.{secrets.token_hex(4)}"
    canary = f"B60-CANARY-{secrets.token_hex(8)}"
    try:
        if (
            _defaults("write", domain, "control", "ok").returncode
            or _defaults("read", domain, "control").stdout.strip() != "ok"
        ):
            pytest.skip("cfprefsd does not serve this session")
        box.run([DEFAULTS, "write", domain, "planted", canary])
        assert canary not in _defaults("read", domain, "planted").stdout, (
            f"MACOS-7: cfprefsd wrote ~/Library/Preferences/{domain}.plist for the confined process"
        )
    finally:
        _defaults("delete", domain)


@macos
@pytest.mark.xfail(
    strict=False,
    reason="reading preferences through cfprefsd is left open (locale and UI defaults); only writes are denied",
)
def test_preferences_of_other_programs_are_not_readable(box: Box) -> None:
    domain = f"org.babylon60.probe.{secrets.token_hex(4)}"
    canary = f"B60-CANARY-{secrets.token_hex(8)}"
    try:
        if (
            _defaults("write", domain, "token", canary).returncode
            or canary not in _defaults("read", domain, "token").stdout
        ):
            pytest.skip("cfprefsd does not serve this session")
        confined = box.run([DEFAULTS, "read", domain, "token"])
        assert canary.encode() not in confined.stdout, "MACOS-7: cfprefsd read a home plist for the confined process"
    finally:
        _defaults("delete", domain)


# MACOS-8 ----------------------------------------------------------------------------------------


@macos
def test_the_pasteboard_is_neither_readable_nor_writable(box: Box) -> None:
    canary = f"B60-CANARY-{secrets.token_hex(8)}"
    previous = subprocess.run(["/usr/bin/pbpaste"], capture_output=True, timeout=30).stdout
    try:
        copied = subprocess.run(["/usr/bin/pbcopy"], input=canary.encode(), capture_output=True, timeout=30)
        if copied.returncode or canary.encode() not in subprocess.run(["/usr/bin/pbpaste"], capture_output=True).stdout:
            pytest.skip("no pasteboard server in this session")
        assert canary.encode() not in box.run(["/usr/bin/pbpaste"]).stdout, (
            "MACOS-8: the confined process read the clipboard"
        )
        planted = f"B60-PASTE-{secrets.token_hex(8)}"
        box.run(["/bin/sh", "-c", f"printf %s {planted} | /usr/bin/pbcopy"])
        after = subprocess.run(["/usr/bin/pbpaste"], capture_output=True, timeout=30).stdout
        assert planted.encode() not in after, "MACOS-8: the confined process replaced what the user pastes next"
    finally:
        subprocess.run(["/usr/bin/pbcopy"], input=previous, capture_output=True, timeout=30)


# MACOS-9, MACOS-11 ------------------------------------------------------------------------------


@macos
@pytest.mark.parametrize("service", SPAWNING_AND_CREDENTIAL_SERVICES)
def test_services_that_act_outside_the_sandbox_are_not_reachable(box: Box, service: str) -> None:
    control = bytes.fromhex(_probe(box, "lookup", service, confined=False)["data"])
    if control != b"0":
        pytest.skip(f"{service} is not registered in this session (bootstrap_look_up returned {control.decode()})")
    report = bytes.fromhex(_probe(box, "lookup", service)["data"])
    assert report != b"0", f"MACOS-9/11: {service} is reachable from inside the sandbox"


# MACOS-10 ----------------------------------------------------------------------------------------


@macos
def test_files_of_other_programs_outside_the_homes_are_not_readable(box: Box) -> None:
    canary = f"B60-CANARY-{secrets.token_hex(8)}"
    user_temp = os.confstr(65537)  # _CS_DARWIN_USER_TEMP_DIR, where `run` creates every session's private TMPDIR
    sibling = Path(tempfile.mkdtemp(prefix="babylon60-run-", dir=user_temp))  # another session's private TMPDIR
    shared = Path(tempfile.mkdtemp(prefix="b60-", dir="/private/tmp"))  # e.g. MIT Kerberos FILE: caches, tool logs
    try:
        for path in (sibling / "note.txt", shared / f"krb5cc_{os.getuid()}"):
            path.write_text(canary)
            path.chmod(0o600)
            assert _probe(box, "read", path, confined=False)["data"] == canary.encode().hex()
            report = _probe(box, "read", path)
            assert report["result"] in DENIED and not report["data"], f"MACOS-10: {path} is readable from the sandbox"
    finally:
        shutil.rmtree(sibling, ignore_errors=True)
        shutil.rmtree(shared, ignore_errors=True)


# MACOS-12 ---------------------------------------------------------------------------------------


@macos
def test_processes_outside_the_sandbox_cannot_be_debugged(box: Box) -> None:
    """A user process without the hardened runtime (here one built on the spot, like most dev builds)."""
    lldb, cc = shutil.which("lldb", path="/usr/bin"), shutil.which("cc", path="/usr/bin")
    target = box.root / "victim"
    built = cc and subprocess.run(
        [cc, "-x", "c", "-", "-o", str(target)], input=b"#include <unistd.h>\nint main(void){sleep(300);}\n"
    )
    if lldb is None or not built or built.returncode:
        pytest.skip("no lldb or no C compiler (Xcode or the Command Line Tools)")
    victim = subprocess.Popen([str(target)])
    try:

        def attach(marker: Path) -> list[str]:
            expression = f'expr (int)system("{_copy_key(box, marker)}")'
            return [lldb, "--batch", "-p", str(victim.pid), "-o", expression, "-o", "process detach"]

        marker = box.root / f"debug-{secrets.token_hex(4)}"
        _control(attach(marker), 180)
        if not _escaped(box, marker):
            pytest.skip("lldb cannot attach here even unconfined (Developer Tools access not granted)")
        marker = box.root / f"debug-{secrets.token_hex(4)}"
        box.run(attach(marker))
        assert not _escaped(box, marker), "MACOS-12: the confined process ran code inside an unconfined process"
    finally:
        victim.kill()
        victim.wait()


# MACOS-5 ---------------------------------------------------------------------------------------


@macos
@pytest.mark.xfail(
    strict=False,
    reason="declared limit (macOS): hdiutil mounts through a DiskImages helper outside the sandbox; "
    "file-mount covers only the caller's own mount(2) (measured on macos-15)",
)
def test_a_disk_image_cannot_be_mounted_over_a_directory_outside_the_grants(box: Box) -> None:
    """``target`` stands for /opt/homebrew/bin: owned by the user, on PATH, outside every grant."""
    target, payload = box.root / "bin", box.root / "payload"
    target.mkdir()
    payload.mkdir()
    (target / "git").write_text("#!/bin/sh\necho original\n")
    (payload / "git").write_text("#!/bin/sh\necho B60-MOUNTED\n")
    image = box.ws / "tools.dmg"  # an agent can as well download one: the network is open
    hdiutil = "/usr/bin/hdiutil"
    made = subprocess.run(
        [hdiutil, "create", "-quiet", "-srcfolder", str(payload), "-format", "UDZO", str(image)],
        capture_output=True,
        timeout=300,
    )
    if made.returncode:
        pytest.skip(f"hdiutil cannot create images here: {made.stderr!r}")
    attach = [hdiutil, "attach", "-quiet", "-nobrowse", "-mountpoint", str(target), str(image)]

    def detach() -> None:
        subprocess.run([hdiutil, "detach", "-force", str(target)], capture_output=True, timeout=120)

    try:
        control = _control(attach, 300)
        if control.returncode or "B60-MOUNTED" not in (target / "git").read_text():
            pytest.skip(f"hdiutil cannot mount over a user-owned directory here even unconfined: {control.stderr!r}")
    finally:
        detach()
    private_tmp = box.root / "tmp"  # `run` gives the agent a writable TMPDIR; so does this attempt
    private_tmp.mkdir(mode=0o700)
    policy = box.policy_with(private_tmp=str(private_tmp))
    try:
        confined = launcher.run(
            launcher.Launch(attach, policy), env={**box.env, "TMPDIR": str(private_tmp)}, cwd=str(box.ws), timeout=300
        )
        assert "B60-MOUNTED" not in (target / "git").read_text(), (
            f"MACOS-5: the confined process replaced what {target} shows to unconfined processes"
        )
        assert confined.returncode != 0, confined.stderr
    finally:
        detach()


# MACOS-13 ---------------------------------------------------------------------------------------


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
            "MACOS-13: shared memory read from the sandbox"
        )
    finally:
        segment.close()
        segment.unlink()


# MACOS-14 ---------------------------------------------------------------------------------------


@macos
@pytest.mark.xfail(
    strict=False,
    reason="MACOS-14: whether XNU answers alike for a denied name and a missing one is what this run measures",
)
def test_denied_paths_do_not_tell_which_names_exist(box: Box) -> None:
    missing = box.home / ".ssh" / f"absent-{secrets.token_hex(4)}"
    assert _probe(box, "stat", missing, confined=False)["result"] == "ENOENT"
    present, absent = _probe(box, "stat", box.key)["result"], _probe(box, "stat", missing)["result"]
    assert present in DENIED
    assert absent == present, f"MACOS-14: stat answers {present} for the key and {absent} for a missing name"


# MACOS-15 and the names a fix relies on ----------------------------------------------------------


@macos
def test_the_fcntl_rule_is_not_skipped_silently() -> None:
    """(when (defined? 'system-fcntl) ...) is a no-op where the operation is unknown; prove the branch is taken."""
    hosts = '(deny file-read* (literal "/private/etc/hosts"))'
    probe = f"(version 1)\n(allow default)\n(when (defined? 'system-fcntl) {hosts})\n"
    done = subprocess.run(
        [seatbelt.SANDBOX_EXEC, "-p", probe, "/bin/cat", "/etc/hosts"], capture_output=True, timeout=30
    )
    assert done.returncode != 0, (
        "MACOS-15: system-fcntl is undefined, so F_MAKECOMPRESSED/F_TRANSFEREXTENTS stay allowed"
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
    "(when (defined? 'mach-priv-task-port) (deny mach-priv-task-port))",
    "(deny user-preference-write)",
    '(deny mach-lookup (global-name "com.apple.pasteboard.1"))',
    '(when (defined? \'file-write-setugid) (deny file-write-setugid (subpath "/")))',
    "(deny system-fcntl (fcntl-command 80 110))",
)
CANDIDATE_RULES = (
    "(deny mach-priv-task-port)",
    "(deny file-write-setugid)",
    "(deny mach-priv-task-port (target others))\n(allow mach-priv-task-port (target same-sandbox))",
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
    """The macOS side of the seccomp setid rule: no setuid program left behind in the workspace."""
    tool = box.ws / f"tool-{mode:o}"
    tool.write_text("#!/bin/sh\nexec /bin/sh\n")
    script = f"import os; os.chmod({str(tool)!r}, {mode})"
    box.run([launcher.interpreter(), "-I", "-S", "-c", script])
    assert not os.stat(tool).st_mode & 0o6000, "the confined process set a setuid or setgid bit"
    os.chmod(tool, mode)  # control: the owner may set it outside the sandbox
    assert os.stat(tool).st_mode & 0o6000
