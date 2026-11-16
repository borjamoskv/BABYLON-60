"""CLAIM-RING1-009 verification: Q16 numerical stability, monotonicity, and adversarial sensitivity."""

from __future__ import annotations

import json
import subprocess
import sys

from scripts.c5_quality_gates.audit_ring1_entropy_solver import (
    REPO_ROOT,
    SEMANTIC_ENTROPY_RS,
    TRACKED_RING1_SOURCES,
    audit_q16_numerical_stability,
    compute_source_digests,
)


def test_q16_numerical_stability_and_monotonicity_on_live_rust_source() -> None:
    rust_src = SEMANTIC_ENTROPY_RS.read_text(encoding="utf-8")
    report = audit_q16_numerical_stability(rust_src)
    assert report["passed"] is True
    assert report["tau_sem_q16"] == 55706
    assert report["bell_partitions_verified"] == 5295
    assert report["lut_entry_mismatches"] == 0
    assert 0.0 < report["max_q16_abs_error_ulp"] <= 4.0
    assert report["threshold_flip_discrepancies"] == 0
    assert report["min_threshold_margin_bits"] > report["max_q16_abs_error_bits"]
    assert report["refinement_monotonicity_pairs"] > 20_000
    assert report["refinement_monotonicity_violations"] == 0


def test_q16_auditor_catches_lut_corruption_threshold_drift_and_monotonicity_inversion() -> None:
    """Prove non-vacuity (INV_C5_EMPTY_TAUTOLOGY): mutated LUT or threshold fails closed."""
    live_src = SEMANTIC_ENTROPY_RS.read_text(encoding="utf-8")

    # 1. Corrupting a single LUT entry by +2 ULP triggers lut_entry_mismatches > 0
    corrupted_lut = live_src.replace("34624", "34626", 1)
    rep_lut = audit_q16_numerical_stability(corrupted_lut)
    assert rep_lut["passed"] is False
    assert rep_lut["lut_entry_mismatches"] >= 1

    # 2. Drifting TAU_SEM_Q16 from 55706 (0.85 bits) to 65536 (1.00 bits) causes classification flips vs 0.85
    drifted_tau = live_src.replace("pub const TAU_SEM_Q16: u32 = 55706;", "pub const TAU_SEM_Q16: u32 = 65536;")
    rep_tau = audit_q16_numerical_stability(drifted_tau)
    assert rep_tau["passed"] is False
    assert rep_tau["threshold_flip_discrepancies"] > 0

    # 3. Zeroing n=2, c=1 contribution (32768 -> 0) breaks strict refinement monotonicity ({0},{1} vs {0,1})
    broken_mono = live_src.replace(
        "/* n=2 */ [0, 32768, 0, 0, 0, 0, 0, 0, 0]",
        "/* n=2 */ [0, 0, 0, 0, 0, 0, 0, 0, 0]",
    )
    rep_mono = audit_q16_numerical_stability(broken_mono)
    assert rep_mono["passed"] is False
    assert rep_mono["refinement_monotonicity_violations"] >= 1


def test_source_digests_cover_all_tracked_ring1_files() -> None:
    digests = compute_source_digests(REPO_ROOT)
    assert set(digests.keys()) == set(TRACKED_RING1_SOURCES)
    assert all(len(val) == 64 for val in digests.values())


def test_cli_static_gate_exits_zero_with_explicit_scope_boundaries() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/c5_quality_gates/audit_ring1_entropy_solver.py"),
            "--static-only",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["passed"] is True
    assert payload["q16_numerical_stability"]["bell_partitions_verified"] == 5295
    assert len(payload["scope_boundaries"]["not_claimed"]) == 2
