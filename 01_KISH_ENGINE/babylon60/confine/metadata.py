"""Permission and ownership changes on the home and protected paths, seen after a session.

Landlock up to ABI 7 does not mediate metadata operations: a confined agent can
still chmod, chown (to another group of the user), change times, set and read
extended attributes, POSIX ACLs included, and inotify-watch paths it cannot
open. Seccomp cannot see paths, and denying those syscalls everywhere would
break ordinary agents (``chmod +x`` in the workspace, file watchers), so they
stay declared limits (``DECLARED_OPEN``). This module makes their most harmful
effect visible instead: ``snapshot`` before the session, ``snapshot`` after it
and ``changes`` between the two.

A snapshot records type, permission bits, owner, group and, on Linux, the POSIX
ACL entries that the mode does not mirror, for:

* each home directory, and each directory between a home and a protected path
  (``~/.config`` for ``~/.config/gh``);
* each protected path;
* the entries inside protected directories, breadth first, at most ``limit``
  per protected directory (``Snapshot.truncated`` names those that hit it).

Symbolic links are recorded, never followed, and no file is ever opened: roots
are read with ``lstat`` or opened as directories with ``O_NOFOLLOW`` (their
parent components resolve as in any path lookup), entries with ``fstatat``
relative to the directory being listed, and every directory is checked by
``(st_dev, st_ino)`` before it is listed. Entries that vanish or change during
the walk are skipped and counted in ``Snapshot.notes``, which also names roots
that are links or could not be listed. Listing a directory is visible to
inotify watchers on it, so take snapshots outside any witness window.

Not covered: changes reverted before the session ends, other paths of the home
(only the home directory entry itself is recorded), entries past ``limit``,
targets of symbolic links, and extended attributes other than POSIX ACLs.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, replace
import errno
import os
import stat
import struct

DEFAULT_LIMIT = 512  # entries recorded inside each protected directory
MAX_LINES = 100  # default cap of ``changes``; a final line counts the rest

# Metadata operations Landlock (ABI <= 7) does not mediate on paths it denies.
# Declared limits: tests/test_confine_metadata.py checks them on the running kernel.
DECLARED_OPEN: dict[str, str] = {
    "chmod": "change permission bits (chmod, fchmodat)",
    "chown": "change the group to another group of the user (chown, fchownat)",
    "utime": "change access and modification times (utime, utimensat)",
    "setxattr": "set user.* extended attributes",
    "getxattr": "read extended attributes",
    "listxattr": "list extended attribute names",
    "posix_acl": "grant access with a POSIX ACL (setxattr system.posix_acl_access)",
    "inotify_add_watch": "watch names and timing of accesses (inotify_add_watch)",
}

UNKNOWN = "?"  # ACL not readable here (no xattr support in this Python, or an error)
ROLES = ("home", "ancestor", "protected", "inside")
_LABELS = {"home": "home directory", "ancestor": "directory above a protected path", "protected": "protected directory"}
_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
_XATTR = hasattr(os, "getxattr")
_ACL_ACCESS, _ACL_DEFAULT = "system.posix_acl_access", "system.posix_acl_default"
_ACL_ABSENT = {code for code in (getattr(errno, "ENODATA", None), errno.EOPNOTSUPP, errno.ENOTSUP) if code}
_ACL_TAGS = {0x01: "user", 0x02: "user", 0x04: "group", 0x08: "group", 0x10: "mask", 0x20: "other"}
_ACL_QUALIFIED = (0x02, 0x08)  # named user and named group entries carry an id
_ACL_MIRRORED = (0x01, 0x10, 0x20)  # owner, mask and other entries mirror the mode bits
_FILE_VERBS = ((4, "read"), (2, "write"), (1, "execute"))
_DIR_VERBS = ((4, "list"), (2, "modify"), (1, "traverse"))
_KINDS = {
    stat.S_IFDIR: "dir",
    stat.S_IFREG: "file",
    stat.S_IFLNK: "symlink",
    stat.S_IFSOCK: "socket",
    stat.S_IFIFO: "fifo",
    stat.S_IFCHR: "char",
    stat.S_IFBLK: "block",
}


@dataclass(frozen=True)
class Entry:
    path: str  # logical path: the given root joined with directory entry names, never resolved
    role: str  # one of ROLES
    kind: str  # dir, file, symlink, socket, fifo, char, block or other
    mode: int  # permission bits, setuid, setgid and sticky included
    uid: int
    gid: int
    dev: int
    ino: int
    acl: str = UNKNOWN  # POSIX ACL entries the mode does not mirror; "" when there are none


@dataclass(frozen=True)
class Snapshot:
    homes: tuple[str, ...]
    entries: tuple[Entry, ...]
    limit: int
    truncated: tuple[str, ...] = ()  # protected directories whose walk stopped at ``limit``
    notes: tuple[str, ...] = ()  # what was not inspected, and why (display form)

    def display(self, path: str) -> str:
        """``path`` relative to the first home (``~/...``), escaped when not printable."""
        return _display(path, self.homes)


def snapshot(homes: Sequence[str], protected: Sequence[str], *, limit: int = DEFAULT_LIMIT) -> Snapshot:
    """Record the homes, the protected paths and up to ``limit`` entries inside each protected directory."""
    if limit < 0:
        raise ValueError("limit must be zero or positive")
    home_paths = tuple(dict.fromkeys(os.path.abspath(home) for home in homes))
    protected_paths = tuple(dict.fromkeys(os.path.abspath(path) for path in protected))
    walk = _Walk(home_paths, limit)
    for home in home_paths:
        walk.root(home, "home")
    for ancestor in dict.fromkeys(ancestor for path in protected_paths for ancestor in _between(home_paths, path)):
        walk.root(ancestor, "ancestor")
    for path in protected_paths:
        walk.protected(path)
    if walk.raced:
        walk.notes.append(f"{walk.raced} entries vanished or changed while being recorded; they were skipped")
    notes = tuple(dict.fromkeys(walk.notes))
    return Snapshot(home_paths, tuple(walk.entries.values()), limit, tuple(walk.truncated), notes)


def changes(before: Snapshot, after: Snapshot, *, max_lines: int | None = MAX_LINES) -> list[str]:
    """Human-readable permission and ownership changes of entries present in both snapshots.

    * Same inode: any change of mode, owner, group or ACL is reported (chmod,
      chown or setfacl, inside or outside the sandbox).
    * Replaced inode (an editor or ``ssh-keygen -R`` saving atomically): reported
      only when the new entry grants access the old one did not; a save that
      keeps or narrows permissions is ordinary.
    * Never compared: contents, sizes, times, plain extended attributes and
      symbolic links. Entries that appear or disappear are not reported.

    Changes that widen access come first. With ``max_lines``, the list is cut
    there and one more line counts what was left out.
    """
    earlier = {entry.path: entry for entry in before.entries}
    found: list[tuple[bool, int, str, str]] = []
    for entry in after.entries:
        prior = earlier.get(entry.path)
        if prior is None or prior == entry:
            continue
        compared = _compare(prior, entry)
        if compared is not None:
            widened, text = compared
            found.append((not widened, ROLES.index(entry.role), entry.path, f"{after.display(entry.path)}: {text}"))
    found.sort()
    lines = [item[3] for item in found]
    if max_lines is not None and len(lines) > max_lines:
        rest = len(lines) - max_lines
        lines = lines[:max_lines] + [f"... and {rest} more permission or ownership changes"]
    return lines


class _Walk:
    def __init__(self, homes: tuple[str, ...], limit: int) -> None:
        self.homes = homes
        self.limit = limit
        self.entries: dict[str, Entry] = {}
        self.truncated: list[str] = []
        self.notes: list[str] = []
        self.raced = 0
        self.proc_fd = _XATTR and os.path.isdir("/proc/self/fd")

    def note(self, path: str, text: str) -> None:
        self.notes.append(f"{_display(path, self.homes)}: {text}")

    def add(self, path: str, role: str, st: os.stat_result, acl: str) -> None:
        existing = self.entries.get(path)
        if existing is None:
            self.entries[path] = Entry(
                path, role, _kind(st.st_mode), stat.S_IMODE(st.st_mode), st.st_uid, st.st_gid, st.st_dev, st.st_ino, acl
            )
        elif ROLES.index(role) < ROLES.index(existing.role):
            self.entries[path] = replace(existing, role=role)

    def root(self, path: str, role: str) -> os.stat_result | None:
        try:
            st = os.lstat(path)
        except (FileNotFoundError, NotADirectoryError):
            return None
        except OSError as exc:
            self.note(path, f"not inspected ({_errname(exc)})")
            return None
        self.add(path, role, st, _acl(path, st))
        if stat.S_ISLNK(st.st_mode):
            if role == "protected":
                self.note(path, "symbolic link, not followed")
            else:
                self.note(path, "symbolic link; the directory it points to is not compared")
        return st

    def protected(self, path: str) -> None:
        try:
            fd = os.open(path, _DIRECTORY_FLAGS)
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                return
            st = self.root(path, "protected")  # a file, a symbolic link or an unreadable directory
            if st is not None and stat.S_ISDIR(st.st_mode):
                self.note(path, f"directory not listed ({_errname(exc)})")
            return
        try:
            st = os.fstat(fd)
            self.add(path, "protected", st, _acl(fd, st))
            self.walk(path, fd)
        finally:
            os.close(fd)

    def walk(self, root: str, root_fd: int) -> None:
        """Breadth first, so the bound keeps the shallow entries (``id_rsa`` before ``cache/...``)."""
        queue: deque[tuple[str, int, int]] = deque()
        budget = self.listdir(root, root_fd, queue, self.limit)
        while queue and budget is not None:
            path, dev, ino = queue.popleft()
            try:
                fd = os.open(path, _DIRECTORY_FLAGS)
            except OSError as exc:
                if exc.errno in (errno.ENOENT, errno.ENOTDIR, errno.ELOOP):
                    self.raced += 1  # removed, or replaced by a file or a link, since it was listed
                else:
                    self.note(path, f"directory not listed ({_errname(exc)})")
                continue
            try:
                st = os.fstat(fd)
                if (st.st_dev, st.st_ino) != (dev, ino):
                    self.raced += 1  # another directory now sits at this path
                    continue
                budget = self.listdir(path, fd, queue, budget)
            finally:
                os.close(fd)
        if budget is None:
            self.truncated.append(root)

    def listdir(self, path: str, fd: int, queue: deque[tuple[str, int, int]], budget: int) -> int | None:
        """Record the entries of the directory open at ``fd``; None when ``budget`` ran out first."""
        subdirs: list[tuple[str, int, int]] = []
        failed: list[OSError] = []
        try:
            with os.scandir(fd) as items:
                for item in items:
                    if budget == 0:
                        return None
                    try:
                        st = item.stat(follow_symlinks=False)  # fstatat(fd, name, AT_SYMLINK_NOFOLLOW)
                    except FileNotFoundError:
                        self.raced += 1
                        continue
                    except OSError as exc:
                        failed.append(exc)
                        continue
                    child = path + item.name if path.endswith("/") else f"{path}/{item.name}"
                    target = f"/proc/self/fd/{fd}/{item.name}" if self.proc_fd else child
                    self.add(child, "inside", st, _acl(target, st))
                    budget -= 1
                    if stat.S_ISDIR(st.st_mode):
                        subdirs.append((child, st.st_dev, st.st_ino))
        except OSError as exc:
            self.note(path, f"listing stopped ({_errname(exc)})")
        if failed:
            self.note(path, f"{len(failed)} entries not inspected ({_errname(failed[0])})")
        queue.extend(sorted(subdirs))
        return budget


def _kind(mode: int) -> str:
    return _KINDS.get(stat.S_IFMT(mode), "other")


def _errname(exc: OSError) -> str:
    return errno.errorcode.get(exc.errno or 0, str(exc.errno))


def _between(homes: Sequence[str], path: str) -> Iterator[str]:
    """Directories strictly between a home and ``path``, by name (``~/.config`` for ``~/.config/gh``)."""
    for home in homes:
        prefix = home.rstrip("/") + "/"
        if path.startswith(prefix):
            parts = path[len(prefix) :].split("/")
            for index in range(1, len(parts)):
                yield prefix + "/".join(parts[:index])


def _display(path: str, homes: Sequence[str]) -> str:
    if homes:
        home = homes[0].rstrip("/")
        if path == homes[0]:
            path = "~"
        elif path.startswith(home + "/"):
            path = "~" + path[len(home) :]
    return path if path.isprintable() else repr(path)


def _acl(target: str | int, st: os.stat_result) -> str:
    """POSIX ACL entries the mode does not mirror, as text: "" when none, ``UNKNOWN`` when unreadable."""
    if not _XATTR:
        return UNKNOWN
    if stat.S_ISLNK(st.st_mode):
        return ""
    names = (_ACL_ACCESS, _ACL_DEFAULT) if stat.S_ISDIR(st.st_mode) else (_ACL_ACCESS,)
    parts: list[str] = []
    for name in names:
        try:
            if isinstance(target, int):
                data = os.getxattr(target, name)
            else:
                data = os.getxattr(target, name, follow_symlinks=False)
        except OSError as exc:
            if exc.errno in _ACL_ABSENT:
                continue
            return UNKNOWN
        parts.extend(_acl_text(data, default=name == _ACL_DEFAULT))
    return ",".join(parts)


def _acl_text(data: bytes, *, default: bool) -> list[str]:
    """Linux ``posix_acl_xattr`` (version 2) entries as ``user:1000:r--``; default entries are prefixed."""
    prefix = "default:" if default else ""
    if len(data) < 4 or (len(data) - 4) % 8 or struct.unpack_from("<I", data)[0] != 2:
        return [f"{prefix}raw:{data.hex()}"]
    entries = []
    for offset in range(4, len(data), 8):
        tag, perm, ident = struct.unpack_from("<HHI", data, offset)
        if not default and tag in _ACL_MIRRORED:
            continue
        qualifier = str(ident) if tag in _ACL_QUALIFIED else ""
        entries.append(f"{prefix}{_ACL_TAGS.get(tag, f'tag{tag:#x}')}:{qualifier}:{_rwx(perm)}")
    return entries


def _rwx(bits: int) -> str:
    return "".join(letter if bits & bit else "-" for bit, letter in ((4, "r"), (2, "w"), (1, "x")))


def _verbs(bits: int, kind: str) -> str:
    return ", ".join(verb for bit, verb in (_DIR_VERBS if kind == "dir" else _FILE_VERBS) if bits & bit)


def _compare(prior: Entry, new: Entry) -> tuple[bool, str] | None:
    """``(widened, text)`` for a reportable difference between two entries at the same path."""
    if "symlink" in (prior.kind, new.kind):
        return None  # a link's own mode means nothing on Linux, and its target is out of scope
    same = (prior.dev, prior.ino, prior.kind) == (new.dev, new.ino, new.kind)
    acl_known = UNKNOWN not in (prior.acl, new.acl)
    attributes = []
    if new.uid != prior.uid:
        attributes.append(f"owner uid {prior.uid} -> {new.uid}")
    if new.gid != prior.gid:
        attributes.append(f"group gid {prior.gid} -> {new.gid}")
    if new.mode != prior.mode:
        attributes.append(f"mode {prior.mode:04o} -> {new.mode:04o}")
    if acl_known and new.acl != prior.acl:
        attributes.append(f"ACL {prior.acl or 'none'} -> {new.acl or 'none'}")
    gained = _gained(prior, new, use_acl=acl_known)
    if same:
        if not attributes:
            return None
        lost = (prior.mode >> 6) & ~(new.mode >> 6) & 7
        effects = gained + ([f"owner can no longer {_verbs(lost, new.kind)}"] if lost else [])
    else:
        if not gained:
            return None  # an atomic save that kept or narrowed access
        attributes.insert(0, "replaced during the session")
        effects = gained
    return bool(gained), "; ".join([", ".join(attributes), *effects])


def _gained(prior: Entry, new: Entry, *, use_acl: bool) -> list[str]:
    """Access the new entry grants that the old one did not, to anyone but the owner."""
    held, now = _access(prior, use_acl=use_acl), _access(new, use_acl=use_acl)
    if new.gid != prior.gid:
        held["group"] = 0  # another group: whatever it holds now is new
    gains = {who: bits & ~held.get(who, 0) & 7 for who, bits in now.items()}
    group = "group" if new.gid == prior.gid else f"group {new.gid}"
    classes = [(_principal(who, group), bits) for who, bits in gains.items() if bits and not who.startswith("default:")]
    if [who for who, _ in classes[:2]] == [group, "others"] and classes[0][1] == classes[1][1]:
        classes[:2] = [(f"{group} and others", classes[0][1])]
    effects = []
    label = _LABELS.get(new.role)
    shared = any(bits for who, bits in held.items() if not who.startswith("default:"))
    if label and new.kind == "dir" and classes and not shared:
        detail = " and ".join(f"{who} ({_verbs(bits, 'dir')})" for who, bits in classes)
        effects.append(f"the {label} became accessible to {detail}")
    else:
        effects.extend(f"{who} can now {_verbs(bits, new.kind)}" for who, bits in classes)
    defaults = [f"{who[8:]}:{_rwx(now[who])}" for who, bits in gains.items() if bits and who.startswith("default:")]
    if defaults:
        effects.append("default ACL for new entries grants " + ", ".join(defaults))
    if new.uid != prior.uid and new.uid != 0:
        effects.append(f"uid {new.uid} now owns it")
    special = new.mode & ~prior.mode
    effects.extend(f"{name} bit added" for bit, name in ((0o4000, "setuid"), (0o2000, "setgid")) if special & bit)
    return effects


def _access(entry: Entry, *, use_acl: bool) -> dict[str, int]:
    """Effective permission bits of everyone but the owner: owning group, others, ACL entries.

    With an extended ACL the mode's group bits are the ACL mask, which limits the
    owning group and every named entry. Default entries (directories) apply to
    entries created later, limited by the default mask; the default owner entry
    grants nothing to anyone else.
    """
    mask = (entry.mode >> 3) & 7
    acl = _acl_bits(entry.acl) if use_acl else {}
    access = {"group": acl.pop("group:", mask) & mask, "others": entry.mode & 7}
    default_mask = acl.pop("default:mask:", 7)
    acl.pop("default:user:", None)
    for key, bits in acl.items():
        if key.startswith("default:"):
            access[key] = bits if key == "default:other:" else bits & default_mask
        elif key.startswith(("user:", "group:")):
            access[key] = bits & mask
        else:
            access[key] = bits  # an ACL this module could not parse: compared as is
    return access


def _acl_bits(text: str) -> dict[str, int]:
    """``user:1000:r--,group::r-x`` as ``{"user:1000": 4, "group:": 5}``."""
    entries: dict[str, int] = {}
    for item in text.split(","):
        key, _, perms = item.rpartition(":")
        if key:
            entries[key] = sum(bit for bit, letter in zip((4, 2, 1), perms) if letter != "-")
    return entries


def _principal(who: str, group: str) -> str:
    if who == "group":
        return group
    if who.startswith(("user:", "group:")):
        tag, _, ident = who.partition(":")
        return f"{tag} {ident} (ACL)"
    return who if who == "others" else f"ACL entry {who}"
