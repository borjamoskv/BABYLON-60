"""CLAIM-L0-007 silicon verification: FFI/PyO3 panic-surface scanner and OS descriptor hygiene."""

from __future__ import annotations

import gc
from pathlib import Path
import sqlite3
import subprocess
import sys
from typing import Any

import pytest

from babylon60.verification.verification_gate import VerificationGate
from scripts.c5_quality_gates.audit_ffi_and_sqlite_hygiene import (
    REPO_ROOT,
    audit_rust_ffi_panic_surface,
    audit_sqlite_descriptor_hygiene,
    scan_rust_source_for_ffi_panics,
    snapshot_open_fds,
)


def test_workspace_ffi_panic_surface_is_zero() -> None:
    report = audit_rust_ffi_panic_surface(REPO_ROOT)
    assert report["scanned_ffi_entrypoints"] >= 60
    assert report["ffi_panic_surface"] == 0, report["violations"]
    assert report["violations"] == []


def test_ffi_scanner_catches_extern_c_pymethods_and_callee_panics_while_ignoring_tests() -> None:
    synthetic_rust = '''
    // .unwrap() inside a comment must never trigger
    const DOC: &str = "string literal .expect(\\"ignored\\") and panic!(\\"ignored\\")";

    fn deep_callee_unreachable(v: u32) -> u32 {
        if v == 99 {
            unreachable!("transitive helper reachable from extern C");
        }
        v
    }

    fn helper_with_expect(x: Option<u32>) -> u32 {
        deep_callee_unreachable(x.expect("boom in helper called from extern C"))
    }

    fn pyo3_helper_unwrap(x: Option<usize>) -> usize {
        x.unwrap()
    }

    fn unused_helper(x: Option<u32>) -> u32 {
        x.unwrap()
    }

    extern "C" {
        fn foreign_import_without_body(ptr: *const u8) -> i32;
    }

    #[no_mangle]
    pub unsafe extern "C" fn bad_c_abi(flag: bool) -> u32 {
        if flag {
            let v: Option<u32> = Some(1);
            return v.unwrap();
        }
        helper_with_expect(Some(2))
    }

    #[pyfunction]
    fn bad_pyfunc() -> usize {
        if false {
            return pyo3_helper_unwrap(Some(1));
        }
        todo!("unimplemented branch")
    }

    #[pymethods]
    impl MyBridge {
        fn ok_method(&self, v: Option<u32>) -> u32 {
            v.unwrap_or(0)
        }

        fn bad_method(&self) -> u32 {
            panic!("explicit panic inside pymethods")
        }
    }

    #[cfg(test)]
    mod tests {
        #[test]
        fn unit_test_can_unwrap() {
            let x: Option<i32> = Some(7);
            assert_eq!(x.unwrap(), 7);
        }
    }
    '''
    entrypoints, violations = scan_rust_source_for_ffi_panics(synthetic_rust, "synthetic.rs")
    assert entrypoints == 4  # bad_c_abi, bad_pyfunc, ok_method, bad_method (foreign_import & tests excluded)
    triples = {(v.boundary, v.symbol, v.primitive) for v in violations}
    assert triples == {
        ('extern "C"', "bad_c_abi", "unwrap()"),
        ('extern "C" callee', "helper_with_expect", "expect()"),
        ('extern "C" callee', "deep_callee_unreachable", "unreachable!()"),
        ("#[pyfunction]", "bad_pyfunc", "todo!()"),
        ("PyO3 callee", "pyo3_helper_unwrap", "unwrap()"),
        ("#[pymethods]", "bad_method", "panic!()"),
    }


def test_sqlite_descriptor_hygiene_zero_leaks_under_gc_disabled() -> None:
    report = audit_sqlite_descriptor_hygiene(iterations=15)
    assert report["gc_disabled_during_measurement"] is True
    assert report["sqlite_descriptor_leaks"] == 0, report["scenarios"]


def test_descriptor_sensor_is_non_vacuous_and_catches_real_unclosed_sqlite_fd(tmp_path: Path) -> None:
    """Prove DENY != Proof: an unclosed sqlite3.Connection with GC disabled increases OS fd count."""
    db_file = tmp_path / "leak_probe.db"
    gc.collect()
    was_enabled = gc.isenabled()
    gc.disable()
    leaked_conn: sqlite3.Connection | None = None
    try:
        before = snapshot_open_fds()
        leaked_conn = sqlite3.connect(str(db_file))
        leaked_conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        during = snapshot_open_fds()
        delta = during - before
        assert len(delta) >= 1, "OS descriptor sensor failed to detect an open SQLite file descriptor"
    finally:
        if leaked_conn is not None:
            leaked_conn.close()
        if was_enabled:
            gc.enable()
    after_close = snapshot_open_fds()
    assert after_close - before == set()


def test_verification_gate_closes_descriptor_on_pragma_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_connect = sqlite3.connect

    def deny_second_pragma(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        conn = real_connect(*args, **kwargs)
        seen = 0

        def auth(action: int, *_rest: object) -> int:
            nonlocal seen
            if action == sqlite3.SQLITE_PRAGMA:
                seen += 1
                if seen == 2:
                    return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        conn.set_authorizer(auth)
        return conn

    monkeypatch.setattr(sqlite3, "connect", deny_second_pragma)
    gc.collect()
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        before = snapshot_open_fds()
        with pytest.raises(sqlite3.DatabaseError):
            VerificationGate(db_path=str(tmp_path / "denied.db"))
        after = snapshot_open_fds()
        assert after - before == set()
    finally:
        if was_enabled:
            gc.enable()


def test_cli_gate_exits_zero_with_valid_json() -> None:
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/c5_quality_gates/audit_ffi_and_sqlite_hygiene.py"), "--json", "--iterations", "5"],
        capture_output=True,
        text=True,
        check=True,
    )
    import json

    payload = json.loads(proc.stdout)
    assert payload["passed"] is True
    assert payload["ffi"]["ffi_panic_surface"] == 0
    assert payload["sqlite_descriptors"]["sqlite_descriptor_leaks"] == 0
