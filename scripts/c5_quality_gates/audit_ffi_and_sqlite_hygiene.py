#!/usr/bin/env python3
"""CLAIM-L0-007 deterministic silicon gate: FFI/PyO3 panic-surface auditor & OS descriptor hygiene probe.

Enforces two physical/static invariants without relying on prose declarations or Python GC:
  1. ``ffi_panic_surface == 0`` across all non-test ``extern "C"`` / ``extern "system"`` functions,
     ``#[pyfunction]`` items, ``#[pymethods]`` impl blocks, and their same-file helper callees.
  2. ``sqlite_descriptor_leaks == 0`` measured directly against the OS file-descriptor table
     (``/dev/fd`` or ``/proc/self/fd``) with ``gc.disable()`` across queries, writes, collision
     rollbacks, and constructor/PRAGMA failures in CORTEX SQLite components.
"""

from __future__ import annotations

import argparse
from contextlib import closing, redirect_stdout
from dataclasses import asdict, dataclass
import gc
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).absolute().parents[2]
if str(REPO_ROOT / "01_KISH_ENGINE") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "01_KISH_ENGINE"))

RUST_SCAN_ROOTS = (
    "src",
    "crates",
    "00_ABZU_KERNEL/crates",
    "01_KISH_ENGINE/cortex/crates",
)
EXCLUDED_RUST_PARTS = frozenset({"target", "tests", "examples", "benches", "babylon60-fuzz", ".git"})

PANIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("unwrap()", re.compile(r"\.\s*unwrap\s*\(")),
    ("expect()", re.compile(r"\.\s*expect\s*\(")),
    ("unwrap_unchecked()", re.compile(r"\.\s*unwrap_unchecked\s*\(")),
    ("panic!()", re.compile(r"\bpanic!\s*[\(\[\{]")),
    ("todo!()", re.compile(r"\btodo!\s*[\(\[\{]")),
    ("unimplemented!()", re.compile(r"\bunimplemented!\s*[\(\[\{]")),
    ("unreachable!()", re.compile(r"\bunreachable!\s*[\(\[\{]")),
)

_EXTERN_FN_RE = re.compile(
    r'\b(?:pub(?:\s*\([^)]*\))?\s+)?(?:unsafe\s+)?extern(?:\s+"(?:C|system|C-unwind|system-unwind)")?\s+fn\s+([A-Za-z_][A-Za-z0-9_]*)'
)
_ABI_LITERAL_RE = re.compile(r'"(?:C|system|C-unwind|system-unwind)"')
_PYFUNC_ATTR_RE = re.compile(r"#\s*\[\s*pyfunction\b[^\]]*\]")
_PYMETHODS_ATTR_RE = re.compile(r"#\s*\[\s*pymethods\b[^\]]*\]")
_FN_DECL_RE = re.compile(
    r"\b(?:pub(?:\s*\([^)]*\))?\s+)?(?:const\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)"
)
_CFG_TEST_RE = re.compile(r"#\s*\[\s*cfg\s*\(\s*test\s*\)\s*\]")


@dataclass(frozen=True)
class FfiPanicViolation:
    file: str
    line: int
    boundary: str
    symbol: str
    primitive: str


