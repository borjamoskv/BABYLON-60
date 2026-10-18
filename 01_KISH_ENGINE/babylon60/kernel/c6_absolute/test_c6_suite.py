#!/usr/bin/env python3
"""
C6-ABSOLUTE COMPLETE TEST SUITE
Automated deterministic verification of all 5 C6 layers:
1. ExergyLinter (AST calculations, guard tracking, anergy penalty)
2. CTREngine (CVaR calculation, threshold gating, thermodynamic aborts)
3. AntiNLPRouter (PoE verification, masking detection, Layer 7 drop)
4. MetabolicDeadManSwitch (Jitter evaluation, Ring -3 electromechanical cutoff)
5. EIP7702Hunter (Mempool entropy sampling, on-chain thermodynamic gating)
"""

import unittest
from .exergy_linter import analyze_source
from .ctre_engine import CommitTimeReconciliationEngine
from .anti_nlp_router import C5DarkSwarmRouter, create_poe_packet, EntropicSludgeException
from .metabolic_dead_man_switch import WetwareThermostat
from .eip7702_hunter import NegentropicHunter


class TestExergyLinter(unittest.TestCase):
    def test_pure_exergic_code(self) -> None:
        code = (
            "def safe_div(a: float, b: float) -> float:\n"
            "    assert b != 0.0, 'ZeroDivision'\n"
            "    res: float = a / b\n"
            "    return res\n"
        )
        res = analyze_source(code, "safe_div.py")
        assert res is not None
        self.assertGreaterEqual(res["exergy_score"], 0.9)
        self.assertEqual(res["status"], "EXERGIC")

    def test_anergic_code_penalties(self) -> None:
        code = "# TODO: Fix this later\n# Just testing\ndef dummy():\n    print ('hello')\n    pass\n"
        res = analyze_source(code, "dummy.py")
        assert res is not None
        self.assertLess(res["exergy_score"], 0.4)
        self.assertEqual(res["status"], "ANERGIC")


class TestCTREngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = CommitTimeReconciliationEngine(alpha=0.05, variance_threshold=0.02)

    def test_commit_on_low_drift(self) -> None:
        drift = [0.005, 0.006, 0.004, 0.007, 0.005]
        action, risk = self.engine.enforce_thermodynamic_brake(drift)
        self.assertEqual(action, "ACTION_COMMIT")
        self.assertLessEqual(risk, 0.02)

    def test_abort_on_tail_shock(self) -> None:
        drift = [0.005] * 95 + [0.08, 0.09, 0.12, 0.15, 0.20]
        action, risk = self.engine.enforce_thermodynamic_brake(drift)
        self.assertEqual(action, "ACTION_ABORT")
        self.assertGreater(risk, 0.02)


class TestAntiNLPRouter(unittest.TestCase):
    def setUp(self) -> None:
        self.router = C5DarkSwarmRouter(strict_hash_verification=True)

    def test_valid_poe_packet(self) -> None:
        packet = create_poe_packet({"counter": 100, "state": "ACTIVE"})
        result = self.router.route_state_delta(packet)
        self.assertTrue(result)

    def test_reject_masking(self) -> None:
        packet = create_poe_packet({"counter": 100}, metadata="As an AI, I suggest...")
        with self.assertRaises(EntropicSludgeException):
            self.router.route_state_delta(packet)

    def test_reject_tampered_hash(self) -> None:
        packet = create_poe_packet({"counter": 100})
        packet["zk_proof_hash"] = "deadbeef" * 8
        with self.assertRaises(EntropicSludgeException):
            self.router.route_state_delta(packet)


class TestWetwareThermostat(unittest.TestCase):
    def test_steady_typing_no_halt(self) -> None:
        thermostat = WetwareThermostat(variance_threshold_ms=100.0)
        # Feed 30 steady keystroke intervals (180ms +/- 5ms)
        for _ in range(30):
            thermostat.register_biometric_event(delta_ms=180.0)
        self.assertFalse(thermostat.is_halted)
        self.assertEqual(thermostat.SSR_RELAY.value(), 1)

    def test_fatigued_typing_triggers_hard_halt(self) -> None:
        thermostat = WetwareThermostat(variance_threshold_ms=50.0)
        # Feed highly erratic intervals to spike variance
        erratic_intervals = [80.0, 450.0, 90.0, 600.0, 70.0, 520.0] * 5
        for interval in erratic_intervals:
            thermostat.register_biometric_event(delta_ms=interval)
        self.assertTrue(thermostat.is_halted)
        self.assertEqual(thermostat.SSR_RELAY.value(), 0)  # Power cutoff verified


class TestEIP7702Hunter(unittest.TestCase):
    def test_hunter_commit_and_abort(self) -> None:
        import random

        random.seed(42)
        ctre = CommitTimeReconciliationEngine(alpha=0.05, variance_threshold=0.030)
        hunter = NegentropicHunter(ctre=ctre)

        res_clean = hunter.scan_and_reconcile(inject_mempool_shock=False)
        self.assertIn("COMMIT", res_clean)

        res_shock = hunter.scan_and_reconcile(inject_mempool_shock=True)
        self.assertIn("ABORT", res_shock)


if __name__ == "__main__":
    unittest.main(verbosity=2)
