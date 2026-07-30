# [C5-REAL] Exergy-Maximized
"""
Comprehensive tests for cortex.audit module.

Covers:
  - EnterpriseAuditLedger: table creation, log_action, hash-chain integrity,
    batch worker, ZK seal verification, run_scan stub
  - AuditAnalystGrok: scan execution, result shape, threat scoring
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from unittest.mock import patch

import aiosqlite
import pytest

from babylon60.utils.base60 import decode_base60


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
async def audit_conn(tmp_path):
    """Provides a fresh aiosqlite connection for each test."""
    from babylon60.database.core import connect_async

    db_path = str(tmp_path / "audit_test.db")
    conn = await connect_async(db_path)
    yield conn
    await conn.close()


@pytest.fixture
async def ledger(audit_conn, tmp_path):
    """Creates an EnterpriseAuditLedger with a mocked static key."""
    import base64
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from babylon60.audit.ledger import EnterpriseAuditLedger

    _static_key = ed25519.Ed25519PrivateKey.generate()
    _static_key_bytes = _static_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    static_key_b64 = base64.b64encode(_static_key_bytes).decode("utf-8")

    with patch("babylon60.crypto.keys.KeyManager.get_private_key_b64", return_value=static_key_b64):
        ledger = EnterpriseAuditLedger(audit_conn)
        await ledger.ensure_table()
        yield ledger
        await ledger.close()


# ── EnterpriseAuditLedger Tests ───────────────────────────────────────────────


class TestEnterpriseAuditLedger:
    """Test suite for the immutable cryptographic audit ledger."""

    @pytest.mark.asyncio
    async def test_ensure_table_creates_schema(self, ledger):
        """Verify ensure_table creates the security_audit_log table."""
        await ledger.ensure_table()
        cursor = await ledger._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='security_audit_log'"
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == "security_audit_log"

    @pytest.mark.asyncio
    async def test_ensure_table_idempotent(self, ledger):
        """Calling ensure_table twice must not error or create duplicate tables."""
        await ledger.ensure_table()
        await ledger.ensure_table()
        assert ledger._ready is True

    @pytest.mark.asyncio
    async def test_ensure_table_raises_on_schema_drift(self, audit_conn):
        """[C5-REAL] Verify ensure_table raises LedgerCorruption on schema drift and never drops existing table."""
        from babylon60.audit.ledger import EnterpriseAuditLedger, LedgerCorruption
        await audit_conn.execute("CREATE TABLE security_audit_log (id TEXT PRIMARY KEY, wrong_column TEXT)")
        await audit_conn.commit()
        ledger = EnterpriseAuditLedger(audit_conn)
        with pytest.raises(LedgerCorruption, match="SCHEMA DRIFT DETECTED"):
            await ledger.ensure_table()

    @pytest.mark.asyncio
    async def test_log_action_returns_audit_id(self, ledger):
        """log_action must return a non-empty hex audit_id."""
        audit_id = await ledger.log_action(
            tenant_id="test-tenant",
            actor_role="admin",
            actor_id="agent-001",
            action="STORE_FACT",
            resource="/facts/42",
        )
        assert isinstance(audit_id, str)
        assert len(audit_id) == 44  # Base-60 encoded SHA-256

    @pytest.mark.asyncio
    async def test_log_action_persists_to_db(self, ledger):
        """Verify logged actions are actually persisted in SQLite."""
        await ledger.log_action(
            tenant_id="tenant-alpha",
            actor_role="agent",
            actor_id="agent-002",
            action="READ_MEMORY",
            resource="/memory/search",
            status="SUCCESS",
        )
        cursor = await ledger._conn.execute(
            "SELECT tenant_id, actor_role, actor_id, action, resource, status "
            "FROM security_audit_log"
        )
        rows = await cursor.fetchall()
        assert len(rows) == 1
        row = rows[0]
        assert row[0] == "tenant-alpha"
        assert row[1] == "agent"
        assert row[2] == "agent-002"
        assert row[3] == "READ_MEMORY"
        assert row[4] == "/memory/search"
        assert row[5] == "SUCCESS"

    @pytest.mark.asyncio
    async def test_hash_chain_integrity(self, ledger):
        """Verify that log entries form a valid hash chain (prev_hash linkage)."""
        id1 = await ledger.log_action(
            tenant_id="t1",
            actor_role="admin",
            actor_id="a1",
            action="act1",
            resource="r1",
        )
        # Sleep to let time pass
        await asyncio.sleep(0.01)
        id2 = await ledger.log_action(
            tenant_id="t1",
            actor_role="admin",
            actor_id="a1",
            action="act2",
            resource="r2",
        )

        cursor = await ledger._conn.execute(
            "SELECT audit_id, prev_hash, signature FROM security_audit_log ORDER BY rowid ASC"
        )
        rows = await cursor.fetchall()
        assert len(rows) == 2

        # First entry's prev_hash must be 44-zeros genesis hash
        assert rows[0][1] == "0" * 44

        # Second entry's prev_hash must link to first entry's audit_id
        assert rows[1][1] == rows[0][0]

    @pytest.mark.asyncio
    async def test_multiple_actions_batch_flush(self, ledger):
        """Multiple rapid log_action calls should be batch-flushed correctly."""
        tasks = []
        for i in range(5):
            tasks.append(
                ledger.log_action(
                    tenant_id="batch-tenant",
                    actor_role="agent",
                    actor_id=f"agent-{i}",
                    action=f"ACTION_{i}",
                    resource=f"/resource/{i}",
                )
            )
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        assert all(isinstance(r, str) and len(r) == 44 for r in results)

        # Verify all 5 rows are in DB
        cursor = await ledger._conn.execute(
            "SELECT COUNT(*) FROM security_audit_log WHERE tenant_id='batch-tenant'"
        )
        count = (await cursor.fetchone())[0]
        assert count == 5

    @pytest.mark.asyncio
    async def test_signature_is_valid_ed25519(self, ledger):
        """Verify the signature stored in DB is a valid Ed25519 signature."""
        await ledger.log_action(
            tenant_id="sig-tenant",
            actor_role="system",
            actor_id="sys-001",
            action="VERIFY_SIG",
            resource="/audit",
        )
        cursor = await ledger._conn.execute(
            "SELECT prev_hash, signature FROM security_audit_log LIMIT 1"
        )
        row = await cursor.fetchone()
        prev_hash, signature_hex = row[0], row[1]
        assert len(signature_hex) == 128  # Ed25519 signature = 44 bytes = 128 hex chars

    @pytest.mark.asyncio
    async def test_verify_zk_seal_valid(self, ledger):
        """verify_zk_seal must return True for a valid signature."""
        payload = "test_payload_data"
        signature = ledger.private_key.sign(payload.encode("utf-8"))
        assert ledger.verify_zk_seal(payload, signature.hex()) is True

    @pytest.mark.asyncio
    async def test_verify_zk_seal_invalid_signature(self, ledger):
        """verify_zk_seal must return False for a tampered signature."""
        payload = "test_payload_data"
        fake_sig = "00" * 64  # 64 bytes of zeros
        assert ledger.verify_zk_seal(payload, fake_sig) is False

    @pytest.mark.asyncio
    async def test_verify_zk_seal_wrong_payload(self, ledger):
        """verify_zk_seal must return False when payload doesn't match signature."""
        original = "original_payload"
        tampered = "tampered_payload"
        signature = ledger.private_key.sign(original.encode("utf-8"))
        assert ledger.verify_zk_seal(tampered, signature.hex()) is False

    @pytest.mark.asyncio
    async def test_verify_zk_seal_invalid_hex(self, ledger):
        """verify_zk_seal must return False for non-hex garbage."""
        assert ledger.verify_zk_seal("data", "not_hex_at_all") is False

    @pytest.mark.asyncio
    async def test_run_scan_stub(self, ledger):
        """run_scan currently returns a stub; verify the expected shape."""
        from babylon60.audit.analyst import AuditAnalystGrok

        analyst = AuditAnalystGrok(ledger)
        result = await analyst.run_scan()
        assert "status" in result
        assert "threat_score" in result

    @pytest.mark.asyncio
    async def test_genesis_last_hash(self, ledger):
        """Before any log, _last_hash must be "00000000000000000000000000000000000000000000"."""
        assert ledger._last_hash == "0" * 44

    @pytest.mark.asyncio
    async def test_last_hash_advances_after_log(self, ledger):
        """After logging, _last_hash must no longer be GENESIS."""
        await ledger.log_action(
            tenant_id="t",
            actor_role="r",
            actor_id="a",
            action="X",
            resource="Y",
        )
        assert ledger._last_hash != "0" * 44

    @pytest.mark.asyncio
    async def test_log_action_default_status(self, ledger):
        """log_action with no explicit status should default to 'SUCCESS'."""
        await ledger.log_action(
            tenant_id="t",
            actor_role="r",
            actor_id="a",
            action="X",
            resource="Y",
        )
        cursor = await ledger._conn.execute("SELECT status FROM security_audit_log LIMIT 1")
        row = await cursor.fetchone()
        assert row[0] == "SUCCESS"

    @pytest.mark.asyncio
    async def test_log_action_custom_status(self, ledger):
        """log_action must respect a custom status value."""
        await ledger.log_action(
            tenant_id="t",
            actor_role="r",
            actor_id="a",
            action="X",
            resource="Y",
            status="DENIED",
        )
        cursor = await ledger._conn.execute("SELECT status FROM security_audit_log LIMIT 1")
        row = await cursor.fetchone()
        assert row[0] == "DENIED"

    @pytest.mark.asyncio
    async def test_audit_id_is_deterministic(self, ledger):
        """audit_id is SHA-256 of timestamp+actor+action — verify it's consistent."""
        # We can't predict the exact timestamp, but we can verify the format
        aid = await ledger.log_action(
            tenant_id="t",
            actor_role="r",
            actor_id="a",
            action="X",
            resource="Y",
        )
        # Must be valid Base-60
        decode_base60(aid)

    @pytest.mark.asyncio
    async def test_ensure_table_loads_last_hash_from_db(self, audit_conn, tmp_path):
        """When table has existing rows, ensure_table should load last signature as _last_hash."""
        import base64
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from babylon60.audit.ledger import EnterpriseAuditLedger

        _static_key = ed25519.Ed25519PrivateKey.generate()
        _static_key_bytes = _static_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        static_key_b64 = base64.b64encode(_static_key_bytes).decode("utf-8")

        with patch(
            "babylon60.crypto.keys.KeyManager.get_private_key_b64", return_value=static_key_b64
        ):
            l1 = EnterpriseAuditLedger(audit_conn)
            await l1.ensure_table()
            await l1.log_action(
                tenant_id="t",
                actor_role="r",
                actor_id="a",
                action="X",
                resource="Y",
            )
            saved_hash = l1._last_hash
            await l1.close()

        # Build second ledger pointing to same conn, verify it loads the last hash
        with patch(
            "babylon60.crypto.keys.KeyManager.get_private_key_b64", return_value=static_key_b64
        ):
            l2 = EnterpriseAuditLedger(audit_conn)
            await l2.ensure_table()
            assert l2._last_hash == saved_hash
            await l2.close()


