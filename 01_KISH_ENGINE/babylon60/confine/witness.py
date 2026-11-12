"""Observers that do not trust the confined process or the broker's own verdict.

``InotifyWitness`` watches the canary inode and its directory from outside the
sandbox (Linux). An open, read, write, rename or creation there is evidence of
an effect, whatever the confined process reported. A queue overflow makes the
observation inconclusive.

``find_token`` scans bytes and files for the canary token in raw, hex (lower and
upper case), base64 (standard and URL-safe, at each of the three byte
alignments the token can have inside a longer encoded stream) and UTF-16 (LE
and BE) form. With the snapshot of ``~/.ssh`` taken by the demo, it is the only
witness available on macOS without privileges.
"""

from __future__ import annotations

import base64
from collections.abc import Callable, Iterable, Sequence
import ctypes
from dataclasses import dataclass, field
import os
import struct
import sys

IN_ACCESS, IN_MODIFY, IN_ATTRIB = 0x1, 0x2, 0x4
IN_OPEN, IN_MOVED_FROM, IN_MOVED_TO, IN_CREATE, IN_DELETE = 0x20, 0x40, 0x80, 0x100, 0x200
IN_DELETE_SELF, IN_MOVE_SELF, IN_Q_OVERFLOW = 0x400, 0x800, 0x4000
WATCH_MASK = (
    IN_ACCESS
    | IN_MODIFY
    | IN_ATTRIB
    | IN_OPEN
    | IN_MOVED_FROM
    | IN_MOVED_TO
    | IN_CREATE
    | IN_DELETE
    | IN_DELETE_SELF
    | IN_MOVE_SELF
)
NAMES = {
    IN_ACCESS: "access",
    IN_MODIFY: "modify",
    IN_ATTRIB: "attrib",
    IN_OPEN: "open",
    IN_MOVED_FROM: "moved_from",
    IN_MOVED_TO: "moved_to",
    IN_CREATE: "create",
    IN_DELETE: "delete",
    IN_DELETE_SELF: "delete_self",
    IN_MOVE_SELF: "move_self",
}


@dataclass
class Observation:
    events: int = 0
    kinds: dict[str, int] = field(default_factory=dict)
    overflow: bool = False
    available: bool = True


def inotify_available() -> bool:
    return sys.platform.startswith("linux")


class InotifyWitness:
    def __init__(self, paths: Sequence[str]) -> None:
        libc = ctypes.CDLL(None, use_errno=True)
        self._fd = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        if self._fd < 0:
            raise OSError(ctypes.get_errno(), "inotify_init1")
        try:
            for path in paths:
                if libc.inotify_add_watch(self._fd, os.fsencode(path), WATCH_MASK) < 0:
                    raise OSError(ctypes.get_errno(), f"inotify_add_watch {path}")
        except BaseException:
            os.close(self._fd)
            raise
        self._observation = Observation()

    def drain(self) -> Observation:
        while True:
            try:
                buffer = os.read(self._fd, 65536)
            except BlockingIOError:
                break
            offset = 0
            while offset < len(buffer):
                _wd, mask, _cookie, length = struct.unpack_from("iIII", buffer, offset)
                offset += 16 + length
                if mask & IN_Q_OVERFLOW:
                    self._observation.overflow = True
                    continue
                self._observation.events += 1
                for bit, name in NAMES.items():
                    if mask & bit:
                        self._observation.kinds[name] = self._observation.kinds.get(name, 0) + 1
        return self._observation

    def close(self) -> Observation:
        observation = self.drain()
        os.close(self._fd)
        return observation

    def __enter__(self) -> InotifyWitness:
        return self

    def __exit__(self, *_exc: object) -> None:
        if self._fd >= 0:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = -1


def _base64_cores(raw: bytes, encode: Callable[[bytes], bytes]) -> list[bytes]:
    """The base64 characters that depend only on ``raw`` when it starts at byte offset 0, 1 or 2 of a group.

    Characters that also carry bits of the bytes before or after the token are
    dropped, so the form matches wherever the token sits in a longer encoded stream.
    """
    cores = []
    for shift in range(3):
        encoded = encode(bytes(shift) + raw)
        first = -(-8 * shift // 6)  # ceil: first character made only of token bits
        last = 8 * (shift + len(raw)) // 6  # floor: end of the characters made only of token bits
        cores.append(encoded[first:last])
    return cores


def token_forms(token: str) -> list[bytes]:
    """Encodings of ``token`` that count as the token appearing somewhere."""
    raw = token.encode()
    forms = [
        raw,
        raw.hex().encode(),
        raw.hex().upper().encode(),
        *_base64_cores(raw, base64.b64encode),
        *_base64_cores(raw, base64.urlsafe_b64encode),
        token.encode("utf-16-le"),
        token.encode("utf-16-be"),
    ]
    return [form for form in dict.fromkeys(forms) if form]


def find_token(token: str, blobs: Iterable[bytes] = (), roots: Iterable[str] = ()) -> list[str]:
    """Where the token appears: ``"output"`` or a path relative to its root."""
    forms = token_forms(token)
    hits: list[str] = []
    for blob in blobs:
        if any(form in blob for form in forms):
            hits.append("output")
            break
    for root in roots:
        for directory, _dirs, files in os.walk(root, followlinks=False):
            for name in files:
                path = os.path.join(directory, name)
                try:
                    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
                except OSError:
                    continue
                try:
                    data = os.read(fd, 1024 * 1024)
                finally:
                    os.close(fd)
                if any(form in data for form in forms):
                    hits.append(os.path.relpath(path, root))
    return hits
