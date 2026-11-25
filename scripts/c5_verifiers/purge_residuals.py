#!/usr/bin/env python3
"""Remove only recognized current-Python bytecode in __pycache__.

Directories, Git metadata, databases, locks and unknown artifacts are preserved.
This scoped cleanup neither certifies a repository nor invokes other verifiers.
Descriptor-relative access does not make stat/unlink atomic against other writers.
"""
from __future__ import annotations

import argparse
from importlib.util import MAGIC_NUMBER
import json
import os
from pathlib import Path
import stat
from typing import TypedDict

REPO_ROOT = Path(__file__).absolute().parent.parent.parent
MAX_DEPTH = 64
MAX_ENTRIES = 10000
EXCLUDED_NAMES = frozenset({'.git', '.hg', '.svn', '.venv', 'venv', 'node_modules',
                            'target', 'dist', 'build', 'scratch', '.pytest_cache', '.ruff_cache', '.mypy_cache'})


class CleanupEntry(TypedDict):
    path: str
    reason: str


class CleanupReport(TypedDict):
    schema: str
    root: str
    scope: str
    status: str
    verification: str
    observed_entries: int
    deleted: list[CleanupEntry]
    preserved: list[CleanupEntry]
    errors: list[CleanupEntry]


def _record(report: CleanupReport, bucket: str, parts: tuple[str, ...], reason: str) -> None:
    entry = CleanupEntry(path='/'.join(parts) or '.', reason=reason)
    if bucket == 'deleted':
        report['deleted'].append(entry)
    elif bucket == 'preserved':
        report['preserved'].append(entry)
    else:
        report['errors'].append(entry)


def _snapshot(value: os.stat_result) -> tuple[int, ...]:
    return (value.st_dev, value.st_ino, value.st_mode, value.st_uid, value.st_nlink,
            value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def _git_metadata(directory: int) -> bool:
    def present(name: str) -> bool:
        try:
            os.stat(name, dir_fd=directory, follow_symlinks=False)
            return True
        except FileNotFoundError:
            return False
    return present('HEAD') and ((present('objects') and present('refs'))
                                or (present('commondir') and present('gitdir')))


def _protected_name(name: str) -> bool:
    lower = name.casefold()
    return ('.lock' in lower or '.db' in lower or '.sqlite' in lower or '.journal' in lower
            or lower.endswith(('-wal', '-shm', '-journal')))


def _delete_bytecode(directory: int, name: str, parts: tuple[str, ...], before: os.stat_result,
                     report: CleanupReport) -> None:
    if before.st_nlink != 1 or before.st_uid != os.getuid():
        _record(report, 'preserved', parts, 'SHARED_OR_FOREIGN_FILE')
        return
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    try:
        opened = os.fstat(descriptor)
        if _snapshot(before) != _snapshot(opened):
            _record(report, 'preserved', parts, 'IDENTITY_CHANGED')
            return
        header = os.read(descriptor, 17)
        if (len(header) < 17 or header[:4] != MAGIC_NUMBER
                or int.from_bytes(header[4:8], 'little') not in (0, 1, 3)):
            _record(report, 'preserved', parts, 'UNRECOGNIZED_BYTECODE_HEADER')
            return
        current = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if _snapshot(opened) != _snapshot(os.fstat(descriptor)) or _snapshot(opened) != _snapshot(current):
            _record(report, 'preserved', parts, 'IDENTITY_CHANGED')
            return
        os.unlink(name, dir_fd=directory)
        _record(report, 'deleted', parts, 'CURRENT_PYTHON_BYTECODE_HEADER')
    finally:
        os.close(descriptor)


def _scan(directory: int, parts: tuple[str, ...], report: CleanupReport, device: int) -> None:
    if len(parts) > MAX_DEPTH:
        _record(report, 'errors', parts, 'DEPTH_LIMIT')
        return
    try:
        if _git_metadata(directory):
            _record(report, 'preserved', parts, 'GIT_METADATA_SUBTREE')
            return
        with os.scandir(directory) as entries:
            for entry in entries:
                if report['observed_entries'] >= MAX_ENTRIES:
                    _record(report, 'errors', parts, 'ENTRY_LIMIT')
                    return
                report['observed_entries'] += 1
                child_parts = (*parts, entry.name)
                try:
                    if entry.name in EXCLUDED_NAMES:
                        _record(report, 'preserved', child_parts, 'EXCLUDED_SUBTREE_OR_METADATA_ENTRY')
                        continue
                    if _protected_name(entry.name):
                        _record(report, 'preserved', child_parts, 'DATABASE_OR_LOCK_NAME')
                        continue
                    metadata = os.stat(entry.name, dir_fd=directory, follow_symlinks=False)
                    if stat.S_ISDIR(metadata.st_mode):
                        child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                        try:
                            current = os.stat(entry.name, dir_fd=directory, follow_symlinks=False)
                            if not os.path.samestat(metadata, os.fstat(child)) or not os.path.samestat(metadata, current):
                                _record(report, 'preserved', child_parts, 'DIRECTORY_IDENTITY_CHANGED')
                            elif metadata.st_dev != device:
                                _record(report, 'preserved', child_parts, 'OTHER_DEVICE')
                            else:
                                _record(report, 'preserved', child_parts, 'DIRECTORIES_NOT_REMOVED')
                                _scan(child, child_parts, report, device)
                        finally:
                            os.close(child)
                    elif stat.S_ISREG(metadata.st_mode) and '__pycache__' in parts and entry.name.endswith('.pyc'):
                        _delete_bytecode(directory, entry.name, child_parts, metadata, report)
                    else:
                        _record(report, 'preserved', child_parts, 'OUTSIDE_RECOGNIZED_BYTECODE_SCOPE')
                except (OSError, NotImplementedError) as error:
                    _record(report, 'errors', child_parts, type(error).__name__)
    except (OSError, NotImplementedError) as error:
        _record(report, 'errors', parts, type(error).__name__)


def purge_repository_residuals() -> CleanupReport:
    """Return observed effects only; never delete database/lock targets or directories.

    Header recognition is not proof of origin or bytecode correctness. Another
    writer can still replace a pathname after the final check and before unlink.
    """
    root = REPO_ROOT.absolute()
    report = CleanupReport(schema='babylon60.residual-cleanup.v2', root=str(root),
                           scope='RECOGNIZED_CURRENT_PYTHON_BYTECODE_IN_PYCACHE', status='RUNNING',
                           verification='NOT_REQUESTED', observed_entries=0, deleted=[], preserved=[], errors=[])
    try:
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            _scan(directory, (), report, os.fstat(directory).st_dev)
        finally:
            os.close(directory)
    except (OSError, AttributeError, NotImplementedError) as error:
        _record(report, 'errors', (), type(error).__name__)
    report['status'] = 'ERROR' if report['errors'] else 'SCOPED_OK'
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='Print scoped cleanup observations as JSON')
    args = parser.parse_args(argv)
    report = purge_repository_residuals()
    if args.json:
        print(json.dumps(report, sort_keys=True, indent=2))
    else:
        print(f"Scoped bytecode cleanup: {report['status']}")
        print(f"Deleted files: {len(report['deleted'])}; preserved entries/subtrees: {len(report['preserved'])}; errors: {len(report['errors'])}")
        print('Directories, Git metadata, database/lock names and unknown cache data are outside deletion scope.')
        print('No repository certification or other verifier was requested.')
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
