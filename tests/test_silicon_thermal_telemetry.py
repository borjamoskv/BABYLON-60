"""Tests para la telemetría térmica de silicio en Apple Silicon / Darwin (C5-REAL)."""

from scripts.c5_thermo.silicon_thermal_telemetry import (
    get_cpu_brand,
    get_thermal_pressure,
    get_thermal_telemetry,
)


def test_get_cpu_brand():
    brand = get_cpu_brand()
    assert isinstance(brand, str)
    assert len(brand) > 0


def test_get_thermal_pressure():
    pressure = get_thermal_pressure()
    assert isinstance(pressure, str)
    assert len(pressure) > 0


def test_get_thermal_telemetry_structure():
    telemetry = get_thermal_telemetry()
    assert "status" in telemetry
    assert "cpu" in telemetry
    assert "pressure" in telemetry
    assert "summary" in telemetry
    assert telemetry["status"] in {"Nominal", "Degradado"}
    assert telemetry["summary"].startswith(telemetry["status"])
    assert telemetry["cpu"] in telemetry["summary"]
