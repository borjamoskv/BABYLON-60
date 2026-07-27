import asyncio
import os
import signal
import sqlite3
import sys
import multiprocessing
import pytest
from unittest.mock import patch


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test_atomic_ledger.db"
    yield str(path)
    if path.exists():
        path.unlink()


async def setup_ledger(db_path):
    import aiosqlite
    from babylon60.database.core import connect_async
    from babylon60.audit.ledger import EnterpriseAuditLedger

    conn = await connect_async(db_path)
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS business_data (id INTEGER PRIMARY KEY, value TEXT)"
    )
    await conn.commit()

    ledger = EnterpriseAuditLedger(conn)
    await ledger.ensure_table()
    return conn, ledger


@pytest.mark.asyncio
async def test_property_a_commit_persists_both(db_path):
    """Propiedad A (Happy Path): commit de negocio + log_action -> Ambos persisten."""
    from babylon60.database.core import causal_write

    conn, ledger = await setup_ledger(db_path)

    with causal_write(conn):
        await conn.execute("INSERT INTO business_data (value) VALUES ('secret_operation')")
        await ledger.log_action(
            tenant_id="tenant_1",
            actor_role="admin",
            actor_id="user_123",
            action="CREATE_SECRET",
            resource="secret_operation",
        )
        await conn.commit()

    await ledger.close()
    await conn.close()

    check_conn = sqlite3.connect(db_path)
    assert check_conn.execute("SELECT count(*) FROM business_data").fetchone()[0] == 1
    assert check_conn.execute("SELECT count(*) FROM security_audit_log").fetchone()[0] == 1
    check_conn.close()


@pytest.mark.asyncio
async def test_property_b_exception_intermediate(db_path):
    """Property B: Exception before commit -> None persist."""
    from babylon60.database.core import causal_write

    conn, ledger = await setup_ledger(db_path)

    try:
        with causal_write(conn):
            await conn.execute("INSERT INTO business_data (value) VALUES ('secret_operation')")
            await ledger.log_action(
                tenant_id="tenant_1",
                actor_role="admin",
                actor_id="user_123",
                action="CREATE_SECRET",
                resource="secret_operation",
            )
            raise ValueError("Artificial Exception")
            await conn.commit()
    except ValueError:
        pass

    await ledger.close()
    await conn.close()

    check_conn = sqlite3.connect(db_path)
    assert check_conn.execute("SELECT count(*) FROM business_data").fetchone()[0] == 0
    assert check_conn.execute("SELECT count(*) FROM security_audit_log").fetchone()[0] == 0
    check_conn.close()


@pytest.mark.asyncio
async def test_property_c_rollback(db_path):
    """Property C: Explicit Rollback -> None persist."""
    from babylon60.database.core import causal_write

    conn, ledger = await setup_ledger(db_path)

    with causal_write(conn):
        await conn.execute("INSERT INTO business_data (value) VALUES ('secret_operation')")
        await ledger.log_action(
            tenant_id="tenant_1",
            actor_role="admin",
            actor_id="user_123",
            action="CREATE_SECRET",
            resource="secret_operation",
        )
        await conn.rollback()

    await ledger.close()
    await conn.close()

    check_conn = sqlite3.connect(db_path)
    assert check_conn.execute("SELECT count(*) FROM business_data").fetchone()[0] == 0
    assert check_conn.execute("SELECT count(*) FROM security_audit_log").fetchone()[0] == 0
    check_conn.close()


def _run_crash_target(db_path):
    async def target():
        import aiosqlite
        from babylon60.database.core import connect_async, causal_write
        from babylon60.audit.ledger import EnterpriseAuditLedger

        conn = await connect_async(db_path)
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS business_data (id INTEGER PRIMARY KEY, value TEXT)"
        )
        await conn.commit()

        ledger = EnterpriseAuditLedger(conn)
        await ledger.ensure_table()

        loop = asyncio.get_running_loop()
        # Schedule a SIGKILL right after log_action but before commit
        loop.call_later(0.01, lambda: os.kill(os.getpid(), signal.SIGKILL))

        with causal_write(conn):
            await conn.execute("INSERT INTO business_data (value) VALUES ('secret_operation')")

            try:
                await ledger.log_action(
                    tenant_id="tenant_1",
                    actor_role="admin",
                    actor_id="user_123",
                    action="CREATE_SECRET",
                    resource="secret_operation",
                )
            except Exception:  # noqa: BLE001
                pass

            await asyncio.sleep(0.05)
            await conn.commit()

    asyncio.run(target())


