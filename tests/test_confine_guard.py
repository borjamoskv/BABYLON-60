"""Aliases of protected paths, missing self paths and the home of a sudo user.

Hardlinks are real links on the test filesystem. Bind mounts are real too: they
are made in a child process inside a private mount namespace (a mount namespace
as root, a user plus mount namespace otherwise) and disappear with it; those
tests skip only when the kernel refuses the namespace. Every home is a throwaway
directory holding a canary, never a real home.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import pwd
import statistics
import subprocess
import sys
import textwrap
import time
from typing import Any

import pytest

from babylon60.confine import aliases, launcher
from babylon60.confine import policy as pol
from babylon60.confine.policy import MIN_LANDLOCK_ABI, PolicyError, build_policy, default_homes

ROOT = Path(__file__).absolute().parents[1]
LINUX = sys.platform.startswith("linux")
REQUIRED = os.environ.get("BABYLON60_REQUIRE_LANDLOCK") == "1"
needs_linux = pytest.mark.skipif(not LINUX, reason="mount namespaces and mountinfo are Linux-only")
CANARY = "B60-CANARY-guard"


@pytest.fixture
def layout(tmp_path: Path) -> dict[str, Path]:
    home = tmp_path / "home"
    ssh = home / ".ssh"
    ssh.mkdir(parents=True)
    key = ssh / "id_rsa"
    key.write_text(f"{CANARY}\n")
    ws = tmp_path / "ws"
    ws.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    return {"root": tmp_path, "home": home, "ssh": ssh, "key": key, "ws": ws, "other": other}


def _build(layout: dict[str, Path], **kwargs: Any) -> pol.Policy:
    kwargs.setdefault("homes", [str(layout["home"])])
    kwargs.setdefault("system", False)
    return build_policy(kwargs.pop("workspace", layout["ws"]), **kwargs)


def _l2(path: Path, links: int) -> str:
    return f"{path} has {links} links; another path to it may be readable (declared limit L2)"


# Hardlinks and other aliases granted directly ------------------------------------------------


@pytest.mark.parametrize("option", ["read", "write"])
def test_hardlink_of_a_protected_key_is_refused_as_a_user_grant(layout: dict[str, Path], option: str) -> None:
    link = layout["other"] / "notes.txt"
    os.link(layout["key"], link)
    with pytest.raises(PolicyError) as refused:
        _build(layout, **{option: [str(link)]})
    assert str(refused.value) == f"Refusing an alias of protected {layout['key']}: {link}"


def test_hardlink_of_a_protected_key_is_skipped_as_a_non_strict_grant(layout: dict[str, Path]) -> None:
    link = layout["other"] / "notes.txt"
    os.link(layout["key"], link)
    policy = _build(layout, runtime=[str(link)])
    assert [g.path for g in policy.grants] == [str(layout["ws"])]
    assert policy.skipped == (f"{link}: Refusing an alias of protected {layout['key']}: {link}",)


def test_hardlink_of_a_nested_protected_entry_is_refused(layout: dict[str, Path]) -> None:
    nested = layout["ssh"] / "deploy" / "ci"
    nested.mkdir(parents=True)
    (nested / "id_ed25519").write_text(f"{CANARY}-nested\n")
    link = layout["other"] / "ci"
    os.link(nested / "id_ed25519", link)
    with pytest.raises(PolicyError, match="alias of protected .*/deploy/ci/id_ed25519"):
        _build(layout, read=[str(link)])


def test_hardlink_of_a_protected_file_is_an_alias_and_the_file_itself_is_inside(layout: dict[str, Path]) -> None:
    netrc = layout["home"] / ".netrc"
    netrc.write_text(f"machine example login agent password {CANARY}\n")
    link = layout["other"] / "netrc"
    os.link(netrc, link)
    with pytest.raises(PolicyError) as alias:
        _build(layout, read=[str(link)])
    assert str(alias.value) == f"Refusing an alias of protected {netrc}: {link}"
    with pytest.raises(PolicyError, match="inside protected path"):
        _build(layout, read=[str(netrc)])


def test_symbolic_links_below_protected_directories_are_not_followed(layout: dict[str, Path]) -> None:
    shared = layout["other"] / "shared"
    shared.mkdir()
    (shared / "readme.txt").write_text("public\n")
    (layout["ssh"] / "shared").symlink_to(shared)
    (layout["ssh"] / "loop").symlink_to(layout["ssh"])
    policy = _build(layout, read=[str(shared), str(shared / "readme.txt")])
    assert {str(shared), str(shared / "readme.txt")} <= {g.path for g in policy.grants}
    assert policy.warnings == ()


# Link counts ---------------------------------------------------------------------------------


def test_extra_links_are_warned_only_when_one_is_outside_the_protected_paths(layout: dict[str, Path]) -> None:
    os.link(layout["key"], layout["ssh"] / "id_rsa.bak")
    assert _build(layout).warnings == ()
    os.link(layout["key"], layout["other"] / "copy")
    assert _build(layout).warnings == (_l2(layout["key"], 3),)


def test_link_warning_counts_a_protected_file_and_aliased_homes_once(layout: dict[str, Path]) -> None:
    netrc = layout["home"] / ".netrc"
    netrc.write_text("x\n")
    os.link(netrc, layout["other"] / "netrc")
    os.link(layout["key"], layout["other"] / "key")
    alias = layout["root"] / "home-alias"
    alias.symlink_to(layout["home"])
    policy = _build(layout, homes=[str(layout["home"]), str(alias)])
    assert policy.warnings == (_l2(netrc, 2), _l2(layout["key"], 2))


# The launcher's own state --------------------------------------------------------------------


def test_missing_self_path_is_protected_through_its_nearest_existing_ancestor(layout: dict[str, Path]) -> None:
    state = layout["other"] / "state"
    (state / "sibling").mkdir(parents=True)
    journal = state / "not-yet" / "journal.db"
    for target in (state, layout["other"]):
        with pytest.raises(PolicyError, match=r"launcher's own state \(.*not-yet/journal\.db\)"):
            _build(layout, write=[str(target)], self_paths=[str(journal)])
    policy = _build(layout, write=[str(state / "sibling")], read=[str(state)], self_paths=[str(journal)])
    assert {g.path: g.access for g in policy.grants}[str(state)] == "ro"
    assert not journal.parent.exists()


def test_missing_self_path_follows_symbolic_links_and_dotdot_like_mkdir(layout: dict[str, Path]) -> None:
    real = layout["other"] / "real"
    (real / "deep").mkdir(parents=True)
    link = layout["root"] / "link"
    link.symlink_to(real / "deep")
    journal = f"{link}/new/../../elsewhere/journal.db"  # physically real/elsewhere/journal.db
    with pytest.raises(PolicyError, match="launcher's own state"):
        _build(layout, write=[str(real)], self_paths=[journal])
    _build(layout, write=[str(real / "deep")], self_paths=[journal])
    Path(journal).parent.mkdir(parents=True)
    assert (real / "elsewhere").is_dir()
    existing = f"{link}/../journal.db"  # an existing file: its directory is real/, not the link's parent
    Path(existing).write_text("")
    assert (real / "journal.db").is_file()
    with pytest.raises(PolicyError, match="launcher's own state"):
        _build(layout, write=[str(real)], self_paths=[existing])


# Homes ---------------------------------------------------------------------------------------


def test_home_of_the_sudo_user_is_a_default_home(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUDO_USER", raising=False)
    base = default_homes()
    entry = next((e for e in pwd.getpwall() if e.pw_dir and os.path.abspath(e.pw_dir) not in base), None)
    if entry is None:
        pytest.skip("the account database has no second home")
    monkeypatch.setenv("SUDO_USER", entry.pw_name)
    assert default_homes() == (*base, os.path.abspath(entry.pw_dir))
    for ignored in ("babylon60-no-such-user", pwd.getpwuid(os.getuid()).pw_name):
        monkeypatch.setenv("SUDO_USER", ignored)
        assert default_homes() == base


# Bounds and speed ----------------------------------------------------------------------------


def test_scan_tree_bounds_entries_and_depth_and_skips_visited_directories(tmp_path: Path) -> None:
    flat = tmp_path / "flat"
    flat.mkdir()
    for index in range(15):
        (flat / f"e{index}").write_text("x")
    scan = aliases.scan_tree(str(flat), limit=10)
    assert (scan.stopped, scan.listed, len(scan.entries)) == ("10 entries", 10, 10)
    deep = tmp_path / "deep"
    chain = [deep.joinpath(*[f"l{i}" for i in range(level + 1)]) for level in range(6)]
    chain[-1].mkdir(parents=True)
    visited: set[tuple[int, int]] = set()
    scan = aliases.scan_tree(str(deep), depth=3, visited=visited)
    assert scan.stopped == "depth 3"
    assert str(chain[3]) in scan.entries.values() and str(chain[4]) not in scan.entries.values()
    assert aliases.scan_tree(str(deep), visited=visited).entries == {}


def test_alias_scan_bound_is_reported(layout: dict[str, Path]) -> None:
    flat = layout["ssh"] / "flat"
    flat.mkdir()
    for index in range(aliases.SCAN_LIMIT + 1):
        os.close(os.open(flat / f"e{index}", os.O_CREAT | os.O_WRONLY | os.O_CLOEXEC, 0o600))
    assert _build(layout).warnings == (
        f"{layout['ssh']}: alias scan stopped at {aliases.SCAN_LIMIT} entries; "
        "hardlinks and bind mounts of entries beyond it are not detected",
    )


def test_guard_stays_fast_with_thousands_of_protected_entries(layout: dict[str, Path]) -> None:
    ssh = layout["ssh"]
    for index in range(3000):
        (ssh / f"known_hosts.{index}").write_text("x")
    for group in range(50):
        (ssh / f"d{group}").mkdir()
        for index in range(20):
            (ssh / f"d{group}" / f"k{index}").write_text("x")
    entries = 1 + 3000 + 50 * 21
    link = layout["other"] / "late"
    os.link(ssh / "d49" / "k19", link)
    samples = []
    for _ in range(7):
        start = time.perf_counter()
        policy = _build(layout, runtime=[str(link)], system=True)
        samples.append(time.perf_counter() - start)
    median = statistics.median(samples)
    print(
        f"\nguard: {entries} protected entries, build_policy median {median * 1000:.1f} ms, max {max(samples) * 1000:.1f} ms"
    )
    assert str(link) not in {g.path for g in policy.grants}
    assert policy.warnings == (_l2(ssh / "d49" / "k19", 2),)
    assert median < 1.0


@pytest.mark.skipif(os.geteuid() == 0, reason="root lists directories whatever their mode")
def test_unlistable_protected_directory_is_reported(layout: dict[str, Path]) -> None:
    gnupg = layout["home"] / ".gnupg"
    gnupg.mkdir(mode=0o700)
    hidden = layout["ssh"] / "hidden"
    hidden.mkdir()
    for path in (gnupg, hidden):
        path.chmod(0o300)
    try:
        warnings = _build(layout).warnings
    finally:
        for path in (gnupg, hidden):
            path.chmod(0o700)
    assert f"{gnupg} could not be listed (Permission denied); " in "\n".join(warnings)
    assert any(w.startswith(f"{layout['ssh']}: 1 directories below it could not be listed") for w in warnings)


# mountinfo -----------------------------------------------------------------------------------


def test_mountinfo_octal_escapes_are_decoded_once() -> None:
    line = (
        rb"36 35 98:0 /src\040dir\134x /mnt/a\040b\011c\012d\134e\134012 rw,noatime master:1 shared:7 - "
        rb"ext4 /dev/my\040disk rw,errors=continue"
    )
    (mount,) = aliases.parse_mountinfo(line + b"\n")
    assert mount.mount_point == "/mnt/a b\tc\nd\\e\\012"
    assert mount.root == "/src dir\\x"
    assert (mount.mount_id, mount.parent_id, mount.device, mount.fstype, mount.source) == (
        36,
        35,
        "98:0",
        "ext4",
        "/dev/my disk",
    )
    (raw,) = aliases.parse_mountinfo(b"22 27 0:21 / /mnt/\xff\xfe rw - proc proc rw\n")
    assert os.fsencode(raw.mount_point) == b"/mnt/\xff\xfe"
    with pytest.raises(aliases.MountinfoError):
        aliases.parse_mountinfo(b"22 27 0:21 / /proc rw,relatime proc proc rw\n")


@needs_linux
def test_the_real_mount_table_parses() -> None:
    mounts = aliases.read_mountinfo()
    assert mounts and any(m.mount_point == "/" for m in mounts)
    assert all(os.path.isabs(m.mount_point) for m in mounts)


# Shared directories and credential files --------------------------------------------------------


@pytest.mark.parametrize("where", ["workspace", "read", "write"])
def test_a_sticky_directory_everyone_can_write_is_refused(layout: dict[str, Path], where: str) -> None:
    shared = layout["root"] / "shared"
    shared.mkdir()
    shared.chmod(0o1777)  # like /tmp: other programs keep sockets and credential caches there
    kwargs: dict[str, Any] = {"workspace": shared} if where == "workspace" else {where: [str(shared)]}
    with pytest.raises(PolicyError, match="everyone can write"):
        _build(layout, **kwargs)
    project = shared / "project"
    project.mkdir()
    assert _build(layout, workspace=project).workspace == str(project)
    shared.chmod(0o777)  # writable by everyone but not sticky: not refused for that
    assert _build(layout, workspace=shared).workspace == str(shared)


@pytest.mark.parametrize(
    "rel", [".npmrc", ".pypirc", ".cargo/credentials.toml", ".config/git/credentials", ".vault-token"]
)
def test_credential_files_are_protected_and_refuse_the_grants_around_them(layout: dict[str, Path], rel: str) -> None:
    secret = layout["home"] / rel
    secret.parent.mkdir(parents=True, exist_ok=True)
    secret.write_text(f"{CANARY}\n")
    policy = _build(layout)
    assert str(secret) in policy.protected
    with pytest.raises(PolicyError, match="protected"):
        _build(layout, read=[str(secret)])
    if secret.parent != layout["home"]:
        with pytest.raises(PolicyError, match="contains protected path"):
            _build(layout, read=[str(secret.parent)])
        secret.unlink()  # absent: the directory around it can be granted again
        assert _build(layout, read=[str(secret.parent)]).grants


def test_write_grants_inside_a_self_directory_are_refused_and_siblings_are_not(layout: dict[str, Path]) -> None:
    code = layout["root"] / "launcher"
    (code / "lib").mkdir(parents=True)
    with pytest.raises(PolicyError, match="inside the launcher's own state"):
        _build(layout, write=[str(code / "lib")], self_paths=[str(code)])
    assert _build(layout, read=[str(code / "lib")], self_paths=[str(code)]).grants
    assert _build(layout, write=[str(layout["other"])], self_paths=[str(code)]).grants
    # A self path that is a file (the journal, the interpreter) has nothing inside it.
    journal = layout["root"] / "journal.db"
    journal.write_bytes(b"")
    assert _build(layout, write=[str(layout["other"])], self_paths=[str(journal)]).grants


# Bind mounts, made for real in a private mount namespace ---------------------------------------

NAMESPACE = r"""
import ctypes
import json
import os
import sys

