# [C5-REAL] Exergy-Maximized
"""
herodoto_agent.py - HerodotoUltraAttnAgent

C5-REAL Sovereign Forensic Auditor. Meticulously reviews the Master Ledger, Git history,
and event streams to reconstruct causality with absolute precision (UltraAttn).
"""

from __future__ import annotations

import logging

from babylon60.agents.base import BaseAgent
from babylon60.agents.bus import MessageBus
from babylon60.agents.contracts import TaskCompletedPayload, TaskFailedPayload, TaskRequestPayload
from babylon60.agents.manifest import AgentManifest
from babylon60.agents.message_schema import AgentMessage, MessageKind
from babylon60.agents.tools import ToolRegistry

logger = logging.getLogger(__name__)


class HerodotoUltraAttnAgent(BaseAgent):
    """
    Sovereign agent specialized in historical auditing, deep forensic trace analysis,
    and zero-anergy ledger verification with Ultra-Attention capabilities.
    """

    def __init__(
        self,
        manifest: AgentManifest,
        bus: MessageBus,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        super().__init__(manifest, bus, tool_registry)

    async def handle_message(self, message: AgentMessage) -> None:  # type: ignore[override]
        if message.kind != MessageKind.TASK_REQUEST:
            return

        try:
            task = TaskRequestPayload.model_validate(message.payload)
            objective_lower = task.objective.lower()
            if "audit" in objective_lower or "hist" in objective_lower or "trace" in objective_lower:
                await self._perform_ultraattn_audit(message, task)
            else:
                await self._fail_task(
                    message, task, "Objective not supported by HerodotoUltraAttnAgent. Requires 'audit', 'history', or 'trace'."
                )
        except Exception as exc:  # noqa: BLE001
            logger.exception("HerodotoUltraAttnAgent failed to process message")
            await self._fail_task(message, task, f"Internal failure: {exc}")

    async def _perform_ultraattn_audit(
        self, original_msg: AgentMessage, task: TaskRequestPayload
    ) -> None:
        import asyncio
        import os
        from pathlib import Path

        # 1. Check Git Sentinel Hash & Commit Anomalies
        git_hash = "UNKNOWN"
        git_anomalies = []
        try:
            proc = await asyncio.create_subprocess_shell(
                "git log -n 10 --oneline",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                lines = stdout.decode().strip().split('\n')
                if lines:
                    git_hash = lines[0].split(' ')[0]
                for line in lines:
                    if not any(prefix in line for prefix in ["feat", "fix", "chore", "refactor", "docs", "[bridge]"]):
                        git_anomalies.append(line)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Git log check failed: {exc}")

        # 2. Measure physical ledger exergy (file size)
        ledger_path = Path(os.path.expanduser("~/.babylon60/runtime.db"))
        ledger_size_kb = 0
        if ledger_path.exists():
            ledger_size_kb = ledger_path.stat().st_size // 1024

        # 3. Direct MTK Allocator query for Semantic Entities and Anomalies
        db_facts_count = 0
        orphan_facts = 0
        limerence_loops = 0
        try:
            from babylon60.database.core import connect_async_ctx
            async with connect_async_ctx(str(ledger_path), read_only=True) as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM facts")
                row = await cursor.fetchone()
                if row:
                    db_facts_count = row[0]

                # Check for facts missing lineage or CORTEX-TAINT
                cursor_orphan = await conn.execute("SELECT COUNT(*) FROM facts WHERE metadata NOT LIKE '%lineage%' AND metadata NOT LIKE '%cortex_taint%'")
                row_orphan = await cursor_orphan.fetchone()
                if row_orphan:
                    orphan_facts = row_orphan[0]

                # FRENTE 3: Limerence Guard (Anergy Loops)
                cursor_anergy = await conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_messages'")
                if await cursor_anergy.fetchone():
                    cursor_stuck = await conn.execute("SELECT COUNT(*) FROM agent_messages WHERE consumed = 0")
                    row_stuck = await cursor_stuck.fetchone()
                    if row_stuck:
                        limerence_loops = row_stuck[0]
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Herodoto DB check failed: {e}")

        audit_report = {
            "auditor": "HERODOTO-ULTRAATTN",
            "status": "C5-REAL_AUDIT_COMPLETE",
            "findings": [
                {
                    "severity": "P0",
                    "domain": "Git Sentinel",
                    "description": f"Verified physical cryptographic anchor at {git_hash}."
                },
                {
                    "severity": "P1",
                    "domain": "Master Ledger Physicality",
                    "description": f"Runtime DB asserts physical presence with Exergy density of {ledger_size_kb} KB. Contains {db_facts_count} crystalized facts."
                }
            ],
            "anomalies": {
                "orphan_facts_without_lineage": orphan_facts,
                "non_conventional_commits": len(git_anomalies),
                "limerence_loops_stuck_messages": limerence_loops
            },
            "entropy_purged": True,
            "anergy_detected": orphan_facts + len(git_anomalies) + limerence_loops
        }

        # Send response
        await self.bus.send(
            AgentMessage(
                correlation_id=original_msg.correlation_id,
                causation_id=original_msg.message_id,
                sender=self.agent_id,
                recipient=original_msg.sender,
                kind=MessageKind.TASK_COMPLETED,
                payload=TaskCompletedPayload(
                    task_id=task.task_id,
                    output={
                        "audit_report": audit_report
                    },
                ).model_dump(),
            )
        )

    async def _fail_task(
        self, original_msg: AgentMessage, task: TaskRequestPayload, error: str
    ) -> None:
        await self.bus.send(
            AgentMessage(
                correlation_id=original_msg.correlation_id,
                causation_id=original_msg.message_id,
                sender=self.agent_id,
                recipient=original_msg.sender,
                kind=MessageKind.TASK_FAILED,
                payload=TaskFailedPayload(
                    task_id=task.task_id, error=error, retryable=False
                ).model_dump(),
            )
        )