def strip_rust_comments_and_literals(source: str) -> str:
    """Replace comments and string/char literal interiors with spaces while preserving newlines."""
    out: list[str] = []
    n = len(source)
    i = 0
    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""

        # Line comment
        if ch == "/" and nxt == "/":
            out.append("  ")
            i += 2
            while i < n and source[i] != "\n":
                out.append(" ")
                i += 1
            continue

        # Nested block comment
        if ch == "/" and nxt == "*":
            depth = 1
            out.append("  ")
            i += 2
            while i < n and depth > 0:
                c0 = source[i]
                c1 = source[i + 1] if i + 1 < n else ""
                if c0 == "/" and c1 == "*":
                    depth += 1
                    out.append("  ")
                    i += 2
                elif c0 == "*" and c1 == "/":
                    depth -= 1
                    out.append("  ")
                    i += 2
                else:
                    out.append("\n" if c0 == "\n" else " ")
                    i += 1
            continue

        # Raw string r#"..."# or br#"..."#
        if ch in ("r", "b"):
            start = i
            if ch == "b" and nxt == "r":
                i += 2
            elif ch == "r":
                i += 1
            else:
                i = start
            if i > start:
                hashes = 0
                while i < n and source[i] == "#":
                    hashes += 1
                    i += 1
                if i < n and source[i] == '"':
                    out.append(" " * (i - start) + '"')
                    i += 1
                    closing_seq = '"' + ("#" * hashes)
                    while i < n and not source.startswith(closing_seq, i):
                        out.append("\n" if source[i] == "\n" else " ")
                        i += 1
                    if i < n:
                        out.append('"' + (" " * hashes))
                        i += len(closing_seq)
                    continue
                i = start

        # Preserve ABI string literal immediately following `extern` (e.g. extern "C")
        if ch == '"':
            abi_m = _ABI_LITERAL_RE.match(source, i)
            if abi_m is not None and re.search(r"\bextern\s+$", "".join(out[-24:])):
                out.append(abi_m.group(0))
                i = abi_m.end()
                continue

        # Ordinary string or byte string
        if ch == '"' or (ch == "b" and nxt == '"'):
            if ch == "b":
                out.append(' "')
                i += 2
            else:
                out.append('"')
                i += 1
            while i < n:
                c0 = source[i]
                if c0 == "\\":
                    out.append(" ")
                    i += 1
                    if i < n:
                        out.append("\n" if source[i] == "\n" else " ")
                        i += 1
                    continue
                if c0 == '"':
                    out.append('"')
                    i += 1
                    break
                out.append("\n" if c0 == "\n" else " ")
                i += 1
            continue

        # Character literal (distinguished from lifetime 'a by closing quote)
        if ch == "'":
            if i + 2 < n and source[i + 1] != "\\" and source[i + 2] == "'":
                out.append("' '")
                i += 3
                continue
            if i + 3 < n and source[i + 1] == "\\":
                end_q = source.find("'", i + 2)
                if 0 < end_q - i <= 12 and "\n" not in source[i:end_q]:
                    out.append("'" + (" " * (end_q - i - 1)) + "'")
                    i = end_q + 1
                    continue

        out.append(ch)
        i += 1

    return "".join(out)


def _find_matching_brace(text: str, open_idx: int) -> int:
    depth = 0
    for idx in range(open_idx, len(text)):
        c = text[idx]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return idx
    return len(text) - 1


def _blank_span_preserving_newlines(buf: list[str], start: int, end_inclusive: int) -> None:
    for idx in range(start, min(end_inclusive + 1, len(buf))):
        if buf[idx] != "\n":
            buf[idx] = " "


def strip_cfg_test_items(sanitized: str) -> str:
    """Blank out #[cfg(test)] items while preserving exact line offsets."""
    buf = list(sanitized)
    n = len(sanitized)
    pos = 0
    while pos < n:
        m = _CFG_TEST_RE.search("".join(buf), pos)
        if m is None:
            break
        cursor = m.end()
        # Advance past additional attributes (#[...]) to the item's '{' or ';'
        while cursor < n:
            ch = buf[cursor]
            if ch.isspace():
                cursor += 1
                continue
            if ch == "#" and cursor + 1 < n and buf[cursor + 1] == "[":
                end_bracket = "".join(buf).find("]", cursor + 2)
                cursor = (end_bracket + 1) if end_bracket != -1 else (cursor + 1)
                continue
            break
        while cursor < n and buf[cursor] not in ("{", ";"):
            cursor += 1
        if cursor >= n:
            _blank_span_preserving_newlines(buf, m.start(), n - 1)
            break
        if buf[cursor] == ";":
            _blank_span_preserving_newlines(buf, m.start(), cursor)
            pos = cursor + 1
        else:
            close_idx = _find_matching_brace("".join(buf), cursor)
            _blank_span_preserving_newlines(buf, m.start(), close_idx)
            pos = close_idx + 1
    return "".join(buf)


