# [C5-REAL] Exergy-Maximized
"""
cat_id: poc-herodoto
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import asyncio
import json
import logging

from babylon60.agents.builtins.herodoto_agent import HerodotoUltraAttnAgent
from babylon60.agents.bus import SqliteMessageBus
from babylon60.agents.contracts import TaskRequestPayload
from babylon60.agents.manifest import AgentManifest
from babylon60.agents.message_schema import AgentMessage, MessageKind
from babylon60.agents.tools import ToolRegistry

logging.basicConfig(level=logging.INFO)

async def main():
    bus = SqliteMessageBus()
    manifest = AgentManifest(
        agent_id="agent-herodoto",
        purpose="Forensic Auditor"
    )
    agent = HerodotoUltraAttnAgent(manifest, bus, ToolRegistry())

    captured_messages = []
    async def mock_send(msg):
        captured_messages.append(msg)

    agent.bus.send = mock_send

    task_payload = TaskRequestPayload(
        task_id="task-audit-001",
        objective="perform deep audit of the system",
        context={}
    )

    msg = AgentMessage(
        correlation_id="corr-1",
        causation_id="cause-1",
        sender="agent-sender",
        recipient="agent-herodoto",
        kind=MessageKind.TASK_REQUEST,
        payload=task_payload.model_dump()
    )

    await agent.handle_message(msg)

    logging.getLogger(__name__).info("\n--- PoC OUTPUT ---")
    if captured_messages:
        logging.getLogger(__name__).info(json.dumps(captured_messages[0].payload, indent=2))
    else:
        logging.getLogger(__name__).info("No response from agent")
    logging.getLogger(__name__).info("------------------\n")

if __name__ == "__main__":
    asyncio.run(main())
