"""Regression controls for exaggerated agent counts and missing binary evidence."""

import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).absolute().parents[1] / "scripts/c5_quality_gates/grok_sampling_benchmark.py"
spec = importlib.util.spec_from_file_location("grok_sampling_benchmark", SCRIPT)
assert spec is not None and spec.loader is not None
grok = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grok)


@pytest.mark.parametrize(
    "data", [b"", b"\0" * 1048576, b"not a binary" * 300, struct.pack("<8I", 0xFEEDFACF, 0x100000C, 0, 2, 1, 24, 0, 0)]
)
def test_invalid_binary_never_verifies(data: bytes, tmp_path: Path) -> None:
    binary = tmp_path / "fake"
    binary.write_bytes(data)
    report = grok.run_benchmark(binary, sample_only=True)
    assert report["passed"] is False
    assert report["verified_agents"] == 0
    assert report["tasks_executed"] == 0


def test_short_structural_header_is_not_a_full_sample(tmp_path: Path) -> None:
    binary = tmp_path / "short"
    binary.write_bytes(struct.pack("<8I", 0xFEEDFACF, 0x100000C, 0, 2, 1, 8, 0, 0) + struct.pack("<2I", 0x19, 8))
    report = grok.run_benchmark(binary, sample_only=True)
    assert report["passed"] is False
    assert report["tasks_executed"] == 0


def test_missing_binary_fails(tmp_path: Path) -> None:
    report = grok.run_benchmark(tmp_path / "absent", sample_only=True)
    assert report["status"] == "FAIL_INVALID_INPUT"
    assert report["real_verification"] is False


def test_real_binary_is_not_evidence_of_grok_agents() -> None:
    report = grok.run_benchmark(Path("/bin/ls"))
    assert report["passed"] is False
    assert report["real_verification"] is False
    assert report["tasks_executed"] == 0


def test_explicit_sampling_counts_actual_tasks_only() -> None:
    report = grok.run_benchmark(Path("/bin/ls"), sample_only=True)
    # Test fixture is a local system executable; it is not presented as Grok.
    if sys.platform != "darwin":
        assert report["passed"] is False
        return
    assert report["status"] == "SAMPLING_COMPLETED"
    assert report["tasks_executed"] == len(report["samples"]) == 360
    assert report["bytes_sampled_with_repetition"] == 360 * 256
    assert report["verified_agents"] == 0
    assert report["verification_rate"] is None
    assert report["real_verification"] is False
    assert "mean_exergy" not in report


def test_explicit_simulation_cannot_be_promoted() -> None:
    report = grok.run_benchmark(None, simulation=True)
    assert report["status"] == "SIMULATION_COMPLETED"
    assert report["mode"] == "simulation"
    assert report["verified_agents"] == 0
    assert report["real_verification"] is False


@pytest.mark.parametrize("args", [[], ["/nonexistent"], ["/bin/ls"]])
def test_grok_cli_verification_fails(args: list[str], tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=tmp_path, capture_output=True, text=True, timeout=30
    )
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["real_verification"] is False
    assert not list(tmp_path.iterdir())