from babylon60.confine import aliases, launcher
from babylon60.confine.policy import PolicyError, build_policy

ARGS = json.loads(sys.argv[1])
libc = ctypes.CDLL(None, use_errno=True)
CLONE_NEWNS, CLONE_NEWUSER, MS_BIND, MS_REC, MS_PRIVATE = 0x00020000, 0x10000000, 0x1000, 0x4000, 0x40000


def _private_namespace():
    for flags in ([CLONE_NEWNS] if os.geteuid() == 0 else []) + [CLONE_NEWUSER | CLONE_NEWNS]:
        if libc.unshare(flags) == 0:
            break
    else:
        return "unshare: " + os.strerror(ctypes.get_errno())
    if libc.mount(None, b"/", None, MS_REC | MS_PRIVATE, None) != 0:
        return "mount --make-rprivate /: " + os.strerror(ctypes.get_errno())
    return None


problem = _private_namespace()
if problem:
    print(json.dumps({"namespace": problem}))
    sys.exit(0)


def mount(source, target, fstype=None, flags=MS_BIND):
    kind = fstype.encode() if fstype else None
    if libc.mount(os.fsencode(source), os.fsencode(target), kind, flags, None) != 0:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err), target)


def policy(**kwargs):
    kwargs.setdefault("homes", [ARGS["home"]])
    kwargs.setdefault("system", False)
    try:
        built = build_policy(kwargs.pop("workspace", ARGS["ws"]), **kwargs)
    except PolicyError as exc:
        return {"refused": str(exc)}
    return {"grants": [g.path for g in built.grants], "skipped": list(built.skipped), "warnings": list(built.warnings)}
