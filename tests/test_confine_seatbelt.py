"""macOS Seatbelt backend: the rendered profile everywhere, its effect with the real ``sandbox-exec``.

Rendering tests run on every platform and check only the SBPL text that
``seatbelt.render_profile`` emits (order, forms, escaping, toggles). Behaviour
tests run only on macOS (the macos-15 CI job); set BABYLON60_REQUIRE_SEATBELT=1
there so a missing backend fails instead of skipping. Until a macOS run passes,
every Seatbelt behaviour asserted here stays NO_VERIFICADO.
"""

from __future__ import annotations

from collections.abc import Iterator
import dataclasses
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading

import pytest

from babylon60.confine import demo, launcher, seatbelt
from babylon60.confine.policy import PROTECTED_RELATIVE, Grant, Policy, build_policy, default_homes

REQUIRED = os.environ.get("BABYLON60_REQUIRE_SEATBELT") == "1"
macos = pytest.mark.skipif(
    sys.platform != "darwin" and not REQUIRED,
    reason="Seatbelt is macOS-only; BABYLON60_REQUIRE_SEATBELT=1 fails instead",
)
DENIED = ("EPERM", "EACCES")
DATA = "/System/Volumes/Data"
STRING = r'"(?:[^"\\]|\\.)*"'

# ---------------------------------------------------------------- rendering

HOME = "/Users/agent"
DEMO_HOME = "/private/var/folders/xy/abc123/T/babylon60-demo-k3/home"
WS = "/Users/agent/work/ws"
TMP = "/private/var/folders/xy/abc123/T/b60-tmp"


def _synthetic(**changes: object) -> Policy:
    """A macOS-shaped policy; render_profile only reads paths, so nothing here has to exist."""
    grants = (
        Grant(WS, "rw", 1, 2, True, "workspace"),
        Grant("/usr", "ro", 1, 3, True, "system"),
        Grant("/dev/null", "dev", 1, 4, False, "system"),
        Grant(TMP, "rw", 1, 5, True, "tmp"),
        Grant(f"{HOME}/.nvm", "ro", 1, 6, True, "preset:claude-code"),
        Grant(f"{HOME}/.codex", "rw", 1, 7, True, "preset:codex"),
        Grant("/opt/b60-tools/bin/tool", "ro", 1, 8, False, "user"),
        Grant("/dev/ttys003", "dev", 1, 9, False, "tty"),
    )
    protected = tuple(f"{home}/{rel}" for home in (HOME, DEMO_HOME) for rel in PROTECTED_RELATIVE)
    policy = Policy(WS, (HOME, DEMO_HOME), protected, grants)
    return dataclasses.replace(policy, **changes)  # type: ignore[arg-type]


def _top_level_forms(profile: str) -> list[str]:
    """Split the profile into s-expressions, checking parentheses and string quoting."""
    forms: list[str] = []
    depth, start, in_string, escaped = 0, 0, False, False
    for index, char in enumerate(profile):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "(":
            start = index if depth == 0 else start
            depth += 1
        elif char == ")":
            depth -= 1
            assert depth >= 0, profile[: index + 1]
            if depth == 0:
                forms.append(profile[start : index + 1])
        else:
            assert depth > 0 or char.isspace(), f"text outside a rule at offset {index}"
    assert depth == 0 and not in_string
    return forms


def _paths(rule: str, kind: str) -> list[str]:
    return [json.loads(token) for token in re.findall(rf"\({kind} ({STRING})\)", rule)]


def _regexes(rule: str) -> list[re.Pattern[str]]:
    return [re.compile(pattern) for pattern in _paths(rule, "regex")]


def _matches(patterns: list[re.Pattern[str]], path: str) -> bool:
    return any(pattern.search(path) for pattern in patterns)


def _rule(lines: list[str], prefix: str) -> int:
    return next(index for index, line in enumerate(lines) if line.startswith(prefix))


