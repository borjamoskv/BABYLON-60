# [C5-REAL] Exergy-Maximized

from __future__ import annotations

import pytest

from babylon60.extensions.hypervisor.belief_object import (
    BeliefConfidence,
    BeliefObject,
    VerdictAction,
)
from babylon60.extensions.llm._models import IntentProfile
from babylon60.extensions.llm.cognitive_handoff import CognitiveHandoff

# ─── IntentProfile Extensions ───────────────────────────────────────────────


class TestCognitiveIntents:
    def test_belief_audit_exists(self):
        assert IntentProfile.BELIEF_AUDIT.value == "belief_audit"

    def test_episodic_processing_exists(self):
        assert IntentProfile.EPISODIC_PROCESSING.value == "episodic_processing"

    def test_original_intents_preserved(self):
        """Regression: new intents must not break existing ones."""
        assert IntentProfile.CODE.value == "code"
        assert IntentProfile.REASONING.value == "reasoning"
        assert IntentProfile.CREATIVE.value == "creative"
        assert IntentProfile.ARCHITECT.value == "architect"
        assert IntentProfile.GENERAL.value == "general"


# ─── CognitiveHandoff (No Router - Heuristic Mode) ─────────────────────────


class TestCognitiveHandoffNoRouter:
    """Test CognitiveHandoff without a router (offline/testing mode)."""

    def _make_handoff(self) -> CognitiveHandoff:
        return CognitiveHandoff(router=None)

    @pytest.mark.asyncio
    async def test_c1_belief_skipped(self):
        """C1 hypothesis beliefs should be auto-skipped by prescreen."""
        handoff = self._make_handoff()
        belief = BeliefObject(
            proposition="Maybe the sky is green",
            project="test",
            confidence_score=0.1,
        )
        verdict = await handoff.process_belief(belief)
        assert verdict.action == VerdictAction.SKIP

    @pytest.mark.asyncio
    async def test_c2_belief_accepted(self):
        """C2+ beliefs should pass through audit in no-router mode."""
        handoff = self._make_handoff()
        belief = BeliefObject(
            proposition="SQLite is suitable for local persistence",
            project="cortex",
            confidence_score=0.4,
        )
        verdict = await handoff.process_belief(belief)
        assert verdict.action == VerdictAction.ACCEPT

    @pytest.mark.asyncio
    async def test_axiomatic_context_no_escalation_without_router(self):
        """Without router, axiomatic context doesn't trigger real Opus call."""
        handoff = self._make_handoff()
        belief = BeliefObject(
            proposition="New claim about entropy",
            project="physics",
            confidence_score=0.7,
        )
        axiomatic_ctx = BeliefObject(
            proposition="Entropy always increases",
            project="physics",
            confidence_score=0.99,
        )
        verdict = await handoff.process_belief(belief, [axiomatic_ctx])
        # Without router, escalation to Opus returns ACCEPT (no real LLM)
        assert verdict.action == VerdictAction.ACCEPT

    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        """Telemetry counters should track escalations and quarantines."""
        handoff = self._make_handoff()
        assert handoff.stats["total_tokens"] == 0
        assert handoff.stats["escalation_count"] == 0
        assert handoff.stats["quarantine_count"] == 0


# ─── CognitiveHandoff Invariants ────────────────────────────────────────────


class TestCognitiveHandoffInvariants:
    """Test the three core invariants of the Cognitive Handoff."""

    def test_involves_axiomatics_true(self):
        """Invariant check: C5 beliefs trigger premium escalation."""
        axiomatic = BeliefObject(
            proposition="Fundamental truth",
            project="test",
            confidence_score=0.99,
        )
        normal = BeliefObject(
            proposition="Regular claim",
            project="test",
            confidence_score=0.7,
        )
        assert CognitiveHandoff._involves_axiomatics(normal, [axiomatic]) is True

    def test_involves_axiomatics_false(self):
        """No C5 beliefs → no premium escalation."""
        beliefs = [BeliefObject(proposition=f"b-{i}", project="test") for i in range(3)]
        candidate = BeliefObject(proposition="candidate", project="test")
        assert CognitiveHandoff._involves_axiomatics(candidate, beliefs) is False

    def test_format_belief_for_prompt(self):
        """Prompt formatting should include belief content and context."""
        belief = BeliefObject(
            proposition="The API uses gRPC",
            project="cortex",
            confidence_score=0.7,
        )
        context = [
            BeliefObject(
                proposition="The API uses REST",
                project="cortex",
                confidence_score=0.9,
            ),
        ]
        prompt = CognitiveHandoff._format_belief_for_prompt(belief, context)
        assert "The API uses gRPC" in prompt
        assert "The API uses REST" in prompt
        assert "0.7" in prompt
        assert "0.9" in prompt

    def test_default_providers(self):
        """Default provider assignments should match the plan."""
        handoff = CognitiveHandoff(router=None)
        assert handoff._architect == "anthropic"
        assert handoff._auditor_premium == "anthropic"
        assert handoff._auditor_economic == "z_ai"
        assert handoff._infra == "gemini"
