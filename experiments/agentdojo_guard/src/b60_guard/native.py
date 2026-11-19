"""Native Ring-0 Rust broker loader and commit-only capability wrapper."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from functools import lru_cache
from importlib.machinery import ExtensionFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Protocol


class NativeBroker(Protocol):
    """Protocol exposed by ``_babylon60_mcp.McpBroker``."""

    def revision(self) -> int: ...
    def update_policy(self, feature: str, global_policy: str) -> None: ...
    def discover(self, name: str, digest: bytes, effect: str, scope: str | None = None) -> None: ...
    def authorize(self, name: str, digest: bytes, effect: str, scope: str | None = None) -> None: ...
    def revoke(self, name: str) -> None: ...
    def issue(
        self,
        name: str,
        digest: bytes,
        effect: str,
        args: bytes,
        scope: str | None = None,
        resource: str | None = None,
    ) -> object: ...
    def validate(
        self,
        token: object,
        name: str,
        digest: bytes,
        effect: str,
        args: bytes,
        scope: str | None = None,
        resource: str | None = None,
    ) -> None: ...
    def commit_once(
        self,
        token: object,
        name: str,
        digest: bytes,
        effect: str,
        args: bytes,
        scope: str | None = None,
        resource: str | None = None,
    ) -> bytes: ...


class CommitOnlyBroker:
    """Least-privilege broker handle exposing only ``commit_once``.

    Holds only the bound ``commit_once`` callable rather than a Python attribute
    referencing ``McpBroker``, so callers receive no ``issue``/``authorize`` API.
    """

    __slots__ = ("_commit_once",)

    def __init__(self, commit_once_fn: Callable[..., bytes]) -> None:
        self._commit_once = commit_once_fn

    def commit_once(
        self,
        token: object,
        name: str,
        digest: bytes,
        effect: str,
        args: bytes,
        scope: str | None = None,
        resource: str | None = None,
    ) -> bytes:
        return self._commit_once(token, name, digest, effect, args, scope, resource)


def _repo_root() -> Path:
    # INV_C5_PATH_SYMLINK_CONFINEMENT: keep logical path hierarchy via absolute().
    return Path(__file__).absolute().parents[4]


def _default_library_name() -> str:
    if sys.platform == "darwin":
        return "libbabylon60.dylib"
    if sys.platform == "win32":
        return "babylon60.dll"
    return "libbabylon60.so"


def resolve_native_library_path() -> Path:
    """Locate the compiled ``_babylon60_mcp`` cdylib built with ``--features python``."""
    env_val = os.environ.get("BABYLON60_TEST_CAPABILITY_LIBRARY") or os.environ.get("BABYLON60_DYLIB_PATH")
    if env_val:
        path = Path(env_val).absolute()
        if not path.is_file():
            raise FileNotFoundError(f"Configured native broker library not found: {path}")
        return path

    lib_name = _default_library_name()
    candidates = [
        _repo_root() / "target" / "py" / "debug" / lib_name,
        _repo_root() / "target" / "py" / "release" / lib_name,
        _repo_root() / "target" / "debug" / lib_name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "Compiled _babylon60_mcp library not found. Build with: "
        "cargo build --locked -p babylon60_root --lib --features python --target-dir target/py"
    )


@lru_cache(maxsize=2)
def load_native_module(library_path: Path | None = None) -> ModuleType:
    """Load the ``_babylon60_mcp`` PyO3 module from the native cdylib."""
    target = (library_path or resolve_native_library_path()).absolute()
    loader = ExtensionFileLoader("_babylon60_mcp", str(target))
    spec = spec_from_file_location("_babylon60_mcp", target, loader=loader)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot build extension spec for {target}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def blake3_bytes(data: bytes) -> bytes:
    """Return the canonical 32-byte Ring-0 BLAKE3 digest."""
    mod = load_native_module()
    return bytes(mod.blake3_digest(data))


def blake3_hex(data: bytes) -> str:
    """Return the hex-encoded Ring-0 BLAKE3 digest."""
    return blake3_bytes(data).hex()


def new_native_broker(library_path: Path | None = None) -> NativeBroker:
    """Instantiate a fresh, isolated Rust ``McpBroker``."""
    mod = load_native_module(library_path)
    return mod.McpBroker()
