"""Isolated measurement semantics; no hardware or render processes are launched."""

import json
import subprocess
import time

import pytest

from scripts.c5_thermo import silicon_thermal_telemetry as thermal
from babylon60.transducers import render_exergy_guard as render


@pytest.mark.parametrize("failure", [OSError("unavailable"), subprocess.CalledProcessError(1, "pmset")])
def test_thermal_failure_does_not_claim_nominal(monkeypatch, failure):
    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(subprocess, "run", fail)
    data = thermal.get_thermal_telemetry()
    assert data["status"] == "No medido"
    assert data["cpu"] == "No identificado"


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("", "No medido"),
        ("unexpected output", "No medido"),
        ("No thermal warning level has been recorded", "Nominal"),
        ("Thermal warning level: 1", "Degradado"),
    ],
)
def test_thermal_classifies_only_recognized_output(monkeypatch, output, expected):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, output))
    assert thermal.get_thermal_telemetry()["status"] == expected


def test_cache_receipt_reports_unmeasured_values_as_null(tmp_path, monkeypatch):
    cache = render.RenderCacheStore(tmp_path / "cache")
    manifest_hash = "a" * 64
    source = tmp_path / "source.mp4"
    source.write_bytes(b"isolated test artifact")
    original = render.RenderExergyReceipt(
        manifest_hash=manifest_hash,
        tier="final",
        cache_hit=False,
        verified=True,
        output_path=str(source),
        wall_time_s=1.0,
        estimated_joules=None,
        exergy_phi=None,
        involuntary_cs=None,
        max_rss_mb=None,
        metrics={"width": 1},
    )
    cache.store(manifest_hash, source, original)
    ticks = iter([10.0, 10.5])
    monkeypatch.setattr(time, "perf_counter", lambda: next(ticks))
    destination = tmp_path / "output.mp4"
    receipt = cache.lookup(manifest_hash, destination)
    assert receipt is not None
    assert receipt.cache_hit
    assert receipt.wall_time_s == 0.5
    assert destination.read_bytes() == b"isolated test artifact"
    data = json.loads(json.dumps(receipt.to_dict()))
    for field in ("estimated_joules", "exergy_phi", "involuntary_cs", "max_rss_mb"):
        assert data[field] is None
    assert data["metrics"] == {"width": 1}
