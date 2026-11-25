import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
import sys
import tempfile
import time
import unittest

import httpx

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents_archi.orchestrator.blackboard import (
    BlackboardArbiter,
    BlackboardStatus,
    BlackboardTopic,
    ColdPathCurator,
    MAX_PAYLOAD_BYTES,
)
from agents_archi.orchestrator.kda_dag_swarm import (
    KahnDagSwarmScheduler,
    KdaSwarmMemory,
    SwarmDagNode,
    ThermalLock,
)
from agents_archi.orchestrator.royal_rumble import CortexWalStore
from agents_archi.orchestrator.swarm import (
    InferenceBackend,
    RobustLLMClient,
    SwarmConfig,
    SwarmOrchestrator,
)


class TestSwarmEntropyRegressions(unittest.TestCase):
    def test_blackboard_concurrency_indexes_payload_cap_and_chunked_compaction_b1_b4(self) -> None:
        with tempfile.TemporaryDirectory(prefix="babylon-bb-") as td:
            wal = CortexWalStore(os.path.join(td, "bb.sqlite3"))
            self.addCleanup(wal.close)
            arbiter = BlackboardArbiter(wal)

            # B2: Verify composite indexes exist
            cur = wal._conn.cursor()
            indexes = {
                row[0]
                for row in cur.execute("SELECT name FROM sqlite_master WHERE type='index';").fetchall()
            }
            self.assertIn("idx_blackboard_task_status_topic_tick", indexes)
            self.assertIn("idx_blackboard_task_status_tick", indexes)

            # B3: Reject oversized payload (> MAX_PAYLOAD_BYTES)
            oversized = arbiter.publish(
                task_id="t-cap",
                logical_tick=1,
                topic=BlackboardTopic.HYPOTHESIS,
                author_agent_id="agent-a",
                target_path="src/mod.py",
                claim="valid claim",
                payload={"blob": "x" * (MAX_PAYLOAD_BYTES + 128)},
            )
            self.assertFalse(oversized.admitted)
            self.assertEqual(oversized.reason, "DENY_PAYLOAD_TOO_LARGE")

            # B1: Concurrent multi-thread identical + distinct publishes without TOCTOU IntegrityError
            db_path = os.path.join(td, "bb.sqlite3")

            def _publish_worker(idx: int) -> bool:
                worker_wal = CortexWalStore(db_path)
                try:
                    worker_arbiter = BlackboardArbiter(worker_wal)
                    res = worker_arbiter.publish(
                        task_id="t-conc",
                        logical_tick=1,
                        topic=BlackboardTopic.HYPOTHESIS,
                        author_agent_id=f"author-{idx % 4}",
                        target_path="docs/mod.py",
                        claim=f"claim-{idx % 10}",
                        allow_sensitive_on_free=True,
                    )
                    return res.admitted
                finally:
                    worker_wal.close()

            with ThreadPoolExecutor(max_workers=8) as pool:
                outcomes = list(pool.map(_publish_worker, range(40)))
            self.assertTrue(all(outcomes))
            self.assertEqual(len(arbiter.poll_subscription("t-conc")), 10)

            # B4: Chunked compaction > 500 tuples
            proof_hash = hashlib.sha256(b"verified-evidence").hexdigest()
            for i in range(520):
                pub = arbiter.publish(
                    task_id="t-chunk",
                    logical_tick=i + 1,
                    topic=BlackboardTopic.HYPOTHESIS,
                    author_agent_id="author-1",
                    target_path="docs/mod.py",
                    claim=f"chunk-claim-{i}",
                    allow_sensitive_on_free=True,
                )
                self.assertTrue(pub.admitted)
                arbiter.resolve(
                    tuple_id=pub.tuple_id,
                    verifier_agent_id="verifier-2",
                    new_status=BlackboardStatus.VERIFIED,
                    evidence_hash=proof_hash,
                    logical_tick=i + 2,
                )

            curator = ColdPathCurator(arbiter)
            digest = curator.compact_resolved_tuples("t-chunk", logical_tick=1000)
            self.assertEqual(len(digest.compacted_tuple_ids), 520)
            self.assertEqual(arbiter.poll_subscription("t-chunk", status=BlackboardStatus.VERIFIED), [])

    def test_thermal_lock_recovers_stale_pid_and_blocks_live_pid_k2(self) -> None:
        with tempfile.TemporaryDirectory(prefix="babylon-tlock-") as td:
            lock_path = os.path.join(td, "thermal.lock")

            # Dead PID -> should recover stale lock
            with open(lock_path, "w", encoding="utf-8") as f:
                f.write("pid:99999999;time:0")
            with ThermalLock(lock_path):
                self.assertTrue(os.path.exists(lock_path))
            self.assertFalse(os.path.exists(lock_path))

            # Live PID (current process) -> must remain fail-closed
            with open(lock_path, "w", encoding="utf-8") as f:
                f.write(f"pid:{os.getpid()};time:{time.time_ns()}")
            with self.assertRaises(RuntimeError):
                with ThermalLock(lock_path):
                    pass
            os.remove(lock_path)

    def test_kda_dag_sync_offload_and_node_timeout_k4(self) -> None:
        with tempfile.TemporaryDirectory(prefix="babylon-kda-") as td:
            lock_path = os.path.join(td, "dag.lock")
            sched = KahnDagSwarmScheduler(concurrency_limit=8)
            mem = KdaSwarmMemory(capacity=32)

            def slow_sync(_mem: KdaSwarmMemory) -> None:
                time.sleep(0.03)

            for i in range(8):
                sched.add_node(SwarmDagNode(f"n-{i}", [], slow_sync))

            t0 = time.perf_counter()
            asyncio.run(sched.execute_dag(mem, lock_path=lock_path, node_timeout_s=0.5))
            elapsed = time.perf_counter() - t0
            # 8 sync nodes x 30ms running concurrently should finish well under 240ms sequential
            self.assertLess(elapsed, 0.18)

            # Timeout enforcement
            sched_timeout = KahnDagSwarmScheduler(concurrency_limit=2)
            sched_timeout.add_node(SwarmDagNode("slow", [], lambda _m: time.sleep(0.2)))
            with self.assertRaises(asyncio.TimeoutError):
                asyncio.run(sched_timeout.execute_dag(mem, lock_path=lock_path, node_timeout_s=0.03))

    def test_swarm_shared_http_pool_and_cb_half_open_s1_s2(self) -> None:
        created_clients = 0
        original_async_client = httpx.AsyncClient

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"model": "local", "choices": [{"message": {"content": "ok"}}]})

        transport = httpx.MockTransport(handler)

        def counting_client(**kwargs):
            nonlocal created_clients
            created_clients += 1
            return original_async_client(transport=transport, **kwargs)

        cfg = SwarmConfig(
            p_cores=4,
            s_threads=1,
            backend=InferenceBackend.LOCAL_VLLM,
            mcts_delay_s=0.0,
            retry_base_delay_s=0.2,
            circuit_breaker_threshold=2,
            circuit_breaker_cooldown_s=0.05,
        )
        orch = SwarmOrchestrator(cfg)

        orig = httpx.AsyncClient
        try:
            httpx.AsyncClient = counting_client  # type: ignore[misc]
            out = asyncio.run(orch.execute_dag([f"task-{i}" for i in range(10)]))
        finally:
            httpx.AsyncClient = orig  # type: ignore[misc]

        self.assertEqual(out["total_tasks"], 10)
        # S1: All 10 tasks shared a single pooled AsyncClient
        self.assertEqual(created_clients, 1)

        # S2: Jitter stays within [0.5*base, 1.0*base] and CB half-open releases after cooldown
        client = RobustLLMClient(cfg)
        delay = client._backoff_delay(1)
        self.assertGreaterEqual(delay, 0.1)
        self.assertLessEqual(delay, 0.2)

        client._record_failure()
        client._record_failure()
        self.assertTrue(client.is_circuit_breaker_tripped)
        time.sleep(0.06)
        self.assertFalse(client.is_circuit_breaker_tripped)

    def test_kda_lfu_o1_eviction_k1(self) -> None:
        async def _run() -> None:
            mem = KdaSwarmMemory(capacity=2)
            await mem.put("k1", b"v1")
            await mem.put("k2", b"v2")
            # Bump k1 frequency so k2 is the LFU victim
            self.assertEqual(await mem.get("k1"), b"v1")
            await mem.put("k3", b"v3")
            self.assertEqual(await mem.get("k1"), b"v1")
            self.assertIsNone(await mem.get("k2"))
            self.assertEqual(await mem.get("k3"), b"v3")
            # Bump k3 above k1? No, k1 has freq=3, k3 has freq=2 -> k3 evicted next
            await mem.put("k4", b"v4")
            self.assertIsNone(await mem.get("k3"))
            self.assertEqual(await mem.get("k4"), b"v4")

        asyncio.run(_run())

    def test_kernel_telemetry_rate_based_thrashing_s4(self) -> None:
        from agents_archi.orchestrator.swarm import KernelTelemetry

        # Long campaign: 3000 cs over 100s = 30 cs/s -> NOT thrashing
        long_ok = KernelTelemetry(wall_time_s=100.0, involuntary_cs=3000)
        self.assertFalse(long_ok.is_thrashing())
        self.assertAlmostEqual(long_ok.involuntary_cs_per_sec, 30.0)

        # Short burst: 1000 cs in 0.5s = 2000 cs/s > 1500 cs/s -> thrashing
        burst = KernelTelemetry(wall_time_s=0.5, involuntary_cs=1000)
        self.assertTrue(burst.is_thrashing())
        self.assertIn("involuntary_cs_per_sec", burst.to_dict())

    def test_blackboard_digest_system_note_constant_bound_b5(self) -> None:
        from agents_archi.orchestrator.blackboard import BlackboardDigest

        digest = BlackboardDigest(
            task_id="t-big",
            compacted_at_tick=42,
            verified_claims=tuple(f"verified-claim-{i}-" + ("a" * 80) for i in range(50)),
            falsified_claims=tuple(f"falsified-claim-{i}-" + ("b" * 80) for i in range(50)),
            compacted_tuple_ids=tuple(f"id-{i}" for i in range(100)),
            executive_summary="deterministic_compaction: 50 verified, 50 falsified",
        )
        note = digest.to_system_note(max_claims_per_bucket=4, max_chars=512)
        self.assertEqual(note["role"], "system")
        self.assertLessEqual(len(note["content"]), 512)
        self.assertTrue(note["content"].endswith("..."))


if __name__ == "__main__":
    unittest.main()
