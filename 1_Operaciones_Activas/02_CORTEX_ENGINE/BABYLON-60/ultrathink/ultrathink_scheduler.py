# C5-REAL EXERGY CERTIFIED
# ultrathink_scheduler.py — Async scheduler with BFTLedgerActor and Prometheus metrics

"""Scheduler for ULTRATHINK swarm.

* Uses :class:`babylon60.bft.ledger_actor.BFTLedgerActor` as the single-writer
  to guarantee Byzantine‑fault‑tolerant ordering of events.
* Exposes Prometheus metrics on a configurable port (default 8000).
"""

import asyncio
import os
import logging
import time
from pathlib import Path

try:
    from prometheus_client import start_http_server, Gauge, Counter, Histogram
except ImportError:
    def start_http_server(*args, **kwargs):
        _ = (args, kwargs)

    class DummyMetric:
        def __init__(self, *args, **kwargs):
            _ = (args, kwargs)
        def set(self, *args, **kwargs):
            _ = (args, kwargs)
        def inc(self, *args, **kwargs):
            _ = (args, kwargs)
        def observe(self, *args, **kwargs):
            _ = (args, kwargs)

    Gauge = Counter = Histogram = DummyMetric

class ConsensusEngineStub:
    """Base stub for consensus engines in ULTRATHINK scheduler."""

    def propose(self, payload: bytes) -> None:
        _ = payload


from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------
SCHEDULER_QUEUE_SIZE = Gauge(
    "ultrathink_scheduler_queue_size",
    "Current number of pending scheduler tasks",
)
LEDGER_WRITE_LATENCY_MS = Histogram(
    "ultrathink_ledger_write_latency_ms",
    "Latency of writes to the BFT ledger (ms)",
)
PROPOSALS_TOTAL = Counter(
    "ultrathink_proposals_total",
    "Total number of proposal attempts (including retries)",
)
PROPOSALS_SUCCESS = Counter(
    "ultrathink_proposals_success",
    "Number of proposals that eventually succeeded",
)

# ---------------------------------------------------------------------------
# Scheduler configuration
# ---------------------------------------------------------------------------
MAX_RETRIES: int = 5
BASE_BACKOFF_S: float = 0.05  # seconds, exponential back‑off base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("ultrathink.scheduler")


async def propose_with_backoff(
    actor: Any,
    payload: Any,
    task_id: int,
) -> bool:
    """Create a :class:`LedgerEvent` or propose payload and append it to the BFT actor.

    Retries on ``TimeoutError``, ``OSError``, ``ValueError``, or ``RuntimeError``
    according to ``MAX_RETRIES``.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            PROPOSALS_TOTAL.inc()
            if hasattr(actor, "propose"):
                p_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
                actor.propose(p_bytes)
            else:
                event = LedgerEvent(
                    stream="scheduler",
                    entity_id=f"task-{task_id}",
                    event_type="CREATED",
                    payload={"data": payload},
                    cortex_taint="[CORTEX-TAINT:borjamoskv:seal:scheduler]",
                    source_db="ultrathink",
                    source_table="scheduler",
                    source_pk=str(task_id),
                )
                start = time.time()
                future = actor.append(event)
                await future
                elapsed_ms = (time.time() - start) * 1000
                LEDGER_WRITE_LATENCY_MS.observe(elapsed_ms)
            PROPOSALS_SUCCESS.inc()
            return True
        except (TimeoutError, OSError, ValueError, RuntimeError) as exc:
            if attempt == MAX_RETRIES:
                log.error(f"Task {task_id} failed after {MAX_RETRIES} attempts: {exc}")
                return False
            backoff = BASE_BACKOFF_S * (2 ** (attempt - 1))
            await asyncio.sleep(backoff)
    return False


async def main() -> None:
    # -------------------------------------------------------------------
    # Metrics server
    # -------------------------------------------------------------------
    metrics_port = int(os.getenv("PROMETHEUS_PORT", "8000"))
    start_http_server(metrics_port)
    log.info(f"Prometheus metrics exposed on :{metrics_port}/")

    # -------------------------------------------------------------------
    # BFT ledger actor setup
    # -------------------------------------------------------------------
    db_path = Path("ultrathink_scheduler_ledger.db")
    actor = BFTLedgerActor(db_path)
    await actor.start()

    # -------------------------------------------------------------------
    # Payload preparation (fallback to dummy tasks if map file missing)
    # -------------------------------------------------------------------
    map_file = "docs/C5_SKILLS_BRIDGES_MAP.md"
    payloads: list[str] = []
    if os.path.exists(map_file):
        with open(map_file, encoding="utf-8") as f:
            for line in f:
                if "**" in line:
                    vector = line.split("**")[1]
                    payloads.append(f"EXEC_VECTOR:{vector}")
    if not payloads:
        log.warning("No mapped vectors found, falling back to dummy tasks.")
        payloads = [f"task-{i}" for i in range(1000)]

    total_tasks = len(payloads)
    SCHEDULER_QUEUE_SIZE.set(total_tasks)

    t0 = time.monotonic()
    tasks = [
        asyncio.create_task(propose_with_backoff(actor, payloads[i], i))
        for i in range(total_tasks)
    ]
    results = await asyncio.gather(*tasks)
    successes = sum(1 for r in results if r)

    elapsed = time.monotonic() - t0
    log.info(f"Completed: {successes}/{total_tasks} proposals in {elapsed:.3f}s")
    if elapsed > 0:
        log.info(f"Throughput: {int(successes / elapsed)} proposals/s")

    await actor.stop()


if __name__ == "__main__":
    asyncio.run(main())