"""


def _in_namespace(layout: dict[str, Path], body: str, **extra: object) -> dict[str, Any]:
    """Run ``body`` in a child with a private mount namespace and return its last JSON line."""
    args = {name: str(path) for name, path in layout.items()} | extra
    env = {**os.environ, "PYTHONPATH": str(ROOT / "01_KISH_ENGINE")}
    done = subprocess.run(
        [sys.executable, "-c", NAMESPACE + textwrap.dedent(body), json.dumps(args)],
        env=env,
        cwd=str(layout["root"]),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert done.returncode == 0, done.stderr
    result: dict[str, Any] = json.loads(done.stdout.splitlines()[-1])
    if "namespace" in result:
        pytest.skip(f"the kernel refused a private mount namespace: {result['namespace']}")
    return result


def _mount_refusal(what: str, point: Path, grant: Path) -> str:
    return f"Refusing a grant with a mount of {what} inside it ({point}): {grant}"


@needs_linux
@pytest.mark.parametrize(
    ("source", "kind", "what"),
    [
        ("ssh", "dir", "protected path {ssh}"),
        ("home", "dir", "a home directory or one of its ancestors"),
        ("root", "dir", "a home directory or one of its ancestors"),
        ("config", "dir", "an ancestor of protected path {home}/.config/gh"),
        ("deploy", "dir", "protected {ssh}/deploy"),
        ("key", "file", "protected {key}"),
    ],
)
def test_mount_below_the_workspace_that_exposes_protected_content_is_refused(
    layout: dict[str, Path], source: str, kind: str, what: str
) -> None:
    (layout["home"] / ".config" / "gh").mkdir(parents=True)
    (layout["ssh"] / "deploy").mkdir()
    sources = {**layout, "config": layout["home"] / ".config", "deploy": layout["ssh"] / "deploy"}
    result = _in_namespace(
        layout,
        """
        point = os.path.join(ARGS["ws"], "a", "b", "view")
        os.makedirs(os.path.dirname(point))
        if ARGS["kind"] == "dir":
            os.mkdir(point)
        else:
            open(point, "w").close()
        mount(ARGS["source"], point)
        print(json.dumps(policy()))
        """,
        source=str(sources[source]),
        kind=kind,
    )
    expected = what.format(**{name: str(path) for name, path in layout.items()})
    point = layout["ws"] / "a" / "b" / "view"
    assert result == {"refused": _mount_refusal(expected, point, layout["ws"])}


@needs_linux
def test_mount_below_a_non_strict_grant_skips_only_that_grant(layout: dict[str, Path]) -> None:
    result = _in_namespace(
        layout,
        """
        point = os.path.join(ARGS["other"], "keys")
        os.mkdir(point)
        mount(ARGS["ssh"], point)
        print(json.dumps(policy(runtime=[ARGS["other"]])))
        """,
    )
    other = layout["other"]
    reason = _mount_refusal(f"protected path {layout['ssh']}", other / "keys", other)
    assert result == {"grants": [str(layout["ws"])], "skipped": [f"{other}: {reason}"], "warnings": []}


@needs_linux
def test_bind_mounted_protected_entry_granted_directly_is_an_alias(layout: dict[str, Path]) -> None:
    (layout["ssh"] / "deploy").mkdir()
    (layout["ssh"] / "deploy" / "id_ed25519").write_text(f"{CANARY}-deploy\n")
    view, ssh_view = layout["other"] / "view", layout["other"] / "ssh-view"
    result = _in_namespace(
        layout,
        """
        os.mkdir(ARGS["view"])
        mount(os.path.join(ARGS["ssh"], "deploy"), ARGS["view"])
        os.mkdir(ARGS["ssh_view"])
        mount(ARGS["ssh"], ARGS["ssh_view"])
        print(json.dumps({
            "dir": policy(read=[ARGS["view"]]),
            "file": policy(read=[os.path.join(ARGS["view"], "id_ed25519")]),
            "ssh_view": policy(read=[ARGS["ssh_view"]]),
            "ssh": policy(read=[ARGS["ssh"]]),
        }))
        """,
        view=str(view),
        ssh_view=str(ssh_view),
    )
    ssh = layout["ssh"]
    assert result["dir"] == {"refused": f"Refusing an alias of protected {ssh / 'deploy'}: {view}"}
    assert result["file"] == {
        "refused": f"Refusing an alias of protected {ssh / 'deploy' / 'id_ed25519'}: {view / 'id_ed25519'}"
    }
    assert result["ssh_view"] == {"refused": f"Refusing an alias of protected {ssh}: {ssh_view}"}
    assert result["ssh"] == {"refused": f"Refusing a grant inside protected path {ssh}: {ssh}"}


@needs_linux
def test_grant_inside_a_bind_mounted_protected_directory_is_refused_beyond_the_scan_bounds(
    layout: dict[str, Path],
) -> None:
    deep = layout["ssh"] / "deep"
    levels = [f"l{index}" for index in range(aliases.SCAN_DEPTH + 8)]
    deep.joinpath(*levels).mkdir(parents=True)
    os.mkfifo(deep / "agent.fifo")  # neither a directory nor a regular file: never recorded itself
    view = layout["other"] / "view"
    beyond = view.joinpath(*levels)
    result = _in_namespace(
        layout,
        """
        os.mkdir(ARGS["view"])
        mount(ARGS["deep"], ARGS["view"])
        print(json.dumps({
            "fifo": policy(read=[os.path.join(ARGS["view"], "agent.fifo")]),
            "beyond": policy(read=[ARGS["beyond"]]),
            "direct": policy(read=[os.path.join(ARGS["deep"], *ARGS["levels"])]),
        }))
        """,
        deep=str(deep),
        view=str(view),
        beyond=str(beyond),
        levels=levels,
    )
    assert result["fifo"] == {"refused": f"Refusing a grant inside an alias of protected {deep}: {view / 'agent.fifo'}"}
    # Entries are recorded down to one level below the deepest directory entered.
    recorded = deep.joinpath(*levels[: aliases.SCAN_DEPTH])
    assert result["beyond"] == {"refused": f"Refusing a grant inside an alias of protected {recorded}: {beyond}"}
    assert result["direct"]["refused"].startswith(f"Refusing a grant inside protected path {layout['ssh']}: ")


@needs_linux
def test_mounts_are_found_by_identity_not_by_path(layout: dict[str, Path]) -> None:
    alias = layout["root"] / "alias"
    alias.symlink_to(layout["root"])
    result = _in_namespace(
        layout,
        """
        point = os.path.join(ARGS["ws"], "keys")
        os.mkdir(point)
        mount(ARGS["ssh"], point)
        print(json.dumps(policy(workspace=ARGS["alias_ws"])))
        """,
        alias_ws=str(alias / "ws"),
    )
    reason = _mount_refusal(f"protected path {layout['ssh']}", layout["ws"] / "keys", alias / "ws")
    assert result == {"refused": reason}


@needs_linux
def test_mounts_that_expose_nothing_protected_are_accepted(layout: dict[str, Path]) -> None:
    (layout["other"] / "data").mkdir()
    result = _in_namespace(
        layout,
        """
        for name, source, fstype, flags in (
            ("data", os.path.join(ARGS["other"], "data"), None, MS_BIND),  # unrelated directory
            ("scratch", "none", "tmpfs", 0),  # a fresh filesystem
            ("hidden", ARGS["ssh"], None, MS_BIND),  # covered below by a tmpfs: unreachable by path
            ("hidden", "none", "tmpfs", 0),
        ):
            point = os.path.join(ARGS["ws"], name)
            os.makedirs(point, exist_ok=True)
            mount(source, point, fstype, flags)
        outside = os.path.join(ARGS["other"], "keys")  # protected, but below no grant
        os.mkdir(outside)
        mount(ARGS["ssh"], outside)
        print(json.dumps(policy()))
        """,
    )
    assert result == {"grants": [str(layout["ws"])], "skipped": [], "warnings": []}


@needs_linux
@pytest.mark.parametrize("journal_exists", [True, False])
def test_mount_of_the_launcher_state_is_refused_below_write_grants_only(
    layout: dict[str, Path], journal_exists: bool
) -> None:
    state = layout["other"] / "state"
    state.mkdir()
    journal = state / "journal.db"
    if journal_exists:
        journal.write_text("")
    readonly_ws = layout["root"] / "ws2"
    readonly_ws.mkdir()
    result = _in_namespace(
        layout,
        """
        point = os.path.join(ARGS["ws"], "state")
        os.mkdir(point)
        mount(ARGS["state"], point)
        print(json.dumps({
            "rw": policy(self_paths=[ARGS["journal"]]),
            "ro": policy(workspace=ARGS["ws2"], read=[ARGS["ws"]], self_paths=[ARGS["journal"]]),
        }))
        """,
        state=str(state),
        journal=str(journal),
        ws2=str(readonly_ws),
    )
    reason = _mount_refusal(f"the launcher's own state ({journal})", layout["ws"] / "state", layout["ws"])
    assert result["rw"] == {"refused": reason}
    assert result["ro"]["grants"] == [str(readonly_ws), str(layout["ws"])]


@needs_linux
def test_mount_points_with_escaped_characters(layout: dict[str, Path]) -> None:
    names = ["with space", "tab\there", "new\nline", "back\\slash", "literal \\012"]
    result = _in_namespace(
        layout,
        """
        points = []
        for name in ARGS["names"]:
            points.append(os.path.join(ARGS["other"], name))
            os.mkdir(points[-1])
            mount("none", points[-1], "tmpfs", 0)
        listed = {m.mount_point for m in aliases.read_mountinfo()}
        point = os.path.join(ARGS["ws"], ARGS["names"][2])
        os.mkdir(point)
        mount(ARGS["ssh"], point)
        print(json.dumps({"unlisted": [p for p in points if p not in listed], "policy": policy()}))
        """,
        names=names,
    )
    assert result["unlisted"] == []
    reason = _mount_refusal(f"protected path {layout['ssh']}", layout["ws"] / "new\nline", layout["ws"])
    assert result["policy"] == {"refused": reason}


@needs_linux
def test_guard_stays_fast_with_hundreds_of_mounts(layout: dict[str, Path]) -> None:
    result = _in_namespace(
        layout,
        """
        import time
        for index in range(400):
            point = os.path.join(ARGS["other"], f"m{index}")
            os.mkdir(point)
            mount("none", point, "tmpfs", 0)
        for index in range(100):
            point = os.path.join(ARGS["ws"], f"m{index}")
            os.mkdir(point)
            mount("none", point, "tmpfs", 0)
        samples = []
        for _ in range(5):
            start = time.perf_counter()
            built = policy(system=True)
            samples.append(time.perf_counter() - start)
        print(json.dumps({"policy": built, "samples": samples, "mounts": len(aliases.read_mountinfo())}))
        """,
    )
    median = statistics.median(result["samples"])
    print(f"\nguard: {result['mounts']} mounts (100 below the workspace), build_policy median {median * 1000:.1f} ms")
    assert "refused" not in result["policy"] and str(layout["ws"]) in result["policy"]["grants"]
    assert median < 2.0


@needs_linux
@pytest.mark.skipif(
    launcher.landlock_abi() < MIN_LANDLOCK_ABI and not REQUIRED, reason="Landlock is not available in this kernel"
)
def test_landlock_follows_a_bind_mount_below_the_workspace(layout: dict[str, Path]) -> None:
    """Non-vacuity: a policy checked before the mount exists exposes the key through it; checking again refuses."""
    result = _in_namespace(
        layout,
        """
        runtime = [launcher.interpreter_prefix()]
        built = build_policy(ARGS["ws"], homes=[ARGS["home"]], runtime=runtime)
        point = os.path.join(ARGS["ws"], "keys")
        os.mkdir(point)
        mount(ARGS["ssh"], point)
        env = {"PATH": "/usr/bin:/bin", "HOME": ARGS["home"], "LC_ALL": "C"}

        def cat(path):
            done = launcher.run(launcher.session_launch(["/bin/cat", path], built), env=env, cwd=ARGS["ws"])
            return {"rc": done.returncode, "out": done.stdout.decode(), "err": done.stderr.decode(), "status": done.status}

        print(json.dumps({
            "through_bind": cat(os.path.join(point, "id_rsa")),
            "direct": cat(ARGS["key"]),
            "checked_again": policy(system=True, runtime=runtime),
        }))
        """,
    )
    through, direct = result["through_bind"], result["direct"]
    assert through["status"]["ok"] and through["status"]["landlock_abi"] >= MIN_LANDLOCK_ABI
    assert through["rc"] == 0 and CANARY in through["out"]
    assert direct["rc"] != 0 and "Permission denied" in direct["err"] and CANARY not in direct["out"]
    reason = _mount_refusal(f"protected path {layout['ssh']}", layout["ws"] / "keys", layout["ws"])
    assert result["checked_again"] == {"refused": reason}
