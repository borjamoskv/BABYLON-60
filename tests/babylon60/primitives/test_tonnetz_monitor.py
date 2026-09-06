from babylon60.primitives.tonnetz_monitor import (
    compute_shannon_entropy,
    evaluate_tonnetz_oversight,
)


def test_ax_tz_1_homeostatic_triadic_compliance():
    """Verify AX-TZ-1: Zero anergy produces pure C major triad with 0 cents detuning."""
    trace = [1.0, 0.0, 0.0]
    entropy = compute_shannon_entropy(trace)
    exergy = 0.05

    telemetry = evaluate_tonnetz_oversight(entropy, exergy)

    assert telemetry.state == "HOMEOSTATIC_PURE"
    assert telemetry.triad_notes == ["C", "E", "G"]
    assert telemetry.is_major is True
    assert telemetry.microtonal_cents_offset == 0.0
    assert telemetry.eu_ai_act_status == "OVERSIGHT_ACTIVE_STABLE"


def test_ax_tz_2_dissonance_alert_trigger():
    """Verify AX-TZ-2: High entropy and exergy trigger microtonal detuning and alert status."""
    trace = [0.25, 0.25, 0.25, 0.25]
    entropy = compute_shannon_entropy(trace)  # 2.0 bits
    exergy = 1.5

    telemetry = evaluate_tonnetz_oversight(entropy, exergy)

    assert telemetry.state == "ANERGY_ALERT_DISSONANT"
    assert telemetry.is_major is False
    assert telemetry.microtonal_cents_offset > 50.0
    assert telemetry.eu_ai_act_status == "OVERSIGHT_ALERT_TRIGGERED"
