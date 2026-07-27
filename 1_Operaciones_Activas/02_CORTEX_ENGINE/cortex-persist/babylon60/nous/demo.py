"""
NOUS Intent Architecture - End to End C5-REAL Demo.
"""

import logging

logger = logging.getLogger(__name__)
from babylon60.nous.dry_run import DryRunSimulator
from babylon60.nous.judge import DeterministicJudge
from babylon60.nous.ledger import MutationLedger
from babylon60.nous.parser import IntentParser


def run_demo():
    logger.info("=== [NOUS] INITIALIZING C5-REAL KERNEL ===")
    logger.info("\n[1] STOCHASTIC INTENT RECEIVED")
    raw_llm_output = '\n    {\n        "description": "Create a users table and add a generic metadata column",\n        "actions": [\n            {\n                "action_type": "CREATE_TABLE",\n                "table_name": "users",\n                "parameters": {\n                    "id": "INTEGER PRIMARY KEY",\n                    "username": "TEXT NOT NULL"\n                }\n            },\n            {\n                "action_type": "ADD_COLUMN",\n                "table_name": "users",\n                "parameters": {\n                    "name": "metadata",\n                    "type": "JSON"\n                }\n            }\n        ]\n    }\n    '
    try:
        intent = IntentParser.parse_llm_json(raw_llm_output)
        logger.info(
            f" -> Parsed AST: {len(intent.actions)} actions derived from '{intent.description}'"
        )
        verdict = DeterministicJudge.evaluate(intent)
        logger.info(
            f"\n[2] DETERMINISTIC JUDGE VERDICT: {('APPROVED' if verdict.approved else 'REJECTED')}"
        )
        if not verdict.approved:
            logger.info(f" -> Reason: {verdict.reason}")
            return
        for w in verdict.warnings:
            logger.info(f" -> Warning: {w}")
        logger.info("\n[3] DRY-RUN SIMULATION")
        is_valid = DryRunSimulator.simulate(intent)
        logger.info(f" -> Simulation {('PASSED' if is_valid else 'FAILED')}")
        if not is_valid:
            return
        logger.info("\n[4] STATE CRYSTALLIZATION (LEDGER)")
        ledger = MutationLedger()
        ast_dict = [a.model_dump() for a in intent.actions]
        new_hash = ledger.record_mutation(intent.description, ast_dict)
        logger.info(" -> Mutation sealed.")
        logger.info(f" -> New State Hash: {new_hash}")
        logger.info(f" -> Ledger Integrity Valid: {ledger.verify_chain()}")
    except Exception as e:  # noqa: BLE001
        logger.info(f"System Error: {e}")


if __name__ == "__main__":
    run_demo()
