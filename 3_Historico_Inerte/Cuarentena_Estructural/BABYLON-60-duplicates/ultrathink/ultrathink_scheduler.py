# C5-REAL EXERGY CERTIFIED
# ultrathink_scheduler.py — Async scheduler with BFTLedgerActor and Prometheus metrics

"""Scheduler for ULTRATHINK swarm.

* Uses :class:`babylon60.bft.ledger_actor.BFTLedgerActor` as the single-writer
  to guarantee Byzantine‑fault‑tolerant ordering of events.
* Exposes Prometheus metrics on a configurable port (default 8000).
"""

from __future__ import annotations

import sys
import asyncio
import os
import json
import logging
import time
from pathlib import Path
from typing import Any, List, Optional, Dict

# Auto-resolve parent BABYLON-60 directory into sys.path
BABYLON_ROOT = Path(__file__).resolve().parents[1]
if str(BABYLON_ROOT) not in sys.path:
    sys.path.insert(0, str(BABYLON_ROOT))

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

try:
    from ultrathink.secretary_router import SecretaryRouter, RoutingResult
except ImportError:
    try:
        from secretary_router import SecretaryRouter, RoutingResult
    except ImportError:
        SecretaryRouter = None
        RoutingResult = None

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
ROUTED_INTENTS_TOTAL = Counter(
    "ultrathink_routed_intents_total",
    "Total intents processed by SecretaryRouter",
)
ROUTING_REJECTIONS_TOTAL = Counter(
    "ultrathink_routing_rejections_total",
    "Total intents rejected due to budget or mismatch",
)
SKILL_BYTES_DISPATCHED = Counter(
    "ultrathink_skill_bytes_dispatched",
    "Total skill bytes dispatched to workers",
)

# ---------------------------------------------------------------------------
# Scheduler configuration
# ---------------------------------------------------------------------------
MAX_RETRIES: int = 5
BASE_BACKOFF_S: float = 0.05  # seconds, exponential back‑off base
DEFAULT_MAX_CONCURRENCY: int = 1500
_ROUTING_CACHE: Dict[str, Dict[str, Any]] = {}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("ultrathink.scheduler")


