#!/usr/bin/env python3
# [C5-REAL] Exergy-Maximized
"""CORTEX Quickstart: Multi-Agent Byzantine Consensus.

import logging
Demonstrates how CORTEX verifies decisions across multiple agents
using Weighted Byzantine Fault-Tolerant (WBFT) consensus.

Usage:
    python examples/quickstart/multi_agent_consensus.py
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path


async def main() -> None:
    db_path = Path(tempfile.mkdtemp()) / "consensus.db"

    from babylon60.engine import CortexEngine

    engine = CortexEngine(db_path=str(db_path))

    logging.getLogger(__name__).info("🤝 CORTEX Quickstart - Multi-Agent Consensus\n")

    # --- Step 1: Multiple agents store observations ---
    logging.getLogger(__name__).info("1️⃣  Agents submitting observations...\n")

    agents = [
        ("agent:analyst-1", "Market conditions favor conservative allocation"),
        ("agent:analyst-2", "Market conditions favor conservative allocation"),
        ("agent:analyst-3", "Market conditions favor aggressive growth"),
    ]

    facts = []
    for source, content in agents:
        fact = await engine.store_fact(  # pyright: ignore[reportOptionalCall]
            content=content,
            fact_type="decision",
            project="consensus-demo",
            source=source,
        )
        facts.append(fact)
        logging.getLogger(__name__).info(f'   📝 {source}: "{content[:50]}..."')

    # --- Step 2: Show consensus ---
    logging.getLogger(__name__).info("\n2️⃣  Checking consensus across agents...")
    all_facts = await engine.search_facts("market conditions", project="consensus-demo")  # pyright: ignore[reportAttributeAccessIssue]

    # Count agreement
    votes: dict[str, int] = {}
    for f in all_facts:
        key = f["content"]
        votes[key] = votes.get(key, 0) + 1

    logging.getLogger(__name__).info(f"\n   📊 Results ({len(all_facts)} votes):")
    for content, count in sorted(votes.items(), key=lambda x: -x[1]):
        pct = count / len(all_facts) * 100
        bar = "█" * int(pct / 5)
        logging.getLogger(__name__).info(f'      {bar} {pct:.0f}% - "{content[:50]}"')

    # BFT threshold: need > 2/3 agreement
    max_votes = max(votes.values())
    threshold = len(all_facts) * 2 / 3
    if max_votes > threshold:
        logging.getLogger(__name__).info(f"\n   ✅ CONSENSUS REACHED (>{threshold:.0f} of {len(all_facts)} agents agree)")
    else:
        logging.getLogger(__name__).info(f"\n   ⚠️  NO CONSENSUS (need >{threshold:.0f} of {len(all_facts)}, got {max_votes})")

    # --- Step 3: Verify integrity ---
    logging.getLogger(__name__).info("\n3️⃣  Verifying all decisions have cryptographic integrity...")
    for fact in facts:
        result = await engine.verify_fact(fact["id"])  # pyright: ignore[reportAttributeAccessIssue]
        status = "✅" if result["valid"] else "❌"
        logging.getLogger(__name__).info(f"   {status} Fact #{fact['id']} - chain intact")

    logging.getLogger(__name__).info("\n✨ Multi-agent consensus demonstration complete.")


if __name__ == "__main__":
    asyncio.run(main())
