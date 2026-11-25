import os
import unittest
import tempfile
from unittest.mock import patch

# Fix path to import correctly
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents_archi.orchestrator.lifecycle import DynamicLifecycleManager, SubagentState

class TestLifecycleResilience(unittest.TestCase):
    def setUp(self):
        wal_dir = tempfile.TemporaryDirectory(prefix="babylon-test-wal-")
        self.addCleanup(wal_dir.cleanup)
        self.test_wal_dir = wal_dir.name
        self.test_wal_path = os.path.join(self.test_wal_dir, "lifecycle.wal")
        wal_path = patch.object(DynamicLifecycleManager, "WAL_PATH", self.test_wal_path)
        wal_path.start()
        self.addCleanup(wal_path.stop)

    def test_causal_resurrection(self):
        # 1. Create a manager and spawn some agents
        manager1 = DynamicLifecycleManager()
        agent1 = manager1.spawn("agent-1", role="writer")
        agent2 = manager1.spawn("agent-2", role="critic")
        
        agent1.transition_to(SubagentState.EXECUTING, reason="starting task")
        agent2.transition_to(SubagentState.PLANNING, reason="planning")
        
        # Verify WAL exists and has 4 lines (2 spawns + 2 transitions)
        with open(self.test_wal_path, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 4)
            
        # 2. Simulate Crash by creating a new manager instance (which reads the WAL)
        manager2 = DynamicLifecycleManager()
        
        # Verify resurrected agents
        self.assertIn("agent-1", manager2._agents)
        self.assertIn("agent-2", manager2._agents)
        
        res_agent1 = manager2.get("agent-1")
        res_agent2 = manager2.get("agent-2")
        
        self.assertEqual(res_agent1.current_state, SubagentState.EXECUTING)
        self.assertEqual(res_agent2.current_state, SubagentState.PLANNING)

    def test_thermodynamic_throttle(self):
        manager = DynamicLifecycleManager()
        deadlocked = manager.scan_deadlocks()
        self.assertEqual(deadlocked, [])
        manager.close()

    def test_fsm_transition_budget_and_bounded_history_h3(self):
        manager = DynamicLifecycleManager(default_max_transitions=4, default_max_history=3)
        self.addCleanup(manager.close)
        agent = manager.spawn("loop-agent", role="worker")
        agent.transition_to(SubagentState.PLANNING, "p1")
        agent.transition_to(SubagentState.EXECUTING, "e1")
        agent.transition_to(SubagentState.VERIFYING, "v1")
        agent.transition_to(SubagentState.PLANNING, "p2")
        # 5th transition exceeds budget (4) -> fail-stop POISONED
        with self.assertRaises(RuntimeError):
            agent.transition_to(SubagentState.EXECUTING, "e2")
        self.assertEqual(agent.current_state, SubagentState.POISONED)
        self.assertLessEqual(len(agent.history), 3)

    def test_watchdog_detects_waiting_for_input_h4(self):
        manager = DynamicLifecycleManager(default_timeout_s=0.05)
        self.addCleanup(manager.close)
        agent = manager.spawn("waiter-1", role="worker")
        agent.transition_to(SubagentState.PLANNING, "start")
        agent.transition_to(SubagentState.WAITING_FOR_INPUT, "blocked on child")
        deadlocked = manager.scan_deadlocks(now=agent.state_entered_at + 0.1)
        self.assertIn("waiter-1", deadlocked)
        self.assertEqual(agent.current_state, SubagentState.DEADLOCKED)

    def test_throttle_actuator_and_drop_telemetry_h5_h6(self):
        manager = DynamicLifecycleManager(enforce_throttle=True)
        self.addCleanup(manager.close)
        for i in range(DynamicLifecycleManager.KUDURRU_QUEUE_DEPTH + 10):
            manager.submit_proposal({"id": i})
        stats = manager.telemetry()
        self.assertEqual(stats["proposals_accepted"], DynamicLifecycleManager.KUDURRU_QUEUE_DEPTH)
        self.assertEqual(stats["proposals_dropped"], 10)
        self.assertGreater(stats["drop_rate"], 0.0)

        # Activate throttle actuator -> blocks spawn and proposals
        manager.throttled = True
        self.assertFalse(manager.submit_proposal({"id": "throttled"}))
        with self.assertRaises(RuntimeError):
            manager.spawn("blocked-agent", role="worker")
        self.assertEqual(manager.throttled_rejections, 2)

    def test_edin_effective_concurrency_and_sync_offload_h2(self):
        import asyncio
        import time
        from agents_archi.topologies.edin import EdinTopology

        def slow_sync(item: str) -> bool:
            time.sleep(0.02)
            return True

        topo = EdinTopology(worker_count=10, max_batch_concurrency=16)
        self.assertEqual(topo.effective_concurrency, 10)
        t0 = time.perf_counter()
        res = asyncio.run(topo.execute_parallel_verification([f"t-{i}" for i in range(20)], slow_sync, timeout_s=0.5))
        elapsed = time.perf_counter() - t0
        self.assertEqual(res["passed"], 20)
        self.assertEqual(res["effective_concurrency"], 10)
        # 20 items x 20ms with 10 concurrent threads should finish well under sequential 400ms
        self.assertLess(elapsed, 0.25)

if __name__ == '__main__':
    unittest.main()
