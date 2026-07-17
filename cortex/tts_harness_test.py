import unittest
from cortex.tts_harness import dispatch_tts_harness, TTSHarnessState, DOMAINS, PRIMITIVES, MODIFIERS

class TestTTSHarness(unittest.TestCase):
    def test_1000_tts_primitives(self):
        state = TTSHarnessState()
        tested = 0
        for d in range(10):
            for p in range(10):
                for m in range(10):
                    code, name, score = dispatch_tts_harness(d, p, m, state)
                    self.assertEqual(code, d * 100 + p * 10 + m)
                    self.assertTrue(name.startswith("TTS-"))
                    tested += 1
        self.assertEqual(tested, 1000)
        self.assertEqual(state.execution_count, 1000)
        print(f"✅ Python TTS & Harness: 1000/1000 primitives verified. Final Harness Score: {state.harness_score:.6f}")

if __name__ == "__main__":
    unittest.main()