def test_rules_come_in_the_order_their_precedence_needs() -> None:
    profile = seatbelt.render_profile(_synthetic())
    lines = profile.splitlines()
    assert lines == _top_level_forms(profile), "one well-formed rule per line"
    assert lines[:2] == ["(version 1)", "(allow default)"]
    assert lines[2].startswith('(deny file-read* file-write* (subpath "/Users")')
    write_fallback = lines.index("(deny file-write*)")
    link_fallback = lines.index("(deny file-link file-clone)")
    devices = _rule(lines, '(allow file-write* (literal "/dev/null")')
    workspace = _rule(lines, f'(allow file-read* file-write* file-link file-clone (subpath "{WS}")')
    other_terminals = lines.index('(deny file-read* file-write* (regex "^/dev/ttys[0-9]+$"))')
    own_terminal = lines.index('(allow file-read* file-write* (literal "/dev/ttys003"))')
    unix_deny = lines.index("(deny network-outbound (remote unix-socket))")
    unix_allow = _rule(lines, "(allow network-outbound (remote unix-socket")
    assert 2 < write_fallback < devices < workspace and link_fallback < workspace
    assert workspace < other_terminals < own_terminal
    assert unix_deny < unix_allow
    assert lines[-2].startswith("(deny file-write-unlink file-clone (literal ")
    assert lines[-1].startswith(f'(deny file-read* file-write* file-link file-clone (subpath "{HOME}/.ssh")')


def test_ancestors_of_the_protected_set_can_be_neither_renamed_nor_cloned() -> None:
    lines = seatbelt.render_profile(_synthetic()).splitlines()
    ancestors = set(_paths(lines[-2], "literal"))
    expected = {"/Users", HOME, f"{HOME}/.config", f"{HOME}/Library", DEMO_HOME, os.path.dirname(DEMO_HOME)}
    assert expected | {DATA + path for path in expected} <= ancestors
    assert not ancestors & {"/", WS, f"{HOME}/work", f"{HOME}/.ssh", f"{HOME}/.config/gh"}
    assert (
        lines[-2]
        == "(deny file-write-unlink file-clone " + " ".join(f'(literal "{a}")' for a in sorted(ancestors)) + ")"
    )


def test_writes_are_an_allow_list() -> None:
    lines = seatbelt.render_profile(_synthetic()).splitlines()
    assert lines.count("(deny file-write*)") == 1
    writable: set[str] = set()
    for line in lines:
        operations = line.split(" (", 1)[0]
        if line.startswith("(allow") and "file-write*" in operations:
            assert "(regex" not in line
            writable.update(_paths(line, "literal"), _paths(line, "subpath"))
    granted = {path for grant in (WS, TMP, f"{HOME}/.codex") for path in (grant, DATA + grant)}
    devices = {"/dev/null", "/dev/zero", "/dev/dtracehelper", "/dev/tty", "/dev/fd", "/dev/ttys003"}
    assert writable == granted | devices
    assert '(subpath "/usr")' not in "\n".join(lines), "system grants keep the default, read-only"


def test_read_only_grants_may_be_cloned_but_not_linked() -> None:
    lines = seatbelt.render_profile(_synthetic()).splitlines()
    preset = lines[_rule(lines, f'(allow file-read* file-clone (subpath "{HOME}/.nvm")')]
    tool = lines[_rule(lines, '(allow file-read* file-clone (literal "/opt/b60-tools/bin/tool")')]
    for rule in (preset, tool):
        assert "file-link" not in rule and "file-write*" not in rule
    assert lines[_rule(lines, f'(allow file-read* file-write* file-link file-clone (subpath "{HOME}/.codex")')]
    assert lines[-1].split(" (", 1)[0] == "(deny file-read* file-write* file-link file-clone"
    assert "(when (defined? 'system-fcntl) (deny system-fcntl (fcntl-command 80 110)))" in lines


@pytest.mark.parametrize(
    ("path", "twin"),
    [
        (f"{HOME}/.ssh", f"{DATA}{HOME}/.ssh"),
        ("/Users", f"{DATA}/Users"),
        ("/private/var/folders/xy", f"{DATA}/private/var/folders/xy"),
        ("/opt/homebrew/bin", f"{DATA}/opt/homebrew/bin"),
        ("/usr/local/bin", f"{DATA}/usr/local/bin"),
        ("/Library/Developer", f"{DATA}/Library/Developer"),
        (f"{DATA}{HOME}", HOME),
        ("/usr/bin", None),
        ("/Usersx", None),
        ("/var/folders/xy", None),
        (f"{DATA}/sw", None),
        (DATA, None),
    ],
)
def test_data_volume_twins_follow_the_firmlinks(path: str, twin: str | None) -> None:
    assert seatbelt._data_volume_twin(path) == twin


