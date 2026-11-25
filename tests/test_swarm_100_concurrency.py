# ============================================================================
# BABYLON-60 v5.0 — TEST CONCURRENTE SWARM-100 (SHARUR-3600)
# ============================================================================
from scripts.c5_quality_gates.swarm_100_stress_campaign import run_swarm_100_campaign


def test_swarm_100_concurrent_campaign() -> None:
    """Ejecuta la campaña de 100 workers concurrentes verificando contención y fail-closed rate."""
    sitrep, telemetries = run_swarm_100_campaign()

    assert sitrep["metrics"]["total_workers"] == 100
    assert sitrep["adjudication"]["legitimate_accepted"] == 50
    assert sitrep["adjudication"]["adversarial_blocked_fail_closed"] == 50
    assert sitrep["adjudication"]["critical_errors"] == 0
    assert sitrep["adjudication"]["fail_closed_rate_pct"] == 100.0
    assert sitrep["adjudication"]["merkle_integrity_verified"] is True
    assert len(telemetries) == 100
