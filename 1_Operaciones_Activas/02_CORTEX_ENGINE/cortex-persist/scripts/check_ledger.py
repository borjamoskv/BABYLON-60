# [C5-REAL] Exergy-Maximized
"""
cat_id: check-ledger
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import asyncio
import os

from babylon60.audit.ledger import EnterpriseAuditLedger
from babylon60.database.core import connect_async


async def run():
    db_path = os.environ.get(
        "CORTEX_DB_PATH", os.path.expanduser("~/.gemini/antigravity/cortex.db")
    )
    logging.getLogger(__name__).info(f"Using DB: {db_path}")
    db = await connect_async(db_path)
    ledger = EnterpriseAuditLedger(db)
    await ledger.ensure_table()
    res = await ledger.verify_chain()
    logging.getLogger(__name__).info("Ledger chain status:", res)

    # check ledger records
    cursor = await db.execute("SELECT COUNT(*) FROM security_audit_log")
    count = await cursor.fetchone()
    logging.getLogger(__name__).info("Ledger events count:", count[0])

    await db.close()


if __name__ == "__main__":
    asyncio.run(run())
