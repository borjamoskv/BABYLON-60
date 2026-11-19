"""Metadata outside Landlock's reach: permission and ownership snapshots of the home and protected paths.

The unit tests use real files in throwaway homes and real syscalls. The Linux
probe runs a real confined process and records which metadata operations the
running Landlock ABI leaves open on a throwaway ``~/.ssh``; set
BABYLON60_REQUIRE_LANDLOCK=1 to fail instead of skipping when Landlock is missing.
"""

from __future__ import annotations

import errno
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time
from typing import Any

import pytest

from babylon60.confine import launcher, metadata
from babylon60.confine.policy import MIN_LANDLOCK_ABI, PROTECTED_RELATIVE, Policy, build_policy

LINUX = sys.platform.startswith("linux")
ABI = launcher.landlock_abi()
REQUIRED = os.environ.get("BABYLON60_REQUIRE_LANDLOCK") == "1"
needs_landlock = pytest.mark.skipif(
    not LINUX or (ABI < MIN_LANDLOCK_ABI and not REQUIRED),
    reason=f"Landlock ABI {ABI} < {MIN_LANDLOCK_ABI}; set BABYLON60_REQUIRE_LANDLOCK=1 to fail instead",
)
NO_ID = 0xFFFFFFFF
ACL_USER_OBJ, ACL_USER, ACL_GROUP_OBJ, ACL_MASK, ACL_OTHER = 0x01, 0x02, 0x04, 0x10, 0x20