def test_every_rule_names_the_data_volume_twin() -> None:
    lines = seatbelt.render_profile(_synthetic()).splitlines()
    assert {f"{DATA}/Users", f"{DATA}{HOME}", f"{DATA}{DEMO_HOME}"} <= set(_paths(lines[2], "subpath"))
    assert f"{DATA}{WS}" in _paths(lines[_rule(lines, "(allow file-read* file-write* file-link file-clone")], "subpath")
    assert f"{DATA}{HOME}/work" in _paths(lines[_rule(lines, "(allow file-read-metadata")], "literal")
    protected = _paths(lines[-1], "subpath")
    for rel in PROTECTED_RELATIVE:
        assert f"{HOME}/{rel}" in protected and f"{DATA}{HOME}/{rel}" in protected


def test_deny_rules_match_any_ascii_case_and_allow_rules_stay_exact() -> None:
    lines = seatbelt.render_profile(_synthetic()).splitlines()
    homes, protected = _regexes(lines[2]), _regexes(lines[-1])
    for path in (
        "/USERS",
        "/users/AGENT/.Ssh/id_rsa",
        f"{DATA}/users/agent",
        "/PRIVATE/var/FOLDERS/xy/ABC123/t/babylon60-demo-k3/HOME/x",
        f"{DATA.upper()}/PRIVATE/VAR/FOLDERS/XY/ABC123/T/BABYLON60-DEMO-K3/HOME",
    ):
        assert _matches(homes, path), path
    for path in ("/Usersx", "/opt/Users", "/private/var/folders/xy/abc123/T/babylon60-demo-k3/homey"):
        assert not _matches(homes, path), path
    variants = [f"{home}/{rel}".upper() for home in (HOME, DEMO_HOME, DATA + HOME) for rel in PROTECTED_RELATIVE]
    for path in (*variants, f"{HOME}/.SSH/id_rsa", f"{HOME}/.Config/GH/hosts.yml", f"{HOME}/library/keychains/x"):
        assert _matches(protected, path), path
    for path in (f"{HOME}/.sshx", f"{WS}/.ssh", f"{HOME}/.config/ghx", f"{HOME}/.config", f"{HOME}/Library"):
        assert not _matches(protected, path), path
    assert not any("(regex" in line for line in lines if line.startswith("(allow"))


def test_unix_socket_rules_follow_the_launch_flag() -> None:
    policy = _synthetic()
    closed = seatbelt.render_profile(policy).splitlines()
    opened = seatbelt.render_profile(policy, unix_sockets=True).splitlines()
    deny = "(deny network-outbound (remote unix-socket))"
    allow = (
        '(allow network-outbound (remote unix-socket (path-literal "/private/var/run/mDNSResponder"))'
        ' (remote unix-socket (path-literal "/private/var/run/syslog")))'
    )
    assert closed.index(deny) + 1 == closed.index(allow)
    assert [line for line in closed if line not in (deny, allow)] == opened
    assert not any("unix-socket" in line for line in opened)


def test_other_terminals_are_denied_unless_ptys_are_allowed() -> None:
    deny = '(deny file-read* file-write* (regex "^/dev/ttys[0-9]+$"))'
    own = '(allow file-read* file-write* (literal "/dev/ttys003"))'
    closed = seatbelt.render_profile(_synthetic()).splitlines()
    assert closed.index(deny) < closed.index(own)
    assert "/dev/ptmx" not in "\n".join(closed)
    opened = seatbelt.render_profile(_synthetic(allow_ptys=True)).splitlines()
    assert deny not in opened and own in opened
    assert '(allow file-read* file-write* (literal "/dev/ptmx") (regex "^/dev/ttys[0-9]+$"))' in opened
    terminals = re.compile(seatbelt.TERMINALS)
    assert terminals.search("/dev/ttys003") and terminals.search("/dev/ttys1000")
    for path in ("/dev/tty", "/dev/ttys", "/dev/ttys00a", "/dev/ttys003/x", "/x/dev/ttys003"):
        assert not terminals.search(path), path


