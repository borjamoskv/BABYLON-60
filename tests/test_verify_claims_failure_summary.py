"""verify_claims records a bounded, path-free failure cause instead of the pytest session header."""

from __future__ import annotations

from pathlib import Path

from scripts.c5_quality_gates.verify_claims import ERROR_SUMMARY_LIMIT, extract_failure_summary, local_path_redactions

# Captured through run_command (stdout + stderr per step) with pytest 9.1.1 and cargo/rustc 1.97.0
# (RUST_BACKTRACE=1, CI unset). Only the probe directory was replaced by a synthetic checkout path and
# trailing whitespace removed; temporary paths, thread ids and timings are as captured.
REDACTIONS = [("/Users/operator/BABYLON-60", "<repo>"), ("/Users/operator", "~"), ("/tmp", "<tmp>")]

PYTEST_ASSERTION_FAILURE = """\
============================= test session starts ==============================
platform linux -- Python 3.13.18, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/operator/BABYLON-60
configfile: pyproject.toml
plugins: hypothesis-6.165.1, anyio-4.14.2, asyncio-1.4.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 2 items

tests/test_ledger_probe.py .F

=================================== FAILURES ===================================
____________________ test_ledger_snapshot_matches_checkout _____________________
tests/test_ledger_probe.py:11: in test_ledger_snapshot_matches_checkout
    assert snapshot == checkout
E   AssertionError: assert PosixPath('/tmp/pytest-of-root/pytest-0/test_ledger_snapshot_matches_c0/ledger.db') == PosixPath('/Users/operator/BABYLON-60/tests/ledger.db')
=========================== short test summary info ============================
FAILED tests/test_ledger_probe.py::test_ledger_snapshot_matches_checkout - As...
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
========================= 1 failed, 1 passed in 0.57s ==========================
"""

PYTEST_COLLECTION_ERROR = """\
============================= test session starts ==============================
platform linux -- Python 3.13.18, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/operator/BABYLON-60
configfile: pyproject.toml
plugins: hypothesis-6.165.1, anyio-4.14.2, asyncio-1.4.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 0 items / 1 error

==================================== ERRORS ====================================
___________________ ERROR collecting tests/test_mcp_probe.py ___________________
ImportError while importing test module '/Users/operator/BABYLON-60/tests/test_mcp_probe.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/local/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_mcp_probe.py:1: in <module>
    import babylon60_probe_missing_module  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'babylon60_probe_missing_module'
=========================== short test summary info ============================
ERROR tests/test_mcp_probe.py
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.17s ===============================
"""

CARGO_TEST_PANIC = """\
running 2 tests
test tests::quorum_of_zero_is_zero ... ok
test tests::quorum_is_strict_majority ... FAILED

failures:

---- tests::quorum_is_strict_majority stdout ----

thread 'tests::quorum_is_strict_majority' (587) panicked at src/lib.rs:17:9:
assertion `left == right` failed
  left: 2
 right: 3
stack backtrace:
   0: __rustc::rust_begin_unwind
             at /rustc/2d8144b7880597b6e6d3dfd63a9a9efae3f533d3/library/std/src/panicking.rs:689:5
   1: core::panicking::panic_fmt
             at /rustc/2d8144b7880597b6e6d3dfd63a9a9efae3f533d3/library/core/src/panicking.rs:80:14
   2: core::panicking::assert_failed_inner
             at /rustc/2d8144b7880597b6e6d3dfd63a9a9efae3f533d3/library/core/src/panicking.rs:439:17
   3: core::panicking::assert_failed::<u32, u32>
             at /rustc/2d8144b7880597b6e6d3dfd63a9a9efae3f533d3/library/core/src/panicking.rs:394:5
   4: quorum_probe::tests::quorum_is_strict_majority
             at ./src/lib.rs:17:9
   5: quorum_probe::tests::quorum_is_strict_majority::{closure#0}
             at ./src/lib.rs:16:35
   6: <quorum_probe::tests::quorum_is_strict_majority::{closure#0} as core::ops::function::FnOnce<()>>::call_once
             at /rustc/2d8144b7880597b6e6d3dfd63a9a9efae3f533d3/library/core/src/ops/function.rs:250:5
   7: <fn() -> core::result::Result<(), alloc::string::String> as core::ops::function::FnOnce<()>>::call_once
             at /rustc/2d8144b7880597b6e6d3dfd63a9a9efae3f533d3/library/core/src/ops/function.rs:250:5
note: Some details are omitted, run with `RUST_BACKTRACE=full` for a verbose backtrace.


failures:
    tests::quorum_is_strict_majority

test result: FAILED. 1 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.34s


   Compiling quorum_probe v0.1.0 (/Users/operator/BABYLON-60)
warning: unused variable: `unused_weight`
 --> src/lib.rs:2:9
  |
2 |     let unused_weight = 3;
  |         ^^^^^^^^^^^^^ help: if this is intentional, prefix it with an underscore: `_unused_weight`
  |
  = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default

warning: `quorum_probe` (lib) generated 1 warning (run `cargo fix --lib -p quorum_probe` to apply 1 suggestion)
warning: `quorum_probe` (lib test) generated 1 warning (1 duplicate)
    Finished `test` profile [unoptimized + debuginfo] target(s) in 6.05s
     Running unittests src/lib.rs (target/debug/deps/quorum_probe-e2846b826857367f)
error: test failed, to rerun pass `--lib`
"""

