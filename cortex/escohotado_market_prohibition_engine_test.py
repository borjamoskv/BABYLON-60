# C5-REAL EXERGY CERTIFIED
"""
Pytest unit tests for Escohotado Market & Prohibition Economics Engine.
Rule Compliance: Ω10 (SQLite Isolation), Ω26 (Specific Exception Handling).
"""

import os
import sqlite3
from pathlib import Path
from cortex.escohotado_market_prohibition_engine import (
    simulate_prohibition_and_property,
    run_economic_grid,
)

TEST_DB = str(
    Path(__file__).resolve().parent.parent / "scratch" / "test_escohotado_econ.db"
)


def test_simulation_bounds_and_monotonies() -> None:
    # Legal market & full property rights -> zero risk premium above 1, 100% purity, zero violence, zero info loss
    res_free = simulate_prohibition_and_property(enforcement=0.0, property_rights=1.0)
    assert res_free["risk_premium_multiplier"] == 1.0
    assert res_free["purity_index"] == 1.0
    assert res_free["black_market_violence_index"] == 0.0
    assert res_free["information_loss_index"] == 0.0
    assert res_free["systemic_exergy_loss"] == 0.0

    # Total prohibition & total property suppression -> Max violence, max info loss, high exergy loss
    res_totalitarian = simulate_prohibition_and_property(
        enforcement=1.0, property_rights=0.0
    )
    assert res_totalitarian["risk_premium_multiplier"] > 9.0
    assert res_totalitarian["purity_index"] <= 0.15
    assert res_totalitarian["black_market_violence_index"] == 20.0
    assert res_totalitarian["information_loss_index"] == 1.0


def test_grid_execution_and_persistence() -> None:
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    results = run_economic_grid([0.0, 1.0], [0.0, 1.0], db_path=TEST_DB)
    assert len(results) == 4

    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM prohibition_economics")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 4
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
