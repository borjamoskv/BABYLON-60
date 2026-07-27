import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
import subprocess

from babylon60.swarm.omega_daemon import ExergyGuard, EntropySensor

def test_exergy_guard_evaluate():
    guard = ExergyGuard(max_exergy_joules=Decimal("100.0"))
    assert guard.evaluate(Decimal("50.0")) is True
    assert guard.evaluate(Decimal("150.0")) is False

def test_exergy_guard_consume():
    guard = ExergyGuard(max_exergy_joules=Decimal("100.0"))
    guard.consume(Decimal("40.0"))
    assert guard.current_exergy == Decimal("60.0")

    # Check it doesn't go below 0
    guard.consume(Decimal("100.0"))
    assert guard.current_exergy == Decimal("0.0")

@patch("subprocess.run")
def test_check_ram_free_mb(mock_run):
    guard = ExergyGuard()

    mock_run.return_value = MagicMock(stdout="Pages free: 1000.")
    ram = guard.check_ram_free_mb()
    assert ram == (1000 * 16384) / (1024 * 1024)

@patch("subprocess.run")
def test_get_ram_pressure(mock_run):
    guard = ExergyGuard()

    mock_run.return_value = MagicMock(stdout="System RAM pressure: Normal")
    assert guard.get_ram_pressure() == "Normal"

@patch("subprocess.run")
def test_reclaim(mock_run):
    guard = ExergyGuard()

    mock_run.side_effect = [
        MagicMock(stdout="Pages free: 1000."), # before
        MagicMock(stdout=""), # purge
        MagicMock(stdout="Pages free: 2000.") # after
    ]
    reclaimed, status = guard.reclaim()
    assert status == "OK"
    assert reclaimed > 0

@pytest.mark.asyncio
async def test_entropy_sensor_scan():
    sensor = EntropySensor()
    entropy = await sensor.scan()
    assert isinstance(entropy, Decimal)
    assert entropy >= 0
