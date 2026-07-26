#!/usr/bin/env python3
"""Exergy optimizer helper.

Runs the exergy optimizer agent, extracts the numeric score and
returns True iff the score meets the required threshold (≥ 950).

The function also logs a ledger event for auditability.
"""

import json
import subprocess
import sys
import uuid
from pathlib import Path
from datetime import datetime
from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent

EXERGY_THRESHOLD = 950.0
OPTIMIZER_SCRIPT = "scripts/exergy_optimizer_agent.py"


def _run_agent() -> float:
    """Execute the optimizer and parse its output."""
    proc = subprocess.run(
        [sys.executable, OPTIMIZER_SCRIPT],
        cwd="/Users/borjafernandezangulo/30_BABYLON-60",
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Exergy optimizer failed: {proc.stderr}")
    try:
        data = json.loads(proc.stdout)
        return float(data.get("score", 0.0))
    except (json.JSONDecodeError, TypeError, ValueError, KeyError):
        import re
        match = re.search(r"ExergyScore:\s*([0-9.]+)", proc.stdout)
        if match:
            return float(match.group(1))
        raise RuntimeError(f"Unable to parse exergy output from stdout: {proc.stdout[:200]}")




def _record_event(score: float) -> None:
    """Persist the exergy check in the Cortex ledger."""
    async def _inner():
        actor = BFTLedgerActor(Path("cortex.db"))
        await actor.start()
        try:
            payload = {"score": score, "threshold": EXERGY_THRESHOLD}
            event = LedgerEvent(
                stream="audit",
                entity_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"exergy:{datetime.utcnow().isoformat()}")),
                event_type="exergy_check",
                payload=payload,
                cortex_taint="exergy_optimizer",
                source_db="cortex.db",
                source_table="events",
                source_pk=str(uuid.uuid4()),
            )
            await actor.append(event)
        finally:
            await actor.stop()
    import asyncio
    asyncio.run(_inner())




def run_exergy_optimizer() -> bool:
    """Public API – returns True if the exergy score meets the threshold."""
    try:
        score = _run_agent()
    except (RuntimeError, ValueError, OSError) as e:
        print(f"⚠️  Exergy check failed: {e}", file=sys.stderr)
        return False
    _record_event(score)
    return score >= EXERGY_THRESHOLD