def test_paths_are_escaped_in_literals_and_regexes(tmp_path: Path) -> None:
    home = tmp_path / 'h"o\\me (1)+[a].b{2}|$^*?'
    (home / ".ssh").mkdir(parents=True)
    ws = tmp_path / "ws"
    odd = ws / 'quo"te'
    odd.mkdir(parents=True)
    profile = seatbelt.render_profile(build_policy(ws, homes=[str(home)], read=[str(odd)], system=False))
    lines = profile.splitlines()
    assert lines == _top_level_forms(profile)
    assert '"' + str(odd).replace('"', '\\"') + '"' in profile
    assert str(home) in _paths(lines[2], "subpath")
    homes = _regexes(lines[2])
    assert _matches(homes, str(home)) and _matches(homes, str(home).upper() + "/.ssh/id_rsa")
    for old, new in ((".", "X"), ("(1)+", "11"), ("[a]", "a"), ("b{2}", "bb")):
        assert not _matches(homes, str(home).replace(old, new)), (old, new)


def test_regexes_are_split_to_fit_and_overlong_paths_are_refused() -> None:
    home = "/private/var/folders/" + "/".join(["d" * 40] * 4)
    protected = tuple(f"{home}/{rel}" for rel in PROTECTED_RELATIVE)
    policy = Policy(WS, (home,), protected, (Grant(WS, "rw", 1, 2, True, "workspace"),))
    lines = seatbelt.render_profile(policy).splitlines()
    literals = [token for line in lines for token in re.findall(STRING, line)]
    assert max(len(token.encode()) for token in literals) <= seatbelt.MAX_STRING_BYTES
    regexes = _regexes(lines[-1])
    parents = {os.path.dirname(path) for path in protected}
    assert len(regexes) > len(parents) * len(seatbelt._forms(home)), "the long group was split"
    for path in protected:
        assert _matches(regexes, path.upper() + "/x"), path
    with pytest.raises(ValueError, match="too long"):
        seatbelt.render_profile(dataclasses.replace(policy, homes=("/" + "h" * 300,)))


def test_rendering_is_deterministic() -> None:
    assert seatbelt.render_profile(_synthetic()) == seatbelt.render_profile(_synthetic())


# ---------------------------------------------------------------- behaviour (macOS)

ATTEMPT = r"""
import ctypes, errno, json, os, socket, sys

def _libc(name, *args):
    libc = ctypes.CDLL(None, use_errno=True)
    if getattr(libc, name)(*args) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))

def read(path):
    with open(path, "rb") as handle:
        return handle.read(4096)

def write(path):
    with open(path, "ab") as handle:
        handle.write(b"B60-WRITE\n")

def mkdir(path):
    os.mkdir(path)

def link(source, target):
    os.link(source, target)

def rename(source, target):
    os.rename(source, target)

def clone(source, target):
    _libc("clonefile", os.fsencode(source), os.fsencode(target), ctypes.c_uint32(0))

def chmod(path):
    os.chmod(path, 0o600)

def utime(path):
    os.utime(path, (0, 0))

def setxattr(path):
    _libc("setxattr", os.fsencode(path), b"org.babylon60.test", b"x", ctypes.c_size_t(1),
          ctypes.c_uint32(0), ctypes.c_int(0))

def open_tty(path):
    os.close(os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK))

def openpty():
    master, slave = os.openpty()
    os.close(master)
    os.close(slave)

def reach(path):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(10)
        client.connect(path)

def receive(path):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(10)
        client.connect(path)
        return client.recv(64)

def resolve(host):
    return socket.getaddrinfo(host, 80, proto=socket.IPPROTO_TCP)[0][4][0].encode()

def loopback():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        with socket.create_connection(server.getsockname(), timeout=5) as client:
            peer, _ = server.accept()
            with peer:
                client.sendall(b"ok")
                return peer.recv(2)

report = {"result": "ok", "data": ""}
try:
    data = globals()[sys.argv[1]](*sys.argv[2:])
    report["data"] = (data or b"").hex()
except OSError as exc:
    report["result"] = errno.errorcode.get(exc.errno or 0, "E%s" % exc.errno)
print(json.dumps(report), flush=True)
"""


