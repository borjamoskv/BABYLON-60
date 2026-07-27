# MOSKV-85 STRESS TEST SUITE
# Author: Borja Moskv (borjamoskv)
# Reality Level: C5-REAL
# Version: 1.0.0

import unittest
import threading
import time
import os
import sqlite3
from moskv85 import Moskv85Interpreter

class StressTestMoskv85(unittest.TestCase):
    def setUp(self):
        self.db_path = "stress_consensus.db"
        # Make sure no stale DB exists
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
    def tearDown(self):
        # Cleanup database and journals
        for ext in ["", "-wal", "-shm"]:
            path = self.db_path + ext
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

    def test_ast_depth_stress(self):
        """Stress tests the recursive AST compiler depth with massive nested blocks."""
        depth = 500
        # Build nested brackets: [[[[... 1 ...]]]]
        code = "[" * depth + "1" + "]" * depth
        interpreter = Moskv85Interpreter(db_path=self.db_path)
        interpreter.execute_block(code)
        
        # The stack should contain a single deeply nested list structure
        stack_val = interpreter.pop()
        self.isinstance_nested(stack_val, depth - 1)

    def isinstance_nested(self, val, remaining_depth):
        if remaining_depth <= 0:
            self.assertEqual(val, [1])
            return
        self.assertEqual(len(val), 1)
        self.isinstance_nested(val[0], remaining_depth - 1)

    def test_concurrency_stress(self):
        """Stress tests channel message-passing with concurrent producers and one consumer."""
        interpreter = Moskv85Interpreter(db_path=self.db_path)
        
        # 1. Create channel -> ID 0
        interpreter.execute_block("F") 
        
        # 2. Launch 20 concurrent threads. Each sends 50 messages (value 7) to channel 0.
        # Opcode structure inside thread: [ 7 0 O ] Y
        # Since '1' and '0' is just parsed, let's use 7 for simplicity
        producers_count = 20
        msg_per_producer = 50
        
        # Thread body in MOSKV-85: pushes 7, pushes 0 (chan_id), sends via O.
        # Run it msg_per_producer times.
        # We can construct a loop or just repeat the instructions.
        thread_code = "7 0 O " * msg_per_producer
        
        # Spawn producers
        for _ in range(producers_count):
            interpreter.execute_block(f"[{thread_code}] Y")
            
        # 3. Main thread receives all messages: 0 T. Sums them.
        # Sum logic: 0 T, then loop (producers_count * msg_per_producer - 1) times adding them.
        total_messages = producers_count * msg_per_producer
        
        # Let's read and accumulate in the stack
        accumulate_code = "0 T " * total_messages + "+ " * (total_messages - 1)
        interpreter.execute_block(accumulate_code)
        
        # Total sum should be 7 * total_messages = 7000
        self.assertEqual(interpreter.pop(), 7 * total_messages)

    def test_bft_file_write_stress(self):
        """Stress tests concurrent SQLite WAL writes using the BFT consensus mechanism."""
        interpreter = Moskv85Interpreter(db_path=self.db_path)
        
        # Spawn 15 concurrent threads, each trying to write to its own file.
        # This stresses the database lock, busy timeout (5000ms) and WAL.
        threads_count = 15
        filepaths = [f"/tmp/bft_stress_{i}.txt" for i in range(threads_count)]
        
        # Cleanup filepaths first
        for fp in filepaths:
            if os.path.exists(fp):
                os.remove(fp)

        # Thread code: pushes filepath string, pushes payload string, calls W
        # e.g. "\/tmp/bft_stress_0.txt\"\ \"data\"\ W"
        for i in range(threads_count):
            thread_code = f"\\{filepaths[i]}\\ \\stress_payload_{i}\\ W"
            interpreter.execute_block(f"[{thread_code}] Y")
            
        # Give validator threads time to resolve Quorum consensus
        time.sleep(2.5)
        
        # Assert all files written correctly and consensus registered committed = 1
        for i in range(threads_count):
            fp = filepaths[i]
            self.assertTrue(os.path.exists(fp), f"File {fp} was not written")
            with open(fp, "r") as f:
                self.assertEqual(f.read(), f"stress_payload_{i}")
            os.remove(fp)

        # Connect to DB and check WAL and commits
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM proposals WHERE committed = 1;")
        committed_count = c.fetchone()[0]
        conn.close()
        
        self.assertEqual(committed_count, threads_count)

if __name__ == "__main__":
    unittest.main()
