"""Policy C: OS capabilities for staging, exact grants for publication.

This cold-path component does not mint hardware attestations. Its caller is the
trusted authority boundary; untrusted installers never receive a broker handle.
All clock and epoch observations are injected by that caller.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
import ctypes
from dataclasses import dataclass
from functools import lru_cache
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import subprocess
import threading
from typing import Iterator

from blake3 import blake3


class InstallPolicyError(RuntimeError):
    """Terminal failure of the installation grant; no permissive fallback."""


class InstallAuthority:
    """Serialize revocation and publication at the same authority frontier."""

    def __init__(self, epoch: int, logical_tick: Callable[[], int]) -> None:
        if epoch < 0:
            raise InstallPolicyError("Negative authority epoch")
        self._epoch = epoch
        self._clock = logical_tick
        self._last_tick = -1
        self._lock = threading.RLock()

    def observe(self) -> tuple[int, int]:
        with self._lock:
            tick = self._clock()
            if tick < self._last_tick or tick < 0:
                raise InstallPolicyError("Logical clock rollback")
            self._last_tick = tick
            return self._epoch, tick

    def revoke(self, new_epoch: int) -> None:
        with self._lock:
            if new_epoch <= self._epoch:
                raise InstallPolicyError("Revocation epochs must advance")
            self._epoch = new_epoch


DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
MAX_BYTES = 64 * 1024 * 1024
MAX_FILES = 4096


@contextmanager
def open_directory(path: Path) -> Iterator[int]:
    """Walk from a root descriptor; reject symlinks in every component."""
    absolute = path.absolute()
    descriptor = os.open(absolute.anchor, DIRECTORY_FLAGS)
    try:
        for component in absolute.parts[1:]:
            child = os.open(component, DIRECTORY_FLAGS, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor
    finally:
        os.close(descriptor)


def _identity(descriptor: int) -> tuple[int, int]:
    info = os.fstat(descriptor)
    return info.st_dev, info.st_ino


def _relative(path: str) -> tuple[str, ...]:
    parts = PurePosixPath(path).parts
    if not parts or path != "/".join(parts) or any(p in {".", "..", "/"} for p in parts) or "\0" in path:
        raise InstallPolicyError("Invalid relative effect path")
    return parts


@dataclass(frozen=True)
class RuntimeGrant:
    node: Path
    npm_cli: Path
    read_files: tuple[Path, ...]
    read_trees: tuple[Path, ...]


@lru_cache(maxsize=8)
def node_runtime(node: str, npm: str) -> RuntimeGrant:
    """Inspect the installed runtime; realpath is only for OS library aliases."""
    if platform.system() != "Darwin":
        raise InstallPolicyError("Policy C requires the real macOS sandbox")
    executable, cli = Path(os.path.realpath(node)), Path(os.path.realpath(npm))
    libraries: set[Path] = {executable}
    pending = [executable]
    seen: set[Path] = set()
    while pending:
        binary = pending.pop()
        if binary in seen:
            continue
        seen.add(binary)
        listing = subprocess.check_output(["/usr/bin/otool", "-L", str(binary)], text=True)
        for line in listing.splitlines()[1:]:
            name = line.strip().split(" (", 1)[0]
            if name.startswith("@rpath/"):
                leaf = name.removeprefix("@rpath/")
                candidates = [binary.parent / leaf, executable.parent.parent / "lib" / leaf]
                found = next((p for p in candidates if p.is_file()), None)
                if found is None:
                    raise InstallPolicyError(f"Unresolved runtime library: {name}")
                name = str(found)
            elif name.startswith("@loader_path/"):
                name = str(binary.parent / name.removeprefix("@loader_path/"))
            if name.startswith("/") and not name.startswith(("/System/", "/usr/lib/")):
                library = Path(os.path.realpath(name))
                if library not in libraries:
                    libraries.add(library)
                    pending.append(library)
    libraries.update(Path(p) for p in ("/", "/bin/sh", "/bin/bash", "/dev/null", "/dev/urandom", "/dev/random"))
    return RuntimeGrant(
        executable,
        cli,
        tuple(sorted(libraries)),
        (
            Path("/System/Library"),
            Path(os.path.realpath("/System/Cryptexes/OS/System/Library")),
            Path("/usr/lib"),
            cli.parents[1],
        ),
    )


def confinement_profile(stage: Path, runtime: RuntimeGrant) -> str:
    """Every permitted kernel effect has an explicit capability scope.

    Metadata and executable mappings are runtime capabilities. Reading the root
    directory itself is needed by dyld; it does not grant recursive file access.
    Network, IPC, UI control and writes outside staging have no grants.
    """
    with open_directory(stage) as descriptor:
        if os.fstat(descriptor).st_uid != os.getuid():
            raise InstallPolicyError("Staging must belong to the broker user")

    def quote(path: Path) -> str:
        return json.dumps(str(path), ensure_ascii=True)

    rules = [
        "(version 1)",
        "(deny default)",
        "(allow file-read-metadata)",
        "(allow file-map-executable)",
        "(allow process-fork)",
        "(allow sysctl-read)",
        "(allow signal (target self))",
    ]
    for path in runtime.read_files:
        rules.append(f"(allow file-read* (literal {quote(path)}))")
    for path in runtime.read_trees:
        rules.append(f"(allow file-read* (subpath {quote(path)}))")
    for path in (runtime.node, Path("/bin/sh"), Path("/bin/bash")):
        rules.append(f"(allow process-exec (literal {quote(path)}))")
    rules.append(f"(allow file-read* file-write* (subpath {quote(stage.absolute())}))")
    rules.append('(allow file-write* (literal "/dev/null"))')
    return "\n".join(rules) + "\n"


@dataclass(frozen=True)
class InstallScope:
    grant_id: str
    artifact_blake3: str
    stage: Path
    destination_parent: Path
    destination_name: str
    output_roots: tuple[str, ...]
    authority_epoch: int
    expires_tick: int

    def validate(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,150}", self.grant_id):
            raise InstallPolicyError("Invalid grant identity")
        if not re.fullmatch(r"[0-9a-f]{64}", self.artifact_blake3):
            raise InstallPolicyError("Missing admitted artifact digest")
        if _relative(self.destination_name) != (self.destination_name,):
            raise InstallPolicyError("Destination must be a single directory name")
        if not self.output_roots or self.authority_epoch < 0 or self.expires_tick < 0:
            raise InstallPolicyError("An explicit output/epoch/expiry grant is required")
        for root in self.output_roots:
            _relative(root)
        a, b = self.stage.absolute(), self.destination_parent.absolute()
        if a == b or a in b.parents or b in a.parents:
            raise InstallPolicyError("Staging and publication scopes must be disjoint")


@dataclass(frozen=True)
class FileEffect:
    path: str
    digest: str
    mode: int
    content: bytes


@dataclass(frozen=True)
class InstallPermit:
    scope: InstallScope
    files: tuple[FileEffect, ...]
    directories: tuple[str, ...]
    manifest_blake3: str
    destination_identity: tuple[int, int]


@dataclass(frozen=True)
class InstallReceipt:
    grant_id: str
    manifest_blake3: str
    committed_files: tuple[tuple[str, str], ...]
    committed_directories: tuple[str, ...]
    logical_tick: int


def _snapshot(stage: Path, roots: tuple[str, ...]) -> tuple[tuple[FileEffect, ...], tuple[str, ...]]:
    files: list[FileEffect] = []
    directories: list[str] = []
    total = 0

    def visit(parent: int, name: str, relative: str) -> None:
        nonlocal total
        _relative(relative)
        descriptor = os.open(name, FILE_FLAGS, dir_fd=parent)
        try:
            info = os.fstat(descriptor)
            if stat.S_ISDIR(info.st_mode):
                directories.append(relative)
                with os.scandir(descriptor) as entries:
                    names = sorted(entry.name for entry in entries)
                for child in names:
                    visit(descriptor, child, f"{relative}/{child}")
            elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                chunks = bytearray()
                while chunk := os.read(descriptor, min(65536, MAX_BYTES + 1 - total)):
                    chunks.extend(chunk)
                    total += len(chunk)
                    if total > MAX_BYTES:
                        raise InstallPolicyError("Installation snapshot exceeds byte budget")
                content = bytes(chunks)
                mode = 0o755 if info.st_mode & 0o111 else 0o644
                files.append(FileEffect(relative, blake3(content).hexdigest(), mode, content))
            else:
                raise InstallPolicyError("Only private directories and regular unlinked files may be published")
            if len(files) + len(directories) > MAX_FILES:
                raise InstallPolicyError("Installation snapshot exceeds path budget")
        finally:
            os.close(descriptor)

    try:
        with open_directory(stage) as descriptor:
            for root in roots:
                parts = _relative(root)
                if len(parts) != 1:
                    raise InstallPolicyError("Output roots must be direct staging children")
                visit(descriptor, root, root)
    except OSError as error:
        raise InstallPolicyError("Unsafe or missing staged output") from error
    return tuple(files), tuple(directories)


def _manifest(files: tuple[FileEffect, ...], directories: tuple[str, ...]) -> str:
    value = [list(directories), [(f.path, f.digest, f.mode) for f in files]]
    return blake3(json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _rename_exclusive(source_fd: int, source: str, destination_fd: int, destination: str) -> None:
    if platform.system() != "Darwin":
        raise InstallPolicyError("Exclusive publication requires macOS renameatx_np")
    libc = ctypes.CDLL(None, use_errno=True)
    rename = libc.renameatx_np
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(source_fd, os.fsencode(source), destination_fd, os.fsencode(destination), 0x4):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


class InstallBroker:
    """Trusted, local, cold-path authority. Never expose this object to scripts."""

    def __init__(self, state: Path, authority: InstallAuthority) -> None:
        self.state, self.authority = state.absolute(), authority
        with open_directory(self.state) as descriptor:
            info = os.fstat(descriptor)
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise InstallPolicyError("Broker state must be private (0700)")
        self._issued: dict[str, InstallPermit] = {}
        self._lock = authority._lock

    def _guard(self, scope: InstallScope) -> int:
        scope.validate()
        epoch, tick = self.authority.observe()
        if scope.authority_epoch != epoch or tick > scope.expires_tick:
            raise InstallPolicyError("Installation authority is revoked or expired")
        return tick

    def authorize(self, scope: InstallScope, admitted_archive: bytes) -> InstallPermit:
        with self._lock:
            self._guard(scope)
            if blake3(admitted_archive).hexdigest() != scope.artifact_blake3:
                raise InstallPolicyError("Artifact admission digest mismatch")
            if self.state == scope.stage.absolute() or scope.stage.absolute() in self.state.parents:
                raise InstallPolicyError("Broker state cannot be inside installer staging")
            files, directories = _snapshot(scope.stage, scope.output_roots)
            with open_directory(scope.destination_parent) as descriptor:
                destination = _identity(descriptor)
            permit = InstallPermit(scope, files, directories, _manifest(files, directories), destination)
            if scope.grant_id in self._issued:
                raise InstallPolicyError("Grant already issued")
            self._issued[scope.grant_id] = permit
            return permit

    def _materialize_outputs(self, permit: InstallPermit, pending_path: Path) -> None:
        for directory in sorted(permit.directories, key=lambda p: (p.count("/"), p)):
            self._guard(permit.scope)
            parts = _relative(directory)
            with open_directory(pending_path.joinpath(*parts[:-1])) as parent_fd:
                os.mkdir(parts[-1], 0o755, dir_fd=parent_fd)
                os.fsync(parent_fd)
        for effect in permit.files:
            self._guard(permit.scope)
            parts = _relative(effect.path)
            with open_directory(pending_path.joinpath(*parts[:-1])) as parent_fd:
                descriptor = os.open(
                    parts[-1],
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    effect.mode,
                    dir_fd=parent_fd,
                )
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(effect.content)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.fsync(parent_fd)

    def commit(self, permit: InstallPermit) -> InstallReceipt:
        with self._lock:
            scope = permit.scope
            self._guard(scope)
            if self._issued.get(scope.grant_id) is not permit:
                raise InstallPolicyError("Missing or forged effect authorization")
            if _manifest(permit.files, permit.directories) != permit.manifest_blake3:
                raise InstallPolicyError("Effect manifest mismatch")
            for effect in permit.files:
                if blake3(effect.content).hexdigest() != effect.digest:
                    raise InstallPolicyError("Authorized effect content was modified")
            pending = f"pending-{scope.grant_id}"
            with open_directory(self.state) as broker_fd, open_directory(scope.destination_parent) as destination_fd:
                if _identity(destination_fd) != permit.destination_identity:
                    raise InstallPolicyError("Publication directory identity changed")
                # Durable consume-before-effect: crashes cannot replay a grant.
                try:
                    consumed = os.open(
                        f"consumed-{scope.grant_id}",
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        0o600,
                        dir_fd=broker_fd,
                    )
                except FileExistsError as error:
                    raise InstallPolicyError("Installation grant replay") from error
                with os.fdopen(consumed, "wb") as stream:
                    stream.write(permit.manifest_blake3.encode())
                    stream.flush()
                    os.fsync(stream.fileno())
                os.fsync(broker_fd)
                try:
                    self._guard(scope)
                    os.mkdir(pending, 0o700, dir_fd=broker_fd)
                    pending_path = self.state / pending
                    self._materialize_outputs(permit, pending_path)
                    published_tick = self._guard(scope)
                    _rename_exclusive(broker_fd, pending, destination_fd, scope.destination_name)
                    os.fsync(broker_fd)
                    os.fsync(destination_fd)
                except (OSError, InstallPolicyError):
                    shutil.rmtree(self.state / pending, ignore_errors=True)
                    raise
            self._issued.pop(scope.grant_id)
            return InstallReceipt(
                scope.grant_id,
                permit.manifest_blake3,
                tuple((f.path, f.digest) for f in permit.files),
                permit.directories,
                published_tick,
            )
