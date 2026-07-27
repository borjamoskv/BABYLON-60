import os
import pytest
import sqlite3
from scheduler import CortexScheduler

DB_TEST_PATH = "cortex_test.db"

@pytest.fixture
def scheduler():
    if os.path.exists(DB_TEST_PATH):
        os.remove(DB_TEST_PATH)
    
    s = CortexScheduler(db_path=DB_TEST_PATH)
    yield s
    
    # Cleanup
    if os.path.exists(DB_TEST_PATH):
        os.remove(DB_TEST_PATH)
    if os.path.exists(f"{DB_TEST_PATH}-wal"):
        os.remove(f"{DB_TEST_PATH}-wal")
    if os.path.exists(f"{DB_TEST_PATH}-shm"):
        os.remove(f"{DB_TEST_PATH}-shm")

def test_scheduler_initialization(scheduler):
    with sqlite3.connect(DB_TEST_PATH, timeout=5.0) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]
        assert journal_mode.lower() == "wal", "R10 Violation: DB must be in WAL mode"

def test_scheduler_entropy_routing(scheduler):
    # Inject tasks with different entropies
    scheduler.inject_task("HIGH_ENTROPY_TASK", 0.9)
    scheduler.inject_task("LOW_ENTROPY_TASK", 0.1)
    
    # Tick should collapse the lowest entropy first (T=0.0 Flash preference)
    res = scheduler.tick()
    assert res["status"] == "COLLAPSED"
    assert "LOW_ENTROPY_TASK" in res["action"]
    
    # Tick again should collapse the next one
    res2 = scheduler.tick()
    assert res2["status"] == "COLLAPSED"
    assert "HIGH_ENTROPY_TASK" in res2["action"]
    
    # Third tick should be IDLE
    res3 = scheduler.tick()
    assert res3["status"] == "IDLE"

def test_reality_log_anchoring(scheduler):
    task_id = scheduler.inject_task("LOG_TEST", 0.5)
    scheduler.tick()
    
    with sqlite3.connect(DB_TEST_PATH, timeout=5.0) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM reality_loop_logs WHERE target_id = ?", (task_id,))
        log = cursor.fetchone()
        assert log is not None
        assert "EXECUTED_VIA_SCHEDULER: LOG_TEST" in log["action_taken"]