@dataclasses.dataclass
class Box:
    root: Path
    home: Path
    key: Path
    ws: Path
    policy: Policy
    env: dict[str, str]

    def policy_with(self, workspace: Path | None = None, **kwargs: object) -> Policy:
        homes = [str(self.home), *default_homes()]
        runtime = [launcher.interpreter_prefix()]
        return build_policy(workspace or self.ws, homes=homes, runtime=runtime, **kwargs)  # type: ignore[arg-type]

    def run(self, argv: list[str], *, policy: Policy | None = None, unix_sockets: bool = False) -> launcher.Result:
        launch = launcher.Launch(argv, policy or self.policy, unix_sockets=unix_sockets)
        return launcher.run(launch, env=self.env, cwd=str(self.ws))

    def attempt(self, action: str, *args: object, policy: Policy | None = None, unix_sockets: bool = False) -> dict:
        argv = [launcher.interpreter(), "-I", "-S", "-B", "-c", ATTEMPT, action, *map(str, args)]
        result = self.run(argv, policy=policy, unix_sockets=unix_sockets)
        assert result.status.get("ok"), (result.status, result.stderr.decode("utf-8", "replace"))
        for line in reversed(result.stdout.decode("utf-8", "replace").splitlines()):
            try:
                return json.loads(line)
            except ValueError:
                continue
        raise AssertionError(result.stderr.decode("utf-8", "replace"))


@pytest.fixture
def box(tmp_path: Path) -> Box:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    key = home / ".ssh" / "id_rsa"
    key.write_text("B60-CANARY-seatbelt\n")
    ws = tmp_path / "ws"
    ws.mkdir()
    policy = build_policy(ws, homes=[str(home), *default_homes()], runtime=[launcher.interpreter_prefix()])
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "LC_ALL": "C"}
    return Box(tmp_path, home, key, ws, policy, env)


@pytest.fixture
def short_ws() -> Iterator[Path]:
    """A workspace whose socket paths fit the 104-byte sun_path limit."""
    base = Path(tempfile.mkdtemp(prefix="b60-", dir="/tmp"))
    try:
        (base / "ws").mkdir()
        yield base / "ws"
    finally:
        shutil.rmtree(base, ignore_errors=True)


class _Listener(threading.Thread):
    """Unconfined Unix socket server that hands out a token to the first client."""

    def __init__(self, path: Path, payload: bytes) -> None:
        super().__init__(daemon=True)
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(str(path))
        self.server.listen(1)
        self.server.settimeout(20)
        self.payload = payload

    def run(self) -> None:
        try:
            peer, _ = self.server.accept()
            with peer:
                peer.sendall(self.payload)
        except OSError:
            pass

    def close(self) -> None:
        self.server.close()
        self.join(timeout=1)


def _with_terminal(policy: Policy, path: str) -> Policy:
    st = os.stat(path)
    grant = Grant(path, "dev", st.st_dev, st.st_ino, False, "tty")
    return dataclasses.replace(policy, grants=(*policy.grants, grant))


@macos
def test_backend_is_seatbelt() -> None:
    assert launcher.backend() == "seatbelt"


@macos
@pytest.mark.parametrize("variant", ["default", "unix_sockets", "ptys", "terminal"])
def test_profile_is_accepted_by_sandbox_exec(box: Box, variant: str) -> None:
    master, slave = os.openpty()
    try:
        policy = box.policy
        if variant == "ptys":
            policy = dataclasses.replace(policy, allow_ptys=True)
        elif variant == "terminal":
            policy = _with_terminal(policy, os.ttyname(slave))
        profile = seatbelt.render_profile(policy, unix_sockets=variant == "unix_sockets")
        done = subprocess.run(
            [seatbelt.SANDBOX_EXEC, "-p", profile, "/usr/bin/true"], capture_output=True, text=True, timeout=30
        )
    finally:
        os.close(master)
        os.close(slave)
    assert done.returncode == 0, done.stderr


@macos
def test_home_is_denied_and_workspace_is_writable(box: Box) -> None:
    denied = box.run(["/bin/cat", str(box.key)])
    assert denied.returncode != 0 and b"B60-CANARY" not in denied.stdout
    assert b"Operation not permitted" in denied.stderr
    written = box.run(["/bin/sh", "-c", "echo ok > out.txt && cat out.txt"])
    assert written.returncode == 0 and written.stdout == b"ok\n", written.stderr


