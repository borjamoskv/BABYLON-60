import unittest
import asyncio
import os
import sqlite3
from cortex.bft_orchestrator import BFTOrchestrator, DB_PATH

class TestBFTOrchestrator(unittest.TestCase):
    def setUp(self) -> None:
        # Remove DB before each test for isolation
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except OSError:
                pass
        self.orchestrator = BFTOrchestrator(num_nodes=3)

    def tearDown(self) -> None:
        # Cleanup database
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except OSError:
                pass

    def test_clean_bft_execution(self) -> None:
        """Tests that orchestrator runs successfully and achieves consensus for multiple tasks."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_test():
            # Queue 5 tasks covering different domains, primitives, modifiers
            await self.orchestrator.enqueue_task(0, 0, 0)
            await self.orchestrator.enqueue_task(1, 2, 3)
            await self.orchestrator.enqueue_task(5, 5, 5)
            
            # Start loop to process exactly 3 tasks
            await self.orchestrator.start_loop(max_steps=3)
            
        loop.run_until_complete(run_test())
        loop.close()

        # Check that consensus was achieved and stored in Ledger
        self.assertEqual(self.orchestrator.get_ledger_count(), 3)
        
        # Verify node alignment
        hash0 = self.orchestrator.nodes[0].compute_state_hash()
        hash1 = self.orchestrator.nodes[1].compute_state_hash()
        hash2 = self.orchestrator.nodes[2].compute_state_hash()
        self.assertEqual(hash0, hash1)
        self.assertEqual(hash1, hash2)

    def test_byzantine_fault_recovery(self) -> None:
        """Tests that a single corrupted/divergent node is detected, consensus is reached, and the node is recovered."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            # Run one initial step to get nodes out of default zero state
            await self.orchestrator.enqueue_task(1, 1, 1)
            await self.orchestrator.start_loop(max_steps=1)
            
            # Artificially corrupt Node 2 (introduce Byzantine fault)
            self.orchestrator.nodes[2].state_vector.states = [999.0, 0.0, 0.0, 0.0]
            
            # Ensure hashes have diverged
            hash0 = self.orchestrator.nodes[0].compute_state_hash()
            hash2 = self.orchestrator.nodes[2].compute_state_hash()
            self.assertNotEqual(hash0, hash2)
            
            # Enqueue next task
            await self.orchestrator.enqueue_task(2, 2, 2)
            # Process task
            await self.orchestrator.start_loop(max_steps=1)
            
        loop.run_until_complete(run_test())
        loop.close()

        # Verify that ledger successfully has 2 committed entries
        self.assertEqual(self.orchestrator.get_ledger_count(), 2)

        # Check that Node 2 was automatically synchronized back to the majority state
        hash0 = self.orchestrator.nodes[0].compute_state_hash()
        hash1 = self.orchestrator.nodes[1].compute_state_hash()
        hash2 = self.orchestrator.nodes[2].compute_state_hash()
        self.assertEqual(hash0, hash1)
        self.assertEqual(hash1, hash2)
        self.assertAlmostEqual(self.orchestrator.nodes[2].state_vector.states[0], self.orchestrator.nodes[0].state_vector.states[0])

    def test_ledger_immutability(self) -> None:
        """Verifies that direct UPDATEs and DELETEs on the sqlite Master Ledger are rejected by triggers."""
        # Setup initial database row
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def run_test():
            await self.orchestrator.enqueue_task(0, 0, 0)
            await self.orchestrator.start_loop(max_steps=1)
        loop.run_until_complete(run_test())
        loop.close()

        # Try to modify ledger directly via SQL UPDATE
        conn = sqlite3.connect(DB_PATH)
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            conn.execute("UPDATE bft_ledger SET current_hash = 'corrupted_hash' WHERE id = 1;")
            conn.commit()
        self.assertIn("Ledger updates are forbidden", str(ctx.exception))

        # Try to delete from ledger directly via SQL DELETE
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            conn.execute("DELETE FROM bft_ledger WHERE id = 1;")
            conn.commit()
        self.assertIn("Ledger deletions are forbidden", str(ctx.exception))
        
        conn.close()

if __name__ == "__main__":
    unittest.main()
