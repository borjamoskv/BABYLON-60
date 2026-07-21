"""
Pytest unit tests for Escohotado Realidad y Substancia Process Ontology Engine.
Rule Compliance: Ω10 (SQLite Isolation), Ω26 (Specific Exception Handling).
"""

import os
import sqlite3
from pathlib import Path
from cortex.escohotado_substance_ontology import (
    compute_substance_state,
    run_substance_grid,
)

TEST_DB = str(
    Path(__file__).resolve().parent.parent / "scratch" / "test_escohotado_substance.db"
)


def test_substance_state_monism():
    # C5-REAL Monistic Process Reality: Low dualism, high actuality and potentiality
    res_c5 = compute_substance_state(
        potentiality=1.0, actuality=1.0, dualism_separation=0.0
    )
    assert res_c5["substance_exergy_density"] == 1.0
    assert "MONISTIC_PROCESS_REALITY" in res_c5["ontological_regime"]

    # C4-SIM Cartesian/Kantian Split: High dualism separation
    res_dual = compute_substance_state(
        potentiality=1.0, actuality=1.0, dualism_separation=0.9
    )
    assert res_dual["substance_exergy_density"] == 0.1
    assert "CARTESIAN_KANTIAN_DUALIST_SPLIT" in res_dual["ontological_regime"]


def test_grid_execution_and_persistence():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    results = run_substance_grid([0.5, 1.0], [0.5, 1.0], [0.0, 1.0], db_path=TEST_DB)
    assert len(results) == 8

    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM substance_ontology")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 8
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
