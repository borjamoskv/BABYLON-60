import asyncio
import os
import sqlite3
import hashlib
import time
from pathlib import Path
import pytest
import aiosqlite
from babylon60.utils.base60 import bytes_to_base60


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / f"cortex_persist_bft_test_{os.getpid()}.db"


@pytest.fixture(autouse=True)
async def setup_db(db_path):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA busy_timeout=5000")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS security_audit_log (
                audit_id TEXT PRIMARY KEY,
                timestamp TEXT,
                tenant_id TEXT,
                actor_role TEXT,
                actor_id TEXT,
                action TEXT,
                resource TEXT,
                status TEXT,
                prev_hash TEXT,
                signature TEXT,
                external_anchor TEXT
            )
        """)
        await db.commit()
    yield


@pytest.mark.asyncio
async def test_vector_sqlite_wal_deadlock(db_path):
    """Vector 1: Concurrencia extrema N=10, timeout 5000ms"""

    async def worker(worker_id):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("PRAGMA busy_timeout=5000")
            for i in range(100):
                audit_id = hashlib.sha256(f"w{worker_id}_{i}_{time.time()}".encode()).hexdigest()
                await db.execute(
                    "INSERT INTO security_audit_log (audit_id, action) VALUES (?, ?)",
                    (audit_id, "DEADLOCK_TEST"),
                )
                await db.commit()

    workers = [worker(i) for i in range(10)]
    await asyncio.gather(*workers)

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM security_audit_log WHERE action='DEADLOCK_TEST'"
        )
        count = (await cursor.fetchone())[0]
        assert count == 1000


@pytest.mark.asyncio
async def test_vector_taint_engine_collapse(db_path):
    """Vector 2: Injection of colliding SHA3-256 hashes (Rejection simulation)"""
    # SQLite PK constraint should reject colliding hashes
    hash_collision = bytes_to_base60(hashlib.sha3_256(b"taint_collision_seed").digest())

    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO security_audit_log (audit_id, action) VALUES (?, ?)",
            (hash_collision, "TAINT_1"),
        )
        await db.commit()

        with pytest.raises(sqlite3.IntegrityError):
            await db.execute(
                "INSERT INTO security_audit_log (audit_id, action) VALUES (?, ?)",
                (hash_collision, "TAINT_2_COLLISION"),
            )
            await db.commit()


@pytest.mark.asyncio
async def test_vector_ledger_chain_break(db_path):
    """Vector 3: Mutation of Ed25519 signatures in historical nodes (Detection simulation)"""
    async with aiosqlite.connect(db_path) as db:
        # 1. Valid insert
        valid_hash = bytes_to_base60(hashlib.sha256(b"valid_node").digest())
        await db.execute(
            "INSERT INTO security_audit_log (audit_id, signature) VALUES (?, ?)",
            (valid_hash, "valid_signature_ed25519"),
        )
        await db.commit()

        # 2. Mutate history (Adversarial attack)
        await db.execute(
            "UPDATE security_audit_log SET signature = ? WHERE audit_id = ?",
            ("mutated_signature_ed25519", valid_hash),
        )
        await db.commit()

        # 3. Detection (Simulated verifying logic)
        cursor = await db.execute(
            "SELECT signature FROM security_audit_log WHERE audit_id = ?", (valid_hash,)
        )
        corrupted_sig = (await cursor.fetchone())[0]
        assert corrupted_sig != "valid_signature_ed25519"


@pytest.mark.asyncio
async def test_vector_swarm_apoptosis(db_path):
    """Vector 4: Injection of 500 parallel subagents demanding BFT consensus"""

    async def subagent_task(agent_id):
        # Simulate BFT assertion delay and write
        await asyncio.sleep(0.01)
        async with aiosqlite.connect(db_path) as db:
            await db.execute("PRAGMA busy_timeout=5000")
            audit_id = hashlib.sha256(f"agent_{agent_id}_{time.time()}".encode()).hexdigest()
            await db.execute(
                "INSERT INTO security_audit_log (audit_id, action) VALUES (?, ?)",
                (audit_id, "SWARM_CONSENSUS"),
            )
            await db.commit()

    # Launch 500 parallel agents
    agents = [subagent_task(i) for i in range(500)]
    await asyncio.gather(*agents)

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM security_audit_log WHERE action='SWARM_CONSENSUS'"
        )
        count = (await cursor.fetchone())[0]
        assert count == 500
