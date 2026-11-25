"""BROKER Phase Effort Policy & CORTEX Route Attestation.

Implements configurable per-phase effort recommendations (Low / Medium / High)
and persists separated ``requested`` vs. ``provider_confirmed`` observations in
``CortexPersistLedger`` so reports never treat requested settings as confirmed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger
from babylon60.cognitive_pilot.universal_autoroute import UniversalRouteVerdict


class EffortLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


_PHASE_DEFAULTS: dict[str, tuple[EffortLevel, str]] = {
    "explore": (EffortLevel.LOW, "read-only discovery or single-file inspection"),
    "triage": (EffortLevel.LOW, "triage and bounded status checks"),
    "read_only": (EffortLevel.LOW, "bounded read-only verification"),
    "implement": (EffortLevel.MEDIUM, "implementation or multi-file change"),
    "refactor": (EffortLevel.MEDIUM, "multi-file refactoring"),
    "verification": (EffortLevel.MEDIUM, "integration or invariant verification"),
    "architecture": (EffortLevel.HIGH, "initial architecture or ring-0 design"),
    "security": (EffortLevel.HIGH, "security boundary or policy audit"),
    "formal": (EffortLevel.HIGH, "formal proof or cryptographic verification"),
}


@dataclass(frozen=True)
class PhaseRecommendation:
    phase_id: str
    phase_kind: str
    recommended_model: str
    recommended_effort: EffortLevel
    rationale: str


def _model_from_verdict(verdict: UniversalRouteVerdict | None, fallback_model: str) -> str:
    if verdict is None:
        return fallback_model
    if verdict.concrete_option:
        return verdict.concrete_option
    optimal_label = verdict.optimal.get("label") if isinstance(verdict.optimal, Mapping) else None
    if isinstance(optimal_label, str) and optimal_label:
        return optimal_label
    return fallback_model


def recommend_phase_effort(
    phase_id: str,
    phase_kind: str,
    *,
    files_touched: int = 1,
    cross_module: bool = False,
    security_or_formal: bool = False,
    verdict: UniversalRouteVerdict | None = None,
    fallback_model: str = "Gemini 4 Hydrogen",
) -> PhaseRecommendation:
    """Deterministically recommend model and minimum sufficient effort for a phase."""
    normalized_kind = phase_kind.strip().lower()
    if security_or_formal:
        effort = EffortLevel.HIGH
        rationale = "security or formal verification boundary requires High effort"
    elif normalized_kind in _PHASE_DEFAULTS:
        effort, rationale = _PHASE_DEFAULTS[normalized_kind]
    elif cross_module or files_touched > 2:
        effort = EffortLevel.MEDIUM
        rationale = f"multi-file scope (files_touched={files_touched}, cross_module={cross_module})"
    else:
        effort = EffortLevel.LOW
        rationale = "bounded single-scope operation"

    if effort == EffortLevel.LOW and (cross_module or files_touched > 2):
        effort = EffortLevel.MEDIUM
        rationale = f"escalated from {normalized_kind} due to cross-module/multi-file scope"

    model = _model_from_verdict(verdict, fallback_model=fallback_model)
    return PhaseRecommendation(
        phase_id=phase_id,
        phase_kind=normalized_kind,
        recommended_model=model,
        recommended_effort=effort,
        rationale=rationale,
    )


class BrokerAttestationRecorder:
    """Persists BROKER phase recommendations vs. provider-confirmed observations in CORTEX."""

    def __init__(self, ledger: CortexPersistLedger, agent_id: str = "babylon60-broker") -> None:
        self._ledger = ledger
        self._agent_id = agent_id

    def record_phase_route(
        self,
        check_id: str,
        recommendation: PhaseRecommendation,
        observation: Mapping[str, object],
    ) -> dict[str, object]:
        raw_req = observation.get("requested")
        requested = dict(raw_req) if isinstance(raw_req, Mapping) else {}
        raw_conf = observation.get("provider_confirmed")
        confirmed = dict(raw_conf) if isinstance(raw_conf, Mapping) else {}
        req_effort = requested.get("effort")
        conf_effort = confirmed.get("effort")
        effort_mismatch = (
            isinstance(req_effort, str) and req_effort.lower() != recommendation.recommended_effort.value.lower()
        ) or (
            isinstance(conf_effort, str) and isinstance(req_effort, str) and conf_effort.lower() != req_effort.lower()
        )
        record: dict[str, object] = {
            "check_id": check_id,
            "phase_id": recommendation.phase_id,
            "phase_kind": recommendation.phase_kind,
            "recommended": {
                "model": recommendation.recommended_model,
                "effort": recommendation.recommended_effort.value,
                "rationale": recommendation.rationale,
            },
            "requested": requested,
            "provider_confirmed": confirmed,
            "effort_mismatch": effort_mismatch,
            "model_matches": confirmed.get("model_matches"),
            "effort_confirmed": bool(confirmed.get("effort_confirmed", False)),
        }
        event = CortexEvent(
            event_type="broker.route_attestation",
            payload=record,
            cortex_taint="ring0:broker_route_attestation",
            agent_id=self._agent_id,
            domain="broker",
        )
        self._ledger.append_batch([event])
        return record

    def derive_route_attestations(self, check_id: str) -> list[dict[str, object]]:
        """Read persisted BROKER route attestations chronologically from CORTEX."""
        collected: list[dict[str, object]] = []
        before_seq: int | None = None
        for _ in range(10_000):
            page = self._ledger.query_events(
                event_type="broker.route_attestation",
                limit=1000,
                before_seq=before_seq,
            )
            if not page:
                break
            collected.extend(page)
            if len(page) < 1000:
                break
            raw_seq = page[-1]["seq"]
            assert isinstance(raw_seq, int)
            before_seq = raw_seq
        else:
            raise RuntimeError("broker.route_attestation pagination exceeded bound")
        collected.reverse()

        results: list[dict[str, object]] = []
        for row in collected:
            payload = row.get("payload")
            if isinstance(payload, str):
                payload = json.loads(payload)
            if isinstance(payload, dict) and payload.get("check_id") == check_id:
                results.append(payload)
        return results