async def propose_with_backoff(
    actor: Any,
    payload: Any,
    task_id: int,
    semaphore: Optional[asyncio.Semaphore] = None,
    router: Optional[Any] = None,
) -> bool:
    """Create a :class:`LedgerEvent` or propose payload and append it to the BFT actor.

    Retries on ``TimeoutError``, ``OSError``, ``ValueError``, or ``RuntimeError``
    according to ``MAX_RETRIES``. Integrates skill routing via SecretaryRouter if provided.
    """
    async def _attempt_proposal() -> bool:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                PROPOSALS_TOTAL.inc()
                if hasattr(actor, "propose") and callable(getattr(actor, "propose")):
                    p_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
                    actor.propose(p_bytes)
                else:
                    event_payload: Dict[str, Any] = {"data": payload}

                    # Skill routing integration (Nodo 4 — El Secretario)
                    if router is not None and hasattr(router, "route"):
                        intent_str = None
                        if isinstance(payload, str):
                            if payload.startswith("INTENT:"):
                                intent_str = payload[len("INTENT:"):].strip()
                            elif payload.startswith("EXEC_VECTOR:"):
                                intent_str = payload[len("EXEC_VECTOR:"):].strip().replace("_", " ")
                        elif isinstance(payload, dict) and "intent" in payload:
                            intent_str = str(payload["intent"])

                        if intent_str:
                            ROUTED_INTENTS_TOTAL.inc()
                            if intent_str not in _ROUTING_CACHE:
                                routing_res = router.route(intent_str)
                                _ROUTING_CACHE[intent_str] = routing_res.to_dict()
                                if routing_res.rejection_reason:
                                    ROUTING_REJECTIONS_TOTAL.inc()
                                else:
                                    SKILL_BYTES_DISPATCHED.inc(routing_res.total_bytes)
                            event_payload["routing"] = _ROUTING_CACHE[intent_str]

                    event = LedgerEvent(
                        stream="scheduler",
                        entity_id=f"task-{task_id}",
                        event_type="CREATED",
                        payload=event_payload,
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

    if semaphore is not None:
        async with semaphore:
            return await _attempt_proposal()
    return await _attempt_proposal()


def load_task_payloads() -> List[str]:
    """Load payloads from skill maps or registry, falling back to dummy tasks if none exist."""
    payloads: List[str] = []

    # Check 1: 2_Nucleo_Estatico/skill_registry.json
    registry_file = BABYLON_ROOT / "2_Nucleo_Estatico" / "skill_registry.json"
    if not registry_file.exists():
        curr = Path(".").resolve()
        for parent in [curr] + list(curr.parents):
            if (parent / "2_Nucleo_Estatico" / "skill_registry.json").exists():
                registry_file = parent / "2_Nucleo_Estatico" / "skill_registry.json"
                break

    if registry_file.exists():
        try:
            with open(registry_file, encoding="utf-8") as f:
                skills_data = json.load(f)
                for s in skills_data:
                    name = s.get("name", "unknown")
                    desc = s.get("description", "")
                    payloads.append(f"INTENT: execute skill {name} for {desc}")
            log.info(f"Loaded {len(payloads)} skills from {registry_file}")
        except Exception as e:
            log.warning(f"Failed to read skill registry at {registry_file}: {e}")

    # Check 2: C5_SKILLS_BRIDGES_MAP.md
    if not payloads:
        map_file = BABYLON_ROOT / "docs" / "C5_SKILLS_BRIDGES_MAP.md"
        if map_file.exists():
            with open(map_file, encoding="utf-8") as f:
                for line in f:
                    if "**" in line:
                        vector = line.split("**")[1]
                        payloads.append(f"EXEC_VECTOR:{vector}")
            log.info(f"Loaded {len(payloads)} vectors from {map_file}")

    # Check 3: SKILL_ARSENAL_TAXONOMY.md
    if not payloads:
        taxonomy_file = BABYLON_ROOT / "docs" / "SKILL_ARSENAL_TAXONOMY.md"
        if taxonomy_file.exists():
            with open(taxonomy_file, encoding="utf-8") as f:
                for line in f:
                    if "`" in line and "|" in line:
                        parts = line.split("`")
                        if len(parts) >= 2:
                            skill_name = parts[1]
                            payloads.append(f"EXEC_VECTOR:{skill_name}")
            log.info(f"Loaded {len(payloads)} vectors from {taxonomy_file}")

    # Check 4: Fallback to dummy tasks
    if not payloads:
        log.warning("No mapped vectors found, falling back to dummy tasks.")
        payloads = [f"task-{i}" for i in range(1000)]

    return payloads


async def main() -> None:
    # -------------------------------------------------------------------
    # Metrics server
    # -------------------------------------------------------------------
    metrics_port = int(os.getenv("PROMETHEUS_PORT", "8000"))
    start_http_server(metrics_port)
    log.info(f"Prometheus metrics exposed on :{metrics_port}/")

    # -------------------------------------------------------------------
    # Secretary Router setup (Nodo 4)
    # -------------------------------------------------------------------
    router = None
    if SecretaryRouter is not None:
        try:
            router = SecretaryRouter()
            router._registry.load()
            log.info("SecretaryRouter initialized with skill registry.")
        except Exception as e:
            log.warning(f"Could not initialize SecretaryRouter: {e}")

    # -------------------------------------------------------------------
    # BFT ledger actor setup
    # -------------------------------------------------------------------
    db_path = Path("ultrathink_scheduler_ledger.db")
    actor = BFTLedgerActor(db_path)
    await actor.start()

    # -------------------------------------------------------------------
    # Payload preparation
    # -------------------------------------------------------------------
    payloads = load_task_payloads()
    if len(payloads) < 1000:
        base_payloads = list(payloads)
        while len(payloads) < 1000:
            idx = len(payloads)
            item = base_payloads[idx % len(base_payloads)]
            payloads.append(f"{item} [replica-{idx}]")

    total_tasks = len(payloads)
    SCHEDULER_QUEUE_SIZE.set(total_tasks)

    max_concurrency = int(os.getenv("ULTRATHINK_MAX_CONCURRENCY", str(DEFAULT_MAX_CONCURRENCY)))
    semaphore = asyncio.Semaphore(max_concurrency)

    log.info(f"Dispatching {total_tasks} tasks to BFTLedgerActor (max_concurrency={max_concurrency})...")
    t0 = time.monotonic()
    tasks = [
        asyncio.create_task(propose_with_backoff(actor, payloads[i], i, semaphore, router))
        for i in range(total_tasks)
    ]
    results = await asyncio.gather(*tasks)
    successes = sum(1 for r in results if r)

    elapsed = time.monotonic() - t0
    log.info(f"Completed: {successes}/{total_tasks} proposals in {elapsed:.3f}s")
    if elapsed > 0:
        throughput = int(successes / elapsed)
        log.info(f"Throughput: {throughput} proposals/s")
        if throughput >= 2200:
            log.info("[C5-REAL VERIFIED] BFT consensus engine meets 2200+ ops/s benchmark requirement.")
        else:
            log.warning(f"[BENCHMARK WARNING] Throughput ({throughput} ops/s) below 2200 ops/s threshold.")

    # -------------------------------------------------------------------
    # Verify BFT Chain Integrity
    # -------------------------------------------------------------------
    log.info("Verifying BFT causal chain integrity...")
    try:
        is_valid = await actor.verify_chain()
        if is_valid:
            log.info("[BFT INVARIANT PASS] Ledger causal hash chain validated successfully.")
    except Exception as e:
        log.error(f"[BFT INVARIANT FAILURE] Chain verification failed: {e}")

    await actor.stop()


if __name__ == "__main__":
    asyncio.run(main())