def _find_fn_body_span(text: str, decl_end: int) -> tuple[int, int] | None:
    """Locate the '{ ... }' body of a function declaration; return None for ';' declarations."""
    paren_depth = 0
    i = decl_end
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "(":
            paren_depth += 1
        elif ch == ")":
            paren_depth = max(0, paren_depth - 1)
        elif paren_depth == 0:
            if ch == ";":
                return None
            if ch == "{":
                close_idx = _find_matching_brace(text, i)
                return (i, close_idx)
        i += 1
    return None


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def scan_rust_source_for_ffi_panics(source: str, rel_file: str) -> tuple[int, list[FfiPanicViolation]]:
    """Return (entrypoint_count, violations) for a single Rust source string."""
    clean = strip_cfg_test_items(strip_rust_comments_and_literals(source))
    entrypoints: list[tuple[str, str, int, int]] = []  # (boundary, symbol, body_start, body_end)
    covered_spans: list[tuple[int, int]] = []

    # 1. extern "C" / extern "system" fn definitions with bodies
    for m in _EXTERN_FN_RE.finditer(clean):
        span = _find_fn_body_span(clean, m.end())
        if span is not None:
            entrypoints.append(('extern "C"', m.group(1), span[0], span[1]))
            covered_spans.append(span)

    # 2. #[pyfunction] definitions
    for attr in _PYFUNC_ATTR_RE.finditer(clean):
        fn_m = _FN_DECL_RE.search(clean, attr.end())
        if fn_m is None:
            continue
        span = _find_fn_body_span(clean, fn_m.end())
        if span is not None and span not in covered_spans:
            entrypoints.append(("#[pyfunction]", fn_m.group(1), span[0], span[1]))
            covered_spans.append(span)

    # 3. #[pymethods] impl blocks -> every method inside the impl block
    for attr in _PYMETHODS_ATTR_RE.finditer(clean):
        open_brace = clean.find("{", attr.end())
        if open_brace == -1:
            continue
        close_brace = _find_matching_brace(clean, open_brace)
        cursor = open_brace + 1
        while cursor < close_brace:
            fn_m = _FN_DECL_RE.search(clean, cursor, close_brace)
            if fn_m is None:
                break
            span = _find_fn_body_span(clean, fn_m.end())
            if span is None or span[1] > close_brace:
                cursor = fn_m.end()
                continue
            if span not in covered_spans:
                entrypoints.append(("#[pymethods]", fn_m.group(1), span[0], span[1]))
                covered_spans.append(span)
            cursor = span[1] + 1

    # 4. Transitive same-file helper functions called by any FFI / PyO3 entrypoint
    helper_defs: dict[str, tuple[int, int]] = {}
    for fn_m in _FN_DECL_RE.finditer(clean):
        name = fn_m.group(1)
        span = _find_fn_body_span(clean, fn_m.end())
        if span is not None and span not in covered_spans:
            helper_defs[name] = span

    def _collect_transitive_callees(seed_bodies: list[str]) -> set[str]:
        visited: set[str] = set()
        frontier = list(seed_bodies)
        while frontier and helper_defs:
            blob = "\n".join(frontier)
            frontier = []
            for helper_name, span in sorted(helper_defs.items()):
                if helper_name in visited:
                    continue
                if re.search(rf"\b{re.escape(helper_name)}\s*\(", blob):
                    visited.add(helper_name)
                    frontier.append(clean[span[0] : span[1] + 1])
        return visited

    extern_callees = _collect_transitive_callees(
        [clean[s : e + 1] for b, _, s, e in entrypoints if b == 'extern "C"']
    )
    pyo3_callees = _collect_transitive_callees(
        [clean[s : e + 1] for b, _, s, e in entrypoints if b != 'extern "C"']
    ) - extern_callees

    callees: list[tuple[str, str, int, int]] = []
    for helper_name in sorted(extern_callees):
        span = helper_defs[helper_name]
        callees.append(('extern "C" callee', helper_name, span[0], span[1]))
    for helper_name in sorted(pyo3_callees):
        span = helper_defs[helper_name]
        callees.append(("PyO3 callee", helper_name, span[0], span[1]))

    violations: list[FfiPanicViolation] = []
    for boundary, symbol, b_start, b_end in entrypoints + callees:
        body = clean[b_start : b_end + 1]
        for prim_name, pat in PANIC_PATTERNS:
            for hit in pat.finditer(body):
                line = _line_number(clean, b_start + hit.start())
                violations.append(
                    FfiPanicViolation(
                        file=rel_file,
                        line=line,
                        boundary=boundary,
                        symbol=symbol,
                        primitive=prim_name,
                    )
                )

    return (len(entrypoints), violations)


