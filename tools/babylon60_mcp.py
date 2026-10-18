#!/usr/bin/env python3
"""Local stdio tools for a trusted BABYLON-60 checkout; not an OS sandbox.

Requires Python >=3.11, fastmcp and blake3. See docs/03_guides/guide_kernel_mcp.md.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import selectors
import shutil
import signal
import sqlite3
import stat
import subprocess
import sys
import threading
import time
from typing import TYPE_CHECKING, Callable, Literal

from blake3 import blake3

if TYPE_CHECKING:
    from fastmcp import FastMCP


SOURCE_LIMIT = 1024 * 1024
DATABASE_LIMIT = 16 * 1024 * 1024
OUTPUT_LIMIT = 128 * 1024
SOURCE_ROOTS = frozenset({"src", "crates", "00_ABZU_KERNEL", "01_KISH_ENGINE", "proof", "tests"})
EXCLUDED = frozenset({"target", "build", "dist", "scratch", "node_modules", "__pycache__"})
SUFFIXES = frozenset({".rs", ".lean", ".sql", ".toml", ".py"})
PATCH_SUFFIXES = SUFFIXES - {".toml"}
FILTER = re.compile(r"[A-Za-z_][A-Za-z0-9_:]{0,159}\Z")
LEAN_TOKEN = re.compile(r"\b(?:sorry|admit|sorryAx)\b")
PASSED = re.compile(r"test result: ok\. ([0-9]+) passed;")


@dataclass
class CommandResult:
    argv: list[str]
    exit_code: int | None
    stdout: str
    stderr: str
    status: str


def run_command(
    argv: list[str], cwd: Path, *, timeout: float = 180, extra_env: dict[str, str] | None = None
) -> CommandResult:
    """Bound combined output and elapsed time; terminate the subprocess group."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key
        in {
            "PATH",
            "HOME",
            "TMPDIR",
            "LANG",
            "LC_ALL",
            "CARGO_HOME",
            "RUSTUP_HOME",
            "ELAN_HOME",
        }
    }
    env.update(
        {
            "CARGO_NET_OFFLINE": "true",
            "CARGO_TERM_COLOR": "never",
            "GIT_TERMINAL_PROMPT": "0",
            "ELAN_NO_UPDATE_CHECK": "1",
        }
    )
    env.update(extra_env or {})
    try:
        proc = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
    except OSError as error:
        return CommandResult(argv, None, "", str(error), "unavailable")
    assert proc.stdout is not None and proc.stderr is not None
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    status = "completed"
    deadline = time.monotonic() + timeout
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
            selector.register(proc.stderr, selectors.EVENT_READ, "stderr")
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    status = "timeout"
                    break
                for key, _ in selector.select(min(remaining, 0.1)):
                    chunk = os.read(key.fd, 8192)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    room = OUTPUT_LIMIT - sum(map(len, buffers.values()))
                    buffers[key.data].extend(chunk[:room])
                    if len(chunk) > room:
                        status = "output_limit"
                        break
                if status != "completed":
                    break
            if status == "completed":
                try:
                    proc.wait(timeout=max(0.001, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    status = "timeout"
    finally:
        # Also stop descendants that outlive a successful parent.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()
        proc.stdout.close()
        proc.stderr.close()
    if status == "completed" and proc.returncode != 0:
        status = "failed"
    return CommandResult(
        argv,
        proc.returncode,
        buffers["stdout"].decode("utf-8", errors="replace"),
        buffers["stderr"].decode("utf-8", errors="replace"),
        status,
    )


def lean_code(text: str) -> str:
    """Mask nested comments and strings, preserving line numbers for a preflight.

    This is a lexical aid, not an axiom audit or a Lean parser.
    """
    out: list[str] = []
    i = depth = 0
    quoted = False
    while i < len(text):
        pair = text[i : i + 2]
        char = text[i]
        if depth:
            if pair == "/-":
                depth += 1
                out.extend("  ")
                i += 2
                continue
            if pair == "-/":
                depth -= 1
                out.extend("  ")
                i += 2
                continue
            out.append("\n" if char == "\n" else " ")
        elif quoted:
            if char == "\\" and i + 1 < len(text):
                out.extend("  ")
                i += 2
                continue
            if char == '"':
                quoted = False
            out.append("\n" if char == "\n" else " ")
        elif pair == "/-":
            depth = 1
            out.extend("  ")
            i += 2
            continue
        elif pair == "--":
            end = text.find("\n", i)
            end = len(text) if end == -1 else end
            out.extend(" " * (end - i))
            i = end
            continue
        elif char == '"':
            quoted = True
            out.append(" ")
        else:
            out.append(char)
        i += 1
    return "".join(out)


class KernelHarness:
    """Host-selected root and capabilities; clients cannot enable capabilities."""

    def __init__(self, root: Path, *, allow_patches: bool = False, allow_execution: bool = False) -> None:
        self.root = root.expanduser().absolute()
        self.allow_patches = allow_patches
        self.allow_execution = allow_execution
        self._lock = threading.Lock()
        self._root_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)

    def close(self) -> None:
        if self._root_fd >= 0:
            os.close(self._root_fd)
            self._root_fd = -1

    @contextmanager
    def _operation(self) -> Iterator[None]:
        if not self._lock.acquire(blocking=False):
            raise ValueError("Another harness operation is running; retry after it completes.")
        try:
            if self._root_fd < 0:
                raise ValueError("Harness is closed.")
            yield
        finally:
            self._lock.release()

    def _parts(self, rel_path: str, *, database: bool = False) -> list[str]:
        parts = rel_path.split("/")
        if (
            not rel_path
            or len(rel_path) > 1024
            or "\\" in rel_path
            or any(ord(c) < 32 for c in rel_path)
            or any(not p or p.startswith(".") or p in EXCLUDED for p in parts)
        ):
            raise ValueError("Use a relative path without hidden, generated or traversal components.")
        if database:
            if parts[0] not in {"proof", "reports", "tests"} or Path(parts[-1]).suffix not in {
                ".db",
                ".sqlite",
                ".sqlite3",
            }:
                raise ValueError("Use an offline SQLite export under proof/, reports/ or tests/.")
        elif rel_path not in {"Cargo.toml", "pyproject.toml"}:
            if parts[0] not in SOURCE_ROOTS or len(parts) < 2 or Path(parts[-1]).suffix not in SUFFIXES:
                raise ValueError("Path is outside the allowed source roots or extensions.")
        return parts

    @contextmanager
    def _parent(self, parts: list[str]) -> Iterator[int]:
        fd = os.dup(self._root_fd)
        try:
            for part in parts[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
                os.close(fd)
                fd = child
            yield fd
        finally:
            os.close(fd)

    def _read(self, parent: int, name: str, limit: int) -> tuple[bytes, os.stat_result]:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise ValueError("Only regular files with one hard link are accepted.")
            if before.st_size > limit:
                raise ValueError("File exceeds the size limit.")
            with os.fdopen(os.dup(fd), "rb") as stream:
                data = stream.read(limit + 1)
            after = os.fstat(fd)
            if len(data) > limit or self._version(before) != self._version(after):
                raise ValueError("File changed during the read or exceeds the size limit.")
            return data, after
        finally:
            os.close(fd)

    @staticmethod
    def _version(info: os.stat_result) -> tuple[int, ...]:
        return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)

    def read_source(self, rel_path: str, start_line: int = 1, max_lines: int = 200) -> dict[str, object]:
        """Read at most 200 source lines plus the BLAKE3 revision of the full file."""
        if start_line < 1 or not 1 <= max_lines <= 200:
            raise ValueError("start_line >= 1 and 1 <= max_lines <= 200 are required.")
        with self._operation(), self._parent(self._parts(rel_path)) as parent:
            data, _ = self._read(parent, Path(rel_path).name, SOURCE_LIMIT)
        lines = data.decode("utf-8").splitlines(keepends=True)
        return {
            "path": rel_path,
            "revision": blake3(data).hexdigest(),
            "total_lines": len(lines),
            "start_line": start_line,
            "content": "".join(lines[start_line - 1 : start_line - 1 + max_lines]),
        }

    def apply_atomic_patch(
        self, rel_path: str, old_block: str, new_block: str, expected_revision: str
    ) -> dict[str, object]:
        """Replace one exact block with an expected BLAKE3 revision. Requires --allow-patches.

        Source edits only: no dependency manifests, lockfiles or runtime attestation.
        Atomic visibility does not provide CAS against an external uncooperative writer.
        """
        if not self.allow_patches:
            raise ValueError("Patching is disabled; the operator must start with --allow-patches.")
        parts = self._parts(rel_path)
        if Path(parts[-1]).suffix not in PATCH_SUFFIXES:
            raise ValueError("Dependency manifests and lockfiles cannot be patched.")
        if not old_block or old_block == new_block or max(len(old_block), len(new_block)) > SOURCE_LIMIT:
            raise ValueError("Provide a nonempty, changed and bounded exact block.")
        if not re.fullmatch(r"[0-9a-f]{64}", expected_revision):
            raise ValueError("expected_revision must be the BLAKE3 value returned by read_source.")
        with self._operation(), self._parent(parts) as parent:
            data, info = self._read(parent, parts[-1], SOURCE_LIMIT)
            if blake3(data).hexdigest() != expected_revision:
                raise ValueError("Stale revision; reread the source.")
            content = data.decode("utf-8")
            first = content.find(old_block)
            if first < 0 or content.find(old_block, first + 1) >= 0:
                raise ValueError("The old block must match exactly once.")
            replacement = content.replace(old_block, new_block, 1).encode("utf-8")
            if len(replacement) > SOURCE_LIMIT:
                raise ValueError("Patched file exceeds the size limit.")
            temporary = ".b60-patch-" + secrets.token_hex(16)
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o600, dir_fd=parent)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(replacement)
                    stream.flush()
                    os.fchmod(stream.fileno(), stat.S_IMODE(info.st_mode) & 0o777)
                    os.fsync(stream.fileno())
                current, current_info = self._read(parent, parts[-1], SOURCE_LIMIT)
                if current != data or self._version(current_info) != self._version(info):
                    raise ValueError("Source changed before replacement; patch aborted.")
                # Reopen the logical parent to detect directory replacement before commit.
                with self._parent(parts) as fresh:
                    a, b = os.fstat(parent), os.fstat(fresh)
                    if (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino):
                        raise ValueError("Source directory changed; patch aborted.")
                os.replace(temporary, parts[-1], src_dir_fd=parent, dst_dir_fd=parent)
                os.fsync(parent)
            finally:
                try:
                    os.unlink(temporary, dir_fd=parent)
                except FileNotFoundError:
                    pass
        return {
            "path": rel_path,
            "old_revision": expected_revision,
            "revision": blake3(replacement).hexdigest(),
            "status": "patched",
        }

    def _execution_root(self) -> None:
        if not self.allow_execution:
            raise ValueError(
                "Execution is disabled; the operator must start with --allow-execution in a reviewed checkout."
            )
        top = run_command(["git", "rev-parse", "--show-toplevel"], self.root, timeout=10)
        if top.status != "completed" or not os.path.samestat(os.stat(top.stdout.strip()), os.fstat(self._root_fd)):
            raise ValueError("Execution root must be the selected Git worktree root, not a subdirectory.")
        if not os.path.samestat(os.stat(self.root), os.fstat(self._root_fd)):
            raise ValueError("The selected repository root changed; restart the harness.")
        result = run_command(["git", "status", "--porcelain=v1", "--untracked-files=normal"], self.root, timeout=10)
        if result.status != "completed" or result.stdout.strip():
            raise ValueError(
                "Execution requires a clean Git worktree. Prepare a reviewed clean worktree; no lockfile changes here."
            )

    @staticmethod
    def _filter(test_filter: str) -> None:
        if test_filter and not FILTER.fullmatch(test_filter):
            raise ValueError("Use a Rust test-name substring, not command-line flags or shell syntax.")

    @staticmethod
    def _tests_result(result: CommandResult) -> dict[str, object]:
        passed = sum(int(n) for n in PASSED.findall(result.stdout))
        if result.status == "completed" and passed == 0:
            result.status = "no_tests"
        return {**asdict(result), "tests_passed": passed, "kernel_certified": False}

    def run_nemesis_and_cargo(self, test_filter: str = "") -> dict[str, object]:
        """Run the existing adversarial_nemesis target, locked/offline; zero matches fail.

        Executes trusted repository code with host permissions; NOT an OS sandbox.
        Requires --allow-execution and a clean worktree. Does not attest the kernel.
        """
        self._filter(test_filter)
        with self._operation():
            self._execution_root()
            if shutil.which("protoc") is None:
                raise ValueError("Provision protoc before compiling this workspace.")
            cmd = ["cargo", "test", "--locked", "--offline", "-p", "babylon60_root", "--test", "adversarial_nemesis"]
            if test_filter:
                cmd.append(test_filter)
            return self._tests_result(run_command([*cmd, "--", "--nocapture"], self.root))

    def audit_spsc_miri_arm64(self, model: Literal["stacked", "tree"] = "stacked") -> dict[str, object]:
        """Run existing NEMESIS SPSC tests on aarch64-apple-darwin under Miri.

        Tests exercise HardenedSpsc; this does not certify every SPSC implementation
        or physical ARM64 behavior. Native FFI/toolchain failures remain failures.
        """
        if model not in {"stacked", "tree"}:
            raise ValueError("model must be stacked or tree.")
        with self._operation():
            self._execution_root()
            if shutil.which("protoc") is None:
                raise ValueError("Provision protoc before compiling this workspace.")
            flags = "-Zmiri-strict-provenance -Zmiri-symbolic-alignment-check"
            if model == "tree":
                flags += " -Zmiri-tree-borrows"
            cmd = [
                "cargo",
                "+nightly",
                "miri",
                "test",
                "--locked",
                "--offline",
                "-p",
                "babylon60_root",
                "--target",
                "aarch64-apple-darwin",
                "--test",
                "adversarial_nemesis",
                "spsc",
                "--",
                "--nocapture",
            ]
            return self._tests_result(run_command(cmd, self.root, timeout=240, extra_env={"MIRIFLAGS": flags}))

    def verify_lean4_bijection(self) -> dict[str, object]:
        """Preflight tracked proof/lean sources and run Lake with warnings as errors.

        The historical tool name is retained; compilation is NOT a bijection proof.
        Review theorem axioms and Rust trace correspondence separately.
        """
        with self._operation():
            self._execution_root()
            listing = run_command(
                ["git", "ls-files", "-z", "--", "proof/lean/*.lean", "proof/lean/**/*.lean"], self.root, timeout=10
            )
            if listing.status != "completed":
                return asdict(listing)
            files = [name for name in listing.stdout.split("\0") if name]
            if not files:
                raise ValueError("No tracked Lean sources found in proof/lean.")
            violations: list[str] = []
            for name in files:
                with self._parent(self._parts(name)) as parent:
                    data, _ = self._read(parent, Path(name).name, SOURCE_LIMIT)
                code = lean_code(data.decode("utf-8"))
                for match in LEAN_TOKEN.finditer(code):
                    line = code[: match.start()].count("\n") + 1
                    violations.append(f"{name}:{line}:{match.group()}")
            if violations:
                return {"status": "formal_veto", "violations": violations, "bijection_verified": False}
            # A prepared manifest is required; this bridge never performs lake update.
            with self._parent(["proof", "lean", "lake-manifest.json"]) as parent:
                self._read(parent, "lake-manifest.json", SOURCE_LIMIT)
            result = run_command(["lake", "--wfail", "--no-cache", "build"], self.root / "proof" / "lean", timeout=300)
            return {
                **asdict(result),
                "scanned_files": files,
                "bijection_verified": False,
                "scope": "lexical preflight and default Lake build targets only",
            }

    def inspect_sqlite_l0_invariants(self, db_rel_path: str) -> dict[str, object]:
        """Inspect a checkpointed offline SQLite export in memory (<=16 MiB).

        Reject WAL/SHM/journal sidecars. Schemas do not certify writer transaction
        boundaries, FULL synchronization, trigger effectiveness or runtime freshness.
        """
        parts = self._parts(db_rel_path, database=True)
        with self._operation(), self._parent(parts) as parent:
            for suffix in ("-wal", "-shm", "-journal"):
                try:
                    os.stat(parts[-1] + suffix, dir_fd=parent, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                raise ValueError("Use a quiescent checkpointed export without WAL/SHM/journal sidecars.")
            data, _ = self._read(parent, parts[-1], DATABASE_LIMIT)
        if not data.startswith(b"SQLite format 3\0"):
            raise ValueError("Not a SQLite database.")
        if data[18:20] != b"\x01\x01":
            raise ValueError("Export must use rollback journal format; WAL snapshots are not supported.")
        conn = sqlite3.connect(":memory:")
        try:
            conn.deserialize(data)
            conn.execute("PRAGMA query_only=ON")
            conn.execute("PRAGMA trusted_schema=OFF")
            deadline = time.monotonic() + 2
            conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
            rows = conn.execute(
                "SELECT type, name, sql FROM sqlite_schema WHERE type IN ('table','trigger') ORDER BY type, name LIMIT 201"
            ).fetchall()
            objects = [{"type": kind, "name": name, "sql": sql} for kind, name, sql in rows[:200]]
            result: dict[str, object] = {
                "path": db_rel_path,
                "revision": blake3(data).hexdigest(),
                "objects": objects,
                "truncated": len(rows) > 200,
                "runtime_invariants": "not_verified",
                "scope": "schema inventory of offline snapshot; writer PRAGMAs and linearization unknown",
            }
            if len(json.dumps(result).encode()) > OUTPUT_LIMIT:
                raise ValueError("Schema exceeds the output limit.")
            return result
        finally:
            conn.close()

    # Normalized namespace_verb_object aliases (B1: NAME != IDENTITY)
    kernel_source_read = read_source
    kernel_patch_apply = apply_atomic_patch
    kernel_tests_run = run_nemesis_and_cargo
    kernel_miri_audit = audit_spsc_miri_arm64
    kernel_lean4_verify = verify_lean4_bijection
    kernel_sqlite_inspect = inspect_sqlite_l0_invariants


CANONICAL_TOOL_ALIASES: dict[str, str] = {
    "kernel_source_read": "read_source",
    "kernel_patch_apply": "apply_atomic_patch",
    "kernel_tests_run": "run_nemesis_and_cargo",
    "kernel_miri_audit": "audit_spsc_miri_arm64",
    "kernel_lean4_verify": "verify_lean4_bijection",
    "kernel_sqlite_inspect": "inspect_sqlite_l0_invariants",
}

LEGACY_TO_CANONICAL_TOOL: dict[str, str] = {v: k for k, v in CANONICAL_TOOL_ALIASES.items()}


def create_server(harness: KernelHarness, *, use_canonical_names: bool = False) -> FastMCP:
    from fastmcp import FastMCP
    from fastmcp.server.dependencies import get_context
    from fastmcp.tools import ToolResult
    from mcp.types import CallToolResult

    from babylon60.mcp.signature_ui import (
        SIGNATURE_SCHEMA_URI,
        SIGNATURE_TOOL_NAME,
        SIGNATURE_UI_MIME,
        SIGNATURE_UI_URI,
        read_signature_resource,
        render_signature_result,
        signature_tool_descriptor,
        supports_signature_ui,
    )

    presentation = (
        Path(__file__).absolute().parents[1] / "01_KISH_ENGINE" / "babylon60" / "presentation.md"
    ).read_text(encoding="utf-8")
    server = FastMCP("BABYLON-60-Sovereign-Harness", instructions=presentation)

    @server.resource("babylon://presentation/guide", mime_type="text/markdown")
    def presentation_guide() -> str:
        """Shared reading and presentation contract for human-facing Babylon responses."""
        return presentation

    def signature_resource_text(uri: str) -> str:
        contents = read_signature_resource(uri).get("contents")
        if not isinstance(contents, list) or len(contents) != 1:
            raise ValueError("Signature resource must contain exactly one document.")
        document = contents[0]
        if not isinstance(document, dict):
            raise ValueError("Signature resource must be a text document.")
        text = document.get("text")
        if not isinstance(text, str):
            raise ValueError("Signature resource must be a text document.")
        return text

    @server.resource(
        SIGNATURE_UI_URI,
        mime_type=SIGNATURE_UI_MIME,
        app={"csp": {"connectDomains": [], "resourceDomains": []}, "prefersBorder": False},
    )
    def signature_app() -> str:
        """Portable signature panel for clients that support MCP Apps."""
        return signature_resource_text(SIGNATURE_UI_URI)

    @server.resource(SIGNATURE_SCHEMA_URI, mime_type="application/json")
    def signature_schema() -> str:
        """Versioned input schema for evidence-backed response signatures."""
        return signature_resource_text(SIGNATURE_SCHEMA_URI)

    signature_descriptor = signature_tool_descriptor(ui_supported=True)

    @server.tool(
        name=SIGNATURE_TOOL_NAME,
        description=str(signature_descriptor["description"]),
        output_schema=None,
        annotations={"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
        app={"resourceUri": SIGNATURE_UI_URI},
    )
    def signature_render(payload: dict[str, object], format: str = "auto") -> object:
        """Render one signature using current observations supplied by the caller."""
        client_params = get_context().session.client_params
        capabilities = (
            client_params.capabilities.model_dump(by_alias=True, exclude_none=True) if client_params is not None else {}
        )
        result = render_signature_result(payload, format, ui_supported=supports_signature_ui(capabilities))
        return ToolResult.from_mcp_result(CallToolResult.model_validate(result))

    for method in (
        harness.read_source,
        harness.apply_atomic_patch,
        harness.run_nemesis_and_cargo,
        harness.audit_spsc_miri_arm64,
        harness.verify_lean4_bijection,
        harness.inspect_sqlite_l0_invariants,
    ):
        read_only = method.__name__ in {"read_source", "inspect_sqlite_l0_invariants"}
        tool_name = LEGACY_TO_CANONICAL_TOOL.get(method.__name__, method.__name__) if use_canonical_names else None
        server.tool(
            name=tool_name,
            annotations={"readOnlyHint": read_only, "destructiveHint": not read_only, "openWorldHint": not read_only},
        )(method)
    return server


LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


def validate_loopback_host(host: str) -> str:
    """Enforce loopback-only binding for HTTP/MCP transport (INV_C5_OPSEC_CALIBRATION)."""
    normalized = host.strip()
    if normalized not in LOOPBACK_HOSTS:
        raise ValueError(f"Refusing non-loopback HTTP bind address: {host!r}. Allowed: 127.0.0.1, ::1, localhost.")
    return normalized


OPENAPI_PATHS_SPEC: dict[str, object] = {
    "/tools/read_source": {
        "post": {
            "operationId": "read_source",
            "x-canonical-alias": "kernel_source_read",
            "summary": "Read up to 200 lines of a tracked source file with BLAKE3 revision.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["rel_path"],
                            "properties": {
                                "rel_path": {
                                    "type": "string",
                                    "description": (
                                        "Relative repository path under src, crates, 00_ABZU_KERNEL, 01_KISH_ENGINE, "
                                        "proof, or tests."
                                    ),
                                },
                                "start_line": {"type": "integer", "minimum": 1, "default": 1},
                                "max_lines": {"type": "integer", "minimum": 1, "maximum": 200, "default": 120},
                            },
                        }
                    }
                },
            },
            "responses": {"200": {"description": "Source slice and full-file BLAKE3 hex digest."}},
        }
    },
    "/tools/apply_atomic_patch": {
        "post": {
            "operationId": "apply_atomic_patch",
            "x-canonical-alias": "kernel_patch_apply",
            "summary": "Replace one exact block guarded by an expected BLAKE3 revision (requires --allow-patches).",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["rel_path", "old_block", "new_block", "expected_revision"],
                            "properties": {
                                "rel_path": {"type": "string"},
                                "old_block": {"type": "string"},
                                "new_block": {"type": "string"},
                                "expected_revision": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                            },
                        }
                    }
                },
            },
            "responses": {"200": {"description": "Patched file metadata and new BLAKE3 digest."}},
        }
    },
    "/tools/run_nemesis_and_cargo": {
        "post": {
            "operationId": "run_nemesis_and_cargo",
            "x-canonical-alias": "kernel_tests_run",
            "summary": "Run the adversarial_nemesis target in offline/locked mode (requires --allow-execution and clean worktree).",
            "requestBody": {
                "required": False,
                "content": {
                    "application/json": {
                        "schema": {"type": "object", "properties": {"test_filter": {"type": "string", "default": ""}}}
                    }
                },
            },
            "responses": {"200": {"description": "Cargo test execution result."}},
        }
    },
    "/tools/audit_spsc_miri_arm64": {
        "post": {
            "operationId": "audit_spsc_miri_arm64",
            "x-canonical-alias": "kernel_miri_audit",
            "summary": "Run NEMESIS SPSC tests under Miri for aarch64-apple-darwin with strict provenance.",
            "requestBody": {
                "required": False,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "model": {"type": "string", "enum": ["stacked", "tree"], "default": "stacked"}
                            },
                        }
                    }
                },
            },
            "responses": {"200": {"description": "Miri execution report."}},
        }
    },
    "/tools/verify_lean4_bijection": {
        "post": {
            "operationId": "verify_lean4_bijection",
            "x-canonical-alias": "kernel_lean4_verify",
            "summary": "Preflight tracked proof/lean sources for forbidden tokens and run Lake build with warnings as errors.",
            "responses": {"200": {"description": "Lean 4 preflight and Lake build status."}},
        }
    },
    "/tools/inspect_sqlite_l0_invariants": {
        "post": {
            "operationId": "inspect_sqlite_l0_invariants",
            "x-canonical-alias": "kernel_sqlite_inspect",
            "summary": "Inspect an offline checkpointed SQLite export in memory without WAL/SHM sidecars.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["db_rel_path"],
                            "properties": {"db_rel_path": {"type": "string"}},
                        }
                    }
                },
            },
            "responses": {"200": {"description": "In-memory SQLite schema inventory and BLAKE3 digest."}},
        }
    },
    "/tools/babylon_signature_render": {
        "post": {
            "operationId": "babylon_signature_render",
            "summary": "Render a response signature from current, sourced observations.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["payload"],
                            "properties": {
                                "payload": {"type": "object"},
                                "format": {
                                    "type": "string",
                                    "enum": ["auto", "ui", "html", "markdown", "text", "json"],
                                    "default": "auto",
                                },
                            },
                        }
                    }
                },
            },
            "responses": {"200": {"description": "Rendered signature payload."}},
        }
    },
}


