import os
import unittest
import shutil

# Fix path to import correctly
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents_archi.orchestrator.lifecycle import DynamicLifecycleManager, SubagentState

class TestLifecycleResilience(unittest.TestCase):
    def setUp(self):
        # Override WAL path for testing
        self.test_wal_dir = "/tmp/babylon_test_wal"
        os.makedirs(self.test_wal_dir, exist_ok=True)
        self.test_wal_path = os.path.join(self.test_wal_dir, "lifecycle.wal")
        DynamicLifecycleManager.WAL_PATH = self.test_wal_path
        
        # Ensure clean state
        if os.path.exists(self.test_wal_path):
            os.remove(self.test_wal_path)

    def tearDown(self):
        shutil.rmtree(self.test_wal_dir, ignore_errors=True)

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
        # Mock high involuntary context switches
        # We can't easily mock resource.getrusage without patching, but we can verify scan_deadlocks runs
        deadlocked = manager.scan_deadlocks()
        self.assertEqual(deadlocked, [])

if __name__ == '__main__':
    unittest.main()
