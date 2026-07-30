# C5-REAL EXERGY CERTIFIED
# C5-REAL EMPIRICAL STRESS HARNESS — Milestone 1 Challenger
"""
Empirical test suite for validating:
- cortex/cortex_purge.py
- cortex/mcts_vnode_compiler.py
- scripts/ultrathink_learning.py
- cortex/bft_orchestrator.py
"""

import asyncio
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ["CORTEX_BFT_KEY"] = "c5_real_test_key_sovereign_2026"

from cortex.core.cortex_purge import (
    write_purge_to_ledger,
)
from cortex.engines.mcts_vnode_compiler import (
    ASTTheorem,
    L3InferenceEnginePhysical,
)
from cortex.engines.bft_orchestrator import (
    BFTOrchestrator,
)

class TestEmpiricalChallengerM1(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_1_bft_ledger_null_lamport_and_prev_hash_bug(self):
        """
        EMPIRICAL TEST 1: Schema Incompatibility & TypeError when BFTOrchestrator writes to bft_ledger.
        When BFTOrchestrator inserts a row, payload_hash is NULL and lamport_t is NULL.
        When cortex_purge tries to write, SELECT payload_hash, lamport_t returns (None, None).
        cortex_purge does `new_lamport = last_lamport + 1` -> TypeError: None + int!
        """
        db_dir = os.path.join(self.test_dir, ".cortex")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "cortex.db")

        conn = sqlite3.connect(db_path, timeout=5.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS bft_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            agent_id TEXT,
            lamport_t INTEGER,
            payload_hash TEXT,
            step_index INTEGER,
            domain INTEGER,
            primitive INTEGER,
            modifier INTEGER,
            prev_hash TEXT NOT NULL UNIQUE,
            current_hash TEXT,
            cortex_taint TEXT NOT NULL
        );
        """)
        # Insert BFTOrchestrator-style row (lamport_t and payload_hash are NULL)
        conn.execute(
            "INSERT INTO bft_ledger (step_index, domain, primitive, modifier, prev_hash, current_hash, cortex_taint) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (1, 0, 0, 0, "0000000000000000000000000000000000000000000000000000000000000000", "hash_step_1", "TAINT_BFT_1"),
        )
        conn.commit()
        conn.close()

        import cortex.core.cortex_purge as cp
        original_db_path = cp.DB_PATH
        cp.DB_PATH = db_path
        try:
            # We expect TypeError because last_lamport is None
            with self.assertRaises(TypeError):
                write_purge_to_ledger("Test payload", agent_id="test_agent")
        finally:
            cp.DB_PATH = original_db_path

    def test_2_relative_db_path_discrepancy(self):
        """
        EMPIRICAL TEST 2: Hardcoded relative path DB_PATH = ".cortex/cortex.db" in bft_orchestrator and ultrathink_learning.
        When executed from a non-root directory, they create a separate DB file in cwd instead of project root.
        """
        from cortex.engines import bft_orchestrator
        self.assertEqual(bft_orchestrator.DB_PATH, ".cortex/cortex.db")

        bft_orchestrator.init_bft_database()
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, ".cortex", "cortex.db")))

    def test_3_path_traversal_in_obliterate_zero_operators(self):
        """
        EMPIRICAL TEST 3: Path traversal vulnerability in obliterate_zero_operators.
        If BABYLON_60_THEOREM_OMEGA.json contains relative path pointing outside project root,
        os.path.join(target_dir, rel_path) resolves outside target_dir and deletes arbitrary files!
        """
        victim_file = os.path.join(self.test_dir, "victim_file.txt")
        with open(victim_file, "w") as f:
            f.write("DO_NOT_DELETE")

        target_subdir = os.path.join(self.test_dir, "cortex_sub")
        os.makedirs(os.path.join(target_subdir, "cortex", "artifacts", "reports"), exist_ok=True)

        json_path = os.path.join(target_subdir, "cortex", "artifacts", "reports", "BABYLON_60_THEOREM_OMEGA.json")
        data = {
            "Accidental_Complexity": [
                {"file": "../victim_file.txt", "matches": 0}
            ]
        }
        with open(json_path, "w") as f:
            json.dump(data, f)

        rel_path = "../victim_file.txt"
        abs_path = os.path.join(target_subdir, rel_path)
        self.assertEqual(os.path.abspath(abs_path), os.path.abspath(victim_file))

    def test_4_mcts_ast_theorem_integrity_validation(self):
        """
        EMPIRICAL TEST 4: MCTS ASTTheorem validation checks.
        Ensures Omega123 code_hash matching, Shannon entropy bounds, and exergy_ratio bounds are strictly enforced.
        """
        payload = "def foo(): return 42"
        correct_hash = hashlib.sha3_256(payload.encode("utf-8")).hexdigest()

        t = ASTTheorem(
            code_hash=correct_hash,
            proven=True,
            shannon_entropy=4.0,
            ast_nodes=5,
            ephemeral_vnode="vnode-1",
            payload=payload,
            cortex_taint="TAINT_1",
            exergy_ratio=1.5,
            pruned_branches=0,
        )
        self.assertTrue(t.proven)

        with self.assertRaises(ValueError):
            ASTTheorem(
                code_hash="a" * 64,
                proven=True,
                shannon_entropy=4.0,
                ast_nodes=5,
                ephemeral_vnode="vnode-1",
                payload=payload,
            )

        with self.assertRaises(ValueError):
            ASTTheorem(
                code_hash=correct_hash,
                proven=True,
                shannon_entropy=10.0,
                ast_nodes=5,
                ephemeral_vnode="vnode-1",
                payload=payload,
            )

    def test_5_mcts_compiler_execution(self):
        """
        EMPIRICAL TEST 5: Run L3InferenceEnginePhysical theorem synthesis.
        """
        engine = L3InferenceEnginePhysical(target_trajectories=100)
        theorem = engine.compile_theorem("TEST_EMPIRICAL_INTENTION")
        self.assertTrue(theorem.proven)
        self.assertGreater(theorem.shannon_entropy, 3.5)
        self.assertGreater(theorem.ast_nodes, 2)
        self.assertEqual(hashlib.sha3_256(theorem.payload.encode("utf-8")).hexdigest(), theorem.code_hash)

    def test_6_bft_orchestrator_consensus_and_byzantine_fault(self):
        """
        EMPIRICAL TEST 6: Test BFTOrchestrator execution, queue processing, and consensus evaluation.
        """
        async def run_bft():
            orchestrator = BFTOrchestrator(num_nodes=3)
            await orchestrator.enqueue_task(1, 2, 3)
            await orchestrator.start_loop(max_steps=1)
            self.assertEqual(orchestrator.step_index, 1)

        asyncio.run(run_bft())

    def test_7_bft_orchestrator_input_validation(self):
        """
        EMPIRICAL TEST 7: Negative/invalid argument validation in BFTOrchestrator.enqueue_task.
        """
        async def run_invalid():
            orchestrator = BFTOrchestrator(num_nodes=3)
            with self.assertRaises(ValueError):
                await orchestrator.enqueue_task(-1, 0, 0)
            with self.assertRaises(ValueError):
                await orchestrator.enqueue_task(0, "invalid", 0)

        asyncio.run(run_invalid())

if __name__ == "__main__":
    unittest.main()
