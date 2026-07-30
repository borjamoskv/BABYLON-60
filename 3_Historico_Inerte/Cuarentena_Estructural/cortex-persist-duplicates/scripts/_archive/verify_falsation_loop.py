"""BABYLON60 v7 — Sovereign Falsation Loop Verification.

Final C5-REAL verification of the truth resolution pipeline.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add BABYLON60 to path
sys.path.append("~/30_BABYLON60")

from babylon60.memory.encoder import AsyncEncoder
from babylon60.memory.ledger import EventLedgerL3
from babylon60.memory.manager import Babylon60MemoryManager
from babylon60.memory.sqlite_vec_store import SovereignVectorStoreL2
from babylon60.memory.working import WorkingMemoryL1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("babylon60.verify_falsation")


async def verify_loop():
    # 1. Setup
    encoder = AsyncEncoder()
    l2 = SovereignVectorStoreL2(encoder, db_path="babylon60_verify_v2.db")
    l3 = EventLedgerL3(db_path="babylon60_verify_ledger_v2.db")
    l1 = WorkingMemoryL1()

    manager = Babylon60MemoryManager(l1, l2, l3, encoder)

    tenant_id = "test_verify"
    project_id = "falsation_verify"
    subject_hash = "verify_subject_123"

    logger.info("--- STEP 1: Storing Fact A (Paris) ---")
    await manager.store(
        tenant_id=tenant_id,
        project_id=project_id,
        content="La capital de Francia es París.",
        metadata={"subject": "capital_francia"},
    )

    logger.info("--- STEP 2: Storing Fact B (Lyon) - Triggering Conflict ---")
    result = await manager.store(
        tenant_id=tenant_id,
        project_id=project_id,
        content="La capital de Francia es Lyon.",
        metadata={"subject": "capital_francia"},
    )

    logger.info("RESULT: %s", result)
    request_id = result.split(":")[-1] if "conflict" in result else None

    if not request_id:
        logger.error("❌ No conflict/request_id detected.")
        return

    logger.info("--- STEP 3: Simulating Bridge Response (Verdict A) ---")
    bridge_responses_dir = Path(
        "~/Downloads/WIKIPEDIA BORJA MOSKV/CODEX H/autodidact-engine/bridge/a2a-sovereign/responses"
    )
    response_path = bridge_responses_dir / f"falsation-{request_id}.json"

    import json
    import time

    response_payload = {
        "kind": "falsation_response",
        "request_id": request_id,
        "verdict": "A",
        "reason": "Verified via C5-REAL simulation.",
        "timestamp": time.time(),
    }
    response_path.write_text(json.dumps(response_payload), encoding="utf-8")

    import hashlib

    subject_hash = hashlib.sha256(b"capital_francia").hexdigest()

    logger.info("--- STEP 4: Polling for Background Resolution ---")
    # We wait a few seconds for the background task to pick up the response
    for i in range(5):
        logger.info("Polling L2 status... (%d/5)", i + 1)
        conn = l2._get_conn()
        cursor = conn.execute(
            "SELECT confidence, is_conflict FROM facts_meta WHERE subject_hash = ?", (subject_hash,)
        )
        row = cursor.fetchone()
        if row:
            logger.info("DB STATUS: confidence=%s, is_conflict=%s", row[0], bool(row[1]))
            if row[0] == "C5" and not bool(row[1]):
                logger.info("✅ SUCCESS: Fact resolved to C5-REAL.")
                break
        await asyncio.sleep(2)

    await manager.close()
    logger.info("--- VERIFICATION COMPLETE ---")


if __name__ == "__main__":
    asyncio.run(verify_loop())
