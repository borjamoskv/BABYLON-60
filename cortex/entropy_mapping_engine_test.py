# C5-REAL EXERGY CERTIFIED
"""
Unit and Property-Based Tests for cortex/entropy_mapping_engine.py (ULTRATHINK Ω31)
"""

import math
import unittest
from hypothesis import given, strategies as st, settings

from cortex.entropy_mapping_engine import (
    ThermodynamicEntropyEngine,
    ThermodynamicState,
)

class TestThermodynamicEntropyEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ThermodynamicEntropyEngine()

    def test_shannon_entropy_empty(self) -> None:
        self.assertEqual(self.engine.compute_shannon_entropy([]), 0.0)
        self.assertEqual(self.engine.compute_shannon_entropy([0.0, 0.0]), 0.0)

    def test_shannon_entropy_uniform(self) -> None:
        # Uniform distribution over 4 outcomes -> S = ln(4) = 2 * ln(2)
        probs = [0.25, 0.25, 0.25, 0.25]
        s = self.engine.compute_shannon_entropy(probs)
        self.assertAlmostEqual(s, math.log(4.0), places=6)

    def test_shannon_entropy_deterministic(self) -> None:
        # Deterministic outcome [1.0, 0.0, 0.0] -> S = 0.0
        probs = [1.0, 0.0, 0.0]
        s = self.engine.compute_shannon_entropy(probs)
        self.assertEqual(s, 0.0)

    def test_kl_divergence_identical(self) -> None:
        p = [0.5, 0.5]
        q = [0.5, 0.5]
        d_kl = self.engine.compute_kl_divergence(p, q)
        self.assertAlmostEqual(d_kl, 0.0, places=6)

    def test_kl_divergence_positive(self) -> None:
        p = [0.8, 0.2]
        q = [0.5, 0.5]
        d_kl = self.engine.compute_kl_divergence(p, q)
        self.assertGreater(d_kl, 0.0)

    def test_kl_divergence_invalid(self) -> None:
        p = [0.5, 0.5]
        q = [0.0, 1.0]
        # P > 0 where Q = 0 -> D_KL = infinity
        self.assertEqual(self.engine.compute_kl_divergence(p, q), float("inf"))

        with self.assertRaises(ValueError):
            self.engine.compute_kl_divergence([0.5], [0.5, 0.5])

        with self.assertRaises(ValueError):
            self.engine.compute_kl_divergence([], [])

        with self.assertRaises(ValueError):
            self.engine.compute_kl_divergence([0.0, 0.0], [0.0, 0.0])

    def test_map_domain_entropy(self) -> None:
        counts = {"D0": 112, "D1": 112, "D2": 112, "D3": 112}
        state = self.engine.map_domain_entropy(counts)
        self.assertIsInstance(state, ThermodynamicState)
        self.assertEqual(state.total_samples, 448)
        self.assertGreater(state.shannon_entropy, 0.0)
        self.assertGreater(state.landauer_energy_joules, 0.0)
        self.assertTrue(state.cortex_taint.startswith("CORTEX-TAINT"))

    def test_map_domain_entropy_empty_counts(self) -> None:
        state = self.engine.map_domain_entropy({})
        self.assertEqual(state.total_samples, 8)
        self.assertGreater(state.shannon_entropy, 0.0)

    @settings(deadline=None)
    @given(st.lists(st.floats(min_value=0.01, max_value=100.0), min_size=1, max_size=20))
    def test_property_shannon_entropy_non_negative(self, probs: list[float]) -> None:
        s = self.engine.compute_shannon_entropy(probs)
        self.assertGreaterEqual(s, 0.0)
        # S <= ln(N)
        max_s = math.log(len(probs))
        self.assertLessEqual(s, max_s + 1e-9)

if __name__ == "__main__":
    unittest.main()
