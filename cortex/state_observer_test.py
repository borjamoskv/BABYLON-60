import unittest
from cortex.state_observer import dispatch_state_observer, StateVector

class TestStateObserver(unittest.TestCase):
    def test_1000_primitives(self) -> None:
        state = StateVector()
        tested = 0
        for d in range(10):
            for p in range(10):
                for m in range(10):
                    code, name, norm_err = dispatch_state_observer(d, p, m, state)
                    self.assertEqual(code, d * 100 + p * 10 + m)
                    self.assertTrue(name.startswith("OBS-"))
                    tested += 1
        self.assertEqual(tested, 1000)
        self.assertEqual(state.execution_count, 1000)
        print(f"✅ Python State Observer: 1000/1000 primitives verified. Final Norm Error: {state.norm_error:.6f}")

if __name__ == "__main__":
    unittest.main()
