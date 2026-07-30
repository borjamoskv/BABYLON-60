#!/usr/bin/env python3
# [C5-REAL] Exergy-Maximized
"""CORTEX Quickstart: EU AI Act Compliance Report.

import logging
Demonstrates how to generate a compliance report that satisfies
EU AI Act Article 12 requirements for logging and traceability.

Usage:
    python examples/quickstart/compliance_report.py
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path


async def main() -> None:
    db_path = Path(tempfile.mkdtemp()) / "compliance.db"

    from babylon60.engine import CortexEngine

    engine = CortexEngine(db_path=str(db_path))

    logging.getLogger(__name__).info("📋 CORTEX Quickstart - EU AI Act Compliance Report\n")

    # --- Step 1: Simulate an agent's decision history ---
    logging.getLogger(__name__).info("1️⃣  Simulating agent decision history...\n")

    decisions = [
        ("decision", "Approved loan application #443 - risk score 0.23"),
        ("decision", "Rejected application #444 - income verification failed"),
        ("knowledge", "Risk model v2.1 deployed - AUC 0.94 on validation set"),
        ("error", "Timeout on credit bureau API - retried 3x, succeeded"),
        ("decision", "Approved application #445 - manual review flagged"),
    ]

    for fact_type, content in decisions:
        await engine.store_fact(  # pyright: ignore[reportOptionalCall]
            content=content,
            fact_type=fact_type,
            project="fintech-agent",
            source="agent:loan-processor",
        )
        logging.getLogger(__name__).info(f"   📝 [{fact_type}] {content[:60]}")

    # --- Step 2: Generate compliance report ---
    logging.getLogger(__name__).info("\n2️⃣  Generating EU AI Act compliance report...\n")
    report = await engine.compliance_report(project="fintech-agent")  # pyright: ignore[reportAttributeAccessIssue]

    logging.getLogger(__name__).info("   🏛️  EU AI Act Article 12 Compliance")
    logging.getLogger(__name__).info(f"   {'=' * 40}")
    logging.getLogger(__name__).info(f"   Score:         {report.get('score', 'N/A')}/5")
    logging.getLogger(__name__).info(f"   Status:        {report.get('status', 'unknown')}")
    logging.getLogger(__name__).info(f"   Total Facts:   {report.get('total_facts', 0)}")
    logging.getLogger(__name__).info(f"   Verified:      {report.get('verified_count', 0)}")

    checks = report.get("checks", {})
    if checks:
        logging.getLogger(__name__).info("\n   Requirements:")
        for check, passed in checks.items():
            icon = "✅" if passed else "❌"
            logging.getLogger(__name__).info(f"     {icon} {check}")

    # --- Step 3: Verify data integrity ---
    logging.getLogger(__name__).info("\n3️⃣  Verifying ledger integrity...")
    integrity = await engine.verify_integrity(project="fintech-agent")  # pyright: ignore[reportAttributeAccessIssue]
    icon = "✅" if integrity.get("valid", False) else "❌"
    logging.getLogger(__name__).info(f"   {icon} Ledger: {integrity.get('status', 'unknown')}")
    if "merkle_root" in integrity:
        logging.getLogger(__name__).info(f"   🌳 Merkle root: {integrity['merkle_root'][:16]}...")

    logging.getLogger(__name__).info("\n✨ Compliance report ready for regulatory submission.")
    logging.getLogger(__name__).info("   All decisions are hash-chained and Merkle-sealed.")


if __name__ == "__main__":
    asyncio.run(main())
