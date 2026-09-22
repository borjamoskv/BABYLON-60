import pytest
import asyncio
from babylon60.c5_telemetry import (
    SomaticMarkovBlanket,
    SomaticStatus,
    ThermodynamicValve,
)


def test_somatic_markov_blanket_optimal_regime():
    blanket = SomaticMarkovBlanket()
    reading = blanket.evaluate(
        heart_rate_bpm=68.0,
        hrv_sdnn_ms=55.0,
        package_temp_celsius=42.0,
        uninterrupted_duty_cycles=1000,
    )
    assert reading.status == SomaticStatus.OPTIMAL_THROUGHPUT
    assert reading.burnout_risk_score < 0.25


def test_somatic_markov_blanket_cooling_throttle():
    blanket = SomaticMarkovBlanket()
    # HR elevado y temp moderada -> throttle
    reading = blanket.evaluate(
        heart_rate_bpm=120.0,
        hrv_sdnn_ms=22.0,
        package_temp_celsius=88.0,
        uninterrupted_duty_cycles=5000,
    )
    assert reading.status == SomaticStatus.COOLING_THROTTLE_REQUIRED
    assert reading.burnout_risk_score > 0.5


def test_somatic_markov_blanket_thermal_apoptosis():
    blanket = SomaticMarkovBlanket()
    # Temperatura crítica o agotamiento extremo
    reading = blanket.evaluate(
        heart_rate_bpm=155.0,
        hrv_sdnn_ms=10.0,
        package_temp_celsius=102.0,
        uninterrupted_duty_cycles=100_000_000,
    )
    assert reading.status == SomaticStatus.THERMAL_APOPTOSIS
    assert reading.burnout_risk_score >= 0.8


@pytest.mark.asyncio
async def test_somatic_telemetry_valve_ingestion():
    valve = ThermodynamicValve()
    valve.start()
    blanket = SomaticMarkovBlanket(valve=valve)

    reading = await blanket.record_and_ingest(
        heart_rate_bpm=72.0,
        hrv_sdnn_ms=48.0,
        package_temp_celsius=45.0,
        uninterrupted_duty_cycles=2000,
    )
    assert reading.status == SomaticStatus.OPTIMAL_THROUGHPUT

    # Permitir que el worker consuma el evento
    await asyncio.sleep(0.05)
    await valve.stop()