def build_openapi_spec(root: Path | None = None, *, use_canonical_names: bool = False) -> dict[str, object]:
    """Synthesize the canonical OpenAPI 3.1.0 specification directly from in-memory schema."""
    del root  # Retained for signature compatibility; spec is synthesized in-memory.
    paths_out: dict[str, object] = OPENAPI_PATHS_SPEC
    if use_canonical_names:
        canonical_paths: dict[str, object] = {}
        for legacy_path, spec_obj in OPENAPI_PATHS_SPEC.items():
            if isinstance(spec_obj, dict) and isinstance(spec_obj.get("post"), dict):
                post_copy = dict(spec_obj["post"])
                legacy_op = str(post_copy.get("operationId", ""))
                alias_op = LEGACY_TO_CANONICAL_TOOL.get(legacy_op, legacy_op)
                post_copy["operationId"] = alias_op
                post_copy["x-legacy-operation-id"] = legacy_op
                canonical_paths[f"/tools/{alias_op}"] = {"post": post_copy}
            else:
                canonical_paths[legacy_path] = spec_obj
        paths_out = canonical_paths
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "BABYLON-60 Sovereign Kernel Harness API",
            "version": "1.0.0",
            "description": (
                "Esquema OpenAPI 3.1.0 isomorfo a tools/babylon60_mcp.py para acoplar ChatGPT Actions, "
                "xAI Grok Tool-Use, Gemini Extensions y clientes HTTP/OpenAPI al sustrato local de BABYLON-60."
            ),
        },
        "servers": [
            {
                "url": "http://127.0.0.1:6061",
                "description": "Local loopback bridge (INV_C5_OPSEC_CALIBRATION)",
            }
        ],
        "paths": paths_out,
    }


