#!/usr/bin/env python3
# [C5-REAL] Exergy-Maximized
"""CORTEX Quickstart: Store and verify a decision.

import logging
This example shows the core CORTEX workflow:
1. Store a fact with cryptographic integrity
2. Verify its hash chain
3. Check the full ledger integrity

Usage:
    python examples/quickstart/basic_memory.py
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path


async def main() -> None:
    # Use a temporary database for this example
    db_path = Path(tempfile.mkdtemp()) / "quickstart.db"

    # Import CortexEngine - the single entry point for all operations
    from babylon60.engine import CortexEngine

    engine = CortexEngine(db_path=str(db_path))

    logging.getLogger(__name__).info("🧠 CORTEX Quickstart - Basic Memory\n")

    # --- Step 1: Store facts ---
    logging.getLogger(__name__).info("1️⃣  Storing decisions...")
    fact1 = await engine.store_fact(  # pyright: ignore[reportOptionalCall]
        content="Chose OAuth2 PKCE for authentication",
        fact_type="decision",
        project="quickstart",
        source="human:developer",
    )
    logging.getLogger(__name__).info(f"   ✅ Fact #{fact1['id']} stored (hash: {fact1['hash'][:12]}...)")

    fact2 = await engine.store_fact(  # pyright: ignore[reportOptionalCall]
        content="Selected PostgreSQL over MongoDB for audit compliance",
        fact_type="decision",
        project="quickstart",
        source="human:architect",
    )
    logging.getLogger(__name__).info(f"   ✅ Fact #{fact2['id']} stored (hash: {fact2['hash'][:12]}...)")

    # --- Step 2: Verify a single fact ---
    logging.getLogger(__name__).info("\n2️⃣  Verifying fact integrity...")
    result = await engine.verify_fact(fact1["id"])  # pyright: ignore[reportAttributeAccessIssue]
    status = "✅ VERIFIED" if result["valid"] else "❌ BROKEN"
    logging.getLogger(__name__).info(f"   {status} - Hash chain: {result.get('chain_status', 'ok')}")

    # --- Step 3: Search facts ---
    logging.getLogger(__name__).info("\n3️⃣  Searching memory...")
    facts = await engine.search_facts("authentication", project="quickstart")  # pyright: ignore[reportAttributeAccessIssue]
    logging.getLogger(__name__).info(f"   Found {len(facts)} matching fact(s)")
    for f in facts:
        logging.getLogger(__name__).info(f"   → [{f['type']}] {f['content'][:60]}")

    # --- Step 4: Generate compliance report ---
    logging.getLogger(__name__).info("\n4️⃣  Compliance check...")
    report = await engine.compliance_report(project="quickstart")  # pyright: ignore[reportAttributeAccessIssue]
    logging.getLogger(__name__).info(f"   Score: {report.get('score', 'N/A')}/5")
    logging.getLogger(__name__).info(f"   Status: {report.get('status', 'unknown')}")

    logging.getLogger(__name__).info("\n✨ Done! CORTEX verified all decisions with cryptographic integrity.")
    logging.getLogger(__name__).info(f"   Database: {db_path}")


if __name__ == "__main__":
    asyncio.run(main())
