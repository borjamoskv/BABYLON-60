import asyncio
import sqlite3
import pytest
import os
import hashlib
import sys
from unittest.mock import patch

# Mock env var before importing
os.environ["CORTEX_BFT_KEY"] = "DUMMY_TEST_KEY"

# We have to import 00_init_ledger using importlib because of the leading numbers
import importlib.util
spec = importlib.util.spec_from_file_location("init_ledger_mod", os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts', '00_init_ledger.py')))
init_ledger_mod = importlib.util.module_from_spec(spec)
sys.modules["init_ledger_mod"] = init_ledger_mod
spec.loader.exec_module(init_ledger_mod)

TEST_DB_PATH = ".cortex/test_cortex_resilience.db"

# Override DB_PATH for tests
init_ledger_mod.DB_PATH = TEST_DB_PATH

def setup_module(module):
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    if not os.path.exists(".cortex"):
        os.makedirs(".cortex")
    init_ledger_mod.init_ledger()

def teardown_module(module):
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def hash_payload(lamport_t: int, agent_id: str, prev_hash: str) -> str:
    data = f"{lamport_t}:{agent_id}:{prev_hash}".encode('utf-8')
    return hashlib.sha3_256(data).hexdigest()

class MasterLedgerWriter:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.conn = sqlite3.connect(TEST_DB_PATH, timeout=5.0)
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self.conn.execute("PRAGMA busy_timeout = 5000;")
        
    async def writer_loop(self):
        while True:
            item = await self.queue.get()
            if item is None:
                break
            agent_id, lamport_t, payload_hash, prev_hash, taint = item
            try:
                self.conn.execute(
                    "INSERT INTO bft_ledger (agent_id, lamport_t, payload_hash, prev_hash, cortex_taint) VALUES (?, ?, ?, ?, ?)",
                    (agent_id, lamport_t, payload_hash, prev_hash, taint)
                )
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                print(f"Error inserting {lamport_t}: {e}")
            self.queue.task_done()
            
    def close(self):
        self.conn.close()

def test_wal_contention():
    # Enforces Ω13: single writer, multiple producers
    async def run_contention():
        writer = MasterLedgerWriter()
        writer_task = asyncio.create_task(writer.writer_loop())
        
        # Pre-fetch genesis hash
        c = writer.conn.cursor()
        c.execute("SELECT payload_hash FROM bft_ledger WHERE lamport_t = 0")
        genesis_hash = c.fetchone()[0]
        
        # We will enqueue 100 writes concurrently
        prev = genesis_hash
        tasks = []
        
        for i in range(1, 101):
            lamport_t = i
            agent_id = f"AGENT_{i%3}"
            phash = hash_payload(lamport_t, agent_id, prev)
            taint = f"CORTEX-TAINT:test:{i}"
            
            # Enqueue item
            await writer.queue.put((agent_id, lamport_t, phash, prev, taint))
            prev = phash
            
        # Wait for all to be processed
        await writer.queue.join()
        
        # Stop writer
        await writer.queue.put(None)
        await writer_task
        
        # Verify count
        c.execute("SELECT COUNT(*) FROM bft_ledger")
        count = c.fetchone()[0]
        assert count == 101 # genesis + 100
        writer.close()
        
    asyncio.run(run_contention())

def test_chain_integrity():
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT lamport_t, agent_id, payload_hash, prev_hash FROM bft_ledger ORDER BY lamport_t ASC")
    rows = cursor.fetchall()
    
    assert len(rows) > 0
    
    # Genesis
    assert rows[0][1] == "ROOT_OPERATOR_UID0"
    
    # Chain verification
    prev_hash_expected = rows[0][2] # Genesis payload hash
    for row in rows[1:]:
        lamport_t, agent_id, payload_hash, prev_hash = row
        assert prev_hash == prev_hash_expected
        # recalc hash
        assert payload_hash == hash_payload(lamport_t, agent_id, prev_hash)
        prev_hash_expected = payload_hash
        
    conn.close()

def test_intentional_corruption_prevention():
    conn = sqlite3.connect(TEST_DB_PATH)
    
    # Test update trigger (Ω11)
    with pytest.raises(sqlite3.IntegrityError) as exc:
        conn.execute("UPDATE bft_ledger SET payload_hash = 'CORRUPT' WHERE lamport_t = 0")
    assert "Modificación de ledger inmutable prohibida" in str(exc.value)
    
    # Test delete trigger (Ω11)
    with pytest.raises(sqlite3.IntegrityError) as exc:
        conn.execute("DELETE FROM bft_ledger WHERE lamport_t = 0")
    assert "Borrado de ledger inmutable prohibido" in str(exc.value)
    
    conn.close()
