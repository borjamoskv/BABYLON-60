# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import pytest
from benchmarks.encb.runner import ENCBRunner


def test_encb_runner_metrics():
    """Verify that all ENCB metrics are calculated with both baselines."""
    runner = ENCBRunner()

    # 1. Persistent False Belief Rate (PFBR)
    pfbr = runner.persistent_false_belief_rate()
    assert "cortex_full" in pfbr
    assert "naive_overwrite" in pfbr
    assert 0.0 <= pfbr["cortex_full"] <= 1.0
    assert 0.0 <= pfbr["naive_overwrite"] <= 1.0

    # 2. Epistemic Debt Integral (EDI)
    edi = runner.epistemic_debt_integral()
    assert "cortex_full" in edi
    assert "naive_overwrite" in edi
    assert edi["cortex_full"] >= 0.0
    assert edi["naive_overwrite"] >= 0.0

    # 3. Recovery Round
    rec = runner.recovery_round()
    assert "cortex_full" in rec
    assert "naive_overwrite" in rec
    assert rec["cortex_full"] >= 0.0
    assert rec["naive_overwrite"] >= 0.0

    # 4. Contamination Latency
    lat = runner.contamination_latency()
    assert "cortex_full" in lat
    assert "naive_overwrite" in lat
    assert lat["cortex_full"] > 0.0
    assert lat["naive_overwrite"] > 0.0

    # 5. Structural Contradiction Mass
    mass = runner.structural_contradiction_mass()
    assert "cortex_full" in mass
    assert "naive_overwrite" in mass
    assert 0.0 <= mass["cortex_full"] <= 1.0
    assert 0.0 <= mass["naive_overwrite"] <= 1.0


def test_encb_runner_run_all():
    """Verify the overall run_all interface returns a valid exit code."""
    runner = ENCBRunner()
    exit_code = runner.run_all()
    assert exit_code in (0, 1)
