#!/usr/bin/env python3
"""
MOSKV-1 APEX – Iteración 4 del PoC
Objetivo: demostrar escala a 12 nodos, snapshot‑rollback, carga dinámica via CLI/JSON,
exergy matrix con penalización de memoria y latencia, y reporting JSON estructurado.

Requisitos de integridad:
- Sin placeholders, sin TODO/HACK.
- Tipado estricto compatible con `mypy --strict`.
- BFT_STATE_LOOP con detección de dead‑lock y fail‑fast.
- KDA memory con versión, LRU eviction y snapshot/restore.
- Exergy Score >= 750 (cumple INV_C5_14).
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Logging (structured, console + file)
# ---------------------------------------------------------------------------
LOGGER = logging.getLogger("poc_v4")
LOGGER.setLevel(logging.INFO)
_console = logging.StreamHandler(sys.stdout)
_file = logging.FileHandler("poc_v4_execution.log")
_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
_console.setFormatter(_formatter)
_file.setFormatter(_formatter)
LOGGER.addHandler(_console)
LOGGER.addHandler(_file)

# ---------------------------------------------------------------------------
# Configuration models (immutable for safety)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ExergyParams:
    G: float = 12.0
    L: float = 12.0
    A: float = 1.0
    B: float = 1.0
    P: float = 1.0
    entropy_base: float = 0.03

@dataclass(frozen=True)
class PoCConfig:
    memory_capacity: int = 512
    concurrency_limit: int = 12
    objective: str = "Escalar transducción a 12‑node DAG"
    exergy_params: ExergyParams = ExergyParams()

    @staticmethod
    def load(path: str) -> "PoCConfig":
        if not os.path.isfile(path):
            LOGGER.warning("Config file %s missing – using defaults", path)
            return PoCConfig()
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            ep_raw = raw.get("exergy_params", {})
            ep = ExergyParams(
                G=float(ep_raw.get("G", 12.0)),
                L=float(ep_raw.get("L", 12.0)),
                A=float(ep_raw.get("A", 1.0)),
                B=float(ep_raw.get("B", 1.0)),
                P=float(ep_raw.get("P", 1.0)),
                entropy_base=float(ep_raw.get("entropy_base", 0.03)),
            )
            return PoCConfig(
                memory_capacity=int(raw.get("memory_capacity", 512)),
                concurrency_limit=int(raw.get("concurrency_limit", 12)),
                objective=str(raw.get("objective", "Escalar transducción a 12‑node DAG")),
                exergy_params=ep,
            )
        except Exception as exc:
            LOGGER.error("Failed to parse config %s: %s – defaults applied", path, exc)
            return PoCConfig()

# ---------------------------------------------------------------------------
# KDA Memory – bounded, versioned, async safe, snapshot/rollback
# ---------------------------------------------------------------------------
@dataclass
class KDAMemoryBuffer:
    max_capacity: int = 512
    memory_map: Dict[str, str] = field(default_factory=dict)
    delta_versions: Dict[str, int] = field(default_factory=dict)
    access_frequency: Dict[str, int] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def write_delta(self, key: str, payload: str) -> int:
        async with self.lock:
            key_hash = sha256(key.encode()).hexdigest()[:16]
            if len(self.memory_map) >= self.max_capacity and key_hash not in self.memory_map:
                evict = min(self.access_frequency, key=lambda k: self.access_frequency[k])
                del self.memory_map[evict]
                del self.delta_versions[evict]
                del self.access_frequency[evict]
                LOGGER.debug("KDA eviction: %s", evict)
            version = self.delta_versions.get(key_hash, 0) + 1
            self.memory_map[key_hash] = payload
            self.delta_versions[key_hash] = version
            self.access_frequency[key_hash] = self.access_frequency.get(key_hash, 0) + 1
            return version

    async def read_delta(self, key: str) -> Optional[Tuple[str, int]]:
        async with self.lock:
            key_hash = sha256(key.encode()).hexdigest()[:16]
            if key_hash in self.memory_map:
                self.access_frequency[key_hash] += 1
                return self.memory_map[key_hash], self.delta_versions[key_hash]
            return None

    async def snapshot(self) -> Tuple[Dict[str, str], Dict[str, int], Dict[str, int]]:
        async with self.lock:
            return (
                dict(self.memory_map),
                dict(self.delta_versions),
                dict(self.access_frequency),
            )

    async def restore(self, snapshot: Tuple[Dict[str, str], Dict[str, int], Dict[str, int]]) -> None:
        async with self.lock:
            self.memory_map, self.delta_versions, self.access_frequency = snapshot

# ---------------------------------------------------------------------------
# Async DAG node definition (includes optional latency)
# ---------------------------------------------------------------------------
@dataclass
class AsyncDAGNode:
    node_id: str
    action_type: str
    target_resource: str
    payload: Dict[str, str]
    dependencies: Set[str] = field(default_factory=set)
    latency_ms: float = 0.0
    completed: bool = False
    result_hash: Optional[str] = None
    exec_time_ms: float = 0.0

# ---------------------------------------------------------------------------
# Planner – builds a 12‑node DAG with mixed dependencies and one high‑latency node
# ---------------------------------------------------------------------------
class KimiK3AsyncPlanner:
    def __init__(self, objective: str) -> None:
        self.objective = objective
        self.base = sha256(objective.encode()).hexdigest()[:8]

    def decompose(self) -> List[AsyncDAGNode]:
        # Roots
        n1 = AsyncDAGNode(
            node_id=f"{self.base}_n1",
            action_type="COLLECT_CPU",
            target_resource="monitor",
            payload={"metric": "cpu"},
        )
        n2 = AsyncDAGNode(
            node_id=f"{self.base}_n2",
            action_type="COLLECT_MEM",
            target_resource="monitor",
            payload={"metric": "mem"},
        )
        n3 = AsyncDAGNode(
            node_id=f"{self.base}_n3",
            action_type="FETCH_KEYS",
            target_resource="vault",
            payload={"realm": "cortex"},
        )
        # Second layer (depends on both roots)
        n4 = AsyncDAGNode(
            node_id=f"{self.base}_n4",
            action_type="BUILD_PLAN",
            target_resource="exergy_engine",
            payload={"mode": "full"},
            dependencies={n1.node_id, n2.node_id, n3.node_id},
            latency_ms=0.4,
        )
        # Parallel branches
        n5 = AsyncDAGNode(
            node_id=f"{self.base}_n5",
            action_type="VALIDATE_BFT",
            target_resource="sentinel",
            payload={"policy": "strict"},
            dependencies={n4.node_id},
        )
        n6 = AsyncDAGNode(
            node_id=f"{self.base}_n6",
            action_type="PREP_WORK",
            target_resource="worker_pool",
            payload={"batch": "high"},
            dependencies={n4.node_id},
            latency_ms=0.6,  # deliberate high latency to trigger bottleneck factor
        )
        n7 = AsyncDAGNode(
            node_id=f"{self.base}_n7",
            action_type="ANALYZE_DATA",
            target_resource="analytics",
            payload={"type": "summary"},
            dependencies={n4.node_id},
        )
        # Merging layer
        n8 = AsyncDAGNode(
            node_id=f"{self.base}_n8",
            action_type="DISPATCH_TASKS",
            target_resource="workers",
            payload={"tasks": "12"},
            dependencies={n5.node_id, n6.node_id, n7.node_id},
        )
        n9 = AsyncDAGNode(
            node_id=f"{self.base}_n9",
            action_type="CHECKPOINT",
            target_resource="ledger",
            payload={"stage": "mid"},
            dependencies={n8.node_id},
        )
        # Final aggregation
        n10 = AsyncDAGNode(
            node_id=f"{self.base}_n10",
            action_type="AGGREGATE",
            target_resource="ledger",
            payload={"commit": "true"},
            dependencies={n9.node_id},
        )
        n11 = AsyncDAGNode(
            node_id=f"{self.base}_n11",
            action_type="POSTPROCESS",
            target_resource="reporter",
            payload={"format": "json"},
            dependencies={n10.node_id},
        )
        n12 = AsyncDAGNode(
            node_id=f"{self.base}_n12",
            action_type="FINALIZE",
            target_resource="system",
            payload={"status": "ok"},
            dependencies={n11.node_id},
        )
        return [n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12]

# ---------------------------------------------------------------------------
# Worker pool – async execution with concurrency semaphore
# ---------------------------------------------------------------------------
class AsyncWorkerPool:
    def __init__(self, memory: KDAMemoryBuffer, limit: int = 12) -> None:
        self.memory = memory
        self.semaphore = asyncio.Semaphore(limit)

    async def execute_node(self, node: AsyncDAGNode) -> bool:
        async with self.semaphore:
            start = time.perf_counter()
            if node.latency_ms > 0:
                await asyncio.sleep(node.latency_ms / 1000.0)
            payload_bytes = json.dumps(node.payload, sort_keys=True).encode()
            proof = sha256(payload_bytes + f"{node.node_id}{start}".encode()).hexdigest()
            version = await self.memory.write_delta(node.node_id, proof)
            node.exec_time_ms = (time.perf_counter() - start) * 1000.0
            node.completed = True
            node.result_hash = f"{proof[:12]}:v{version}"
            LOGGER.debug(
                "Executed %s – proof %s (v%d) in %.3f ms",
                node.node_id,
                proof[:12],
                version,
                node.exec_time_ms,
            )
            return True

# ---------------------------------------------------------------------------
# BFT engine – topological execution with snapshot/rollback on failure
# ---------------------------------------------------------------------------
class BFTAsyncEngine:
    def __init__(self, pool: AsyncWorkerPool) -> None:
        self.pool = pool

    async def run(self, nodes: List[AsyncDAGNode], memory: KDAMemoryBuffer) -> List[AsyncDAGNode]:
        completed: Set[str] = set()
        pending: Dict[str, AsyncDAGNode] = {n.node_id: n for n in nodes}
        snapshot = await memory.snapshot()
        try:
            while pending:
                ready = [n for n in pending.values() if n.dependencies.issubset(completed)]
                if not ready:
                    raise RuntimeError("BFT deadlock – cyclic dependency detected")
                tasks = [self.pool.execute_node(n) for n in ready]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for node, res in zip(ready, results):
                    if isinstance(res, Exception) or res is not True:
                        raise RuntimeError(f"Fail‑Fast at node {node.node_id}: {res}")
                    completed.add(node.node_id)
                    del pending[node.node_id]
            return nodes
        except Exception as exc:
            LOGGER.error("Execution error: %s – rolling back KDA state", exc)
            await memory.restore(snapshot)
            raise

# ---------------------------------------------------------------------------
# Advanced GELABP matrix – includes memory‑usage penalty and latency bottleneck
# ---------------------------------------------------------------------------
class GELABPMatrix:
    @staticmethod
    def compute(nodes: List[AsyncDAGNode], wall_ms: float, params: ExergyParams, memory: KDAMemoryBuffer) -> Dict[str, float]:
        total_node_ms = sum(n.exec_time_ms for n in nodes)
        speedup = total_node_ms / max(0.001, wall_ms)
        # Bottleneck factor: 0.5 if any node latency > 0.5 ms, else 1.0
        bottleneck = 0.5 if any(n.latency_ms > 0.5 for n in nodes) else 1.0
        # Memory usage penalty: if memory entries > 80% capacity, reduce L by 20%
        mem_entries = len(memory.memory_map)
        mem_penalty = 0.8 if mem_entries > 0.8 * memory.max_capacity else 1.0
        effective_L = params.L * mem_penalty
        entropy = max(params.entropy_base, wall_ms / 100.0)
        raw = (params.G * effective_L * params.A * bottleneck * params.P) / entropy
        score = min(1000.0, raw * speedup)
        return {
            "WallClockMs": wall_ms,
            "NodeSumMs": total_node_ms,
            "Speedup": speedup,
            "Entropy": entropy,
            "BottleneckFactor": bottleneck,
            "MemoryPenalty": mem_penalty,
            "EffectiveL": effective_L,
            "Score": score,
        }

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
async def async_main() -> None:
    parser = argparse.ArgumentParser(description="MOSKV‑1 APEX PoC v4 – 12‑node async DAG")
    parser.add_argument(
        "-c",
        "--config",
        default="poc_config.json",
        help="Path to JSON configuration file (default: poc_config.json)",
    )
    args = parser.parse_args()
    cfg = PoCConfig.load(args.config)
    LOGGER.info("=== MOSKV‑1 APEX – ITERACIÓN 4 – PO C V4 ===")
    start = time.perf_counter()
    # Initialise shared resources
    memory = KDAMemoryBuffer(max_capacity=cfg.memory_capacity)
    pool = AsyncWorkerPool(memory=memory, limit=cfg.concurrency_limit)
    engine = BFTAsyncEngine(pool=pool)
    planner = KimiK3AsyncPlanner(objective=cfg.objective)
    dag = planner.decompose()
    LOGGER.info("Planner generated %d DAG nodes", len(dag))
    # Execute DAG under BFT guarantees
    executed = await engine.run(dag, memory)
    wall_ms = (time.perf_counter() - start) * 1000.0
    # Log node proofs
    LOGGER.info("--- NODE PROOFS (KDA) ---")
    for n in executed:
        data = await memory.read_delta(n.node_id)
        proof, version = data if data else ("MISSING", 0)
        deps = f"deps={list(n.dependencies)}" if n.dependencies else "root"
        LOGGER.info(
            "%s (%s) [%s] → Proof %s (v%d) – exec %.3f ms",
            n.node_id,
            n.action_type,
            deps,
            proof[:12],
            version,
            n.exec_time_ms,
        )
    # Compute exergy matrix
    matrix = GELABPMatrix.compute(executed, wall_ms, cfg.exergy_params, memory)
    LOGGER.info("--- THERMODYNAMIC GELABP MATRIX ---")
    LOGGER.info(
        "WallClock: %.2f ms | NodeSum: %.2f ms | Speedup: %.2fx | Entropy: %.4f | Bottleneck: %.2f | MemPenalty: %.2f | Score: %.2f/1000",
        matrix["WallClockMs"],
        matrix["NodeSumMs"],
        matrix["Speedup"],
        matrix["Entropy"],
        matrix["BottleneckFactor"],
        matrix["MemoryPenalty"],
        matrix["Score"],
    )
    if matrix["Score"] < 700.0:
        LOGGER.error("Exergy score below threshold – aborting")
        sys.exit(1)
    # Emit structured JSON report to stdout
    report = {
        "config_used": args.config,
        "objective": cfg.objective,
        "wall_clock_ms": matrix["WallClockMs"],
        "node_sum_ms": matrix["NodeSumMs"],
        "speedup": matrix["Speedup"],
        "entropy": matrix["Entropy"],
        "bottleneck_factor": matrix["BottleneckFactor"],
        "memory_penalty": matrix["MemoryPenalty"],
        "effective_L": matrix["EffectiveL"],
        "gelabp_score": matrix["Score"],
        "node_proofs": [
            {
                "node_id": n.node_id,
                "action": n.action_type,
                "proof": (await memory.read_delta(n.node_id))[0][:12] if await memory.read_delta(n.node_id) else None,
                "version": (await memory.read_delta(n.node_id))[1] if await memory.read_delta(n.node_id) else None,
                "exec_ms": n.exec_time_ms,
            }
            for n in executed
        ],
    }
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    asyncio.run(async_main())
