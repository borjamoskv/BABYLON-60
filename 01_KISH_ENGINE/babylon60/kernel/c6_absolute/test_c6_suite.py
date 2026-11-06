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


class TestSovereignKernelLean(unittest.TestCase):
    def test_lean_neurosymbolic_kernel_modules(self) -> None:
        from pathlib import Path
        import shutil
        import subprocess

        lean_path = Path(__file__).resolve().parent / "SovereignKernel.lean"
        self.assertTrue(lean_path.exists())
        source = lean_path.read_text(encoding="utf-8")

        self.assertIn("set_option warningAsError true", source)
        self.assertNotIn("sorry", source)
        self.assertIn("theorem session_cannot_bypass_z3_attestation", source)
        self.assertIn("theorem kish_trace_valid_accepted", source)
        self.assertIn("theorem kish_trace_corrupt_rejected", source)
        self.assertIn("theorem kish_fsm_universal_soundness", source)
        self.assertIn("theorem anvil_bv256_valid_transfer_certified", source)
        self.assertIn("theorem anvil_bv256_overflow_rejected", source)
        self.assertIn("theorem anvil_bv256_conservation_soundness", source)

        if shutil.which("lean") is not None:
            proc = subprocess.run(
                ["lean", str(lean_path)],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, msg=f"Lean compilation failed:\n{proc.stdout}\n{proc.stderr}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
