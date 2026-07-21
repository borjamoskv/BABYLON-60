"""
Pytest unit tests for CORTEX Escohotado Chaos & Thermodynamic Engine.
Rule Compliance: Ω31 (Entropy Verification), Ω26 (Specific Exception Handling).
"""

import os
import sqlite3
from pathlib import Path
from cortex.escohotado_chaos_engine import (
    compute_entropy,
    simulate_system,
    run_simulation_grid,
)

TEST_DB = str(
    Path(__file__).resolve().parent.parent / "scratch" / "test_escohotado_chaos.db"
)


def test_entropy_computation() -> None:
    # Monotonic constant sequence -> Zero entropy
    seq_constant = [0.5] * 100
    assert compute_entropy(seq_constant) == 0.0

    # Distributed sequence -> Non-zero entropy
    seq_var = [i / 100.0 for i in range(100)]
    s = compute_entropy(seq_var)
    assert s > 1.0


def test_simulation_system_regimes() -> None:
    # Coercive collapse case
    res_freeze = simulate_system(r=2.5, c=0.5)
    assert res_freeze["regime"] in ["SYSTEMIC_COLLAPSE", "STAGNANT_COERCIVE_FREEZE"]

    # Complex self-organization case
    res_chaos = simulate_system(r=3.9, c=0.0)
    assert res_chaos["entropy_s"] > 1.0


def test_grid_execution_and_db_persistence() -> None:
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    results = run_simulation_grid([3.5, 3.8], [0.0, 0.1], db_path=TEST_DB)
    assert len(results) == 4

    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM chaos_metrics")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 4
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