CARGO_RUN_VIOLATION = """\
crash probe  dir=/tmp/b60_claim_hbaum4y8/run
crash point           iters    state
after_dispatch            3  unknown
violations: 1
  VIOLATION iteration=2: replay accepted after reopen

   Compiling crash_probe v0.1.0 (/Users/operator/BABYLON-60)
warning: unused variable: `stale_marker`
 --> src/main.rs:6:9
  |
6 |     let stale_marker = 0;
  |         ^^^^^^^^^^^^ help: if this is intentional, prefix it with an underscore: `_stale_marker`
  |
  = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default

warning: `crash_probe` (bin "crash_probe") generated 1 warning (run `cargo fix --bin "crash_probe" -p crash_probe` to apply 1 suggestion)
    Finished `release` profile [optimized] target(s) in 0.37s
     Running `target/release/crash_probe --dir /tmp/b60_claim_hbaum4y8/run`
"""


def _pytest_run_with_failures(count: int) -> str:
    lines = ["=" * 30 + " FAILURES " + "=" * 30]
    for i in range(count):
        lines += [
            "_" * 20 + f" test_quorum[{i}] " + "_" * 20,
            f"tests/test_quorum.py:{10 + i}: in test_quorum",
            f"E   AssertionError: assert {i} == {i + 1}",
        ]
    lines.append("=" * 25 + " short test summary info " + "=" * 25)
    lines += [
        f"FAILED tests/test_quorum.py::test_quorum[{i}] - AssertionError: assert {i} == {i + 1}" for i in range(count)
    ]
    lines.append("=" * 25 + f" {count} failed, 3 passed in 1.24s " + "=" * 25)
    return "\n".join(lines)


def test_pytest_failure_keeps_cause_without_session_header_or_local_paths() -> None:
    assert extract_failure_summary(PYTEST_ASSERTION_FAILURE, redactions=REDACTIONS) == (
        "tests/test_ledger_probe.py .F\n"
        "\n"
        "= FAILURES =\n"
        "_ test_ledger_snapshot_matches_checkout _\n"
        "tests/test_ledger_probe.py:11: in test_ledger_snapshot_matches_checkout\n"
        "    assert snapshot == checkout\n"
        "E   AssertionError: assert PosixPath('<tmp>/pytest-of-<user>/pytest-<n>/test_ledger_snapshot_matches_c0"
        "/ledger.db') == PosixPath('<repo>/tests/ledger.db')\n"
        "= short test summary info =\n"
        "FAILED tests/test_ledger_probe.py::test_ledger_snapshot_matches_checkout - As...\n"
        "! stopping after 1 failures !\n"
        "= 1 failed, 1 passed in 0.57s ="
    )