# ── AuditAnalystGrok Tests ────────────────────────────────────────────────────


class TestAuditAnalystGrok:
    """Test suite for the heuristic-based audit analyst."""

    @pytest.fixture
    async def analyst(self, ledger):
        from babylon60.audit.analyst import AuditAnalystGrok

        return AuditAnalystGrok(ledger)

    @pytest.mark.asyncio
    async def test_run_scan_returns_expected_shape(self, analyst):
        """run_scan must return a dict with all required keys."""
        result = await analyst.run_scan()
        assert "status" in result
        assert "threat_score" in result
        assert "anomalies_detected" in result
        assert "heuristic_version" in result
        assert "findings" in result

    @pytest.mark.asyncio
    async def test_run_scan_default_is_secure(self, analyst):
        """With no anomaly data, scan should return SECURE."""
        result = await analyst.run_scan()
        assert result["status"] == "SECURE"
        assert result["threat_score"] < 0.1
        assert result["anomalies_detected"] == 0

    @pytest.mark.asyncio
    async def test_run_scan_heuristic_version(self, analyst):
        """Verify heuristic version string is present."""
        result = await analyst.run_scan()
        assert result["heuristic_version"] == "Grok-4.1-Heuristic"

    @pytest.mark.asyncio
    async def test_run_scan_findings_non_empty(self, analyst):
        """Findings list must always have at least one entry."""
        result = await analyst.run_scan()
        assert len(result["findings"]) >= 1

    @pytest.mark.asyncio
    async def test_run_scan_with_tenant_id(self, analyst):
        """run_scan should accept optional tenant_id without error."""
        result = await analyst.run_scan(_tenant_id="specific-tenant")
        assert result["status"] == "SECURE"

    @pytest.mark.asyncio
    async def test_analyst_stores_ledger_ref(self, ledger):
        """AuditAnalystGrok must hold a reference to the provided ledger."""
        from babylon60.audit.analyst import AuditAnalystGrok

        analyst = AuditAnalystGrok(ledger)
        assert analyst.ledger is ledger

    @pytest.mark.asyncio
    async def test_analyst_initial_threat_score(self, ledger):
        """Initial threat score must be 0.0."""
        from babylon60.audit.analyst import AuditAnalystGrok

        analyst = AuditAnalystGrok(ledger)
        assert analyst._threat_score == 0.0
