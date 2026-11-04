"""Conservative workspace cache cleanup; SQLite state is never purged."""

import importlib.util
import logging
import os
import stat
from pathlib import Path

logger = logging.getLogger("CORTEX.ITERA")


def _unlink_identified_bytecode(name: str, directory_fd: int) -> bool:
    """Unlink one regular, magic-verified, unreplaced .pyc entry; return True if removed."""
    fd = None
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or os.read(fd, 4) != importlib.util.MAGIC_NUMBER:
            return False
        current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if (info.st_dev, info.st_ino) != (current.st_dev, current.st_ino):
            return False
        os.unlink(name, dir_fd=directory_fd)
        return True
    except OSError:
        # Uninspectable/replaced objects remain in place.
        return False
    finally:
        if fd is not None:
            os.close(fd)


def run_auto_purge() -> None:
    """Remove identified Python bytecode files under cwd; leave directories intact."""
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "fwalk"):
        raise RuntimeError("Cache cleanup requires descriptor-relative O_NOFOLLOW support")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    root_fd = os.open(Path.cwd(), flags)
    removed = 0
    try:
        for relative, directories, files, directory_fd in os.fwalk(
            ".", topdown=True, follow_symlinks=False, dir_fd=root_fd
        ):
            directories[:] = [name for name in directories if name not in {".git", ".venv", "node_modules"}]
            if "__pycache__" not in Path(relative).parts:
                continue
            for name in files:
                if name.endswith(".pyc") and _unlink_identified_bytecode(name, directory_fd):
                    removed += 1
    finally:
        os.close(root_fd)
    logger.info("Removed %d identified bytecode files; SQLite and directories preserved", removed)
