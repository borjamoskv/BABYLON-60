# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import logging
from typing import Any, ClassVar

from babylon60.crypto.hash_registry import cortex_hash
from babylon60.swarm.byzantine_judge import ByzantineJudge
from babylon60.swarm.generator_agent import GeneratorAgent
from babylon60.swarm.legion import Squadron, SwarmAgent, SwarmSignal

logger = logging.getLogger("babylon60.swarm.generator_squadron")


class GeneratorSquadron(Squadron):
    """
    Orchestrates the Generator Swarm loop: MAP, SHARD, SYNC, CRYSTALLIZE.
    Runs Quorum Consensus via the ByzantineJudge over generated proposals.
    """

    SQUAD_NAME: ClassVar[str] = "GENERATOR"
    REPLICAS: ClassVar[int] = 3

    def __init__(self, engine: Any = None):
        super().__init__(engine)
        self.judge = ByzantineJudge()

    def _create_agent(self, agent_id: str) -> SwarmAgent:
        return GeneratorAgent(agent_id, self.bus, self.engine, km=self.judge.km)

    async def _map(self, target_pattern: str | None = None) -> list[str]:
        # Generator targets are mapped as individual modules or tasks
        return [target_pattern] if target_pattern else ["default_spec"]

    async def _crystallize(self, signals: list[SwarmSignal]) -> dict[str, Any]:
        """Gathers generated AST proposals and triggers Byzantine Consensus."""
        # 1. Base crystallization (checks system-wide invariants)
        report = await super()._crystallize(signals)

        # 2. Extract proposed AST payloads
        proposals = []
        for s in signals:
            if s.status == "SUCCESS" and isinstance(s.payload, dict):
                # Ensure all required keys for ByzantineJudge exist
                if all(k in s.payload for k in ("agent_id", "ast_code", "signature_b64", "timestamp")):
                    proposals.append(s.payload)

        if not proposals:
            logger.error("No valid AST proposals received by the Squadron.")
            report["consensus"] = "FAILED"
            report["reason"] = "No valid proposals matching cryptographic requirements"
            return report

        # 3. Byzantine Consensus execution
        consensus_proof = self.judge.evaluate_proposals(original_state={}, proposals=proposals)

        if consensus_proof:
            winning_agent = consensus_proof["winning_agent"]
            winning_ast = consensus_proof["ast_code"]
            consensus_hash = cortex_hash(winning_ast.encode("utf-8"))

            report["consensus"] = "PASSED"
            report["winner"] = winning_agent
            report["ast_code"] = winning_ast
            report["consensus_proof"] = consensus_proof

            # 4. Commit to Enterprise Audit Ledger
            try:
                from babylon60.audit.ledger import EnterpriseAuditLedger
                from babylon60.database.core import connect_async_ctx

                db_path = "cortex_ledger.db"
                if self.engine and hasattr(self.engine, "_db_path"):
                    db_path = self.engine._db_path

                async with connect_async_ctx(str(db_path)) as conn:
                    ledger = EnterpriseAuditLedger(conn)
                    await ledger.ensure_table()
                    await ledger.log_action(
                        tenant_id="default",
                        actor_role="squadron",
                        actor_id=f"Squadron-{self.SQUAD_NAME}",
                        action="QUORUM_CONSENSUS",
                        resource="ast_code",
                        status="SUCCESS",
                        payload_dict={
                            "winning_agent": winning_agent,
                            "ast_hash": consensus_hash,
                            "timestamp": consensus_proof["consensus_timestamp"],
                            "signature": consensus_proof["consensus_signature_b64"]
                        }
                    )
                logger.info("Consensus committed to Enterprise Audit Ledger successfully.")
            except Exception as e:  # noqa: BLE001
                logger.error("Failed to write consensus proof to Ledger: %s", e)
        else:
            logger.error("Byzantine consensus failed. All proposals rejected.")
            report["consensus"] = "FAILED"
            report["reason"] = "All proposals failed validation or isolation checks"

        return report
