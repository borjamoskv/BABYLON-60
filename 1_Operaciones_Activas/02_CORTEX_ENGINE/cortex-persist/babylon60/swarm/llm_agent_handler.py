# [C5-REAL] Exergy-Maximized
"""LLM Agent Handler — Hydrates AgentCatalogEntry into live LLM calls.

Implements the AgentHandler protocol from swarm/runtime.py,
bridging the 93 YAML agent definitions to actual LLM execution
via the LLMProvider infrastructure.

Axioms:
    AX-044: Intelligence is evaluated as agentic capability.
    AX-045: Causal chain enforced: Registry → Handler → LLM → Ledger.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from babylon60.extensions.agents.registry import AgentCatalogEntry
    from babylon60.swarm.runtime import SubagentRequest

logger = logging.getLogger("babylon60.swarm.llm_agent_handler")

# Intent string → IntentProfile enum value mapping
_INTENT_MAP: dict[str, str] = {
    "code": "code",
    "architect": "architect",
    "reasoning": "reasoning",
    "synthesis": "reasoning",
    "creative": "creative",
    "belief_audit": "belief_audit",
    "episodic_processing": "episodic_processing",
}


def _resolve_intent(intent_str: str) -> Any:
    """Resolve an intent string to IntentProfile enum, with fallback."""
    from babylon60.extensions.llm._models import IntentProfile

    mapped = _INTENT_MAP.get(intent_str, "general")
    try:
        return IntentProfile(mapped)
    except ValueError:
        return IntentProfile.GENERAL


def _compute_max_tokens(entry: AgentCatalogEntry) -> int:
    """Derive max_tokens from guardrails config.

    Uses 10% of max_session_tokens, clamped to [512, 16384].
    """
    raw = entry.guardrails.max_session_tokens // 10
    return max(512, min(raw, 16384))


class LLMAgentHandler:
    """Hydrates an AgentCatalogEntry into a live LLM execution handler.

    Implements the ``AgentHandler`` protocol expected by ``SubagentRunner``.
    Each instance is bound to a single agent definition and uses its
    ``system_prompt``, ``provider``, and ``resolved_model`` to dispatch
    LLM calls through the standard ``LLMProvider`` infrastructure.

    Features:
        - Guardrails enforcement (token limits from YAML config)
        - Conversation memory accumulation (multi-turn support)
        - Full IntentProfile resolution (all 7 enum variants)
        - Execution telemetry (latency, tokens, model)
    """

    __slots__ = (
        "_entry",
        "_llm",
        "_history",
        "_turn_count",
        "_total_tokens_estimate",
    )

    def __init__(self, agent_entry: AgentCatalogEntry) -> None:
        self._entry = agent_entry
        self._llm: Any = None
        self._history: list[dict[str, str]] = []
        self._turn_count: int = 0
        self._total_tokens_estimate: int = 0

    def _ensure_llm(self) -> Any:
        if self._llm is None:
            from babylon60.extensions.llm.provider import LLMProvider

            self._llm = LLMProvider(
                provider=self._entry.provider or "ollama",
                model=self._entry.resolved_model,
            )
        return self._llm

    def _check_guardrails(self) -> str | None:
        """Check if guardrails would be violated by another turn.

        Returns:
            Error message if guardrails are exceeded, None otherwise.
        """
        gr = self._entry.guardrails

        if gr.max_turns and self._turn_count >= gr.max_turns:
            return (
                f"[GUARDRAIL] max_turns={gr.max_turns} reached for {self._entry.id}. "
                "Session terminated."
            )

        warn_tokens = int(gr.max_session_tokens * gr.warn_threshold)
        if self._total_tokens_estimate >= gr.max_session_tokens:
            return (
                f"[GUARDRAIL] max_session_tokens={gr.max_session_tokens} "
                f"exhausted for {self._entry.id}. Session terminated."
            )

        if self._total_tokens_estimate >= warn_tokens:
            logger.warning(
                "⚠️ [GUARDRAIL] %s approaching token limit: %d/%d (%.0f%%)",
                self._entry.id,
                self._total_tokens_estimate,
                gr.max_session_tokens,
                (self._total_tokens_estimate / gr.max_session_tokens) * 100,
            )

        return None

    async def run(self, req: SubagentRequest) -> Any:
        """Execute an LLM call using this agent's persona.

        Args:
            req: SubagentRequest with prompt and context.

        Returns:
            dict with response text and execution telemetry.
        """
        # Guardrails check
        guardrail_error = self._check_guardrails()
        if guardrail_error:
            return {"text": guardrail_error, "status": "GUARDRAIL_ABORT"}

        llm = self._ensure_llm()

        system = self._entry.system_prompt
        if not system:
            system = f"You are {self._entry.name}, a sovereign agent."

        # Build prompt with context injection
        prompt = req.prompt
        if req.context:
            context_block = "\n".join(f"- {k}: {v}" for k, v in req.context.items())
            prompt = f"{prompt}\n\n## Context\n{context_block}"

        # Inject conversation history for multi-turn
        if self._history:
            history_block = "\n".join(
                f"[{msg['role'].upper()}]: {msg['content'][:200]}"
                for msg in self._history[-6:]  # Last 3 exchanges
            )
            prompt = f"## Previous Context\n{history_block}\n\n## Current Task\n{prompt}"

        intent = _resolve_intent(self._entry.intent)
        max_tokens = _compute_max_tokens(self._entry)

        t0 = time.monotonic()

        logger.info(
            "⚡ [HANDLER] %s → provider=%s model=%s intent=%s max_tokens=%d turn=%d",
            self._entry.name,
            self._entry.provider,
            self._entry.resolved_model,
            self._entry.intent,
            max_tokens,
            self._turn_count + 1,
        )

        response = await llm.complete(
            prompt=prompt,
            system=system,
            temperature=0.0,
            max_tokens=max_tokens,
            intent=intent,
        )

        elapsed_ms = (time.monotonic() - t0) * 1000

        # Update state
        self._turn_count += 1
        self._history.append({"role": "user", "content": req.prompt})
        self._history.append({"role": "assistant", "content": response})

        # Estimate token usage (rough: 4 chars ≈ 1 token)
        token_estimate = (len(prompt) + len(response)) // 4
        self._total_tokens_estimate += token_estimate

        telemetry = {
            "text": response,
            "status": "OK",
            "agent_id": self._entry.id,
            "agent_name": self._entry.name,
            "provider": self._entry.provider,
            "model": self._entry.resolved_model,
            "intent": self._entry.intent,
            "turn": self._turn_count,
            "latency_ms": round(elapsed_ms, 1),
            "tokens_estimate": token_estimate,
            "tokens_total": self._total_tokens_estimate,
            "guardrails": {
                "max_turns": self._entry.guardrails.max_turns,
                "max_tokens": self._entry.guardrails.max_session_tokens,
                "usage_pct": round(
                    (self._total_tokens_estimate / self._entry.guardrails.max_session_tokens) * 100,
                    1,
                ),
            },
        }

        logger.info(
            "✅ [HANDLER] %s completed in %.0fms (~%d tokens, turn %d)",
            self._entry.name,
            elapsed_ms,
            token_estimate,
            self._turn_count,
        )

        return telemetry

    def reset(self) -> None:
        """Reset conversation state for a fresh session."""
        self._history.clear()
        self._turn_count = 0
        self._total_tokens_estimate = 0

    @property
    def agent_id(self) -> str:
        return self._entry.id

    @property
    def agent_name(self) -> str:
        return self._entry.name

    @property
    def turn_count(self) -> int:
        return self._turn_count
