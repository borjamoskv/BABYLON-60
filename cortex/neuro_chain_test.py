import unittest
from cortex.neuro_chain import dispatch_neuro_chain, CognitiveChainVector


class TestNeuroChain(unittest.TestCase):
    def test_1000_neuro_primitives(self) -> None:
        vec = CognitiveChainVector()
        tested = 0
        for d in range(10):
            for p in range(10):
                for m in range(10):
                    code, name, entropy = dispatch_neuro_chain(d, p, m, vec)
                    self.assertEqual(code, d * 100 + p * 10 + m)
                    self.assertTrue(name.startswith("NEURO-"))
                    tested += 1
        self.assertEqual(tested, 1000)
        self.assertEqual(vec.execution_count, 1000)
        print(
            f"✅ Python Neuro Chain: 1000/1000 primitives verified. Final Language Entropy: {vec.language_entropy:.6f}"
        )


if __name__ == "__main__":
    unittest.main()
