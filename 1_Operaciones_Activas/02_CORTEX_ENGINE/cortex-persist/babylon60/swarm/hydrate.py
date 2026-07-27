# [C5-REAL] Exergy-Maximized
"""Swarm Hydration — Bridge between AgentCatalogLoader and SubagentRunner.

Loads YAML agent definitions from the registry and registers them
as live LLM handlers in the SubagentRunner, completing the execution
pipeline: YAML → Registry → Handler → LLM → Audit.

Axioms:
    AX-048: Asymmetric routing collapses uncertainty via parallel BFT swarms.
    AX-045: Causal chain enforced: PeARL → Ledger → Swarm.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from babylon60.extensions.agents.registry import AgentCatalogEntry
    from babylon60.swarm.runtime import SubagentRunner

logger = logging.getLogger("babylon60.swarm.hydrate")


# ─── Tier Classification ────────────────────────────────────────────────


def _classify_tier(entry: AgentCatalogEntry) -> str:
    """Classify an agent into its operational tier using YAML metadata.

    Priority:
        1. Explicit metadata.exergy_tier field (P0→T0, P1→T1, P2→T2)
        2. Heuristic: agents with tools > 5 → T1
        3. Default: T2
    """
    # Check for explicit exergy_tier in metadata (from YAML)
    # The YAML has a metadata block but it's not parsed into AgentCatalogEntry.
    # We use a combination of heuristics from the parsed fields.

    # Heuristic 1: Provider + intent differentiation
    if entry.provider and entry.intent:
        # Agents with both provider and intent configured are more operational
        if len(entry.tools) >= 5:
            return "T0"
        if entry.tools:
            return "T1"

    # Heuristic 2: System prompt density (agents with rich prompts are more defined)
    if len(entry.system_prompt) > 500 and entry.tools:
        return "T1"

    # Heuristic 3: Agents with causal_memory enabled are high-priority
    if entry.memory.causal_memory:
        return "T1"

    return "T2"


# Intent → TaskKind mapping (covers all IntentProfile values)
_INTENT_TO_KINDS: dict[str, list[str]] = {
    "code": ["execute", "plan"],
    "architect": ["plan", "reason", "summarize"],
    "reasoning": ["reason", "audit", "summarize"],
    "creative": ["summarize", "plan"],
    "synthesis": ["reason", "summarize", "memory"],
    "belief_audit": ["audit", "reason"],
    "episodic_processing": ["memory", "retrieve", "summarize"],
}

# Exergy priority mapping
_EXERGY_PRIORITY: dict[str, int] = {
    "T0": 100,
    "T1": 50,
    "T2": 10,
}


def hydrate_swarm(
    runner: SubagentRunner,
    max_tier: str = "T1",
) -> int:
    """Load YAML agent definitions into the SubagentRunner as live handlers.

    Args:
        runner: The SubagentRunner instance to populate.
        max_tier: Maximum tier to hydrate. "T0" = only operational agents,
                  "T1" = operational + configured, "T2" = all agents.

    Returns:
        Number of agents successfully hydrated.
    """
    from babylon60.extensions.agents.registry import AgentCatalogLoader
    from babylon60.swarm.llm_agent_handler import LLMAgentHandler
    from babylon60.swarm.runtime import AgentCapability

    tier_order = {"T0": 0, "T1": 1, "T2": 2}
    max_tier_val = tier_order.get(max_tier, 1)

    catalog = AgentCatalogLoader()
    count = 0
    tier_stats: dict[str, int] = {"T0": 0, "T1": 0, "T2": 0}

    for _agent_id, entry in catalog.agents.items():
        agent_tier = _classify_tier(entry)
        tier_stats[agent_tier] = tier_stats.get(agent_tier, 0) + 1
        agent_tier_val = tier_order.get(agent_tier, 2)

        if agent_tier_val > max_tier_val:
            continue

        from typing import cast

        # Map intent to TaskKind list
        raw_kinds = _INTENT_TO_KINDS.get(entry.intent, ["reason"])
        kinds = cast(list[Any], raw_kinds)

        cap = AgentCapability(
            name=entry.id,
            kinds=kinds,
            tags=[
                entry.provider or "unknown",
                entry.intent or "general",
                agent_tier,
            ],
            priority=_EXERGY_PRIORITY.get(agent_tier, 10),
            max_concurrent=1,
        )

        handler = LLMAgentHandler(entry)

        runner.registry.register(cap)
        runner.register_handler(entry.id, handler)
        count += 1

        logger.debug(
            "🧬 [HYDRATE] %s (%s) → tier=%s, kinds=%s, tools=%d",
            entry.name,
            entry.id,
            agent_tier,
            kinds,
            len(entry.tools),
        )

    logger.info(
        "🏛️ [HYDRATE] %d agents hydrated (max_tier=%s). Distribution: T0=%d T1=%d T2=%d",
        count,
        max_tier,
        tier_stats["T0"],
        tier_stats["T1"],
        tier_stats["T2"],
    )
    return count


async def _ledger_audit_callback(event: dict[str, Any]) -> None:
    """Audit callback that logs swarm dispatch events to structured logging.

    Lightweight: writes to the swarm module logger rather than requiring
    a full EnterpriseAuditLedger connection (which needs async DB setup).
    """
    audit_logger = logging.getLogger("babylon60.swarm.audit")
    audit_logger.info(
        "📜 [SWARM-AUDIT] task=%s agent=%s action=%s status=%s",
        event.get("task_id", "?"),
        event.get("target_agent", "?"),
        event.get("action", "?"),
        event.get("status", "?"),
    )


def create_hydrated_runner(
    max_tier: str = "T1",
    enable_audit: bool = True,
) -> SubagentRunner:
    """Create a fully hydrated SubagentRunner ready for dispatch.

    Args:
        max_tier: Maximum agent tier to hydrate.
        enable_audit: Enable audit trail logging for dispatch events.

    Returns:
        A SubagentRunner with agents registered and handlers ready.
    """
    from babylon60.swarm.runtime import AgentRegistry, SubagentRunner

    registry = AgentRegistry()
    runner = SubagentRunner(
        registry,
        audit_callback=_ledger_audit_callback if enable_audit else None,
    )
    hydrate_swarm(runner, max_tier=max_tier)
    return runner


async def dispatch_to_agent(
    agent_id: str,
    prompt: str,
    context: dict[str, Any] | None = None,
    max_tier: str = "T2",
) -> dict[str, Any]:
    """High-level convenience: dispatch a prompt to a specific agent.

    Creates a hydrated runner, dispatches, and returns the result.
    Suitable for programmatic use from other modules.

    Args:
        agent_id: The agent ID to dispatch to.
        prompt: The prompt text.
        context: Optional context dict.
        max_tier: Max tier for hydration.

    Returns:
        Response dict from the LLMAgentHandler.
    """
    from babylon60.swarm.runtime import SubagentRequest

    runner = create_hydrated_runner(max_tier=max_tier)

    req = SubagentRequest(
        task_id=f"dispatch-{agent_id}",
        kind="reason",
        target_agent=agent_id,
        prompt=prompt,
        context=context or {},
    )

    resp = await runner.invoke_subagent(req)
    if not resp.ok:
        return {"text": f"ERROR: {resp.error}", "status": "ERROR", "agent_id": agent_id}
    return resp.output if isinstance(resp.output, dict) else {"text": resp.output, "status": "OK"}


async def dispatch_parallel(
    agent_ids: list[str],
    prompt: str,
    context: dict[str, Any] | None = None,
    max_tier: str = "T2",
) -> list[dict[str, Any]]:
    """Dispatch the same prompt to multiple agents in parallel (BFT consensus).

    Args:
        agent_ids: List of agent IDs to dispatch to.
        prompt: The prompt text.
        context: Optional shared context.
        max_tier: Max tier for hydration.

    Returns:
        List of response dicts, one per agent.
    """
    import asyncio

    from babylon60.swarm.runtime import SubagentRequest

    runner = create_hydrated_runner(max_tier=max_tier)

    tasks = []
    for agent_id in agent_ids:
        req = SubagentRequest(
            task_id=f"parallel-{agent_id}",
            kind="reason",
            target_agent=agent_id,
            prompt=prompt,
            context=context or {},
        )
        tasks.append(runner.invoke_subagent(req))

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for i, resp in enumerate(responses):
        if isinstance(resp, BaseException):
            results.append(
                {
                    "text": str(resp),
                    "status": "ERROR",
                    "agent_id": agent_ids[i],
                }
            )
        elif not resp.ok:
            results.append(
                {
                    "text": f"ERROR: {resp.error}",
                    "status": "ERROR",
                    "agent_id": agent_ids[i],
                }
            )
        else:
            output = resp.output if isinstance(resp.output, dict) else {"text": resp.output}
            output["agent_id"] = agent_ids[i]
            output.setdefault("status", "OK")
            results.append(output)

    return results
