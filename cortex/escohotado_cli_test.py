# C5-REAL EXERGY CERTIFIED
"""
Pytest unit tests for Escohotado Unified CLI Transducer.
Rule Compliance: Ω10 (SQLite Isolation), Ω26 (Specific Exception Handling).
"""

from cortex.escohotado_cli import query_chaos_db, query_econ_db, query_substance_db

def test_cli_ledger_queries() -> None:
    chaos_data = query_chaos_db()
    econ_data = query_econ_db()
    substance_data = query_substance_db()

    assert len(chaos_data) >= 16
    assert len(econ_data) >= 15
    assert len(substance_data) >= 27

    # Verify keys
    assert "entropy_s" in chaos_data[0]
    assert "risk_premium_multiplier" in econ_data[0]
    assert "substance_exergy_density" in substance_data[0]
