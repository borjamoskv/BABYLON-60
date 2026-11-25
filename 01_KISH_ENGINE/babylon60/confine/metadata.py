"""Permission, ownership, time and ``user.*`` attribute changes on the home and protected paths, seen after a session.

Landlock up to ABI 7 does not mediate metadata operations: a confined agent can
still chmod, chown (to another group of the user), change times, set and read
extended attributes, POSIX ACLs included, and inotify-watch paths it cannot
open. Seccomp cannot see paths, and denying those syscalls everywhere would
break ordinary agents (``chmod +x`` in the workspace, file watchers), so they
stay declared limits (``DECLARED_OPEN``). This module makes their most harmful
effect visible instead: ``snapshot`` before the session, ``snapshot`` after it
and ``changes`` between the two.

A snapshot records type, permission bits, owner, group, modification and access
times, the ``user.*`` extended attributes (names and a digest of each value)
and, on Linux, the POSIX ACL entries that the mode does not mirror, for:

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
the walk, a file replaced while its attributes are read included, are skipped
and counted in ``Snapshot.notes``, which also names roots
that are links or could not be listed. Listing a directory is visible to
inotify watchers on it, so take snapshots outside any witness window.

Times are compared against the session window, the wall-clock interval between
the start of the first snapshot and the end of the second. A read or a write
stamps the current time, which lies inside the window, so a time that changed
to a value inside it is ordinary (``ssh`` appending to ``known_hosts`` in
another terminal, any read of a file, this module listing a directory) and is
not reported. A time that changed to a value outside the window was set with
``utime``/``utimensat``: that is reported, for modification and access times
alike. ``TIME_SLACK_NS`` on each side absorbs coarse clocks. The window is this
machine's clock: timestamps coarser than the slack (FAT access dates), a file
server whose clock differs by more than it, or a clock stepped during the
session can make an ordinary read or write near either end of the session look
set, and the reported line says so. The values of a time are printed for the
user and kept out of the journal (``changes(timestamps=False)``).

Extended attributes are read with ``listxattr``/``getxattr``, by path or through
the directory descriptor the walk already holds, never by opening a file:
through ``os`` on Linux and through libc on macOS, where ``user.`` is a naming
convention rather than a namespace. macOS offers no call relative to an open
directory, so there an entry's attributes are read by its full path and only
its last component is kept from being followed. Only names that start with ``user.`` are
recorded, and only on regular files and directories, the two kinds Linux lets
hold them. Where they cannot be read, ``Snapshot.unchecked`` says so and what
is unknown is left uncompared: the whole entry when its names cannot be listed
(another platform, a filesystem that refuses, on macOS a file whose mode denies
reading), only the values when the names list and the values do not (on Linux
a file whose mode denies reading).

A value is compared by a digest of its bytes. macOS hands a value over only
whole (measured: ``getxattr`` refuses an offset for anything but the resource
fork, and a buffer shorter than the value) and APFS takes values of at least
128 MiB, so there a value larger than ``MAX_XATTR_BYTES`` is compared by its
length alone and ``Snapshot.unchecked`` names the entry (the first
``SHOWN_PATHS`` per reason; the rest are counted). Linux values cannot
exceed 64 KiB and are always digested.

Not covered: changes reverted before the session ends, a time set to a value
inside the session window (``touch``), times and attributes of symbolic links
and of entries replaced during the session, attributes of entries that are
neither regular files nor directories, on macOS a ``user.*`` value larger than
``MAX_XATTR_BYTES`` replaced by another of the same length, other paths of the
home (only the home directory entry itself is recorded), entries past
``limit``, targets of symbolic links, and extended attributes other than
``user.*`` and POSIX ACLs.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Iterator, Sequence
import ctypes
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import errno
import functools
import hashlib
import os
import stat
import string
import struct
import sys
import time
from typing import Any

DEFAULT_LIMIT = 512  # entries recorded inside each protected directory
MAX_LINES = 100  # default cap of ``changes``; a final line counts the rest
TIME_SLACK_NS = 2_000_000_000  # widens the session window: coarse clocks and two-second timestamps
USER_PREFIX = "user."  # the extended attributes compared (a namespace on Linux, a convention on macOS)
MAX_XATTR_BYTES = 1 << 20  # macOS: larger values are compared by size only, and ``Snapshot.unchecked`` says so
SHOWN_ATTRIBUTES = 5  # attribute names listed per kind of change; the rest are counted
MAX_NAME_CHARS = 80  # of one attribute name in a line of ``changes``; longer names are cut
SHOWN_PATHS = 3  # entries named per reason in ``Snapshot.unchecked``; the rest are counted

# Said of a time that moved outside the session window. A read or a write stamps the current time.
RETIMED = "a time outside the session: set with utime, unless the filesystem keeps another clock than this machine"

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
_XATTR_READER = "os" if hasattr(os, "listxattr") else "libc" if sys.platform == "darwin" else None
_XATTR_NOFOLLOW = 0x0001  # macOS <sys/xattr.h>
_SIZE_ONLY = "size:"  # in place of a digest: the length of a value too large to read
_NO_READER = ""  # the reason, in ``Snapshot.unread``, when this platform has no way to read attributes at all
# A value read that says the attribute, or its file, is no longer there.
_XATTR_GONE = {
    code for code in (errno.ENOENT, getattr(errno, "ENODATA", None), getattr(errno, "ENOATTR", None)) if code
}
# Characters of an attribute name shown as they are; any other is escaped, because whoever sets
# an attribute picks its name and the name goes into a line others read.
_NAME_SAFE = frozenset(string.ascii_letters + string.digits + "._-:@#+=")
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
    mtime_ns: int | None = None
    atime_ns: int | None = None
    # ``user.*`` attributes as sorted (name, digest of the value) pairs; None when not read
    xattrs: tuple[tuple[str, str], ...] | None = None


@dataclass(frozen=True)
class Snapshot:
    homes: tuple[str, ...]
    entries: tuple[Entry, ...]
    limit: int
    truncated: tuple[str, ...] = ()  # protected directories whose walk stopped at ``limit``
    notes: tuple[str, ...] = ()  # what was not inspected, and why (display form)
    unchecked: tuple[str, ...] = ()  # why ``user.*`` attributes were not read, where they were not
    started_ns: int | None = None  # wall clock around the walk: ``changes`` builds the session window from it
    finished_ns: int | None = None
    unread: tuple[tuple[str, tuple[str, ...]], ...] = ()  # what ``unchecked`` says: (reason, display paths)

    def display(self, path: str) -> str:
        """``path`` relative to the first home (``~/...``), escaped when not printable."""
        return _display(path, self.homes)


def snapshot(homes: Sequence[str], protected: Sequence[str], *, limit: int = DEFAULT_LIMIT) -> Snapshot:
    """Record the homes, the protected paths and up to ``limit`` entries inside each protected directory."""
    if limit < 0:
        raise ValueError("limit must be zero or positive")
    home_paths = tuple(dict.fromkeys(os.path.abspath(home) for home in homes))
    protected_paths = tuple(dict.fromkeys(os.path.abspath(path) for path in protected))
    started = time.time_ns()
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
    entries, unread = tuple(walk.entries.values()), walk.unread()
    finished = time.time_ns()
    return Snapshot(
        home_paths, entries, limit, tuple(walk.truncated), notes, _unread_lines(unread), started, finished, unread
    )


def unchecked(*snapshots: Snapshot) -> list[str]:
    """``Snapshot.unchecked`` of several snapshots as one list: each reason once, naming the entries of all of them.

    ``run`` calls it with the snapshots taken before and after a session: an entry whose ``user.*``
    attributes could not be read in either one was not compared in full.
    """
    merged: dict[str, dict[str, None]] = {}
    for snap in snapshots:
        for reason, paths in snap.unread:
            merged.setdefault(reason, {}).update(dict.fromkeys(paths))
    return list(_unread_lines((reason, tuple(paths)) for reason, paths in sorted(merged.items())))


def _unread_lines(unread: Iterable[tuple[str, Sequence[str]]]) -> tuple[str, ...]:
    """``(reason, display paths)`` pairs as text, naming ``SHOWN_PATHS`` entries per reason and counting the rest."""
    lines = []
    for reason, paths in unread:
        if reason == _NO_READER:
            lines.append(f"user.* attributes are not read on this platform ({sys.platform})")
            continue
        entries = "1 entry" if len(paths) == 1 else f"{len(paths)} entries"
        rest = len(paths) - SHOWN_PATHS
        named = ", ".join(paths[:SHOWN_PATHS]) + (f" and {rest} more" if rest > 0 else "")
        lines.append(f"user.* attributes not read on {entries} ({reason}): {named}")
    return tuple(lines)


def changes(
    before: Snapshot, after: Snapshot, *, max_lines: int | None = MAX_LINES, timestamps: bool = True
) -> list[str]:
    """Human-readable metadata changes of entries present in both snapshots.

    * Same inode: any change of mode, owner, group, ACL or ``user.*`` attributes
      is reported (chmod, chown, setfacl or setxattr, inside or outside the
      sandbox), and so is a modification or access time that moved outside the
      session window (utime; see the module docstring).
    * Replaced inode (an editor or ``ssh-keygen -R`` saving atomically): reported
      only when the new entry grants access the old one did not; a save that
      keeps or narrows permissions is ordinary.
    * Never compared: contents, sizes, times that moved inside the session
      window, extended attributes other than ``user.*`` and POSIX ACLs, and
      symbolic links. Entries that appear or disappear are not reported.

    Changes that widen access come first. With ``max_lines``, the list is cut
    there and one more line counts what was left out.

    A time that moved is described as moved to before or to after the session,
    followed by its old and new value. ``timestamps=False`` leaves the values
    out and changes nothing else: that is the form for a journal body, whose
    digest takes no wall-clock value (INV_C5_CANONICAL_LOGICAL_TICK).
    """
    earlier = {entry.path: entry for entry in before.entries}
    window = _window(before, after)
    found: list[tuple[bool, int, str, str]] = []
    for entry in after.entries:
        prior = earlier.get(entry.path)
        if prior is None or prior == entry:
            continue
        compared = _compare(prior, entry, window, timestamps)
        if compared is not None:
            widened, text = compared
            found.append((not widened, ROLES.index(entry.role), entry.path, f"{after.display(entry.path)}: {text}"))
    found.sort()
    lines = [item[3] for item in found]
    if max_lines is not None and len(lines) > max_lines:
        rest = len(lines) - max_lines
        lines = lines[:max_lines] + [f"... and {rest} more metadata changes"]
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
        self.xattr_failed: dict[str, list[str]] = {}  # reason -> display paths, in walk order

    def note(self, path: str, text: str) -> None:
        self.notes.append(f"{_display(path, self.homes)}: {text}")

    def unread(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        if _XATTR_READER is None:
            return ((_NO_READER, ()),)
        return tuple((reason, tuple(paths)) for reason, paths in sorted(self.xattr_failed.items()))

    def add(self, path: str, role: str, st: os.stat_result, target: str | int) -> bool:
        """Record ``path``; ``target`` is how to reach it for extended attributes (a path or a descriptor).

        False when another file took its place between ``st`` and the reading of its attributes and
        ACL (an atomic save, ``ssh-keygen -R``): recording them under the old inode would make a
        replacement look like ``setxattr`` on the same file, so the entry is skipped and counted.
        """
        existing = self.entries.get(path)
        if existing is None:
            xattrs, failure = _user_xattrs(target, st)
            acl = _acl(target, st)
            read_by_path = isinstance(target, str) and (stat.S_ISREG(st.st_mode) or stat.S_ISDIR(st.st_mode))
            if read_by_path and not _same_file(str(target), st):
                self.raced += 1
                return False
            if failure:
                self.xattr_failed.setdefault(failure, []).append(_display(path, self.homes))
            self.entries[path] = Entry(
                path,
                role,
                _kind(st.st_mode),
                stat.S_IMODE(st.st_mode),
                st.st_uid,
                st.st_gid,
                st.st_dev,
                st.st_ino,
                acl,
                st.st_mtime_ns,
                st.st_atime_ns,
                xattrs,
            )
        elif ROLES.index(role) < ROLES.index(existing.role):
            self.entries[path] = replace(existing, role=role)
        return True

    def root(self, path: str, role: str) -> os.stat_result | None:
        try:
            st = os.lstat(path)
        except (FileNotFoundError, NotADirectoryError):
            return None
        except OSError as exc:
            self.note(path, f"not inspected ({_errname(exc)})")
            return None
        self.add(path, role, st, path)
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
            self.add(path, "protected", st, fd if _XATTR else path)
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
                    if not self.add(child, "inside", st, target):
                        continue  # replaced while it was being read: counted in ``raced``
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
    getxattr = getattr(os, "getxattr", None)
    if getxattr is None:
        return UNKNOWN
    for name in names:
        try:
            if isinstance(target, int):
                data = getxattr(target, name)
            else:
                data = getxattr(target, name, follow_symlinks=False)
        except OSError as exc:
            if exc.errno in _ACL_ABSENT:
                continue
            return UNKNOWN
        parts.extend(_acl_text(data, default=name == _ACL_DEFAULT))
    return ",".join(parts)


def _same_file(target: str, st: os.stat_result) -> bool:
    """Whether ``target`` still names the file ``st`` describes, without following a final link."""
    try:
        now = os.lstat(target)
    except OSError:
        return False
    return (now.st_dev, now.st_ino) == (st.st_dev, st.st_ino)


def _user_xattrs(target: str | int, st: os.stat_result) -> tuple[tuple[tuple[str, str], ...] | None, str]:
    """``user.*`` attributes of an entry and, when they could not all be compared in full, why.

    None when the names could not be listed, and for entries that are neither
    regular files nor directories: Linux lets no other kind hold ``user.*``
    attributes (xattr(7)). A value that cannot be read keeps its name with
    ``UNKNOWN`` as digest, so adding or removing it still shows. A value larger
    than ``MAX_XATTR_BYTES`` is recorded by its length alone.
    """
    if _XATTR_READER is None or not (stat.S_ISREG(st.st_mode) or stat.S_ISDIR(st.st_mode)):
        return None, ""
    try:
        if _XATTR_READER == "os":
            names = [os.fsencode(name) for name in _os_listxattr(target)]
        else:
            names = _libc_listxattr(target)
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            return None, ""  # gone since it was listed: nothing is left to compare
        return None, _errname(exc)
    failure = ""
    found = []
    for name in sorted(name for name in names if name.startswith(USER_PREFIX.encode())):
        try:
            if _XATTR_READER == "os":
                digest = _digest(_os_getxattr(target, name))
            else:
                digest = _libc_getxattr(target, name)
        except OSError as exc:
            if exc.errno in _XATTR_GONE:
                continue  # removed since the names were listed
            digest, failure = UNKNOWN, f"{_errname(exc)} reading a value"
        if digest.startswith(_SIZE_ONLY):
            failure = f"a value over {MAX_XATTR_BYTES >> 20} MiB, compared by size only"
        found.append((name.decode("utf-8", "surrogateescape"), digest))
    return tuple(found), failure


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _os_listxattr(target: str | int) -> list[str]:
    return os.listxattr(target) if isinstance(target, int) else os.listxattr(target, follow_symlinks=False)


def _os_getxattr(target: str | int, name: bytes) -> bytes:
    return os.getxattr(target, name) if isinstance(target, int) else os.getxattr(target, name, follow_symlinks=False)


@functools.cache
def _libc() -> Any:
    """macOS ``listxattr``/``getxattr``: the ``os`` module only exposes them on Linux."""
    libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    libc.listxattr.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int)
    libc.listxattr.restype = ctypes.c_ssize_t
    libc.getxattr.argtypes = (
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_size_t,
        ctypes.c_uint32,
        ctypes.c_int,
    )
    libc.getxattr.restype = ctypes.c_ssize_t
    return libc


def _libc_call(function: Any, *args: Any) -> int:
    result = int(function(*args))
    if result < 0:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err))
    return result


def _libc_listxattr(target: str | int) -> list[bytes]:
    if isinstance(target, int):
        raise OSError(errno.ENOTSUP, "extended attributes are read by path on this platform")
    libc, raw = _libc(), os.fsencode(target)
    size = _libc_call(libc.listxattr, raw, None, 0, _XATTR_NOFOLLOW)
    names = ctypes.create_string_buffer(max(size, 1))
    # The buffer's own capacity, never the size just asked: with 0, macOS listxattr answers another
    # size query and leaves the buffer unfilled (measured); with the capacity, names added in between
    # make the call fail with ERANGE, which the caller reports.
    size = _libc_call(libc.listxattr, raw, names, len(names), _XATTR_NOFOLLOW)
    return [name for name in names.raw[:size].split(b"\0") if name]


def _libc_getxattr(target: str | int, name: bytes) -> str:
    libc, raw = _libc(), os.fsencode(str(target))  # always a path here: ``_libc_listxattr`` refuses descriptors
    length = _libc_call(libc.getxattr, raw, name, None, 0, 0, _XATTR_NOFOLLOW)
    if length > MAX_XATTR_BYTES:
        return f"{_SIZE_ONLY}{length}"  # getxattr hands a value over only whole: see the module docstring
    value = ctypes.create_string_buffer(max(length, 1))
    # The capacity, as in ``_libc_listxattr``: a value that grew in between fails with ERANGE, never a short read.
    length = _libc_call(libc.getxattr, raw, name, value, len(value), 0, _XATTR_NOFOLLOW)
    return _digest(value.raw[:length])


def _window(before: Snapshot, after: Snapshot) -> tuple[int, int] | None:
    """The session window, widened by ``TIME_SLACK_NS``; None when a snapshot carries no clock."""
    if before.started_ns is None or after.finished_ns is None:
        return None
    return before.started_ns - TIME_SLACK_NS, after.finished_ns + TIME_SLACK_NS


def _stamp(ns: int) -> str:
    seconds, fraction = divmod(ns, 1_000_000_000)
    try:
        text = datetime.fromtimestamp(seconds, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    except (OverflowError, ValueError, OSError):
        return f"{ns} ns since the epoch"
    return f"{text}.{fraction:09d}Z" if fraction else f"{text}Z"


def _retimed(prior: Entry, new: Entry, window: tuple[int, int] | None, timestamps: bool = True) -> list[str]:
    """Times of the same inode that moved to a value outside the session window: set with utime.

    Each says to which side of the session it moved and, with ``timestamps``, its old and new value.
    """
    if window is None:
        return []
    found = []
    for label, old, now in (
        ("modification", prior.mtime_ns, new.mtime_ns),
        ("access", prior.atime_ns, new.atime_ns),
    ):
        if old is not None and now is not None and now != old and not window[0] <= now <= window[1]:
            side = "before" if now < window[0] else "after"
            values = f" ({_stamp(old)} -> {_stamp(now)})" if timestamps else ""
            found.append(f"{label} time moved to {side} the session{values}")
    return found


def _reattributed(prior: Entry, new: Entry) -> list[str]:
    """``user.*`` attributes of the same inode that were added, removed or given another value."""
    if prior.xattrs is None or new.xattrs is None:
        return []
    old, now = dict(prior.xattrs), dict(new.xattrs)
    kinds = (
        ("added", [name for name in now if name not in old]),
        ("removed", [name for name in old if name not in now]),
        ("changed", [name for name in now if name in old and _differs(old[name], now[name])]),
    )
    found = [f"{kind} ({_names(names)})" for kind, names in kinds if names]
    return ["user.* attributes " + ", ".join(found)] if found else []


def _differs(old: str, now: str) -> bool:
    return old != now and UNKNOWN not in (old, now)


def _names(names: list[str]) -> str:
    """At most ``SHOWN_ATTRIBUTES`` names, each escaped and cut to ``MAX_NAME_CHARS``: whoever sets them picks them."""
    shown = []
    for name in names[:SHOWN_ATTRIBUTES]:
        text = "".join(char if char in _NAME_SAFE else _escaped(char) for char in name)
        shown.append(text if len(text) <= MAX_NAME_CHARS else text[: MAX_NAME_CHARS - 3] + "...")
    rest = len(names) - len(shown)
    return ", ".join(shown) + (f" and {rest} more" if rest else "")


def _escaped(char: str) -> str:
    code = ord(char)
    return f"\\x{code:02x}" if code < 0x100 else f"\\u{code:04x}" if code < 0x10000 else f"\\U{code:08x}"


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


def _compare(
    prior: Entry, new: Entry, window: tuple[int, int] | None = None, timestamps: bool = True
) -> tuple[bool, str] | None:
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
        retimed = _retimed(prior, new, window, timestamps)
        attributes += retimed + _reattributed(prior, new)
        if not attributes:
            return None
        lost = (prior.mode >> 6) & ~(new.mode >> 6) & 7
        effects = gained + ([f"owner can no longer {_verbs(lost, new.kind)}"] if lost else [])
        if retimed:
            effects.append(RETIMED)
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