def audit_rust_ffi_panic_surface(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Scan all production Rust files under RUST_SCAN_ROOTS for FFI/PyO3 panic sites."""
    total_entrypoints = 0
    scanned_files = 0
    all_violations: list[FfiPanicViolation] = []

    for rel_root in RUST_SCAN_ROOTS:
        root_dir = repo_root / rel_root
        if not root_dir.is_dir():
            continue
        for rs_path in sorted(root_dir.rglob("*.rs")):
            rel_parts = set(rs_path.relative_to(repo_root).parts)
            if rel_parts & EXCLUDED_RUST_PARTS:
                continue
            scanned_files += 1
            rel_str = str(rs_path.relative_to(repo_root))
            count, violations = scan_rust_source_for_ffi_panics(
                rs_path.read_text(encoding="utf-8"),
                rel_str,
            )
            total_entrypoints += count
            all_violations.extend(violations)

    return {
        "scanned_rust_files": scanned_files,
        "scanned_ffi_entrypoints": total_entrypoints,
        "ffi_panic_surface": len(all_violations),
        "violations": [asdict(v) for v in all_violations],
    }


def snapshot_open_fds() -> set[int]:
    """Read the live OS file-descriptor table for the current process."""
    fd_dir = "/dev/fd" if os.path.isdir("/dev/fd") else "/proc/self/fd"
    if not os.path.isdir(fd_dir):
        raise RuntimeError("Neither /dev/fd nor /proc/self/fd is available on this OS")
    # listdir itself opens and closes a directory fd internally before returning;
    # subsequent os.fstat filters out that transient dirfd.
    names = os.listdir(fd_dir)
    active: set[int] = set()
    for name in names:
        if not name.isdigit():
            continue
        fd = int(name)
        try:
            os.fstat(fd)
            active.add(fd)
        except OSError:
            continue
    return active


def audit_sqlite_descriptor_hygiene(iterations: int = 20) -> dict[str, Any]:
    """Verify 0 leaked OS file descriptors across CORTEX SQLite components with GC disabled."""
    from babylon60.bft.consensus_committer import BFT_Committer
    from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger
    from babylon60.core.cortex_persist import CortexOntologyLedger, SessionDelta
    from babylon60.database.core import connect_sync
    from babylon60.kernel.mcp_deductive_engine import McpCandidateContract
    from babylon60.kernel.mcp_lifecycle_manager import McpLifecycleManager
    from babylon60.verification.verification_gate import VerificationGate

    scenarios: dict[str, list[int]] = {}
    with tempfile.TemporaryDirectory(prefix="b60_l0_007_") as td:
        root = Path(td).resolve()
        mem = root / ".agent" / "memory"
        (mem / "projects").mkdir(parents=True)
        (mem / "snapshots").mkdir(parents=True)
        (mem / "ghosts.json").write_text("{}", encoding="utf-8")
        (mem / "system.json").write_text("{}", encoding="utf-8")
        (mem / "projects" / "l0_007_probe.json").write_text("{}", encoding="utf-8")

        prev_home = os.environ.get("HOME")
        os.environ["HOME"] = str(root)
        try:
            ledger = CortexPersistLedger(root / "ledger.db")
            mgr = McpLifecycleManager(str(root / "gate.db"))
            onto = CortexOntologyLedger("l0_007_probe")

            # Warmup one cycle so SQLite WAL/SHM and ontology JSON files exist on disk before freezing GC.
            ledger.append_event(CortexEvent("WARMUP", {"n": 0}, "warmup:0"))
            ledger.query_events(limit=1)
            mgr.list_active_mcps()
            with redirect_stdout(io.StringIO()):
                onto.crystallize_session(
                    SessionDelta(
                        task_desc="warmup",
                        last_file="init.py",
                        conversation_id="conv-0",
                        changes=["c0"],
                        decisions=["d0"],
                    )
                )

            gc.collect()
            was_enabled = gc.isenabled()
            gc.disable()
            try:
                # Scenario 1: CortexPersistLedger queries, writes, Merkle/MMR proofs, and batch collision rollback
                before = snapshot_open_fds()
                for idx in range(1, iterations + 1):
                    ledger.append_event(CortexEvent("HYGIENE_EVT", {"idx": idx}, f"hygiene:{idx}"))
                    ledger.query_events(limit=5)
                    ledger.verify_integrity()
                    ledger.get_merkle_root()
                    ledger.get_mmr_root()
                    try:
                        ledger.append_batch([CortexEvent("INVALID", {}, "")])
                    except ValueError:
                        pass
                scenarios["cortex_persist_ledger"] = sorted(snapshot_open_fds() - before)

                # Scenario 2: Forced SQLite authorizer failures on PRAGMA and SELECT
                before = snapshot_open_fds()
                real_connect = sqlite3.connect

                def deny_select(*args: Any, **kwargs: Any) -> sqlite3.Connection:
                    conn = real_connect(*args, **kwargs)
                    conn.set_authorizer(
                        lambda action, *_rest: (
                            sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_SELECT else sqlite3.SQLITE_OK
                        )
                    )
                    return conn

                sqlite3.connect = deny_select  # type: ignore[assignment]
                try:
                    for _ in range(iterations):
                        try:
                            ledger.query_events()
                        except sqlite3.DatabaseError:
                            pass
                finally:
                    sqlite3.connect = real_connect  # type: ignore[assignment]
                scenarios["cortex_ledger_injected_failures"] = sorted(snapshot_open_fds() - before)

                # Scenario 3: VerificationGate context-managed lifecycle + constructor PRAGMA failure
                before = snapshot_open_fds()
                for _ in range(iterations):
                    with VerificationGate(db_path=str(root / "gate.db")) as gate:
                        gate.is_allowed({"action": "read"})

                def deny_pragma(*args: Any, **kwargs: Any) -> sqlite3.Connection:
                    conn = real_connect(*args, **kwargs)
                    conn.set_authorizer(
                        lambda action, *_rest: (
                            sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_PRAGMA else sqlite3.SQLITE_OK
                        )
                    )
                    return conn

                sqlite3.connect = deny_pragma  # type: ignore[assignment]
                try:
                    for _ in range(5):
                        try:
                            VerificationGate(db_path=str(root / "gate_fail.db"))
                        except sqlite3.DatabaseError:
                            pass
                        try:
                            connect_sync(root / "core_fail.db")
                        except sqlite3.DatabaseError:
                            pass
                finally:
                    sqlite3.connect = real_connect  # type: ignore[assignment]
                scenarios["verification_gate_and_core"] = sorted(snapshot_open_fds() - before)

                # Scenario 4: McpLifecycleManager register, list, and detonate
                before = snapshot_open_fds()
                for idx in range(iterations):
                    s_file = root / f"ephemeral_{idx}.py"
                    s_file.write_text("x = 1\n", encoding="utf-8")
                    contract = McpCandidateContract(f"srv_{idx}", f"tool_{idx}", "fd hygiene probe")
                    mgr.register_mcp(contract, str(s_file))
                    mgr.list_active_mcps()
                    mgr.detonate_mcp(f"srv_{idx}")
                scenarios["mcp_lifecycle_manager"] = sorted(snapshot_open_fds() - before)

                # Scenario 5: CortexOntologyLedger descriptor-locked atomic writes & BFT_Committer teardown
                before = snapshot_open_fds()
                with redirect_stdout(io.StringIO()):
                    for idx in range(iterations):
                        onto.crystallize_session(
                            SessionDelta(
                                task_desc=f"step-{idx}",
                                last_file="probe.py",
                                conversation_id=f"conv-{idx}",
                                changes=[f"chg-{idx}"],
                                decisions=[f"dec-{idx}"],
                            )
                        )
                committer = BFT_Committer(db_path=str(root / "committer.db"))
                committer.close()
                with closing(connect_sync(root / "closing_check.db")) as c_conn:
                    c_conn.execute("SELECT 1")
                scenarios["cortex_ontology_and_committer"] = sorted(snapshot_open_fds() - before)
            finally:
                if was_enabled:
                    gc.enable()
        finally:
            if prev_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = prev_home

    total_leaks = sum(len(leaked) for leaked in scenarios.values())
    return {
        "iterations_per_scenario": iterations,
        "gc_disabled_during_measurement": True,
        "sqlite_descriptor_leaks": total_leaks,
        "scenarios": scenarios,
    }


def run_hygiene_audit(repo_root: Path = REPO_ROOT, iterations: int = 20) -> dict[str, Any]:
    ffi_report = audit_rust_ffi_panic_surface(repo_root=repo_root)
    fd_report = audit_sqlite_descriptor_hygiene(iterations=iterations)
    passed = (
        ffi_report["scanned_ffi_entrypoints"] > 0
        and ffi_report["ffi_panic_surface"] == 0
        and fd_report["sqlite_descriptor_leaks"] == 0
    )
    return {
        "passed": passed,
        "ffi": ffi_report,
        "sqlite_descriptors": fd_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="CLAIM-L0-007 FFI panic surface & SQLite FD leak gate")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--iterations", type=int, default=20, help="Iterations per descriptor scenario")
    args = parser.parse_args()

    report = run_hygiene_audit(REPO_ROOT, iterations=args.iterations)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        ffi = report["ffi"]
        fds = report["sqlite_descriptors"]
        print(
            f"[CLAIM-L0-007] FFI entrypoints={ffi['scanned_ffi_entrypoints']} "
            f"(files={ffi['scanned_rust_files']}) | ffi_panic_surface={ffi['ffi_panic_surface']} | "
            f"sqlite_descriptor_leaks={fds['sqlite_descriptor_leaks']}"
        )
        for v in ffi["violations"]:
            print(
                f"  [FFI-PANIC] {v['file']}:{v['line']} [{v['boundary']}] {v['symbol']} -> {v['primitive']}",
                file=sys.stderr,
            )
        for scen, leaked in fds["scenarios"].items():
            if leaked:
                print(f"  [FD-LEAK] {scen}: open fds leaked -> {leaked}", file=sys.stderr)

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