@macos
def test_real_home_stays_denied(box: Box) -> None:
    probe = box.run(["/bin/ls", default_homes()[0]])
    assert probe.returncode != 0 and b"Operation not permitted" in probe.stderr


@macos
def test_writes_outside_the_grants_are_denied(box: Box) -> None:
    outside = box.root / "outside.txt"
    assert box.attempt("write", outside)["result"] in DENIED
    assert box.attempt("mkdir", box.root / "planted")["result"] in DENIED
    assert not outside.exists() and not (box.root / "planted").exists()
    assert box.attempt("write", box.ws / "inside.txt")["result"] == "ok"
    assert (box.ws / "inside.txt").read_bytes() == b"B60-WRITE\n"


@macos
def test_directories_on_path_cannot_be_planted(box: Box) -> None:
    directories = [d for d in ("/opt/homebrew/bin", "/usr/local/bin") if os.path.isdir(d) and os.access(d, os.W_OK)]
    if not directories:
        pytest.skip("no user-writable directory on PATH outside the home on this machine")
    for directory in directories:
        target = Path(directory) / f"b60-plant-{secrets.token_hex(6)}"
        try:
            assert box.attempt("write", target)["result"] in DENIED, directory
            assert not target.exists(), directory
        finally:
            target.unlink(missing_ok=True)


@macos
def test_an_inherited_descriptor_outside_the_grants_stays_writable(box: Box) -> None:
    captured = box.root / "captured.txt"
    with open(captured, "wb") as stdout:
        process, status = launcher.spawn(
            launcher.Launch(["/bin/echo", "inherited"], box.policy), env=box.env, cwd=str(box.ws), stdout=stdout
        )
        _, stderr = process.communicate(timeout=60)
    assert status.get("ok") and process.returncode == 0, stderr
    assert captured.read_bytes() == b"inherited\n"


@macos
def test_standard_devices_and_redirections_work(box: Box) -> None:
    script = "printf a > /dev/null && printf b > /dev/stdout && printf c > /dev/stderr && head -c 2 /dev/zero | wc -c"
    done = box.run(["/bin/sh", "-c", script])
    assert done.returncode == 0, done.stderr
    assert done.stdout.split() == [b"b", b"2"] and done.stderr == b"c"


@macos
def test_private_tmp_and_shell_work(box: Box) -> None:
    private_tmp = box.root / "tmp"
    private_tmp.mkdir(mode=0o700)
    policy = box.policy_with(private_tmp=str(private_tmp))
    assert box.attempt("write", private_tmp / "scratch.txt", policy=policy)["result"] == "ok"
    shell = box.run(["/bin/sh", "-c", "echo ok"], policy=policy)
    assert shell.returncode == 0 and shell.stdout == b"ok\n", shell.stderr


@macos
def test_unix_sockets_need_the_launch_flag(box: Box, short_ws: Path) -> None:
    policy = box.policy_with(workspace=short_ws)
    for allowed in (False, True):
        path = short_ws / f"s{int(allowed)}"
        listener = _Listener(path, b"B60-SOCKET")
        listener.start()
        try:
            report = box.attempt("receive", path, policy=policy, unix_sockets=allowed)
        finally:
            listener.close()
        if allowed:
            assert report == {"result": "ok", "data": b"B60-SOCKET".hex()}
        else:
            assert report["result"] in DENIED and report["data"] == ""


@macos
def test_dns_socket_localhost_and_loopback_stay_reachable(box: Box) -> None:
    assert box.attempt("resolve", "localhost")["result"] == "ok"
    assert box.attempt("loopback") == {"result": "ok", "data": b"ok".hex()}
    responder = "/private/var/run/mDNSResponder"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
        try:
            probe.connect(responder)
        except OSError:
            pytest.skip("mDNSResponder socket unreachable even without confinement")
    assert box.attempt("reach", responder)["result"] == "ok"


@macos
def test_other_terminals_are_denied_and_the_session_terminal_is_not(box: Box) -> None:
    master, slave = os.openpty()
    try:
        name = os.ttyname(slave)
        assert box.attempt("open_tty", name)["result"] in DENIED
        assert box.attempt("open_tty", name, policy=_with_terminal(box.policy, name))["result"] == "ok"
        assert box.attempt("open_tty", name, policy=dataclasses.replace(box.policy, allow_ptys=True))["result"] == "ok"
    finally:
        os.close(master)
        os.close(slave)


