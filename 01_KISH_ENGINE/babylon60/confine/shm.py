"""What a session leaves in ``/dev/shm``, which the agent can write on Linux.

The policy keeps ``/dev/shm`` readable and writable: POSIX semaphores and shared
memory live there (Python ``multiprocessing`` needs them). So a confined agent
can leave files there, executables included, that outlive the session, and
change or remove what other processes of the user keep there. ``babylon60 run``
lists ``/dev/shm`` before and after the session and names, by path, the entries
owned by the user that were added, changed or removed in between: detection,
not prevention.

A listing records for each entry its type, permission bits, owner, size, inode
and modification and change times (for a directory, its type, bits, owner and
inode: what changes inside it is named by its own entries); never contents. No
link is followed: entries are read with ``fstatat`` relative to their open
directory, and directories are entered with ``O_NOFOLLOW`` and checked by
identity. ``MAX_ENTRIES`` entries and ``MAX_DEPTH`` levels bound the work; a
listing cut short, or a directory the user could write in but this cannot list,
is named in ``Listing.unchecked``. Other processes of the user can change
``/dev/shm`` during the session as well, and nothing here tells who did: their
changes are named too.
"""

from __future__ import annotations

from dataclasses import dataclass
import errno
import os
import stat
import sys

from babylon60.confine.persistence import printable
from babylon60.confine.policy import Policy

SHM = "/dev/shm"
MAX_ENTRIES = 10_000  # entries listed below /dev/shm
MAX_DEPTH = 32
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
_UID = 2  # position of the owner in an entry

# (type, permission bits, owner, size, modification time, change time, inode); directories keep 0 for
# size and times, which change with what is created or removed inside them.
Entry = tuple[int, int, int, int, int, int, int]


@dataclass(frozen=True)
class Listing:
    root: str
    entries: dict[bytes, Entry]  # path below ``root``: what it was
    complete: bool  # False when the listing was cut short: an entry missing from it says nothing
    unchecked: tuple[str, ...]  # what was not listed, and why


def granted(policy: Policy) -> str | None:
    """``/dev/shm`` when ``policy`` grants it read and write on Linux; None when nothing there can change."""
    if not sys.platform.startswith("linux"):
        return None
    if any(grant.path == SHM and grant.access == "rw" and grant.is_dir for grant in policy.grants):
        return SHM
    return None


def snapshot(root: str = SHM) -> Listing:
    """List ``root`` (``/dev/shm``) and everything below it, within ``MAX_ENTRIES`` and ``MAX_DEPTH``."""
    walk = _Walk(root)
    try:
        fd = os.open(root, _DIR_FLAGS)
    except OSError as exc:
        return Listing(root, {}, False, (f"{root} ({_errname(exc)}: not compared)",))
    try:
        walk.directory(fd, b"", 0)
    finally:
        os.close(fd)
    return Listing(root, walk.entries, walk.complete, tuple(walk.unchecked))


def changes(before: Listing, after: Listing, uid: int) -> list[str]:
    """Paths of the entries owned by ``uid`` (before or after) that were added, changed or removed."""
    labels: list[str] = []
    for key in sorted(before.entries.keys() | after.entries.keys()):
        old, new = before.entries.get(key), after.entries.get(key)
        if old == new:
            continue
        if (old is None and not before.complete) or (new is None and not after.complete):
            continue  # missing from a listing cut short: not known to be added or removed
        if all(entry is None or entry[_UID] != uid for entry in (old, new)):
            continue
        labels.append(printable(os.fsencode(after.root).rstrip(b"/") + b"/" + key))
    return labels


class _Walk:
    def __init__(self, root: str) -> None:
        self.root = root
        self.entries: dict[bytes, Entry] = {}
        self.unchecked: list[str] = []
        self.left = MAX_ENTRIES
        self.complete = True

    def _cut(self, why: str) -> None:
        if self.complete:
            self.complete = False
            self.unchecked.append(f"{self.root} ({why}: the rest not compared)")

    def directory(self, fd: int, prefix: bytes, depth: int) -> None:
        names: list[bytes] = []
        try:
            with os.scandir(fd) as items:
                for item in items:
                    if len(names) >= self.left:
                        self._cut(f"more than {MAX_ENTRIES} entries")
                        break
                    names.append(os.fsencode(item.name))
        except OSError as exc:
            self.unchecked.append(f"{printable(self._path(prefix))} ({_errname(exc)}: not compared)")
            if not prefix:
                self.complete = False  # nothing listed: nothing known to be added or removed
            return
        self.left -= len(names)
        for name in sorted(names):
            try:
                st = os.stat(name, dir_fd=fd, follow_symlinks=False)
            except OSError:
                continue  # removed while listing
            path = prefix + name
            if not stat.S_ISDIR(st.st_mode):
                self.entries[path] = (
                    stat.S_IFMT(st.st_mode),
                    stat.S_IMODE(st.st_mode),
                    st.st_uid,
                    st.st_size,
                    st.st_mtime_ns,
                    st.st_ctime_ns,
                    st.st_ino,
                )
                continue
            self.entries[path] = (stat.S_IFDIR, stat.S_IMODE(st.st_mode), st.st_uid, 0, 0, 0, st.st_ino)
            if depth + 1 > MAX_DEPTH:
                self._cut(f"deeper than {MAX_DEPTH} levels")
                continue
            try:
                sub = os.open(name, _DIR_FLAGS, dir_fd=fd)
            except OSError as exc:
                if _writable(fd, name):  # the agent could leave something in it that this cannot see
                    self.unchecked.append(f"{printable(self._path(path))} ({_errname(exc)}: not compared)")
                continue
            try:
                opened = os.fstat(sub)
                if (opened.st_dev, opened.st_ino) == (st.st_dev, st.st_ino):
                    self.directory(sub, path + b"/", depth + 1)
            finally:
                os.close(sub)

    def _path(self, relative: bytes) -> bytes:
        return os.fsencode(self.root).rstrip(b"/") + (b"/" + relative.rstrip(b"/") if relative else b"")


def _writable(dir_fd: int, name: bytes) -> bool:
    """Whether this process (by its effective ids) could create entries in the directory ``name``."""
    try:
        if os.access in os.supports_effective_ids:
            return os.access(name, os.W_OK | os.X_OK, dir_fd=dir_fd, effective_ids=True)
        return os.access(name, os.W_OK | os.X_OK, dir_fd=dir_fd)
    except OSError:
        return True  # not known: named, never silently skipped


def _errname(exc: OSError) -> str:
    return errno.errorcode.get(exc.errno or 0, str(exc.errno))
