# [C5-REAL] Exergy-Maximized

"""CORTEX Hypervisor - Belief Engine.

Cognitive governance layer that connects the CognitiveHandoff orchestrator
to the AgencyHypervisor pipeline. Sits between remember() and the database,
intercepting new facts to check for belief contradictions.

Implements Invariant 2: Auditor quarantine overrides all execution.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import TYPE_CHECKING

from babylon60.extensions.hypervisor.belief_object import (
    BeliefConfidence,
    BeliefObject,
    BeliefStatus,
    BeliefVerdict,
    ProvenanceEnvelope,
    VerdictAction,
)

if TYPE_CHECKING:
    from babylon60.extensions.llm.cognitive_handoff import CognitiveHandoff

logger = logging.getLogger(__name__)


class BeliefEngine:
    """Cognitive governance layer for the Hypervisor.

    Evaluates incoming content against existing beliefs using the
    CognitiveHandoff quad-model cascade. If a contradiction is
    detected, the belief is quarantined - this verdict is final
    and cannot be overridden by downstream components.

    Usage::

        engine = BeliefEngine(cortex_engine, cognitive_handoff)
        verdict = await engine.evaluate_incoming(
            content="The launch date is Q3 2026",
            project="my-project",
        )
        if verdict.action == VerdictAction.QUARANTINE:
            ...
    """

    def __init__(
        self,
        cortex_engine=None,
        handoff: CognitiveHandoff | None = None,
        *,
        max_context_beliefs: int = 50,
    ):
        """Initialize the Belief Engine.

        Args:
            cortex_engine: CortexEngine instance for fact storage/retrieval.
            handoff: CognitiveHandoff instance for quad-model auditing.
            max_context_beliefs: Max beliefs to load as audit context.
        """
        self._engine = cortex_engine
        self._handoff = handoff
        self._max_context = max_context_beliefs

        self._cache: dict[str, list[BeliefObject]] = {}


    async def evaluate_incoming(
        self,
        content: str,
        project: str,
        tenant_id: str = "default",
        confidence: BeliefConfidence = BeliefConfidence.C2_TENTATIVE,
        source: str | None = None,
    ) -> BeliefVerdict:
        """Evaluate incoming content for belief contradictions.

        Creates a candidate BeliefObject, loads existing beliefs as
        context, and routes through the CognitiveHandoff cascade.

        Args:
            content: The belief statement to evaluate.
            project: Project namespace.
            tenant_id: Multi-tenant isolation key.
            confidence: Initial confidence level.
            source: Origin of this belief (e.g., "agent:gemini").

        Returns:
            BeliefVerdict with action and reasoning.
        """

        prov_kwargs = (
            {
                "source_type": "model_inference" if "agent:" in source else "external",
                "was_generated_by": source,
            }
            if source
            else {}
        )
        provenance = ProvenanceEnvelope(**prov_kwargs)

        candidate = BeliefObject(
            proposition=content,
            project=project,
            tenant_id=tenant_id,
            confidence_score=0.5,
            provenance=provenance,
        )

        context = await self._load_context(project, tenant_id)

        if self._handoff is None:
            logger.warning("No CognitiveHandoff configured - auto-accepting belief")
            return BeliefVerdict(
                action=VerdictAction.ACCEPT,
                model="none",
                reason="No handoff configured - passthrough mode",
            )

        verdict = await self._handoff.process_belief(candidate, context)

        if verdict.action == VerdictAction.QUARANTINE:
            await self._quarantine_belief(candidate, verdict)

            has_source = bool(candidate.provenance.was_generated_by)
            if (
                verdict.model in ("opus", "fable", "architect", "o1-preview", "o1-mini")
                and has_source
            ):
                source_id = candidate.provenance.was_generated_by
                try:
                    from babylon60.extensions.forensic.slashing import (
                        SlashingEngine,
                        SlashingPenalty,
                    )

                    conn = getattr(self._engine, "conn", None) or getattr(
                        self._engine, "_conn", None
                    )
                    if conn:
                        logger.error(
                            "⚔️ [Ω₃] EPISTEMIC SLASHING: %s quarantined by %s",
                            source_id,
                            verdict.model,
                        )
                        await SlashingEngine.slash(
                            conn=conn,
                            agent_id=str(source_id),
                            penalty_type=SlashingPenalty.CRYPTOGRAPHIC_TAINT,
                            reason=f"Hallucination/Contradiction caught by {verdict.model}: {verdict.reason}",
                            tenant_id=candidate.tenant_id,
                        )
                    else:
                        logger.warning(
                            "⚔️ [Ω₃] EPISTEMIC SLASHING DEFERRED: %s caught by %s (No direct DB conn available)",
                            source_id,
                            verdict.model,
                        )
                except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as exc:  # noqa: BLE001
                    logger.error("Failed to execute Epistemic Slashing: %s", exc)

        elif verdict.action == VerdictAction.ACCEPT:
            await self._persist_belief(candidate)

        return verdict

    async def quarantine(self, belief_id: str, reason: str) -> None:
        """Manually quarantine a belief by ID.

        Args:
            belief_id: The belief ID to quarantine.
            reason: Human-readable reason for quarantine.
        """
        logger.warning("Manual quarantine: %s - %s", belief_id, reason)

        if self._engine is not None:
            await self._engine.store(
                content=f"[QUARANTINE] Belief {belief_id}: {reason}",
                fact_type="decision",
                project="cortex-internal",
                source="belief_engine",
                meta={"belief_id": belief_id, "action": "quarantine"},
                confidence="C4",
            )

    async def get_belief_graph(
        self,
        project: str,
        tenant_id: str = "default",
    ) -> list[BeliefObject]:
        """Retrieve all active beliefs for a project.

        Args:
            project: Project namespace.
            tenant_id: Multi-tenant isolation key.

        Returns:
            List of active BeliefObjects.
        """
        return await self._load_context(project, tenant_id)


    async def _load_context(
        self,
        project: str,
        tenant_id: str,
    ) -> list[BeliefObject]:
        """Load existing beliefs as context for auditing.

        First checks in-memory cache, then falls back to CortexEngine
        fact retrieval (filtering for fact_type='belief').
        """
        cache_key = f"{tenant_id}:{project}"

        if cache_key in self._cache:
            return self._cache[cache_key][: self._max_context]

        if self._engine is None:
            return []

        try:
            facts = await self._engine.recall(
                project=project,
                limit=self._max_context,
                tenant_id=tenant_id,
                fact_type="belief",
            )

            beliefs = []
            for fact in facts:
                try:
                    meta = fact.meta if isinstance(fact.meta, dict) else {}
                    belief_data = meta.get("belief_object")
                    if belief_data and isinstance(belief_data, dict):
                        beliefs.append(BeliefObject.from_dict(belief_data))
                    else:
                        beliefs.append(
                            BeliefObject(
                                proposition=fact.content,
                                project=project,
                                tenant_id=tenant_id,
                                confidence_score=0.5,
                            )
                        )
                except (KeyError, ValueError, TypeError) as exc:
                    logger.debug("Skipping malformed belief fact: %s", exc)

            self._cache[cache_key] = beliefs
            return beliefs[: self._max_context]

        except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as exc:  # noqa: BLE001
            logger.warning("Failed to load belief context: %s", exc)
            return []

    async def _quarantine_belief(
        self,
        belief: BeliefObject,
        verdict: BeliefVerdict,
    ) -> None:
        """Persist a quarantined belief to the engine."""
        quarantined = replace(
            belief,
            state=BeliefStatus.QUARANTINED,
            relations=replace(belief.relations, discards=verdict.contradictions),
            arbitrated_by=verdict.model,
        )

        if self._engine is not None:
            await self._engine.store(
                content=quarantined.content,
                fact_type="belief",
                project=quarantined.project,
                source=f"belief_engine:{verdict.model}",
                meta={
                    "belief_object": quarantined.to_dict(),
                    "verdict_action": verdict.action.value,
                    "verdict_reason": verdict.reason,
                },
                confidence=quarantined.confidence_score,
            )

        cache_key = f"{quarantined.tenant_id}:{quarantined.project}"
        self._cache.pop(cache_key, None)

        if verdict.model != "system_cascade":
            await self._cascade_quarantine(
                root_id=quarantined.id,
                project=quarantined.project,
                tenant_id=quarantined.tenant_id,
                reason=verdict.reason,
            )

    async def _cascade_quarantine(
        self,
        root_id: str,
        project: str,
        tenant_id: str,
        reason: str,
    ) -> None:
        """Recursively quarantine any active beliefs that depend on the root_id (Graph Orphan)."""
        if self._engine is None:
            return

        try:
            facts = await self._engine.recall(
                project=project,
                limit=None,  # Unbounded
                tenant_id=tenant_id,
                fact_type="belief",
            )

            context = []
            for fact in facts:
                meta = fact.meta if hasattr(fact, "meta") else fact.get("meta", {})
                belief_data = meta.get("belief_object")
                if belief_data:
                    context.append(BeliefObject.from_dict(belief_data))
        except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as exc:  # noqa: BLE001
            logger.error("Failed to load unbounded context for cascade: %s", exc)
            return

        for b in context:
            if b.state == BeliefStatus.ACTIVE and root_id in b.relations.entails:
                logger.warning(
                    "⛓️ [CASCADING QUARANTINE] Orphaning dependent belief %s (depends on %s)",
                    b.id,
                    root_id,
                )
                cascade_verdict = BeliefVerdict(
                    action=VerdictAction.QUARANTINE,
                    model="system_cascade",
                    reason=f"Cascading Quarantine: Dependent root belief {root_id} collapsed. Root cause: {reason}",
                )
                await self._quarantine_belief(b, cascade_verdict)
                await self._cascade_quarantine(b.id, project, tenant_id, reason)

    async def _persist_belief(self, belief: BeliefObject) -> None:
        """Persist an accepted belief to the engine."""
        if self._engine is not None:
            await self._engine.store(
                content=belief.content,
                fact_type="belief",
                project=belief.project,
                source="belief_engine",
                meta={"belief_object": belief.to_dict()},
                confidence=belief.confidence_score,
            )

        cache_key = f"{belief.tenant_id}:{belief.project}"
        if cache_key not in self._cache:
            self._cache[cache_key] = []
        self._cache[cache_key].append(belief)