def test_property_d_crash_consistency(db_path):
    """Property D: Unexpected closure (SIGKILL) before commit -> Strict consistency (0 and 0)."""
    p = multiprocessing.Process(target=_run_crash_target, args=(db_path,))
    p.start()
    p.join()

    check_conn = sqlite3.connect(db_path)
    b_count = check_conn.execute("SELECT count(*) FROM business_data").fetchone()[0]
    a_count = check_conn.execute("SELECT count(*) FROM security_audit_log").fetchone()[0]
    check_conn.close()

    # Both must be 0 because the transaction was not closed.
    assert b_count == 0
    assert a_count == 0


def _worker_append(db_path, start, count):
    import asyncio

    async def run():
        import aiosqlite
        from babylon60.database.core import connect_async
        from babylon60.audit.ledger import EnterpriseAuditLedger

        conn = await connect_async(db_path)
        static_key_b64 = os.environ["LEDGER_TEST_STATIC_KEY"]
        with patch(
            "babylon60.crypto.keys.KeyManager.get_private_key_b64", return_value=static_key_b64
        ):
            ledger = EnterpriseAuditLedger(conn)
            await ledger.ensure_table()
            for i in range(start, start + count):
                await ledger.log_action(
                    tenant_id="tenant_1",
                    actor_role="worker",
                    actor_id=f"proc-{os.getpid()}",
                    action="CONCURRENT_ACTION",
                    resource=f"res-{i}",
                    payload_dict={"index": i},
                )
            await ledger.close()
        await conn.close()

    asyncio.run(run())


from concurrent.futures import ProcessPoolExecutor
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


def test_multiprocess_appends(tmp_path):
    """Property E: Multiprocess concurrency must maintain strict linear chain without forks."""
    db_path = tmp_path / "test_multiprocess.db"

    _static_key = ed25519.Ed25519PrivateKey.generate()
    _static_key_bytes = _static_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    os.environ["LEDGER_TEST_STATIC_KEY"] = base64.b64encode(_static_key_bytes).decode("utf-8")

    # Initialize DB schema first
    import asyncio

    async def init_db():
        import aiosqlite
        from babylon60.database.core import connect_async
        from babylon60.audit.ledger import EnterpriseAuditLedger

        conn = await connect_async(str(db_path))
        static_key_b64 = os.environ["LEDGER_TEST_STATIC_KEY"]
        with patch(
            "babylon60.crypto.keys.KeyManager.get_private_key_b64", return_value=static_key_b64
        ):
            ledger = EnterpriseAuditLedger(conn)
            await ledger.ensure_table()
            await ledger.close()
        await conn.close()

    asyncio.run(init_db())

    workers = 4
    appends_per_worker = 50

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(_worker_append, str(db_path), n * appends_per_worker, appends_per_worker)
            for n in range(workers)
        ]
        for f in futures:
            f.result()

    # Verify ledger integrity
    async def verify():
        import aiosqlite
        from babylon60.database.core import connect_async
        from babylon60.audit.ledger import EnterpriseAuditLedger

        conn = await connect_async(str(db_path))
        static_key_b64 = os.environ["LEDGER_TEST_STATIC_KEY"]
        with patch(
            "babylon60.crypto.keys.KeyManager.get_private_key_b64", return_value=static_key_b64
        ):
            ledger = EnterpriseAuditLedger(conn)
            res = await ledger.verify_chain()
            assert res["status"] == "verified", (
                f"Ledger verification failed: {res.get('violations')}"
            )
            assert res["verified_count"] == workers * appends_per_worker
            await ledger.close()
        await conn.close()

    asyncio.run(verify())