def create_openapi_http_server(
    harness: KernelHarness,
    host: str = "127.0.0.1",
    port: int = 6061,
    bearer_token: str = "",
    *,
    use_canonical_names: bool = False,
) -> ThreadingHTTPServer:
    """Create a loopback-confined, Bearer-authenticated OpenAPI 3.1 REST server for ChatGPT Actions / Grok."""
    bound_host = validate_loopback_host(host)
    if not bearer_token or len(bearer_token.strip()) < 16:
        raise ValueError("openapi-http requires a Bearer token of at least 16 characters.")
    expected_auth = f"Bearer {bearer_token.strip()}"
    from babylon60.mcp.signature_ui import render_signature_result

    dispatch_table: dict[str, Callable[..., dict[str, object]]] = {
        "/tools/read_source": harness.read_source,
        "/tools/apply_atomic_patch": harness.apply_atomic_patch,
        "/tools/run_nemesis_and_cargo": harness.run_nemesis_and_cargo,
        "/tools/audit_spsc_miri_arm64": harness.audit_spsc_miri_arm64,
        "/tools/verify_lean4_bijection": harness.verify_lean4_bijection,
        "/tools/inspect_sqlite_l0_invariants": harness.inspect_sqlite_l0_invariants,
        "/tools/babylon_signature_render": lambda payload, format="auto": render_signature_result(
            payload, format=format, ui_supported=False
        ),
        # Canonical functional aliases (B1: NAME != IDENTITY)
        "/tools/kernel_source_read": harness.read_source,
        "/tools/kernel_patch_apply": harness.apply_atomic_patch,
        "/tools/kernel_tests_run": harness.run_nemesis_and_cargo,
        "/tools/kernel_miri_audit": harness.audit_spsc_miri_arm64,
        "/tools/kernel_lean4_verify": harness.verify_lean4_bijection,
        "/tools/kernel_sqlite_inspect": harness.inspect_sqlite_l0_invariants,
    }
    spec_bytes = (json.dumps(build_openapi_spec(use_canonical_names=use_canonical_names), indent=2) + "\n").encode(
        "utf-8"
    )

    class KernelOpenAPIHandler(BaseHTTPRequestHandler):
        timeout = 10.0

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

        def _send_json(self, status_code: int, payload: dict[str, object]) -> None:
            body = (json.dumps(payload, indent=2) + "\n").encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _check_auth(self) -> bool:
            header = self.headers.get("Authorization", "")
            return secrets.compare_digest(header.encode("utf-8"), expected_auth.encode("utf-8"))

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/healthz":
                self._send_json(200, {"status": "ok", "topology": "MOSKV-1"})
                return
            if self.path == "/openapi.json":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(spec_bytes)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(spec_bytes)
                return
            self._send_json(404, {"error": "Not found"})

        def do_POST(self) -> None:  # noqa: N802
            if not self._check_auth():
                self._send_json(401, {"error": "Unauthorized: valid Bearer token required"})
                return
            handler_fn = dispatch_table.get(self.path)
            if handler_fn is None:
                self._send_json(404, {"error": f"Unknown tool endpoint: {self.path}"})
                return
            try:
                content_len = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send_json(400, {"error": "Invalid Content-Length"})
                return
            if content_len > 0:
                content_type = self.headers.get("Content-Type", "").strip().casefold()
                if not content_type.startswith("application/json"):
                    self._send_json(415, {"error": "Unsupported Media Type: application/json required"})
                    return
            if content_len < 0 or content_len > OUTPUT_LIMIT:
                self._send_json(413, {"error": "Payload exceeds limit"})
                return
            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                params = json.loads(raw_body.decode("utf-8")) if raw_body.strip() else {}
                if not isinstance(params, dict):
                    raise ValueError("JSON body must be an object.")
                result = handler_fn(**params)
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                self._send_json(400, {"error": str(error)})
                return
            self._send_json(200, result)

        def do_PUT(self) -> None:  # noqa: N802
            self._send_json(405, {"error": "Method Not Allowed: only GET and POST supported"})

        def do_DELETE(self) -> None:  # noqa: N802
            self._send_json(405, {"error": "Method Not Allowed: only GET and POST supported"})

        def do_PATCH(self) -> None:  # noqa: N802
            self._send_json(405, {"error": "Method Not Allowed: only GET and POST supported"})

    return ThreadingHTTPServer((bound_host, port), KernelOpenAPIHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(os.environ.get("BABYLON60_ROOT", Path(__file__).absolute().parents[1]))
    )
    parser.add_argument("--allow-patches", action="store_true", help="Enable reviewed source edits (no manifests).")
    parser.add_argument(
        "--allow-execution",
        action="store_true",
        help="Run trusted build/test code with host permissions, only in a clean worktree.",
    )
    parser.add_argument(
        "--use-canonical-names",
        action="store_true",
        default=os.environ.get("BABYLON60_MCP_CANONICAL_NAMES", "").strip().lower() in {"1", "true", "yes"},
        help="Expose canonical functional names (kernel_*) as primary in tools/list and OpenAPI.",
    )
    parser.add_argument(
        "--export-openapi",
        type=Path,
        help="Export canonical OpenAPI 3.1.0 JSON specification directly to the given file path.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http", "openapi-http"),
        default="stdio",
        help="Transport mode (stdio default; streamable-http and openapi-http confined to loopback).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Loopback address for HTTP transports (127.0.0.1, ::1, localhost).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=6061,
        help="Loopback TCP port for HTTP transports (default: 6061).",
    )
    parser.add_argument(
        "--bearer-token-env",
        default="BABYLON60_MCP_BEARER_TOKEN",
        help="Environment variable holding the Bearer token for openapi-http.",
    )
    args = parser.parse_args()
    if args.export_openapi is not None:
        target_path = Path(args.export_openapi)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        spec = build_openapi_spec(args.root, use_canonical_names=args.use_canonical_names)
        target_path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
        print(f"Exported canonical OpenAPI 3.1.0 specification to {target_path}")
        return
    if not (1024 <= args.port <= 65535):
        raise ValueError("port must be in 1024..65535.")
    harness = KernelHarness(args.root, allow_patches=args.allow_patches, allow_execution=args.allow_execution)
    try:
        if args.transport == "openapi-http":
            token = os.environ.get(args.bearer_token_env, "")
            http_server = create_openapi_http_server(
                harness,
                host=args.host,
                port=args.port,
                bearer_token=token,
                use_canonical_names=args.use_canonical_names,
            )
            try:
                http_server.serve_forever()
            finally:
                http_server.server_close()
        elif args.transport == "streamable-http":
            host = validate_loopback_host(args.host)
            create_server(harness, use_canonical_names=args.use_canonical_names).run(
                transport="streamable-http", host=host, port=args.port
            )
        else:
            create_server(harness, use_canonical_names=args.use_canonical_names).run(transport="stdio")
    finally:
        harness.close()


if __name__ == "__main__":
    # Direct script invocation has the same source-package access as the launcher.
    sys.path.insert(0, str(Path(__file__).absolute().parents[1] / "01_KISH_ENGINE"))
    main()
