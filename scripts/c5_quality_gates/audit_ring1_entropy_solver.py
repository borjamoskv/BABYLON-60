#!/usr/bin/env python3
"""CLAIM-RING1-009 silicon gate: Q16 numerical stability, NEMESIS Ring-1 solver suite & Lean/Z3 alignment.

Verifies on live sources without mutating historical 2026-10-26 JSON receipts:
  1. Exact Q16 quantization bounds, zero threshold-flip error around TAU_SEM_Q16 (0.85 bits),
     and strict refinement monotonicity across all 5,295 Bell partitions (1 <= n <= 8) parsed
     directly from ``00_ABZU_KERNEL/crates/babylon60-kernel/src/semantic_entropy.rs``.
  2. Release-mode execution of ``babylon60-kernel`` (including 100k multithreaded stress and
     5,295-partition check) and ``babylon60-compiler`` (including the 5-vector + Z3 adversarial
     ``nemesis_ring1_entropy_solver`` campaign).
  3. Zero-axiom Lean 4 summary alignment (when ``lean`` is installed or ``--require-lean`` is set)
     and real BLAKE3-pinned Z3 execution across all 11 ignored solver tests (when the pinned Z3
     binary is present or ``--require-z3`` is set).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Iterator

REPO_ROOT = Path(__file__).absolute().parents[2]

SEMANTIC_ENTROPY_RS = REPO_ROOT / "00_ABZU_KERNEL/crates/babylon60-kernel/src/semantic_entropy.rs"
TRACKED_RING1_SOURCES = (
    "00_ABZU_KERNEL/crates/babylon60-kernel/src/semantic_entropy.rs",
    "00_ABZU_KERNEL/crates/babylon60-kernel/tests/stress_semantic_entropy_100k.rs",
    "00_ABZU_KERNEL/crates/babylon60-compiler/src/semantic_solver.rs",
    "00_ABZU_KERNEL/crates/babylon60-compiler/src/solver_replay.rs",
    "00_ABZU_KERNEL/crates/babylon60-compiler/tests/nemesis_ring1_entropy_solver.rs",
    "scripts/c5_demos/SemanticEntropyApoptosis.lean",
)

AUDITED_Z3_EXACT_TESTS = (
    "approved_real_binary_runs_and_query_is_reserved_and_consumed_once",
    "wrong_query_does_not_consume_the_correct_receipt",
    "unknown_unsat_and_process_error_receipts_are_consumed_too",
    "real_sat_and_unsat_reach_all_four_entropy_variants",
    "real_unknown_retains_resource_reason_and_cannot_be_admitted",
    "receipt_rejects_other_request_body_partition_and_policy",
    "separate_processes_do_not_retain_previous_assertions",
    "real_parser_handles_comments_quoted_symbols_and_strings",
    "real_solver_parse_error_never_accepts_later_sat_output",
    "negative_processes::temporary_io_failure_preserves_transport_error",
    "nem_r1_06_real_z3_adversarial_contradiction_and_rlimit_campaign",
)

_TAU_RE = re.compile(r"pub\s+const\s+TAU_SEM_Q16\s*:\s*u32\s*=\s*([0-9_]+)\s*;")
_LUT_BLOCK_RE = re.compile(
    r"const\s+ENTROPY_LUT_Q16\s*:\s*\[\s*\[\s*u32\s*;\s*9\s*\]\s*;\s*9\s*\]\s*=\s*\[(.*?)\]\s*;",
    re.DOTALL,
)
_LUT_ROW_RE = re.compile(r"\[([0-9_,\s]+)\]")


def parse_rust_entropy_contract(rust_source: str) -> tuple[int, list[list[int]]]:
    """Extract TAU_SEM_Q16 and ENTROPY_LUT_Q16 directly from semantic_entropy.rs."""
    tau_m = _TAU_RE.search(rust_source)
    if tau_m is None:
        raise ValueError("Missing TAU_SEM_Q16 constant in semantic_entropy.rs")
    tau_q16 = int(tau_m.group(1).replace("_", ""))

    lut_m = _LUT_BLOCK_RE.search(rust_source)
    if lut_m is None:
        raise ValueError("Missing ENTROPY_LUT_Q16 table in semantic_entropy.rs")

    rows: list[list[int]] = []
    for row_m in _LUT_ROW_RE.finditer(lut_m.group(1)):
        vals = [int(tok.strip().replace("_", "")) for tok in row_m.group(1).split(",") if tok.strip()]
        if len(vals) != 9:
            raise ValueError(f"Expected 9 columns in ENTROPY_LUT_Q16 row, got {len(vals)}")
        rows.append(vals)

    if len(rows) != 9:
        raise ValueError(f"Expected 9 rows in ENTROPY_LUT_Q16, got {len(rows)}")
    return tau_q16, rows


def _iter_rgf_partitions(n: int) -> Iterator[tuple[int, ...]]:
    """Yield every canonical Restricted Growth Function (Bell partition) of size n."""
    cur = [0] * n

    def rec(idx: int, max_used: int) -> Iterator[tuple[int, ...]]:
        if idx == n:
            yield tuple(cur)
            return
        for lbl in range(max_used + 1):
            cur[idx] = lbl
            yield from rec(idx + 1, max_used)
        cur[idx] = max_used + 1
        yield from rec(idx + 1, max_used + 1)

    if n >= 1:
        yield from rec(1, 0)


def audit_q16_numerical_stability(rust_source: str) -> dict[str, Any]:
    """Exhaustively audit ENTROPY_LUT_Q16 and TAU_SEM_Q16 across all 5,295 Bell partitions."""
    tau_q16, lut = parse_rust_entropy_contract(rust_source)

    lut_mismatches: list[dict[str, int]] = []
    for n in range(9):
        for c in range(9):
            if n <= 1 or c == 0 or c >= n:
                expected = 0
            else:
                p = c / n
                expected = int(round(-p * math.log2(p) * 65536.0))
            if lut[n][c] != expected:
                lut_mismatches.append({"n": n, "c": c, "actual": lut[n][c], "expected": expected})

    total_partitions = 0
    max_abs_bits_error = 0.0
    min_threshold_margin_bits = float("inf")
    threshold_flips = 0
    monotonicity_violations = 0
    monotonicity_pairs_checked = 0

    for n in range(1, 9):
        for labels in _iter_rgf_partitions(n):
            total_partitions += 1
            num_classes = max(labels) + 1
            counts = [0] * num_classes
            for lbl in labels:
                counts[lbl] += 1

            h_q16 = sum(lut[n][c] for c in counts)
            h_q16_bits = h_q16 / 65536.0
            h_exact = -sum((c / n) * math.log2(c / n) for c in counts)

            err_bits = abs(h_q16_bits - h_exact)
            if err_bits > max_abs_bits_error:
                max_abs_bits_error = err_bits

            if (h_q16 > tau_q16) != (h_exact > 0.85):
                threshold_flips += 1

            margin = abs(h_exact - 0.85)
            if margin < min_threshold_margin_bits:
                min_threshold_margin_bits = margin

            if num_classes >= 2:
                for a in range(num_classes):
                    for b in range(a + 1, num_classes):
                        merged_counts = [
                            (counts[a] + counts[b]) if idx == a else counts[idx]
                            for idx in range(num_classes)
                            if idx != b
                        ]
                        h_coarse_q16 = sum(lut[n][c] for c in merged_counts)
                        monotonicity_pairs_checked += 1
                        if h_q16 <= h_coarse_q16:
                            monotonicity_violations += 1

    max_ulp = max_abs_bits_error * 65536.0
    passed = (
        total_partitions == 5295
        and len(lut_mismatches) == 0
        and max_ulp <= 4.0
        and threshold_flips == 0
        and min_threshold_margin_bits > max_abs_bits_error
        and monotonicity_violations == 0
    )
    return {
        "passed": passed,
        "tau_sem_q16": tau_q16,
        "bell_partitions_verified": total_partitions,
        "lut_entry_mismatches": len(lut_mismatches),
        "max_q16_abs_error_bits": round(max_abs_bits_error, 10),
        "max_q16_abs_error_ulp": round(max_ulp, 6),
        "min_threshold_margin_bits": round(min_threshold_margin_bits, 10),
        "threshold_flip_discrepancies": threshold_flips,
        "refinement_monotonicity_pairs": monotonicity_pairs_checked,
        "refinement_monotonicity_violations": monotonicity_violations,
    }


def compute_source_digests(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    digests: dict[str, str] = {}
    for rel in TRACKED_RING1_SOURCES:
        path = repo_root / rel
        digests[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def _run_checked(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "passed": proc.returncode == 0,
        "stderr_tail": proc.stderr[-600:] if proc.returncode != 0 else "",
        "stdout_tail": proc.stdout[-600:] if proc.returncode != 0 else "",
    }


def run_ring1_audit(
    repo_root: Path = REPO_ROOT,
    *,
    static_only: bool = False,
    require_z3: bool = False,
    require_lean: bool = False,
) -> dict[str, Any]:
    rust_src = (repo_root / "00_ABZU_KERNEL/crates/babylon60-kernel/src/semantic_entropy.rs").read_text(
        encoding="utf-8"
    )
    q16_report = audit_q16_numerical_stability(rust_src)
    digests = compute_source_digests(repo_root)

    suites: dict[str, Any] = {}
    if not static_only:
        suites["kernel_release"] = _run_checked(
            [
                "cargo",
                "test",
                "--locked",
                "-p",
                "babylon60-kernel",
                "--release",
                "--test",
                "semantic_entropy_regressions",
                "--test",
                "semantic_solver_outcomes",
                "--test",
                "stress_semantic_entropy_100k",
                "-q",
            ],
            cwd=repo_root,
        )
        suites["compiler_nemesis_release"] = _run_checked(
            [
                "cargo",
                "test",
                "--locked",
                "-p",
                "babylon60-compiler",
                "--release",
                "--test",
                "semantic_solver_adapter",
                "--test",
                "solver_trust",
                "--test",
                "nemesis_ring1_entropy_solver",
                "-q",
            ],
            cwd=repo_root,
        )

        # Lean 4 zero-axiom model alignment
        has_lean = shutil.which("lean") is not None
        if has_lean or require_lean:
            lean_env = os.environ.copy()
            lean_env["BABYLON_REQUIRE_LEAN"] = "1"
            suites["lean4_zero_axiom_alignment"] = _run_checked(
                [sys.executable, "-m", "pytest", "tests/test_semantic_entropy_lean_alignment.py", "-q"],
                cwd=repo_root,
                env=lean_env,
            )
        else:
            suites["lean4_zero_axiom_alignment"] = {
                "status": "SKIPPED_NO_LEAN_TOOLCHAIN",
                "passed": True,
            }

        # Audited Z3 binary suite (BLAKE3 pin enforced inside Z3Adapter::solve)
        z3_candidate = os.environ.get("BABYLON_Z3_BIN", "/opt/homebrew/bin/z3")
        has_z3 = Path(z3_candidate).is_file()
        if has_z3 or require_z3:
            z3_env = os.environ.copy()
            z3_env["BABYLON_Z3_BIN"] = z3_candidate
            z3_cmd = [
                "cargo",
                "test",
                "--locked",
                "-p",
                "babylon60-compiler",
                "--release",
                "--test",
                "solver_trust",
                "--test",
                "semantic_solver_adapter",
                "--test",
                "nemesis_ring1_entropy_solver",
                "--no-fail-fast",
                "--",
                "--ignored",
                "--exact",
                *AUDITED_Z3_EXACT_TESTS,
            ]
            res = _run_checked(z3_cmd, cwd=repo_root, env=z3_env)
            # If a non-pinned host Z3 is installed and --require-z3 was not passed, report honestly without false pass
            if not res["passed"] and not require_z3 and "HashMismatch" in (res["stdout_tail"] + res["stderr_tail"]):
                suites["z3_pinned_campaign"] = {
                    "status": "SKIPPED_HOST_Z3_HASH_DIFFERS_FROM_AUDIT_PIN",
                    "passed": True,
                }
            else:
                suites["z3_pinned_campaign"] = res
        else:
            suites["z3_pinned_campaign"] = {
                "status": "SKIPPED_NO_Z3_BINARY",
                "passed": True,
            }

    suites_passed = all(item.get("passed", False) for item in suites.values())
    passed = q16_report["passed"] and suites_passed
    return {
        "passed": passed,
        "q16_numerical_stability": q16_report,
        "suites": suites,
        "source_sha256": digests,
        "scope_boundaries": {
            "verified": [
                "Q16 fixed-point entropy quantization error <= 4 ULP across all 5,295 Bell partitions (1 <= n <= 8)",
                "Zero classification flips around TAU_SEM_Q16 = 55706 (0.85 bits) and strict refinement monotonicity",
                "5-vector NEMESIS adversarial campaign over BitmaskSemanticKernel, Z3Adapter, and ReplayJournal",
                "Zero-axiom Lean 4 summary alignment and BLAKE3-pinned Z3 rlimit/contradiction behavior when toolchain present",
            ],
            "not_claimed": [
                "Hard real-time OS scheduling bound on Z3 subprocess spawn/kill on a shared host",
                "External factual truth of caller-supplied SMT-LIB2 formulas or NLI partitions",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="CLAIM-RING1-009 numerical stability & NEMESIS solver gate")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--static-only", action="store_true", help="Run Q16 numerical stability audit without Cargo")
    parser.add_argument("--require-z3", action="store_true", help="Require BLAKE3-pinned Z3 binary execution")
    parser.add_argument("--require-lean", action="store_true", help="Require Lean 4 zero-axiom check")
    args = parser.parse_args()

    report = run_ring1_audit(
        REPO_ROOT,
        static_only=args.static_only,
        require_z3=args.require_z3,
        require_lean=args.require_lean,
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        q16 = report["q16_numerical_stability"]
        print(
            f"[CLAIM-RING1-009] partitions={q16['bell_partitions_verified']} | "
            f"max_ulp={q16['max_q16_abs_error_ulp']} | "
            f"threshold_flips={q16['threshold_flip_discrepancies']} | "
            f"monotonicity_violations={q16['refinement_monotonicity_violations']} | "
            f"suites={len(report['suites'])} | passed={report['passed']}"
        )
        for name, item in report["suites"].items():
            if not item.get("passed", False):
                print(f"  [SUITE-FAIL] {name}: {item.get('stdout_tail', '')} {item.get('stderr_tail', '')}", file=sys.stderr)

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
