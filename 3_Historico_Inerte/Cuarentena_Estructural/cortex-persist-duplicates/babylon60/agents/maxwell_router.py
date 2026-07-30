# [C5-REAL] Exergy-Maximized
"""Maxwell Router Agent - The Asymmetric Assessor.

Implements the Maxwell Demon logic to route tasks based on their Shannon entropy.
Hot (High Entropy) tasks are routed to the Boltzmann Engine (UltraThink).
Cold (Low Entropy) tasks are routed to Flash workers.
"""

import logging

from babylon60.agents.base import BaseAgent
from babylon60.agents.bus import MessageBus
from babylon60.agents.manifest import AgentManifest
from babylon60.agents.message_schema import AgentMessage, MessageKind, new_message
from babylon60.agents.state import AgentStatus

logger = logging.getLogger("babylon60.agents.maxwell_router")


class MaxwellRouterAgent(BaseAgent):
    """Router agent that classifies incoming tasks based on thermodynamic gradients.

    Evaluates the entropy of the task prompt. If it exceeds the threshold,
    it delegates to the BoltzmannEngine (Deep Reasoning). Otherwise, it delegates
    to standard Flash workers for exergy preservation.
    """

    def __init__(
        self, manifest: AgentManifest, bus: MessageBus, entropy_threshold: float = 4.0
    ) -> None:
        super().__init__(manifest, bus)
        self.entropy_threshold = entropy_threshold

    def _calculate_shannon_entropy(self, text: str) -> float:
        """Calculates semantic entropy formally via structural distribution.

        Axiom (C5-REAL): Eradicates arbitrary proxies. Uses mathematical Shannon Entropy.
        """
        if not text:
            return 0.0

        from babylon60.extensions.security.utils import calculate_shannon_entropy

        return calculate_shannon_entropy(text)

    async def _handle_message(self, message: AgentMessage) -> None:
        if message.kind != MessageKind.TASK_REQUEST:
            return

        prompt = message.payload.get("prompt", "")
        entropy = self._calculate_shannon_entropy(prompt)

        logger.info("[***] Routing task %s (Entropy: %.2f)", message.correlation_id, entropy)

        # Route based on Maxwell threshold
        if entropy >= self.entropy_threshold:
            target_agent = "boltzmann_engine_01"
            reason = "High entropy task. Routing to Boltzmann Engine (UltraThink)."
        else:
            target_agent = "flash_worker_01"
            reason = "Low entropy task. Routing to Flash Worker (T=0.0)."

        logger.info("[***] Task %s routed to %s", message.correlation_id, target_agent)

        # Emit delegated task
        delegation = new_message(
            sender=self.agent_id,
            recipient=target_agent,
            kind=MessageKind.TASK_REQUEST,
            payload=message.payload,
        )
        await self.bus.send(delegation)

        # Reply to original sender that routing is complete
        reply = new_message(
            sender=self.agent_id,
            recipient=message.sender,
            kind=MessageKind.TASK_RESULT,
            payload={
                "status": "routed",
                "target": target_agent,
                "entropy": entropy,
                "reason": reason,
            },
            correlation_id=message.correlation_id,
        )
        await self.bus.send(reply)

        self.state.status = AgentStatus.IDLE


def create_maxwell_router(
    name: str, bus: MessageBus, entropy_threshold: float = 4.0
) -> MaxwellRouterAgent:
    """Factory for MaxwellRouterAgent."""
    manifest = AgentManifest(
        agent_id=name, purpose="Asymmetric task router based on Shannon entropy.", can_delegate=True
    )
    agent = MaxwellRouterAgent(manifest, bus, entropy_threshold)
    return agent
