"""Acceptance tests for BROKER phase effort policy and CORTEX route attestation."""

from __future__ import annotations

from pathlib import Path

from babylon60.bft.cortex_persist_ledger import CortexPersistLedger
from babylon60.cognitive_pilot.broker_policy import (
    BrokerAttestationRecorder,
    EffortLevel,
    recommend_phase_effort,
)
from babylon60.cognitive_pilot.execution import Provider
from babylon60.cognitive_pilot.universal_autoroute import evaluate_universal_route


def _provider_config(model: str, effort: str) -> dict[str, object]:
    return {
        "backend": "gemini_compat",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": model,
        "reasoning_effort": effort,
        "max_tokens": 4096,
        "max_calls": 4,
        "timeout": 10.0,
        "temperature": 0.0,
        "memory_bytes": 4096,
    }


def test_broker_phase_recommendations_and_requested_vs_confirmed_in_cortex(tmp_path: Path) -> None:
    verdict = evaluate_universal_route(
        model="Gemini 4 Hydrogen",
        mode="Medium",
        task_text="Audita cuatro directorios y reporta cobertura parcial sin inventar.",
        host="antigravity_ui",
    )

    rec_triage = recommend_phase_effort("phase-1", "triage", verdict=verdict)
    rec_impl = recommend_phase_effort("phase-2", "implement", files_touched=3, cross_module=True, verdict=verdict)
    rec_formal = recommend_phase_effort("phase-3", "formal", security_or_formal=True, verdict=verdict)

    assert rec_triage.recommended_effort == EffortLevel.LOW
    assert rec_impl.recommended_effort == EffortLevel.MEDIUM
    assert rec_formal.recommended_effort == EffortLevel.HIGH

    provider = Provider(_provider_config(model="gemini-4-hydrogen", effort="low"))

    # Case 1: Provider confirms model but omits reasoning_effort -> effort_confirmed must stay False.
    provider._consume(
        {
            "id": "resp-1",
            "model": "gemini-4-hydrogen",
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            "choices": [{"message": {"content": '{"action": "final"}'}}],
        }
    )

    # Case 2: Provider returns a different model and explicitly confirms a different effort.
    provider._consume(
        {
            "id": "resp-2",
            "model": "gemini-4-argon",
            "reasoning_effort": "high",
            "usage": {"prompt_tokens": 120, "completion_tokens": 60, "total_tokens": 180},
            "choices": [{"message": {"content": '{"action": "final"}'}}],
        }
    )

    obs1, obs2 = provider.observations
    assert obs1["requested"] == {"model": "gemini-4-hydrogen", "effort": "low"}
    assert obs1["provider_confirmed"] == {
        "model": "gemini-4-hydrogen",
        "effort": None,
        "model_matches": True,
        "effort_confirmed": False,
    }

    assert obs2["requested"] == {"model": "gemini-4-hydrogen", "effort": "low"}
    assert obs2["provider_confirmed"] == {
        "model": "gemini-4-argon",
        "effort": "high",
        "model_matches": False,
        "effort_confirmed": True,
    }

    ledger = CortexPersistLedger(tmp_path / "broker_attestation.db")
    recorder = BrokerAttestationRecorder(ledger)
    recorder.record_phase_route("chk-broker-001", rec_triage, obs1)
    recorder.record_phase_route("chk-broker-001", rec_impl, obs2)

    persisted = recorder.derive_route_attestations("chk-broker-001")
    assert len(persisted) == 2

    assert persisted[0]["phase_id"] == "phase-1"
    rec0 = persisted[0]["recommended"]
    assert isinstance(rec0, dict) and rec0["effort"] == "Low"
    assert persisted[0]["requested"] == {"model": "gemini-4-hydrogen", "effort": "low"}
    conf0 = persisted[0]["provider_confirmed"]
    assert isinstance(conf0, dict) and conf0["effort"] is None
    assert persisted[0]["effort_confirmed"] is False
    assert persisted[0]["effort_mismatch"] is False

    assert persisted[1]["phase_id"] == "phase-2"
    rec1 = persisted[1]["recommended"]
    assert isinstance(rec1, dict) and rec1["effort"] == "Medium"
    assert persisted[1]["model_matches"] is False
    assert persisted[1]["effort_confirmed"] is True
    assert persisted[1]["effort_mismatch"] is True
