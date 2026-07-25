# C5-REAL EXERGY CERTIFIED
import unittest
from cortex.kimi import (
    KimiK3TrajectoryEvaluator,
    KimiStateVector,
    dispatch_kimi,
)


class TestKimiKernel(unittest.TestCase):
    def test_kimi_coverage(self) -> None:
        vec = KimiStateVector()
        count = 0
        for d in range(10):
            for p in range(10):
                for m in range(10):
                    code, name, val = dispatch_kimi(d, p, m, vec)
                    self.assertEqual(code, d * 100 + p * 10 + m)
                    count += 1
        self.assertEqual(count, 1000)

    def test_kimi_k3_trajectory_evaluator(self) -> None:
        evaluator = KimiK3TrajectoryEvaluator()
        result = evaluator.evaluate_trajectory("def test_func(): return 42")
        self.assertTrue(result.trajectory_id.startswith("K3-TRAJ-"))
        self.assertEqual(len(result.code_hash), 64)
        self.assertTrue(result.reward >= 0.0)
        self.assertTrue(result.shannon_entropy > 0.0)
        self.assertTrue(result.cortex_taint.startswith("CORTEX-TAINT:kimik3:"))

    def test_kimi_k3_empty_payload_raises(self) -> None:
        evaluator = KimiK3TrajectoryEvaluator()
        with self.assertRaises(ValueError):
            evaluator.evaluate_trajectory("")


if __name__ == "__main__":
    unittest.main()

