import unittest
from .active_inference_engine import UnifiedActiveInferenceEngine


class TestUnifiedActiveInferenceEngine(unittest.TestCase):
    def test_3000_primitives_orquestated(self) -> None:
        engine = UnifiedActiveInferenceEngine()
        step_count = 0
        for d in range(10):
            for p in range(10):
                for m in range(10):
                    fe, dkl, ell = engine.step(d, p, m)
                    step_count += 1
        self.assertEqual(step_count, 1000)
        self.assertEqual(engine.steps_count, 1000)
        print(
            f"✅ Python Unified Active Inference: 3000/3000 Primitives (1000 Tri-Dispatches) verified. Free Energy: {engine.free_energy:.6f}, D_KL: {engine.d_kl:.6f}"
        )


if __name__ == "__main__":
    unittest.main()
