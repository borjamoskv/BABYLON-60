"""Terminals of the session that starts a confined agent.

The policy does not grant every pseudo-terminal of the user: from inside the
sandbox another terminal tab could be read (keystrokes) or written (a fake
password prompt). ``session_ttys`` names the terminals behind given descriptors
(0-2 by default), so that ``build_policy(ttys=...)`` grants exactly those.
``babylon60 run`` passes the slave of the private pseudo-terminal it allocates
for the agent (``terminal_proxy``), never the user's own terminal: the grant
lets the agent reopen its terminal by path, as Node's libuv does for a TTY on
stdin or stdout.

Names look like ``/dev/pts/3`` on Linux and ``/dev/ttys003`` on macOS.
"""

from __future__ import annotations

from collections.abc import Iterable
import os
import stat

from babylon60.confine.policy import ancestry

STDIO = (0, 1, 2)


def session_ttys(fds: Iterable[int] = STDIO) -> list[str]:
    """Terminal device paths of descriptors ``fds`` (0-2 by default), without duplicates, only beneath ``/dev``.

    A name is kept only when it is a character device, not a symbolic link,
    whose device number is the one behind the descriptor and which sits
    physically beneath ``/dev`` (``(st_dev, st_ino)`` ancestry, never
    ``realpath``). Closed descriptors and descriptors that are not terminals are
    ignored, as is a terminal whose name cannot be found (``os.ttyname`` fails,
    for example a pseudo-terminal from another mount namespace).
    """
    try:
        dev = ancestry("/dev")[0]
    except OSError:
        return []
    names: list[str] = []
    for fd in fds:
        try:
            if not os.isatty(fd):
                continue
            name = os.ttyname(fd)
            held = os.fstat(fd)
            named = os.lstat(name)
            if name in names or not os.path.isabs(name) or not stat.S_ISCHR(named.st_mode):
                continue
            if named.st_rdev != held.st_rdev or dev not in ancestry(name)[1:]:
                continue
        except OSError:
            continue
        names.append(name)
    return names
