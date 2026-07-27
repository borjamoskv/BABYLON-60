# [C5-REAL] P0 regression test: ensure_table must NEVER drop the ledger.
"""
Verifies that EnterpriseAuditLedger.ensure_table raises LedgerCorruption
when the existing schema drifts (missing columns), instead of executing
DROP TABLE — which would destroy the audit trail silently.

This test covers the anti-forensic vector identified in the C5-REAL audit:
an attacker (or a schema migration) that causes column drift would trigger
the old code path to incinerate the entire compliance ledger.
"""

import asyncio
import os
import tempfile

import pytest

from babylon60.audit.ledger import EnterpriseAuditLedger, LedgerCorruption
from babylon60.database.core import connect_async_ctx


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_fail_closed.db")


@pytest.mark.asyncio
async def test_schema_drift_raises_ledger_corruption(db_path):
    """If security_audit_log exists but lacks required columns,
    ensure_table must raise LedgerCorruption — never DROP."""

    # 1. Create a table with the right name but wrong schema (simulates drift)
    async with connect_async_ctx(db_path) as conn:
        conn._conn.authorize_causal_writes()
        await conn.execute(
            """CREATE TABLE security_audit_log (
                id INTEGER PRIMARY KEY,
                audit_id TEXT,
                timestamp TEXT
            )"""
        )
        # Insert a row so we can verify it survives
        await conn.execute(
            "INSERT INTO security_audit_log (audit_id, timestamp) VALUES ('evidence_row', '2026-07-13')"
        )
        await conn.commit()

    # 2. ensure_table must refuse to start
    async with connect_async_ctx(db_path) as conn:
        conn._conn.authorize_causal_writes()
        ledger = EnterpriseAuditLedger(conn)
        with pytest.raises(LedgerCorruption, match="SCHEMA DRIFT DETECTED"):
            await ledger.ensure_table()

    # 3. Verify the evidence row survived — the table was NOT dropped
    async with connect_async_ctx(db_path) as conn:
        conn._conn.authorize_causal_writes()
        cursor = await conn.execute(
            "SELECT audit_id FROM security_audit_log WHERE audit_id = 'evidence_row'"
        )
        row = await cursor.fetchone()
        assert row is not None, "Evidence row was destroyed — DROP TABLE was executed"
        assert row[0] == "evidence_row"


@pytest.mark.asyncio
async def test_clean_schema_starts_normally(db_path):
    """If no table exists, ensure_table creates it and starts normally."""
    async with connect_async_ctx(db_path) as conn:
        conn._conn.authorize_causal_writes()
        ledger = EnterpriseAuditLedger(conn)
        await ledger.ensure_table()
        assert ledger._ready is True


@pytest.mark.asyncio
async def test_correct_schema_starts_normally(db_path):
    """If table exists with correct schema, ensure_table starts normally."""
    async with connect_async_ctx(db_path) as conn:
        conn._conn.authorize_causal_writes()
        ledger = EnterpriseAuditLedger(conn)
        # First call creates the table
        await ledger.ensure_table()
        await ledger.close()

    # Second call on existing correct schema must not raise
    async with connect_async_ctx(db_path) as conn:
        conn._conn.authorize_causal_writes()
        ledger2 = EnterpriseAuditLedger(conn)
        await ledger2.ensure_table()
        assert ledger2._ready is True
        await ledger2.close()


@pytest.mark.asyncio
async def test_falsation_demonstration_vulnerable_vs_c5_real(db_path):
    """[C5-REAL] Empirical Falsation Demonstration (Red vs Green Pair).

    Demonstrates side-by-side:
    1. ROJO (Vulnerable Logic): When schema drift occurred under old ensure_table,
       DROP TABLE IF EXISTS was executed, wiping all historical audit records.
    2. VERDE (C5-REAL Logic): When schema drift occurs under fixed ensure_table,
       LedgerCorruption is raised immediately and all historical rows are preserved 100%.
    """
    db_red = db_path + "_red.db"
    db_green = db_path + "_green.db"

    # --- 1. ROJO (Demonstrate vulnerable DROP TABLE destruction) ---
    async with connect_async_ctx(db_red) as conn:
        conn._conn.authorize_causal_writes()
        await conn.execute("CREATE TABLE security_audit_log (id INTEGER PRIMARY KEY, audit_id TEXT)")
        await conn.execute("INSERT INTO security_audit_log (audit_id) VALUES ('historical_evidence_to_be_destroyed')")
        await conn.commit()

        # Execute vulnerable old logic:
        cursor = await conn.execute("PRAGMA table_info(security_audit_log)")
        cols = await cursor.fetchall()
        col_names = [c[1] for c in cols]
        if cols and ("payload_canonical" not in col_names or "session_id" not in col_names):
            await conn.execute("DROP TABLE IF EXISTS security_audit_log")
            await conn.commit()

        # Assert evidence was wiped (ROJO FALSATION PROVEN)
        cursor = await conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='security_audit_log'")
        assert (await cursor.fetchone())[0] == 0, "Vulnerable DROP TABLE did not drop the table as expected in RED demo"

    # --- 2. VERDE (Demonstrate C5-REAL FAIL-FAST preservation) ---
    async with connect_async_ctx(db_green) as conn:
        conn._conn.authorize_causal_writes()
        await conn.execute("CREATE TABLE security_audit_log (id INTEGER PRIMARY KEY, audit_id TEXT)")
        await conn.execute("INSERT INTO security_audit_log (audit_id) VALUES ('historical_evidence_preserved')")
        await conn.commit()

        ledger = EnterpriseAuditLedger(conn)
        with pytest.raises(LedgerCorruption, match="SCHEMA DRIFT DETECTED"):
            await ledger.ensure_table()

        # Assert evidence survived 100% intact (VERDE PRESERVATION PROVEN)
        cursor = await conn.execute("SELECT audit_id FROM security_audit_log WHERE audit_id='historical_evidence_preserved'")
        row = await cursor.fetchone()
        assert row is not None and row[0] == "historical_evidence_preserved", "Evidence was lost under C5-REAL ensure_table!"