def _write(path: Path, mode: int, data: str = "throwaway\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data)
    path.chmod(mode)
    return path


@pytest.fixture
def box(tmp_path: Path) -> dict[str, Path]:
    home = tmp_path / "home"
    ssh = home / ".ssh"
    ssh.mkdir(parents=True)
    home.chmod(0o700)
    ssh.chmod(0o700)
    key = _write(ssh / "id_rsa", 0o600, "B60-CANARY-metadata\n")
    _write(ssh / "id_rsa.pub", 0o644)
    _write(ssh / "config", 0o600)
    _write(ssh / "known_hosts", 0o644)
    _write(home / ".aws" / "credentials", 0o600)
    _write(home / ".config" / "gh" / "hosts.yml", 0o600)
    for directory in (home / ".aws", home / ".config", home / ".config" / "gh"):
        directory.chmod(0o700)  # not left to the umask
    return {"root": tmp_path, "home": home, "ssh": ssh, "key": key}


def _protected(home: Path) -> list[str]:
    return [str(home / rel) for rel in PROTECTED_RELATIVE]


def _snap(box: dict[str, Path], **kwargs: int) -> metadata.Snapshot:
    return metadata.snapshot([str(box["home"])], _protected(box["home"]), **kwargs)


def _acl(*entries: tuple[int, int, int]) -> bytes:
    """Linux ``posix_acl_xattr`` version 2, entries ordered by tag then id as the kernel requires."""
    return struct.pack("<I", 2) + b"".join(struct.pack("<HHI", tag, perm, ident) for tag, perm, ident in entries)


def _set_acl(path: Path, name: str, data: bytes) -> None:
    if not hasattr(os, "setxattr"):
        pytest.skip("POSIX ACLs through extended attributes are Linux-only")
    try:
        os.setxattr(path, name, data)
    except OSError as exc:
        if exc.errno in (errno.EOPNOTSUPP, errno.ENOTSUP):
            pytest.skip(f"this filesystem has no POSIX ACL support: {exc}")
        raise


def test_snapshot_records_homes_protected_paths_and_their_entries(box: dict[str, Path]) -> None:
    snap = _snap(box)
    by_path = {entry.path: entry for entry in snap.entries}
    home, ssh, key = (str(box[name]) for name in ("home", "ssh", "key"))
    assert (by_path[home].role, by_path[home].kind, by_path[home].mode) == ("home", "dir", 0o700)
    assert (by_path[ssh].role, by_path[ssh].kind, by_path[ssh].mode) == ("protected", "dir", 0o700)
    assert (by_path[key].role, by_path[key].kind, by_path[key].mode) == ("inside", "file", 0o600)
    assert (by_path[key].uid, by_path[key].gid) == (os.stat(key).st_uid, os.stat(key).st_gid)
    assert by_path[str(box["home"] / ".config")].role == "ancestor"
    assert by_path[str(box["home"] / ".config" / "gh" / "hosts.yml")].role == "inside"
    assert str(box["home"] / ".aws" / "credentials") in by_path
    assert not any(".azure" in path or ".kube" in path for path in by_path)  # absent protected paths
    assert all(entry.acl != metadata.UNKNOWN for entry in snap.entries) == hasattr(os, "getxattr")
    assert snap.truncated == () and snap.notes == ()
    assert snap.display(key) == "~/.ssh/id_rsa" and snap.display(home) == "~"


def test_chmod_of_the_key_and_its_directories_is_reported(box: dict[str, Path]) -> None:
    before = _snap(box)
    box["key"].chmod(0o644)
    box["ssh"].chmod(0o755)
    box["home"].chmod(0o755)
    assert metadata.changes(before, _snap(box)) == [
        "~: mode 0700 -> 0755; the home directory became accessible to group and others (list, traverse)",
        "~/.ssh: mode 0700 -> 0755; the protected directory became accessible to group and others (list, traverse)",
        "~/.ssh/id_rsa: mode 0600 -> 0644; group and others can now read",
    ]


def test_widening_comes_first_then_narrowing_and_owner_loss(box: dict[str, Path]) -> None:
    before = _snap(box)
    (box["ssh"] / "known_hosts").chmod(0o600)
    box["key"].chmod(0o000)
    (box["home"] / ".config").chmod(0o751)
    assert metadata.changes(before, _snap(box)) == [
        "~/.config: mode 0700 -> 0751; the directory above a protected path became accessible to "
        "group (list, traverse) and others (traverse)",
        "~/.ssh/id_rsa: mode 0600 -> 0000; owner can no longer read, write",
        "~/.ssh/known_hosts: mode 0644 -> 0600",
    ]


def _other_group(gid: int) -> int | None:
    if os.geteuid() == 0:
        return 65534 if gid != 65534 else 1
    return next((group for group in os.getgroups() if group != gid), None)


def test_chown_to_another_group_is_reported(box: dict[str, Path]) -> None:
    gid = os.stat(box["key"]).st_gid
    other = _other_group(gid)
    if other is None:
        pytest.skip("this user belongs to no other group, so it cannot change a file's group")
    before = _snap(box)
    os.chown(box["key"], -1, other)
    os.chown(box["ssh"] / "config", -1, other)
    (box["ssh"] / "config").chmod(0o640)
    assert metadata.changes(before, _snap(box)) == [
        f"~/.ssh/config: group gid {gid} -> {other}, mode 0600 -> 0640; group {other} can now read",
        f"~/.ssh/id_rsa: group gid {gid} -> {other}",
    ]


def test_new_removed_rewritten_and_retimed_entries_are_not_reported(box: dict[str, Path]) -> None:
    before = _snap(box)
    _write(box["ssh"] / "id_ed25519.pub", 0o644)  # new entry, even a readable one
    (box["ssh"] / "config").unlink()
    with open(box["ssh"] / "known_hosts", "a", encoding="ascii") as handle:  # ssh appends in another terminal
        handle.write("example.org ssh-ed25519 AAAA\n")
    box["key"].write_text("rewritten in place\n")
    os.utime(box["key"], (0, 0))
    if hasattr(os, "setxattr"):
        try:
            os.setxattr(box["key"], "user.babylon60.test", b"planted")
        except OSError as exc:
            if exc.errno not in (errno.EOPNOTSUPP, errno.ENOTSUP):
                raise
    assert metadata.changes(before, _snap(box)) == []


def test_atomic_saves_are_reported_only_when_they_widen_access(box: dict[str, Path], tmp_path: Path) -> None:
    before = _snap(box)

    def replace(target: Path, mode: int) -> None:
        _write(target.with_name(target.name + ".tmp"), mode).rename(target)

    replace(box["ssh"] / "known_hosts", 0o600)  # ssh-keygen -R: new inode, narrower
    replace(box["ssh"] / "config", 0o600)  # an editor saving with the same mode
    replace(box["home"] / ".aws" / "credentials", 0o644)  # new inode, readable by everyone
    box["key"].unlink()
    box["key"].symlink_to(tmp_path / "elsewhere")  # a link's own mode means nothing
    assert metadata.changes(before, _snap(box)) == [
        "~/.aws/credentials: replaced during the session, mode 0600 -> 0644; group and others can now read",
    ]


def test_symbolic_links_are_recorded_and_never_followed(box: dict[str, Path], tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    secret = _write(outside / "secret", 0o600)
    _write(outside / "nested" / "deep", 0o600)
    (box["ssh"] / "link").symlink_to(secret)
    (box["ssh"] / "dirlink").symlink_to(outside)
    aws = box["home"] / ".aws"
    for child in aws.iterdir():
        child.unlink()
    aws.rmdir()
    aws.symlink_to(outside, target_is_directory=True)
    config = box["home"] / ".config"  # a dotfiles setup: ~/.config itself is a link
    config.rename(outside / "config")
    config.symlink_to(outside / "config", target_is_directory=True)
    before = _snap(box)
    by_path = {entry.path: entry for entry in before.entries}
    for link in (box["ssh"] / "link", box["ssh"] / "dirlink", aws, config):
        assert by_path[str(link)].kind == "symlink", link
    assert not any(
        path.startswith((str(outside), str(box["ssh"] / "dirlink") + "/", str(aws) + "/")) for path in by_path
    )
    assert before.notes == (
        "~/.config: symbolic link; the directory it points to is not compared",
        "~/.aws: symbolic link, not followed",
    )
    secret.chmod(0o644)
    outside.chmod(0o777)
    (outside / "config").chmod(0o777)
    (outside / "config" / "gh" / "hosts.yml").chmod(0o644)  # still reached by its logical path ~/.config/gh/...
    assert metadata.changes(before, _snap(box)) == [
        "~/.config/gh/hosts.yml: mode 0600 -> 0644; group and others can now read",
    ]


def test_walk_bound_is_per_protected_directory_and_recorded(box: dict[str, Path]) -> None:
    for index in range(30):
        _write(box["ssh"] / "deep" / f"f{index:02}", 0o600)
    for index in range(3):
        _write(box["home"] / ".gnupg" / f"g{index}", 0o600)
    ssh, gnupg = str(box["ssh"]), str(box["home"] / ".gnupg")
    top_level = {str(path) for path in box["ssh"].iterdir()}  # id_rsa, id_rsa.pub, config, known_hosts, deep
    assert len(top_level) == 5

    def inside(snap: metadata.Snapshot, root: str) -> set[str]:
        return {entry.path for entry in snap.entries if entry.path.startswith(root + "/")}

    bounded = _snap(box, limit=7)
    assert bounded.truncated == (ssh,)
    assert len(inside(bounded, ssh)) == 7 and top_level <= inside(bounded, ssh)  # breadth first: shallow entries kept
    assert len(inside(bounded, gnupg)) == 3  # the bound is per protected directory
    exact = _snap(box, limit=3)  # exactly 3 entries in ~/.gnupg: complete, not truncated
    assert exact.truncated == (ssh,) and len(inside(exact, gnupg)) == 3
    assert _snap(box, limit=5).truncated == (ssh,)  # the top level fits, but deep/ is left unlisted
    nothing = _snap(box, limit=0)
    assert set(nothing.truncated) == {ssh, gnupg, str(box["home"] / ".aws"), str(box["home"] / ".config" / "gh")}
    assert {ssh, gnupg} <= {entry.path for entry in nothing.entries} and not inside(nothing, ssh)
    assert len(_snap(box, limit=100).entries) > len(bounded.entries) and not _snap(box, limit=100).truncated
    with pytest.raises(ValueError):
        _snap(box, limit=-1)


def test_unreadable_directory_is_recorded_and_noted(box: dict[str, Path]) -> None:
    locked = box["ssh"] / "locked"
    _write(locked / "inner", 0o600)
    locked.chmod(0o000)
    try:
        snap = _snap(box)
    finally:
        locked.chmod(0o700)
    by_path = {entry.path: entry for entry in snap.entries}
    assert by_path[str(locked)].mode == 0o000
    if os.geteuid() == 0:  # CAP_DAC_OVERRIDE lists it anyway
        assert str(locked / "inner") in by_path
    else:
        assert str(locked / "inner") not in by_path
        assert "~/.ssh/locked: directory not listed (EACCES)" in snap.notes


CHURN = r"""
import os, sys
base = sys.argv[1]
names = [f"n{index}" for index in range(6)]
step = 0
while True:
    step += 1
    for index, name in enumerate(names):
        path = os.path.join(base, name)
        try:
            if os.path.islink(path) or not os.path.isdir(path):
                os.unlink(path)
            else:
                for child in os.listdir(path):
                    os.unlink(os.path.join(path, child))
                os.rmdir(path)
        except OSError:
            pass
        try:
            kind = (step + index) % 3
            if kind == 0:
                os.mkdir(path)
                for child in range(3):
                    open(os.path.join(path, f"f{child}"), "w").close()
            elif kind == 1:
                open(path, "w").close()
            else:
                os.symlink("/", path)
        except OSError:
            pass
"""


def test_entries_vanishing_during_the_walk_are_tolerated(box: dict[str, Path]) -> None:
    """A real concurrent writer removes and replaces entries (directory, file, link) while snapshots run."""
    churn = box["ssh"] / "churn"
    churn.mkdir()
    worker = subprocess.Popen([sys.executable, "-I", "-S", "-c", CHURN, str(churn)])
    skipped = 0
    try:
        time.sleep(0.05)
        first = _snap(box)
        for _ in range(300):
            current = _snap(box)
            paths = {entry.path for entry in current.entries}
            assert {str(box["ssh"]), str(box["key"]), str(box["ssh"] / "config")} <= paths
            skipped += sum(int(note.split()[0]) for note in current.notes if "vanished or changed" in note)
            for line in metadata.changes(first, current):
                assert line.startswith("~/.ssh/churn/"), line  # only entries the writer replaced
    finally:
        worker.kill()
        worker.wait()
    print(f"300 snapshots under a concurrent writer; {skipped} entries skipped as vanished or changed mid-walk")


def _typical_home(home: Path) -> None:
    """About 800 entries: keys, a GnuPG home, cloud and cluster credentials with their caches, a password store."""
    for name in ("id_ed25519", "id_rsa", "config", "authorized_keys", "known_hosts", "known_hosts.old"):
        _write(home / ".ssh" / name, 0o600)
    for name in ("id_ed25519.pub", "id_rsa.pub"):
        _write(home / ".ssh" / name, 0o644)
    for index in range(4):
        _write(home / ".gnupg" / "private-keys-v1.d" / f"{index:040X}.key", 0o600)
    for name in ("pubring.kbx", "pubring.kbx~", "trustdb.gpg", "gpg-agent.conf", "sshcontrol", "common.conf"):
        _write(home / ".gnupg" / name, 0o600)
    _write(home / ".aws" / "config", 0o644)
    _write(home / ".aws" / "credentials", 0o600)
    _write(home / ".kube" / "config", 0o600)
    for group in range(60):
        _write(
            home / ".kube" / "cache" / "discovery" / "host_6443" / f"g{group}" / "v1" / "serverresources.json", 0o640
        )
    for index in range(40):
        _write(home / ".kube" / "cache" / "http" / f"{index:064x}", 0o640)
    _write(home / ".docker" / "config.json", 0o600)
    _write(home / ".config" / "gh" / "hosts.yml", 0o600)
    for day in range(6):
        for index in range(6):
            _write(home / ".config" / "gcloud" / "logs" / f"2026.11.0{day}" / f"{index}.log", 0o644)
    _write(home / ".config" / "gcloud" / "credentials.db", 0o600)
    for index in range(100):
        _write(home / ".password-store" / f"site{index}.gpg", 0o600)
    for index in range(200):
        _write(home / ".password-store" / ".git" / "objects" / f"{index % 256:02x}" / f"{index:038x}", 0o444)
    _write(home / ".netrc", 0o600)
    _write(home / ".git-credentials", 0o600)


def test_snapshot_of_a_typical_home_is_fast(tmp_path: Path) -> None:
    home = tmp_path / "home"
    _typical_home(home)
    timings = []
    for _ in range(5):
        start = time.perf_counter()
        snap = metadata.snapshot([str(home)], _protected(home))
        timings.append(time.perf_counter() - start)
    print(
        f"{len(snap.entries)} entries; snapshot best {min(timings) * 1000:.1f} ms, worst {max(timings) * 1000:.1f} ms"
    )
    assert len(snap.entries) > 700 and not snap.truncated
    assert min(timings) < 0.050


def test_posix_acl_granting_access_without_a_mode_change_is_reported(box: dict[str, Path]) -> None:
    netrc = _write(box["home"] / ".netrc", 0o664)
    before = _snap(box)
    _set_acl(
        netrc,
        "system.posix_acl_access",
        _acl(
            (ACL_USER_OBJ, 6, NO_ID),
            (ACL_USER, 4, 65534),
            (ACL_GROUP_OBJ, 6, NO_ID),
            (ACL_MASK, 6, NO_ID),
            (ACL_OTHER, 4, NO_ID),
        ),
    )
    assert netrc.stat().st_mode & 0o7777 == 0o664  # the mode alone shows nothing
    _set_acl(
        box["ssh"],
        "system.posix_acl_default",
        _acl(
            (ACL_USER_OBJ, 7, NO_ID),
            (ACL_USER, 4, 65534),
            (ACL_GROUP_OBJ, 0, NO_ID),
            (ACL_MASK, 4, NO_ID),
            (ACL_OTHER, 0, NO_ID),
        ),
    )
    assert box["ssh"].stat().st_mode & 0o7777 == 0o700
    assert metadata.changes(before, _snap(box)) == [
        "~/.netrc: ACL none -> user:65534:r--,group::rw-; user 65534 (ACL) can now read",
        "~/.ssh: ACL none -> default:user::rwx,default:user:65534:r--,default:group::---,default:mask::r--,"
        "default:other::---; default ACL for new entries grants user:65534:r--",
    ]


def test_changes_are_capped_with_a_count_of_the_rest(box: dict[str, Path]) -> None:
    before = _snap(box)
    for path in (box["key"], box["ssh"] / "config", box["ssh"] / "known_hosts", box["ssh"] / "id_rsa.pub"):
        path.chmod(0o666)
    after = _snap(box)
    assert len(metadata.changes(before, after, max_lines=None)) == 4
    capped = metadata.changes(before, after, max_lines=2)
    assert len(capped) == 3 and capped[-1] == "... and 2 more permission or ownership changes"


def test_unprintable_names_are_escaped(box: dict[str, Path]) -> None:
    odd = _write(box["ssh"] / "key\nbabylon60 run: nothing changed", 0o600)
    before = _snap(box)
    odd.chmod(0o604)
    (line,) = metadata.changes(before, _snap(box))
    assert "\n" not in line
    assert line == repr("~/.ssh/key\nbabylon60 run: nothing changed") + ": mode 0600 -> 0604; others can now read"


def test_unknown_acl_is_never_compared() -> None:
    def entry(acl: str) -> metadata.Entry:
        return metadata.Entry("/h/.ssh/id_rsa", "inside", "file", 0o600, 1000, 1000, 1, 2, acl)

    def snap(item: metadata.Entry) -> metadata.Snapshot:
        return metadata.Snapshot(("/h",), (item,), metadata.DEFAULT_LIMIT)

    assert metadata.changes(snap(entry(metadata.UNKNOWN)), snap(entry("user:65534:r--"))) == []
    assert metadata.changes(snap(entry("")), snap(entry("user:65534:r--"))) == [
        "~/.ssh/id_rsa: ACL none -> user:65534:r--"  # the mask (mode group bits) is ---: nothing effective
    ]


def test_display_is_relative_to_the_first_home_only(tmp_path: Path) -> None:
    first, second = tmp_path / "a", tmp_path / "b"
    snap = metadata.snapshot([str(first), str(second)], [])
    assert snap.display(str(first / ".ssh")) == "~/.ssh"
    assert snap.display(str(second / ".ssh")) == str(second / ".ssh")
    assert snap.entries == ()  # neither home exists


PROBE = r"""
import ctypes, errno, json, os, struct, sys

cfg = json.loads(sys.argv[1])
home, ssh, key, config = cfg["home"], cfg["ssh"], cfg["key"], cfg["config"]
out = {}


def attempt(name, operation):
    try:
        operation()
        out[name] = "ok"
    except OSError as exc:
        out[name] = errno.errorcode.get(exc.errno or 0, str(exc.errno))


def chmod():
    os.chmod(key, 0o644)
    os.chmod(ssh, 0o755)
    os.chmod(home, 0o755)


def chown():
    other = [group for group in os.getgroups() if group != cfg["gid"]]
    out["chown_gid"] = other[0] if other else cfg["gid"]
    os.chown(key, -1, out["chown_gid"])


def posix_acl():
    entries = [(0x01, 6, 0xFFFFFFFF), (0x02, 4, 65534), (0x04, 4, 0xFFFFFFFF), (0x10, 4, 0xFFFFFFFF), (0x20, 0, 0xFFFFFFFF)]
    data = struct.pack("<I", 2) + b"".join(struct.pack("<HHI", *entry) for entry in entries)
    os.setxattr(config, "system.posix_acl_access", data)


def inotify_add_watch():
    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.inotify_init1(os.O_CLOEXEC)
    if fd < 0:
        raise OSError(ctypes.get_errno(), "inotify_init1")
    try:
        if libc.inotify_add_watch(fd, os.fsencode(ssh), 0x20 | 0x100) < 0:  # IN_OPEN | IN_CREATE
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
    finally:
        os.close(fd)


attempt("read", lambda: os.close(os.open(key, os.O_RDONLY)))
attempt("chmod", chmod)
attempt("chown", chown)
attempt("utime", lambda: os.utime(key, (0, 0)))
attempt("setxattr", lambda: os.setxattr(key, "user.babylon60.probe", b"planted"))
attempt("getxattr", lambda: os.getxattr(key, "user.babylon60.preset"))
attempt("listxattr", lambda: os.listxattr(key))
attempt("posix_acl", posix_acl)
attempt("inotify_add_watch", inotify_add_watch)
print(json.dumps(out))
"""


def _probe_box(root: Path) -> dict[str, Path]:
    home, ws = root / "home", root / "ws"
    ssh = home / ".ssh"
    ssh.mkdir(parents=True)
    ws.mkdir()
    home.chmod(0o700)
    ssh.chmod(0o700)
    key = _write(ssh / "id_rsa", 0o600, "B60-CANARY-metadata-probe\n")
    config = _write(ssh / "config", 0o640)
    try:  # what getxattr reads; a filesystem without user xattrs makes it untestable, not closed
        os.setxattr(key, "user.babylon60.preset", b"preset")
    except OSError:
        pass
    return {"home": home, "ws": ws, "ssh": ssh, "key": key, "config": config}


def _probe(box: dict[str, Path], policy: Policy | None, gid: int) -> dict[str, Any]:
    cfg: dict[str, Any] = {name: str(box[name]) for name in ("home", "ssh", "key", "config")}
    cfg["gid"] = gid
    argv = [launcher.interpreter(), "-I", "-S", "-B", "-c", PROBE, json.dumps(cfg)]
    launch = launcher.Launch(argv, None) if policy is None else launcher.session_launch(argv, policy)
    env = {"PATH": "/usr/bin:/bin", "HOME": str(box["home"]), "LC_ALL": "C"}
    result = launcher.run(launch, env=env, cwd=str(box["ws"]))
    assert result.status.get("ok"), result.status
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    observed: dict[str, Any] = json.loads(result.stdout.decode().strip().splitlines()[-1])
    observed.update(landlock_abi=result.status.get("landlock_abi"), errata=result.status.get("landlock_errata"))
    return observed


@needs_landlock
def test_landlock_leaves_metadata_operations_open_and_changes_reports_them(tmp_path: Path) -> None:
    control_box = _probe_box(tmp_path / "control")
    control = _probe(control_box, None, os.stat(control_box["key"]).st_gid)
    box = _probe_box(tmp_path / "confined")
    gid = os.stat(box["key"]).st_gid
    policy = build_policy(box["ws"], homes=[str(box["home"])], runtime=[launcher.interpreter_prefix()])
    before = metadata.snapshot(policy.homes, policy.protected)
    confined = _probe(box, policy, gid)
    lines = metadata.changes(before, metadata.snapshot(policy.homes, policy.protected))

    states = {}
    for operation in metadata.DECLARED_OPEN:
        if confined[operation] == "ok":
            states[operation] = "open"
        elif control[operation] != "ok":
            states[operation] = "untestable here"  # the filesystem or kernel lacks it even without confinement
        else:
            states[operation] = "closed"
    table = [f"Landlock ABI {confined['landlock_abi']}, errata {confined['errata']}, uid {os.geteuid()}"]
    table += [f"  {op:<18} control={control[op]:<10} confined={confined[op]:<10} -> {states[op]}" for op in states]
    table += [f"  {'read (non-vacuity)':<18} control={control['read']:<10} confined={confined['read']}"]
    report = "\n".join([*table, "changes():", *(f"  {line}" for line in lines)])
    print(report)

    assert confined["landlock_abi"] == ABI
    assert control["read"] == "ok" and confined["read"] == "EACCES", report  # the sandbox was live
    closed = [op for op, state in states.items() if state == "closed"]
    assert not closed, (
        f"Landlock ABI {ABI} now blocks {', '.join(closed)} under confinement: update the declared limits "
        "(babylon60.confine.metadata.DECLARED_OPEN, the demo's limit rows and the docs).\n" + report
    )
    expected: dict[str, list[str]] = {}
    if states["chmod"] == "open":
        expected["~"] = ["mode 0700 -> 0755", "the home directory became accessible to group and others"]
        expected["~/.ssh"] = ["mode 0700 -> 0755", "the protected directory became accessible to group and others"]
        expected["~/.ssh/id_rsa"] = ["mode 0600 -> 0644", "and others can now read"]
    if states["chown"] == "open" and confined["chown_gid"] != gid:  # the probe had another group to use
        assert os.stat(box["key"]).st_gid == confined["chown_gid"], report
        expected.setdefault("~/.ssh/id_rsa", []).append(f"group gid {gid} -> {confined['chown_gid']}")
    if states["posix_acl"] == "open":
        expected["~/.ssh/config"] = ["ACL none -> user:65534:r--,group::r--", "user 65534 (ACL) can now read"]
    reported = {line.split(": ", 1)[0]: line for line in lines}
    assert set(reported) == set(expected), report  # utime and user.* attributes are not permission changes
    for path, fragments in expected.items():
        assert all(fragment in reported[path] for fragment in fragments), report
