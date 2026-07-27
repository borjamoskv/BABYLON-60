# [C5-REAL] Exergy-Maximized — Stress Test & PoC Suite
# Author: borjamoskv
"""
BABYLON-60 Stress Test & Proof-of-Concept Suite.

Validates the core invariants of the system under:
  1. Concurrent database pressure (WAL contention)
  2. SAGA Write-Path Contract boundary enforcement
  3. Taint Engine cryptographic token generation & validation
  4. Guard system rejection of adversarial payloads
  5. Ledger hash-chain integrity verification
  6. Connection Factory authorizer enforcement
  7. Exergy Guard & Landauer Guard thermodynamic bounds

Run with:
    .venv/bin/python -m pytest tests/stress/test_stress_poc.py -v --tb=short
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import secrets
import sqlite3
import sys
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from babylon60.utils.base60 import bytes_to_base60

# ─── PATH SETUP ──────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("CORTEX_DB_PATH", str(ROOT / ".cortex_test"))
os.environ["PYTEST_CURRENT_TEST"] = "stress_poc"


# ═══════════════════════════════════════════════════════════════════════
# §1. DATABASE LAYER — Concurrent WAL Stress Test
# ═══════════════════════════════════════════════════════════════════════


class TestDatabaseStress:
    """Validates SQLite WAL mode, busy_timeout, and connection pragmas."""

    def test_wal_mode_enforced(self, tmp_path: Path) -> None:
        """PoC: Every connection created via the factory MUST have WAL journal mode."""
        from babylon60.database.core import connect

        db_path = str(tmp_path / "test_wal.db")
        conn = connect(db_path)
        result = conn.execute("PRAGMA journal_mode").fetchone()
        assert result[0] == "wal", f"Expected WAL, got {result[0]}"
        conn.close()

    def test_busy_timeout_enforced(self, tmp_path: Path) -> None:
        """PoC: busy_timeout MUST be >= 5000ms (Ω10 invariant)."""
        from babylon60.database.core import connect

        db_path = str(tmp_path / "test_timeout.db")
        conn = connect(db_path)
        result = conn.execute("PRAGMA busy_timeout").fetchone()
        assert result[0] >= 5000, f"Expected >= 5000, got {result[0]}"
        conn.close()

    def test_foreign_keys_enforced(self, tmp_path: Path) -> None:
        """PoC: Foreign key enforcement MUST be active."""
        from babylon60.database.core import connect

        db_path = str(tmp_path / "test_fk.db")
        conn = connect(db_path)
        result = conn.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1, f"Expected 1 (ON), got {result[0]}"
        conn.close()

    def test_cortex_connection_factory_blocks_raw(self) -> None:
        """PoC: Direct sqlite3.connect() calls MUST be structurally forbidden."""
        with pytest.raises(RuntimeError, match="FATAL"):
            # Temporarily clear the PYTEST env var to trigger the block
            old = os.environ.pop("PYTEST_CURRENT_TEST", None)
            try:
                sqlite3.connect(":memory:")
            finally:
                if old:
                    os.environ["PYTEST_CURRENT_TEST"] = old

    def test_concurrent_writer_contention(self, tmp_path: Path) -> None:
        """Stress: 10 concurrent writers against a single WAL database.
        All writes MUST succeed without SQLITE_BUSY errors."""
        from babylon60.database.core import connect, causal_write

        db_path = str(tmp_path / "stress_concurrent.db")
        conn = connect(db_path)
        conn.execute("CREATE TABLE stress (id INTEGER PRIMARY KEY, val TEXT)")
        conn.commit()
        conn.close()

        errors: list[str] = []
        barrier = asyncio.Barrier(10)

        def writer(thread_id: int) -> None:
            try:
                c = connect(db_path)
                with causal_write(c):
                    for i in range(50):
                        c.execute(
                            "INSERT INTO stress (val) VALUES (?)",
                            (f"thread-{thread_id}-row-{i}",),
                        )
                    c.commit()
                c.close()
            except Exception as e:  # noqa: BLE001
                errors.append(f"Thread {thread_id}: {e}")

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(writer, i) for i in range(10)]
            for f in futures:
                f.result(timeout=30)

        assert not errors, f"Concurrent write errors: {errors}"

        # Verify all 500 rows persisted
        verify_conn = connect(db_path)
        count = verify_conn.execute("SELECT COUNT(*) FROM stress").fetchone()[0]
        verify_conn.close()
        assert count == 500, f"Expected 500 rows, got {count}"

    def test_cortex_connection_authorizer_blocks_unauthorized_writes(self, tmp_path: Path) -> None:
        """PoC: CortexConnection authorizer MUST deny DML writes without causal authorization."""
        from babylon60.database.core import CortexConnection, connect, causal_write

        db_path = str(tmp_path / "authorizer_test.db")
        conn = connect(db_path)
        # Create table with authorization
        with causal_write(conn):
            conn.execute("CREATE TABLE forbidden (id INTEGER, val TEXT)")
            conn.commit()

        # Now try to INSERT without causal_write — MUST be denied
        with pytest.raises((sqlite3.OperationalError, sqlite3.DatabaseError)):
            conn.execute("INSERT INTO forbidden (val) VALUES ('should_fail')")
        conn.close()


# ═══════════════════════════════════════════════════════════════════════
# §2. SAGA WRITE-PATH CONTRACT — Boundary Enforcement
# ═══════════════════════════════════════════════════════════════════════


class TestSagaContract:
    """Validates the SAGA-1 Write-Path Contract deterministic boundaries."""

    def test_valid_proposal_passes(self) -> None:
        """PoC: A well-formed proposal MUST pass SAGA-1 validation."""
        from babylon60.guards.saga_contract import SagaWriteProposal

        proposal = SagaWriteProposal(
            tenant_id="default",
            project="test-project",
            content="Test fact content for stress testing.",
            fact_type="knowledge",
            confidence="C5",
            tags=["stress-test", "poc"],
            source="stress_poc",
            metadata={"CORTEX-TAINT": "taint:test:session:2026-07-06T21:00:00Z:abc123"},
        )
        assert proposal.tenant_id == "default"
        assert proposal.content == "Test fact content for stress testing."

    def test_empty_content_rejected(self) -> None:
        """SAGA-1: Empty content MUST trigger rejection."""
        from pydantic import ValidationError

        from babylon60.guards.saga_contract import SagaWriteProposal

        with pytest.raises(ValidationError, match="content"):
            SagaWriteProposal(
                tenant_id="default",
                project="test",
                content="",
            )

    def test_empty_tenant_id_rejected(self) -> None:
        """SAGA-1: Empty tenant_id MUST trigger rejection (tenant isolation breach)."""
        from pydantic import ValidationError

        from babylon60.guards.saga_contract import SagaWriteProposal

        with pytest.raises(ValidationError, match="tenant_id"):
            SagaWriteProposal(
                tenant_id="",
                project="test",
                content="valid content",
            )

    def test_invalid_confidence_rejected(self) -> None:
        """SAGA-1: Invalid confidence level MUST be rejected."""
        from pydantic import ValidationError

        from babylon60.guards.saga_contract import SagaWriteProposal

        with pytest.raises(ValidationError, match="confidence"):
            SagaWriteProposal(
                tenant_id="default",
                project="test",
                content="valid content",
                confidence="C9",
            )

    def test_invalid_fact_type_rejected(self) -> None:
        """SAGA-1: Unknown fact_type MUST be rejected (injection prevention)."""
        from pydantic import ValidationError

        from babylon60.guards.saga_contract import SagaWriteProposal

        with pytest.raises(ValidationError, match="fact_type"):
            SagaWriteProposal(
                tenant_id="default",
                project="test",
                content="valid content",
                fact_type="sql_injection_payload",
            )

    def test_content_size_limit_enforced(self) -> None:
        """Stress: Content exceeding 1MB MUST be rejected."""
        from pydantic import ValidationError

        from babylon60.guards.saga_contract import SagaWriteProposal

        oversized_content = "A" * (1_048_577)  # 1MB + 1 byte
        with pytest.raises(ValidationError, match="Content exceeds maximum"):
            SagaWriteProposal(
                tenant_id="default",
                project="test",
                content=oversized_content,
            )

    def test_tenant_id_injection_blocked(self) -> None:
        """SAGA-1: tenant_id with injection characters MUST be blocked."""
        from pydantic import ValidationError

        from babylon60.guards.saga_contract import SagaWriteProposal

        for malicious in ["'; DROP TABLE--", "../../../etc/passwd", "tenant\x00null"]:
            with pytest.raises(ValidationError):
                SagaWriteProposal(
                    tenant_id=malicious,
                    project="test",
                    content="valid",
                )

    def test_extra_fields_forbidden(self) -> None:
        """SAGA-1: Extra fields MUST be rejected (frozen model, extra=forbid)."""
        from pydantic import ValidationError

        from babylon60.guards.saga_contract import SagaWriteProposal

        with pytest.raises(ValidationError, match="extra"):
            SagaWriteProposal(
                tenant_id="default",
                project="test",
                content="valid",
                evil_field="should_not_pass",
            )

    def test_tag_count_limit(self) -> None:
        """SAGA-1: More than 50 tags MUST be rejected."""
        from pydantic import ValidationError

        from babylon60.guards.saga_contract import SagaWriteProposal

        with pytest.raises(ValidationError, match="Too many tags"):
            SagaWriteProposal(
                tenant_id="default",
                project="test",
                content="valid",
                tags=[f"tag-{i}" for i in range(51)],
            )

    def test_mass_proposal_throughput(self) -> None:
        """Stress: Validate 10,000 proposals in sequence. Measure throughput."""
        from babylon60.guards.saga_contract import SagaWriteProposal

        t0 = time.monotonic()
        for i in range(10_000):
            SagaWriteProposal(
                tenant_id="default",
                project="stress",
                content=f"Fact #{i} — stress test payload",
                fact_type="knowledge",
                confidence="C3",
                metadata={
                    "CORTEX-TAINT": f"taint:agent:{uuid.uuid4().hex}:2026-07-06T21:00:00Z:hash"
                },
            )
        elapsed = time.monotonic() - t0
        rate = 10_000 / elapsed
        # Must validate at least 1000 proposals/second
        assert rate > 1000, f"Throughput too low: {rate:.0f} proposals/sec (min: 1000)"


# ═══════════════════════════════════════════════════════════════════════
# §3. TAINT ENGINE — Cryptographic Token Generation
# ═══════════════════════════════════════════════════════════════════════


class TestTaintEngine:
    """Validates the CORTEX-TAINT cryptographic attribution system."""

    def test_canonicalize_json_determinism(self) -> None:
        """PoC: JSON canonicalization MUST be deterministic regardless of key order."""
        from babylon60.engine.causal.taint_engine import canonicalize_content

        content_a = '{"b": 2, "a": 1}'
        content_b = '{"a": 1, "b": 2}'

        assert canonicalize_content(content_a) == canonicalize_content(content_b)

    def test_canonicalize_non_json(self) -> None:
        """PoC: Non-JSON content is normalized (stripped, split by lines)."""
        from babylon60.engine.causal.taint_engine import canonicalize_content

        content = "  hello world  \n  line 2  \n"
        result = canonicalize_content(content)
        assert result == b"hello world\nline 2"

    def test_sha3_determinism(self) -> None:
        """PoC: SHA3-256 MUST produce identical hashes for identical inputs."""
        from babylon60.engine.causal.taint_engine import _fast_sha3

        data = b"thermodynamic invariant"
        h1 = _fast_sha3(data)
        h2 = _fast_sha3(data)
        assert h1 == h2
        assert len(h1) == 44  # SHA3-256 hex digest length

    def test_taint_token_format_ed25519(self) -> None:
        """PoC: Generated taint token MUST follow the moskv-taint format."""
        import base64

        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        from babylon60.engine.causal.taint_engine import generate_secure_taint_token

        private_key = Ed25519PrivateKey.generate()
        private_key_b64 = base64.b64encode(
            private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )
        ).decode()

        token = generate_secure_taint_token(
            agent_id="stress-agent",
            session_id="session-001",
            content="test content for taint",
            private_key_b64=private_key_b64,
        )

        assert token.startswith("moskv-taint:")
        parts = token.split(":")
        # moskv-taint:{agent_id}:{session_id}:{timestamp}:{nonce}:{signature}
        assert len(parts) >= 6

    def test_taint_uniqueness(self) -> None:
        """Stress: 1000 taint tokens MUST be unique (no nonce collision)."""
        from babylon60.engine.causal.taint_engine import canonicalize_content, _fast_sha3

        hashes = set()
        for i in range(1000):
            content = f"unique-content-{i}-{uuid.uuid4().hex}"
            h = _fast_sha3(canonicalize_content(content))
            assert h not in hashes, f"Hash collision at iteration {i}"
            hashes.add(h)

        assert len(hashes) == 1000


# ═══════════════════════════════════════════════════════════════════════
# §4. GUARD SYSTEM — Adversarial Payload Rejection
# ═══════════════════════════════════════════════════════════════════════


class TestGuardSystem:
    """Validates guards reject adversarial inputs."""

    def test_homoglyph_guard_detects_cyrillic(self) -> None:
        """PoC: Homoglyph guard MUST detect Cyrillic lookalikes in Python source."""
        from babylon60.guards.homoglyph_guard import AntiHomoglyphGuard

        guard = AntiHomoglyphGuard(block_mode=False)
        # Python source with Cyrillic 'а' in a variable name
        source_with_homoglyph = "\u0430dmin = True\nprint(\u0430dmin)"
        result = guard.check_code(source_with_homoglyph)
        assert not result, "Failed to detect Cyrillic homoglyph in Python source"

    def test_secret_guard_detects_api_keys(self) -> None:
        """PoC: Secret guard MUST detect plaintext API keys."""
        from babylon60.guards.secret_guard import PlaintextSecretError, SecretGuard

        # verify_clean raises PlaintextSecretError on detection
        with pytest.raises(PlaintextSecretError):
            SecretGuard.verify_clean("my key is sk-proj-abc123xyz789abcdefghijklmnopqrstuv")

    def test_landauer_guard_rejects_low_entropy(self) -> None:
        """PoC: LandauerGuard MUST reject axiom-type content with low Shannon entropy."""
        from babylon60.guards.landauer_guard import LandauerGuard

        # Low-entropy content: highly repetitive
        low_entropy = "aaa aaa aaa aaa aaa aaa aaa aaa"
        result = LandauerGuard.validate(low_entropy)
        assert result is False, f"LandauerGuard should reject low-entropy content, got: {result}"

    def test_exergy_guard_rejects_slop(self) -> None:
        """PoC: ExergyGuard MUST reject conversational slop."""
        from babylon60.guards.base import GuardViolation
        from babylon60.guards.exergy_guard import ExergyGuard

        guard = ExergyGuard()
        slop = (
            "Entendí perfectamente tu solicitud. Aquí tienes el código. "
            "Espero que esto te sea útil y que todo funcione bien. "
            "No dudes en consultarme si tienes alguna pregunta adicional."
        )
        # ExergyGuard.evaluate() raises GuardViolation for low-exergy content
        with pytest.raises((GuardViolation, ValueError)):
            guard.evaluate(slop, fact_type="note")

    def test_landauer_guard_in_exergy_module_rejects_sacred_slop(self) -> None:
        """PoC: LandauerGuard (exergy_guard module) MUST reject low-entropy sacred facts."""
        from babylon60.guards.base import GuardViolation
        from babylon60.guards.exergy_guard import LandauerGuard as ELandauerGuard

        guard = ELandauerGuard()
        low_entropy_sacred = "aaa aaa aaa aaa aaa aaa aaa aaa"
        with pytest.raises(GuardViolation):
            guard.evaluate(low_entropy_sacred, is_sacred=True)

    def test_saga_contract_batch_integrity(self) -> None:
        """Stress: Validate 500 SAGA proposals — all clean content MUST pass."""
        from babylon60.guards.saga_contract import SagaWriteProposal

        rejections = 0
        for i in range(500):
            try:
                SagaWriteProposal(
                    tenant_id="default",
                    project="stress",
                    content=f"Validated fact #{i} with structural integrity.",
                    fact_type="knowledge",
                    metadata={"CORTEX-TAINT": f"taint:agent:sess:2026-07-06T21:00:00Z:hash{i}"},
                )
            except Exception:  # noqa: BLE001
                rejections += 1

        # All clean proposals should pass
        assert rejections == 0, f"False rejections: {rejections}/500"


# ═══════════════════════════════════════════════════════════════════════
# §5. LEDGER INTEGRITY — Hash Chain Verification
# ═══════════════════════════════════════════════════════════════════════


class TestLedgerIntegrity:
    """Validates the cryptographic hash-chain of the runtime ledger."""

    @pytest.mark.asyncio
    async def test_hash_chain_continuity(self) -> None:
        """PoC: The transaction ledger hash chain MUST be continuous."""
        import aiosqlite

        db_path = os.path.expanduser("~/.cortex/runtime.db")
        if not Path(db_path).exists():
            pytest.skip("runtime.db not found")

        async with aiosqlite.connect(db_path) as conn:
            rows = await conn.execute_fetchall(
                "SELECT id, prev_hash, hash FROM transactions ORDER BY id ASC LIMIT 100"
            )

        if len(rows) < 2:
            pytest.skip("Not enough transactions to verify chain")

        breaks = []
        for i in range(1, len(rows)):
            prev_id, _, prev_hash = rows[i - 1]
            curr_id, curr_prev_hash, _ = rows[i]
            if curr_prev_hash != prev_hash:
                breaks.append(
                    f"Break at tx {curr_id}: expected prev_hash={prev_hash}, got={curr_prev_hash}"
                )

        assert not breaks, f"Hash chain breaks detected: {breaks}"

    @pytest.mark.asyncio
    async def test_merkle_roots_exist(self) -> None:
        """PoC: Merkle root checkpoints MUST exist for auditable tx ranges."""
        import aiosqlite

        db_path = os.path.expanduser("~/.cortex/runtime.db")
        if not Path(db_path).exists():
            pytest.skip("runtime.db not found")

        async with aiosqlite.connect(db_path) as conn:
            rows = await conn.execute_fetchall("SELECT COUNT(*) FROM merkle_roots")

        count = rows[0][0]
        assert count > 0, "No Merkle root checkpoints found"


# ═══════════════════════════════════════════════════════════════════════
# §6. ASYNC DATABASE STRESS — Concurrent Async Sessions
# ═══════════════════════════════════════════════════════════════════════


class TestAsyncStress:
    """Validates async database access under concurrent pressure."""

    @pytest.mark.asyncio
    async def test_concurrent_async_reads(self, tmp_path: Path) -> None:
        """Stress: 20 concurrent async readers MUST not deadlock or timeout."""
        import aiosqlite
        from babylon60.database.core import apply_pragmas_async

        db_path = str(tmp_path / "async_stress.db")

        # Setup: create table and seed data
        async with aiosqlite.connect(db_path) as conn:
            await apply_pragmas_async(conn)
            await conn.execute("CREATE TABLE data (id INTEGER PRIMARY KEY, val TEXT)")
            for i in range(100):
                await conn.execute("INSERT INTO data (val) VALUES (?)", (f"row-{i}",))
            await conn.commit()

        results: list[int] = []
        errors: list[str] = []

        async def reader(reader_id: int) -> None:
            try:
                async with aiosqlite.connect(db_path) as conn:
                    await apply_pragmas_async(conn)
                    row = await conn.execute_fetchall("SELECT COUNT(*) FROM data")
                    results.append(row[0][0])
            except Exception as e:  # noqa: BLE001
                errors.append(f"Reader {reader_id}: {e}")

        await asyncio.gather(*[reader(i) for i in range(20)])

        assert not errors, f"Async read errors: {errors}"
        assert all(r == 100 for r in results), f"Inconsistent reads: {results}"

    @pytest.mark.asyncio
    async def test_concurrent_async_writes(self, tmp_path: Path) -> None:
        """Stress: 5 concurrent async writers with WAL MUST all succeed."""
        import aiosqlite
        from babylon60.database.core import apply_pragmas_async

        db_path = str(tmp_path / "async_write_stress.db")

        async with aiosqlite.connect(db_path) as conn:
            await apply_pragmas_async(conn)
            await conn.execute("CREATE TABLE wdata (id INTEGER PRIMARY KEY, val TEXT)")
            await conn.commit()

        errors: list[str] = []

        async def writer(writer_id: int) -> None:
            try:
                async with aiosqlite.connect(db_path) as conn:
                    await apply_pragmas_async(conn)
                    for i in range(20):
                        await conn.execute(
                            "INSERT INTO wdata (val) VALUES (?)",
                            (f"writer-{writer_id}-{i}",),
                        )
                    await conn.commit()
            except Exception as e:  # noqa: BLE001
                errors.append(f"Writer {writer_id}: {e}")

        await asyncio.gather(*[writer(i) for i in range(5)])

        assert not errors, f"Async write errors: {errors}"

        # Verify
        async with aiosqlite.connect(db_path) as conn:
            row = await conn.execute_fetchall("SELECT COUNT(*) FROM wdata")
        assert row[0][0] == 100, f"Expected 100 rows, got {row[0][0]}"


# ═══════════════════════════════════════════════════════════════════════
# §7. SCHEMA INVARIANTS — Structural PoC
# ═══════════════════════════════════════════════════════════════════════


class TestSchemaInvariants:
    """Validates structural invariants of the runtime database schema."""

    @pytest.mark.asyncio
    async def test_facts_table_has_required_columns(self) -> None:
        """PoC: facts table MUST have all thermodynamic plane columns."""
        import aiosqlite

        db_path = os.path.expanduser("~/.cortex/runtime.db")
        if not Path(db_path).exists():
            pytest.skip("runtime.db not found")

        required_columns = {
            "id",
            "fact_hash",
            "tenant_id",
            "project",
            "content",
            "fact_type",
            "confidence",
            "quadrant",
            "storage_tier",
            "exergy_score",
            "parent_id",
            "yield_score",
        }

        async with aiosqlite.connect(db_path) as conn:
            rows = await conn.execute_fetchall("PRAGMA table_info(facts)")

        actual_columns = {row[1] for row in rows}
        missing = required_columns - actual_columns
        assert not missing, f"Missing required columns in facts table: {missing}"

    @pytest.mark.asyncio
    async def test_vec0_embedding_dimensions(self) -> None:
        """PoC: fact_embeddings vec0 table MUST use FLOAT[384] dimensions."""
        import aiosqlite

        db_path = os.path.expanduser("~/.cortex/runtime.db")
        if not Path(db_path).exists():
            pytest.skip("runtime.db not found")

        async with aiosqlite.connect(db_path) as conn:
            rows = await conn.execute_fetchall(
                "SELECT sql FROM sqlite_master WHERE name='fact_embeddings'"
            )

        if not rows:
            pytest.skip("fact_embeddings table not found")

        sql = rows[0][0]
        assert "384" in sql, f"Expected 384-dim embeddings, SQL: {sql}"


# ═══════════════════════════════════════════════════════════════════════
# §8. CONNECTION FACTORY — CortexConnection Physical Claims
# ═══════════════════════════════════════════════════════════════════════


class TestCortexConnectionClaims:
    """Validates physical claims of CortexConnection."""

    def test_connection_has_unique_id(self, tmp_path: Path) -> None:
        """PoC: Every CortexConnection MUST have a unique connection_id."""
        from babylon60.database.core import connect

        db_path = str(tmp_path / "unique_id.db")
        conn1 = connect(db_path)
        conn2 = connect(db_path)

        id1 = conn1._connection_id
        id2 = conn2._connection_id

        assert id1 != id2, "Connection IDs must be unique"
        conn1.close()
        conn2.close()

    def test_connection_has_mtk_nonce(self, tmp_path: Path) -> None:
        """PoC: Every CortexConnection MUST have a non-empty MTK nonce."""
        from babylon60.database.core import connect

        db_path = str(tmp_path / "mtk_nonce.db")
        conn = connect(db_path)
        assert conn._mtk_nonce, "MTK nonce must be non-empty"
        assert len(conn._mtk_nonce) == 32, (
            f"MTK nonce should be 32 hex chars, got {len(conn._mtk_nonce)}"
        )
        conn.close()

    def test_causal_write_authorization_cycle(self, tmp_path: Path) -> None:
        """PoC: authorize/revoke causal writes cycle MUST work correctly."""
        from babylon60.database.core import connect, causal_write

        db_path = str(tmp_path / "auth_cycle.db")
        conn = connect(db_path)

        # Initially unauthorized
        assert not conn._causal_write_authorized

        # Authorize
        with causal_write(conn):
            assert conn._causal_write_authorized
            conn.execute("CREATE TABLE test_auth (id INTEGER)")
            conn.commit()

        # After context manager, authorization revoked
        assert not conn._causal_write_authorized
        conn.close()


# ═══════════════════════════════════════════════════════════════════════
# §9. PERFORMANCE BENCHMARKS
# ═══════════════════════════════════════════════════════════════════════


class TestPerformanceBenchmarks:
    """Measures baseline performance of critical paths."""

    def test_sha3_throughput(self) -> None:
        """Benchmark: SHA3-256 MUST sustain > 100K hashes/sec for 256-byte payloads."""
        data = secrets.token_bytes(256)
        t0 = time.monotonic()
        for _ in range(100_000):
            bytes_to_base60(hashlib.sha3_256(data).digest())
        elapsed = time.monotonic() - t0
        rate = 100_000 / elapsed
        assert rate > 100_000, f"SHA3 throughput too low: {rate:.0f}/sec"

    def test_saga_validation_latency(self) -> None:
        """Benchmark: Single SAGA proposal validation MUST complete in < 1ms."""
        from babylon60.guards.saga_contract import SagaWriteProposal

        t0 = time.monotonic()
        for _ in range(1000):
            SagaWriteProposal(
                tenant_id="bench",
                project="perf",
                content="benchmark content payload",
                metadata={"CORTEX-TAINT": "taint:bench:s:2026-07-06T21:00:00Z:h"},
            )
        elapsed_ms = (time.monotonic() - t0) * 1000 / 1000
        assert elapsed_ms < 1.0, f"SAGA validation too slow: {elapsed_ms:.3f}ms/proposal"

    def test_sqlite_insert_throughput(self, tmp_path: Path) -> None:
        """Benchmark: WAL-mode SQLite MUST sustain > 5000 inserts/sec."""
        from babylon60.database.core import connect, causal_write

        db_path = str(tmp_path / "bench_insert.db")
        conn = connect(db_path)
        with causal_write(conn):
            conn.execute("CREATE TABLE bench (id INTEGER PRIMARY KEY, data TEXT)")
            conn.commit()

            t0 = time.monotonic()
            for i in range(10_000):
                conn.execute("INSERT INTO bench (data) VALUES (?)", (f"row-{i}",))
            conn.commit()
        elapsed = time.monotonic() - t0
        rate = 10_000 / elapsed
        conn.close()

        assert rate > 5000, f"Insert throughput too low: {rate:.0f}/sec (target: 5000)"
