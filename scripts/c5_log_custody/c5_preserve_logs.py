#!/usr/bin/env python3
"""Preserve explicit, minimized evidence receipts; never copy session contents."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import time
import uuid

REPO_ROOT = Path(__file__).absolute().parent.parent.parent
MAX_SOURCE_BYTES = 16 * 1024 * 1024
MAX_RECEIPTS = 100
MAX_RETENTION_DAYS = 30


def _private_directory(path: Path) -> int:
    """Walk each component using directory descriptors, rejecting symlinks."""
    absolute = path.absolute()
    fd = os.open(absolute.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in absolute.parts[1:]:
            if part == "..":
                raise ValueError("Parent traversal is not allowed")
            try:
                os.mkdir(part, 0o700, dir_fd=fd)
            except FileExistsError:
                pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise PermissionError("Evidence destination must be private (0700) and user-owned")
        return fd
    except BaseException:
        os.close(fd)
        raise


def harvest_provider_logs(
    provider_key: str,
    selected_files: list[Path] | None = None,
    *,
    destination: Path | None = None,
    retention_days: int = 7,
) -> list[str]:
    """Store bounded digest/size receipts, never paths, messages or reasoning."""
    if provider_key not in {"agent", "claude"}:
        raise ValueError("Unknown provider")
    if not selected_files:
        raise ValueError("Select evidence files explicitly; global collection is disabled")
    if len(selected_files) > MAX_RECEIPTS or not 1 <= retention_days <= MAX_RETENTION_DAYS:
        raise ValueError("Evidence selection or retention exceeds its bound")
    target = destination or Path.home() / ".babylon60" / "private_evidence"
    # This is a security containment check, not discovery of the logical repo root.
    if target.resolve().is_relative_to(REPO_ROOT.resolve()):
        raise ValueError("Evidence destination must be outside the repository")
    receipts = []
    for source in selected_files:
        fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_SOURCE_BYTES:
                raise ValueError("Evidence source must be a bounded regular file")
            data = stream.read(MAX_SOURCE_BYTES + 1)
            if len(data) > MAX_SOURCE_BYTES:
                raise ValueError("Evidence source exceeded size bound")
        receipts.append({"provider": provider_key, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    directory = _private_directory(target)
    try:
        now = time.time()
        # Only this tool's UUID receipt namespace is eligible for retention cleanup.
        existing = []
        for name in os.listdir(directory):
            if not name.startswith("receipt-") or not name.endswith(".json"):
                continue
            try:
                uuid.UUID(name[8:-5])
            except ValueError:
                continue
            info = os.stat(name, dir_fd=directory, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("Unexpected entry in receipt namespace")
            if info.st_mtime < now - retention_days * 86400:
                os.unlink(name, dir_fd=directory)
            else:
                existing.append((info.st_mtime, name))
        for _, name in sorted(existing)[: max(0, len(existing) + len(receipts) - MAX_RECEIPTS)]:
            os.unlink(name, dir_fd=directory)
        names = []
        for receipt in receipts:
            name = f"receipt-{uuid.uuid4()}.json"
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(receipt, stream)
            names.append(name)
        return names
    finally:
        os.close(directory)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["agent", "claude"], required=True)
    parser.add_argument("--file", type=Path, action="append", required=True, dest="selected_files")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--retention-days", type=int, default=7)
    args = parser.parse_args()
    names = harvest_provider_logs(
        args.provider, args.selected_files, destination=args.destination, retention_days=args.retention_days
    )
    print(f"Stored {len(names)} minimized evidence receipts")


if __name__ == "__main__":
    main()
