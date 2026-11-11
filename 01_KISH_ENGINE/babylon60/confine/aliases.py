"""Other names for protected files and directories.

A path allow-list can be bypassed through an alias. A hardlink gives a protected
file a second name; a bind mount grafts a protected directory or file into
another place of the mount tree. Landlock attaches each rule to an inode and, on
access, walks up the hierarchy of the path that was used, crossing mount points,
so a rule on a directory also covers every mount below it.

This module gathers the facts by inode identity ``(st_dev, st_ino)`` and never
resolves paths (INV_C5_PATH_SYMLINK_CONFINEMENT):

* ``scan_tree`` records the directories and regular files below a directory
  without following symbolic links, up to a bound;
* ``read_mountinfo`` parses ``/proc/self/mountinfo`` (Linux), decoding the octal
  escapes the kernel writes for space, tab, newline and backslash;
* ``mounts_beneath`` finds the mount points below a set of directories.

``policy.py`` decides what to refuse.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable, Iterator
from dataclasses import dataclass, field
import os
import re
import stat
import sys

Identity = tuple[int, int]
MOUNTINFO = "/proc/self/mountinfo"
SCAN_LIMIT = 20_000  # entries listed below one protected directory
SCAN_DEPTH = 32  # directory levels entered below it (one descriptor open per level)
_ESCAPE = re.compile(rb"\\([0-7]{3})")
_OPEN_DIR = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC


class MountinfoError(ValueError):
    """A mountinfo line does not have the documented layout."""


@dataclass(frozen=True)
class Mount:
    mount_id: int
    parent_id: int
    device: str  # "major:minor"
    root: str  # root of the mount inside its filesystem (a bind mount shows its source here)
    mount_point: str  # relative to this process's root
    fstype: str
    source: str


def unescape(raw: bytes) -> str:
    """Decode the ``\\ooo`` octal escapes of a mountinfo field into a filesystem path."""
    return os.fsdecode(_ESCAPE.sub(lambda match: bytes((int(match.group(1), 8),)), raw))


def parse_mountinfo(data: bytes) -> list[Mount]:
    """Parse ``/proc/<pid>/mountinfo`` (proc_pid_mountinfo(5)).

    Fields are separated by single spaces, which the kernel escapes inside
    paths, together with tab, newline and backslash. Optional fields end at a
    lone ``-``; filesystem type, source and superblock options follow it.
    """
    mounts: list[Mount] = []
    for line in data.split(b"\n"):
        if not line:
            continue
        fields = line.split(b" ")
        try:
            separator = fields.index(b"-", 6)
            fstype, source = fields[separator + 1], fields[separator + 2]
            mounts.append(
                Mount(
                    int(fields[0]),
                    int(fields[1]),
                    fields[2].decode("ascii"),
                    unescape(fields[3]),
                    unescape(fields[4]),
                    unescape(fstype),
                    unescape(source),
                )
            )
        except (ValueError, IndexError) as exc:
            raise MountinfoError(f"unexpected mountinfo line: {line[:160]!r}") from exc
    return mounts


def read_mountinfo(path: str = MOUNTINFO) -> list[Mount] | None:
    """The mount table of this process; ``None`` off Linux, where there is no such file.

    Raises ``OSError`` when it cannot be read (for example without ``/proc``)
    and ``MountinfoError`` when it cannot be parsed.
    """
    if not sys.platform.startswith("linux"):
        return None
    with open(path, "rb") as handle:
        return parse_mountinfo(handle.read())


def mounts_beneath(
    directories: Collection[Identity],
    mounts: Iterable[Mount],
    ancestry: Callable[[str], list[Identity]],
) -> Iterator[tuple[Mount, list[Identity], Identity]]:
    """Yield ``(mount, containing directories, identity of the mount's root)`` for mounts below ``directories``.

    A mount point lies below a directory when the directory's identity appears
    in its ``..`` ancestry, the walk Landlock makes from the mount's root up to
    ``/`` (it skips the covered mount point itself). The parent of each mount
    point is walked first and the mount's root is examined only when it lies
    below one of ``directories``, so mounts elsewhere, such as a stale network
    or FUSE mount, are never touched. A mount point whose path cannot be
    resolved is skipped: the confined process, with the same or fewer
    privileges, cannot resolve it either (transient errors of network
    filesystems aside).
    """
    parents: dict[str, list[Identity] | None] = {}
    for mount in mounts:
        point = mount.mount_point
        parent = os.path.dirname(point)
        if not os.path.isabs(point) or parent == point:
            continue  # "/" has no ancestry above it
        if parent not in parents:
            try:
                parents[parent] = ancestry(parent)
            except OSError:
                parents[parent] = None
        chain = parents[parent]
        if chain is None:
            continue
        containing = [ident for ident in chain if ident in directories]
        if not containing:
            continue
        try:
            st = os.stat(point, follow_symlinks=False)
        except OSError:
            continue
        yield mount, containing, (st.st_dev, st.st_ino)


@dataclass
class Linked:
    """A regular file with more than one link, and the name it was found under."""

    path: str
    ident: Identity
    nlink: int
    dentry: tuple[Identity, str]  # (identity of its directory, name)


@dataclass
class Scan:
    """Directories and regular files found below one directory."""

    entries: dict[Identity, str] = field(default_factory=dict)  # identity -> first path found
    linked: list[Linked] = field(default_factory=list)
    listed: int = 0  # entries listed, of any type
    stopped: str = ""  # why the walk ended early, if it did
    errors: list[str] = field(default_factory=list)  # directories that could not be listed


class _Bound(Exception):
    pass


def scan_tree(
    top: str,
    *,
    limit: int = SCAN_LIMIT,
    depth: int = SCAN_DEPTH,
    visited: set[Identity] | None = None,
) -> Scan:
    """List every directory and regular file below directory ``top``, without following symbolic links.

    ``top`` is opened the way ``policy.ancestry`` opens it, so a symbolic link
    there is followed; below it, directories are opened relative to their
    parent's descriptor with ``O_NOFOLLOW`` and nothing is followed. Each
    directory's own entries are recorded before any subdirectory is entered, so
    the bounds cut the deepest entries first. Directories in ``visited`` are not
    listed again, which keeps overlapping trees from being counted twice.
    Raises ``OSError`` when ``top`` cannot be opened as a directory.
    """
    scan = Scan()
    seen = visited if visited is not None else set()
    # (descriptor, path, subdirectories still to enter); every open descriptor is on this stack.
    stack: list[tuple[int, str, list[str]]] = [(os.open(top, _OPEN_DIR), top, [])]
    try:
        stack[-1] = (stack[-1][0], top, _enter(stack[-1][0], top, scan, limit, seen))
        while stack:
            parent_fd, parent, pending = stack[-1]
            if not pending:
                os.close(stack.pop()[0])
                continue
            name = pending.pop()
            path = os.path.join(parent, name)
            if len(stack) > depth:
                scan.stopped = scan.stopped or f"depth {depth}"
                continue
            try:
                child = os.open(name, _OPEN_DIR | os.O_NOFOLLOW, dir_fd=parent_fd)
            except OSError as exc:
                scan.errors.append(f"{path} ({exc.strerror})")
                continue
            stack.append((child, path, []))
            stack[-1] = (child, path, _enter(child, path, scan, limit, seen))
    except _Bound:
        scan.stopped = f"{limit} entries"
    finally:
        for open_fd, _path, _pending in stack:
            os.close(open_fd)
    return scan


def _enter(fd: int, path: str, scan: Scan, limit: int, seen: set[Identity]) -> list[str]:
    """List an open directory unless it was listed already; return its subdirectories still to enter."""
    st = os.fstat(fd)
    ident = (st.st_dev, st.st_ino)
    if ident in seen:
        return []
    seen.add(ident)
    return _list(fd, path, ident, scan, limit, seen)


def _list(fd: int, path: str, ident: Identity, scan: Scan, limit: int, seen: set[Identity]) -> list[str]:
    """Record the entries of one open directory; return its subdirectories in listing order, reversed."""
    subdirectories: list[str] = []
    try:
        with os.scandir(fd) as entries:
            for entry in entries:
                if scan.listed >= limit:
                    raise _Bound
                scan.listed += 1
                if entry.is_symlink():
                    continue
                try:
                    st = entry.stat(follow_symlinks=False)
                except OSError:
                    continue  # removed while listing
                child = (st.st_dev, st.st_ino)
                if stat.S_ISDIR(st.st_mode):
                    scan.entries.setdefault(child, os.path.join(path, entry.name))
                    if child not in seen:
                        subdirectories.append(entry.name)
                elif stat.S_ISREG(st.st_mode):
                    member = os.path.join(path, entry.name)
                    scan.entries.setdefault(child, member)
                    if st.st_nlink > 1:
                        scan.linked.append(Linked(member, child, st.st_nlink, (ident, entry.name)))
    except OSError as exc:
        scan.errors.append(f"{path} ({exc.strerror})")
    subdirectories.reverse()  # popped from the end, so entered in listing order
    return subdirectories