@macos
def test_creating_a_pty_needs_allow_ptys(box: Box) -> None:
    assert box.attempt("openpty")["result"] != "ok"
    assert box.attempt("openpty", policy=dataclasses.replace(box.policy, allow_ptys=True))["result"] == "ok"


@macos
def test_firmlink_and_case_variants_of_the_home_are_denied(box: Box) -> None:
    twin = seatbelt._data_volume_twin(os.path.realpath(box.key))
    case = box.root / "HOME" / ".SSH" / "ID_RSA"
    variants = [path for path in (twin, str(case)) if path and os.path.exists(path)]
    if not variants:
        pytest.skip("neither a data-volume twin nor a case-insensitive volume here")
    for path in variants:
        report = box.attempt("read", path)
        assert report["result"] in DENIED and b"B60-CANARY".hex() not in report["data"], path


@macos
def test_case_variant_cannot_create_a_protected_directory(box: Box) -> None:
    config = box.home / ".config"
    config.mkdir()
    if not (box.home / ".CONFIG").exists():
        pytest.skip("case-sensitive volume")
    policy = box.policy_with(write=[str(config)])  # .config/gh is protected but absent
    assert box.attempt("mkdir", config / "GH", policy=policy)["result"] in DENIED
    assert box.attempt("mkdir", config / "gh", policy=policy)["result"] in DENIED
    assert not (config / "gh").exists()
    assert box.attempt("mkdir", config / "other", policy=policy)["result"] == "ok"


@macos
def test_a_protected_path_created_inside_a_grant_cannot_be_carried_away(box: Box) -> None:
    config = box.home / ".config"
    config.mkdir()
    policy = box.policy_with(write=[str(config)])  # .config/gh is protected but absent, so .config is granted
    (config / "gh").mkdir()
    (config / "gh" / "hosts.yml").write_text("B60-CANARY-gh\n")  # created later, as `gh auth login` would
    assert box.attempt("read", config / "gh" / "hosts.yml", policy=policy)["result"] in DENIED
    assert box.attempt("clone", config, box.ws / "cfg-clone", policy=policy)["result"] in DENIED
    assert box.attempt("rename", config, box.ws / "cfg-moved", policy=policy)["result"] in DENIED
    assert config.is_dir() and not (box.ws / "cfg-clone").exists() and not (box.ws / "cfg-moved").exists()
    assert box.attempt("write", config / "settings.json", policy=policy)["result"] == "ok"


@macos
def test_protected_files_cannot_be_cloned_but_workspace_files_can(box: Box) -> None:
    report = box.attempt("clone", box.key, box.ws / "clone")
    assert report["result"] in DENIED and not (box.ws / "clone").exists()
    (box.ws / "a.txt").write_text("ok")
    assert box.attempt("clone", box.ws / "a.txt", box.ws / "b.txt")["result"] == "ok"
    assert (box.ws / "b.txt").read_text() == "ok"


@macos
def test_a_hard_link_cannot_reach_a_file_outside_the_write_grants(box: Box) -> None:
    outside = box.root / "outside.txt"
    outside.write_text("original")
    link = box.ws / "link"
    report = box.attempt("link", outside, link)
    if link.exists():
        box.attempt("write", link)
    assert outside.read_text() == "original", "a write through the link reached a file outside the grants"
    assert report["result"] in DENIED and not link.exists(), report


@macos
def test_metadata_writes_outside_the_grants_are_denied(box: Box) -> None:
    outside = box.root / "outside.txt"
    outside.write_text("original")
    before = os.stat(outside)
    for action in ("chmod", "utime", "setxattr"):
        assert box.attempt(action, outside)["result"] in DENIED, action
    after = os.stat(outside)
    assert (after.st_mode, after.st_mtime_ns) == (before.st_mode, before.st_mtime_ns)


@macos
def test_demo_blocks_every_applicable_vector(tmp_path: Path) -> None:
    report = demo.run_demo(journal_path=tmp_path / "journal.db", workers=4)
    totals = report.document["totals"]
    assert report.exit_code == 0, "\n".join(report.transcript)
    assert totals["passed"] == 0 and totals["inconclusive"] == 0
    assert report.document["platform"]["backend"] == "seatbelt"
