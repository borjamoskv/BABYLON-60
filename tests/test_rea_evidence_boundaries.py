"""Negative controls for static REA claims; no application or hardware required."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).absolute().parents[1]
sys.path[:0] = [str(ROOT / "01_KISH_ENGINE"), str(ROOT / "02_EDIN_SWARMS")]
from babylon60.transducers.clean_room_aot_dissector import CleanRoomAotDissector as C  # noqa: E402


@pytest.mark.parametrize("target", ["claw-code", "openclaw", "deepseek-harness"])
def test_missing_target_evidence_is_rejected(target):
    with pytest.raises(ValueError, match="MISSING_EVIDENCE"):
        C.dissect_external_harness_target(target)


def test_hardware_words_in_comments_do_not_attest_hardware():
    audit = C.audit_hardware_confinement("// align(64) Ordering::Acquire Ordering::Release MAP_SHARED SecureEnclave")
    assert audit.confinement_preserved is False
    assert "RUNTIME_CONFINEMENT_EVIDENCE" in audit.missing_invariants


@pytest.mark.parametrize("target", ["claw-code", "openclaw", "deepseek-harness"])
def test_explicit_simulation_cannot_be_promoted_to_verification(target):
    report = C.dissect_external_harness_target(target, simulation=True)
    assert report.verdict_code == "REA_SUBAGENT_AOT_SIMULATED"
    assert report.real_verification is False
    with pytest.raises(ValueError, match="UNVERIFIED"):
        C.synthesize_harness_aot_bridge(report)
    bridge = C.synthesize_harness_aot_bridge(report, simulation=True)
    assert bridge.manifest_payload["execution_allowed"] is False
    assert "mcp_server" not in bridge.manifest_payload
    assert "cordis_plugin" not in bridge.manifest_payload
    assert bridge.portable_launcher == bridge.loopback_endpoint == ""


def test_unrelated_real_binary_and_complete_fixture_are_not_verified():
    fixture = C.build_canonical_harness_fixture("claw-code")
    inputs = {key: value for key, value in fixture.items() if key not in ("target_kind", "subagent_id")}
    inputs["binary_payload"] = Path("/bin/ls").read_bytes()
    report = C.dissect_external_harness_target("claw-code", **inputs)
    assert report.real_verification is False
    assert report.verdict_code == "REA_SUBAGENT_AOT_REJECTED"
    with pytest.raises(ValueError, match="UNVERIFIED"):
        C.synthesize_harness_aot_bridge(report, simulation=True)


def test_invalid_binary_fails_even_in_simulation():
    report = C.dissect_external_harness_target("claw-code", binary_payload=b"not a binary", simulation=True)
    assert report.verdict_code == "REA_SUBAGENT_AOT_REJECTED"
    assert report.real_verification is False


@pytest.mark.parametrize("action", ["dissect", "bridge", "swarm"])
def test_cli_default_does_not_claim_verification(action, tmp_path):
    import json
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(ROOT / "01_KISH_ENGINE/babylon60/cli/main_dispatcher.py"), "rea", action, "--json"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert report["real_verification"] is False
    assert "MISSING_EVIDENCE" in report["error"]


def test_topology_missing_evidence_fails(tmp_path):
    import asyncio
    from agents_archi.topologies.rea_harness_topology import ReaHarnessSwarmTopology

    with pytest.raises((ValueError, RuntimeError), match="MISSING_EVIDENCE"):
        asyncio.run(ReaHarnessSwarmTopology().execute_rea_swarm(lock_path=str(tmp_path / "lock")))