def test_pytest_collection_error_keeps_import_cause() -> None:
    summary = extract_failure_summary(PYTEST_COLLECTION_ERROR, redactions=REDACTIONS)
    for line in (
        "ImportError while importing test module '<repo>/tests/test_mcp_probe.py'.",
        "E   ModuleNotFoundError: No module named 'babylon60_probe_missing_module'",
        "ERROR tests/test_mcp_probe.py",
        "! Interrupted: 1 error during collection !",
        "= 1 error in 0.17s =",
    ):
        assert line in summary.splitlines()
    assert "rootdir" not in summary and "platform linux" not in summary and "/Users/" not in summary


def test_cargo_test_panic_keeps_message_and_result_without_build_noise() -> None:
    assert extract_failure_summary(CARGO_TEST_PANIC, redactions=REDACTIONS) == (
        "running 2 tests\n"
        "test tests::quorum_of_zero_is_zero ... ok\n"
        "test tests::quorum_is_strict_majority ... FAILED\n"
        "\n"
        "failures:\n"
        "\n"
        "- tests::quorum_is_strict_majority stdout -\n"
        "\n"
        "thread 'tests::quorum_is_strict_majority' (<tid>) panicked at src/lib.rs:17:9:\n"
        "assertion `left == right` failed\n"
        "  left: 2\n"
        " right: 3\n"
        "note: Some details are omitted, run with `RUST_BACKTRACE=full` for a verbose backtrace.\n"
        "\n"
        "failures:\n"
        "    tests::quorum_is_strict_majority\n"
        "\n"
        "test result: FAILED. 1 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.34s\n"
        "\n"
        "error: test failed, to rerun pass `--lib`"
    )


def test_cargo_run_keeps_program_output_that_precedes_the_build_log() -> None:
    assert extract_failure_summary(CARGO_RUN_VIOLATION, redactions=REDACTIONS) == (
        "crash probe  dir=<tmp>/b60_claim_<rand>/run\n"
        "crash point           iters    state\n"
        "after_dispatch            3  unknown\n"
        "violations: 1\n"
        "  VIOLATION iteration=2: replay accepted after reopen"
    )
    rows = "\n".join(f"{'after_reopen':<20} {i:>6} {'rejected':>8}" for i in range(60))
    summary = extract_failure_summary(
        CARGO_RUN_VIOLATION.replace("violations: 1", rows + "\nviolations: 1"), redactions=REDACTIONS
    )
    assert len(summary) <= ERROR_SUMMARY_LIMIT
    assert summary.startswith("[... +") and summary.endswith("  VIOLATION iteration=2: replay accepted after reopen")
    assert "violations: 1" in summary and "warning:" not in summary and "Compiling" not in summary


def test_many_failures_are_bounded_prioritised_and_deterministic() -> None:
    output = _pytest_run_with_failures(60)
    summary = extract_failure_summary(output)
    assert len(output) > 4 * ERROR_SUMMARY_LIMIT and len(summary) <= ERROR_SUMMARY_LIMIT
    assert summary.splitlines()[0] == "E   AssertionError: assert 0 == 1"
    assert summary.index("[... +") < summary.index("FAILED tests/test_quorum.py::test_quorum[59]")
    assert summary.endswith("= 60 failed, 3 passed in 1.24s =")
    assert extract_failure_summary(output) == summary


def test_short_messages_pass_through_and_redaction_respects_path_boundaries() -> None:
    vacuous = "VACUOUS_EVIDENCE: el comando salió con 0 pero ejecutó 0 tests"
    assert extract_failure_summary(vacuous, redactions=REDACTIONS) == vacuous
    assert extract_failure_summary("") == ""
    assert (
        extract_failure_summary("cache /var/tmp/x, /tmp/x", redactions=[("/tmp", "<tmp>")])
        == "cache /var/tmp/x, <tmp>/x"
    )
    assert extract_failure_summary("open /srv/a(b+c)/x", redactions=[("/srv/a(b+c)", "<repo>")]) == "open <repo>/x"
    assert extract_failure_summary("FAILED t.py::t - OSError: '/Users/operat...") == (
        "FAILED t.py::t - OSError: '/Users/<user>"
    )
    redactions = local_path_redactions(Path("/srv/ci/BABYLON-60"))
    assert ("/srv/ci/BABYLON-60", "<repo>") in redactions
    assert all(prefix.startswith("/") and prefix.rstrip("/") for prefix, _ in redactions)
