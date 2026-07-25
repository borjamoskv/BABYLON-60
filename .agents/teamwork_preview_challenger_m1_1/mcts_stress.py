# C5-REAL EXERGY CERTIFIED
# MCTS VNODE COMPILER STRESS HARNESS
import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cortex.mcts_vnode_compiler import (
    EphemeralVNodePhysical,
    L3InferenceEnginePhysical,
    MCTSTreeSearchError,
    calculate_shannon_entropy,
)

class TestMCTSStress(unittest.TestCase):

    def test_mcts_entropy_edge_cases(self):
        # Empty bytes
        self.assertEqual(calculate_shannon_entropy(b""), 0.0)

        # Single character repeated (zero entropy)
        self.assertEqual(calculate_shannon_entropy(b"AAAAAAA"), 0.0)

        # All 256 byte values equally distributed (max entropy ~8.0)
        max_bytes = bytes(range(256)) * 10
        self.assertAlmostEqual(calculate_shannon_entropy(max_bytes), 8.0, places=2)

    def test_mcts_tree_search_budget_exhaustion(self):
        # Engine with small target budget where no node passes threshold
        # If we pass intention that generates AST with low entropy or node count
        engine = L3InferenceEnginePhysical(target_trajectories=2)
        # Should either compile theorem or raise MCTSTreeSearchError
        try:
            theorem = engine.compile_theorem("LOW_BUDGET_INTENTION")
            self.assertTrue(theorem.proven)
        except MCTSTreeSearchError as e:
            self.assertIn("Imposible colapsar un teorema válido", str(e))

    def test_ephemeral_vnode_invalid_payloads(self):
        vnode = EphemeralVNodePhysical("test-vnode")

        # Empty payload
        is_valid, entropy, node_count = vnode.execute_physical_test("")
        self.assertFalse(is_valid)
        self.assertEqual(entropy, 0.0)

        # Syntax error payload
        is_valid, entropy, node_count = vnode.execute_physical_test("def broken_syntax(")
        self.assertFalse(is_valid)
        self.assertEqual(node_count, 0)

        # Valid payload but low entropy/node count
        is_valid, entropy, node_count = vnode.execute_physical_test("x = 1")
        self.assertFalse(is_valid)

if __name__ == "__main__":
    unittest.main()
