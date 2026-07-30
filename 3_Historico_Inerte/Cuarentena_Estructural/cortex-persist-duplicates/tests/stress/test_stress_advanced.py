# [C5-REAL] Exergy-Maximized — Advanced Stress Test Suite
# Author: borjamoskv
"""
Advanced stress scenarios for BABYLON-60 Persist.

Sections:
  §1. Concurrent mixed read-write stress (ThreadPoolExecutor)
  §2. SAGA proposal fuzzing (SagaWriteProposal edge cases)
  §3. Taint engine stress (cryptographic token throughput)
  §4. Guard adversarial battery (SecretGuard, LandauerGuard, ExergyGuard)
  §5. Database crash recovery (GC-simulated crash)
  §6. Connection pool exhaustion (50 simultaneous connections)
"""

from __future__ import annotations

import logging

import gc
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

os.environ["PYTEST_CURRENT_TEST"] = "stress_advanced"

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# §1. CONCURRENT MIXED READ-WRITE STRESS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestConcurrentMixedReadWrite:
    """Verify 10 concurrent readers + 5 concurrent writers on WAL-mode SQLite."""

    def test_concurrent_readers_writers(self, tmp_path: Path) -> None:
        """10 readers + 5 writers simultaneously; expect 200 total rows."""
        from babylon60.database.core import causal_write, connect

        db_path = str(tmp_path / "concurrent_rw.db")
        conn_seed = connect(db_path)

        # Seed 100 rows
        with causal_write(conn_seed):
            conn_seed.execute(
                "CREATE TABLE stress_data (id INTEGER PRIMARY KEY AUTOINCREMENT, val TEXT)"
            )
            for i in range(100):
                conn_seed.execute("INSERT INTO stress_data (val) VALUES (?)", (f"seed-{i}",))
            conn_seed.commit()
        conn_seed.close()

        writer_errors: list[Exception] = []
        reader_errors: list[Exception] = []
        reader_counts: list[int] = []

        def writer_task(worker_id: int) -> None:
            """Each writer inserts 20 rows."""
            try:
                wconn = connect(db_path)
                for j in range(20):
                    with causal_write(wconn):
                        wconn.execute(
                            "INSERT INTO stress_data (val) VALUES (?)",
                            (f"w{worker_id}-{j}",),
                        )
                        wconn.commit()
                wconn.close()
            except Exception as exc:  # noqa: BLE001
                writer_errors.append(exc)

        def reader_task(worker_id: int) -> None:
            """Each reader reads COUNT(*)."""
            try:
                rconn = connect(db_path, read_only=True)
                row = rconn.execute("SELECT COUNT(*) FROM stress_data").fetchone()
                reader_counts.append(row[0])
                rconn.close()
            except Exception as exc:  # noqa: BLE001
                reader_errors.append(exc)

        with ThreadPoolExecutor(max_workers=15) as pool:
            futures = []
            for wid in range(5):
                futures.append(pool.submit(writer_task, wid))
            for rid in range(10):
                futures.append(pool.submit(reader_task, rid))
            for f in as_completed(futures):
                f.result()

        assert not writer_errors, f"Writer errors: {writer_errors}"
        assert not reader_errors, f"Reader errors: {reader_errors}"

        # Final verification: 100 seed + 5 writers * 20 rows = 200
        verify_conn = connect(db_path, read_only=True)
        total = verify_conn.execute("SELECT COUNT(*) FROM stress_data").fetchone()[0]
        verify_conn.close()
        assert total == 200, f"Expected 200 rows, got {total}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# §2. SAGA PROPOSAL FUZZING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestSagaProposalFuzzing:
    """Stress test SagaWriteProposal with edge cases and boundary conditions."""

    _BASE_KWARGS = {
        "tenant_id": "stress-tenant",
        "project": "stress-project",
        "content": "baseline content for fuzzing",
        "taint_already_verified": True,
    }

    def _make(self, **overrides):
        from babylon60.guards.saga_contract import SagaWriteProposal

        kw = {**self._BASE_KWARGS, **overrides}
        return SagaWriteProposal(**kw)

    def test_unicode_content_emoji(self) -> None:
        """Unicode emoji content should pass validation."""
        proposal = self._make(content="🔥🧬🌀 Exergía máxima alcanzada 🎯")
        assert proposal.content == "🔥🧬🌀 Exergía máxima alcanzada 🎯"

    def test_unicode_content_cjk(self) -> None:
        """CJK characters should pass validation."""
        proposal = self._make(content="熱力学的エントロピーの最小化 知識グラフ")
        assert proposal.content == "熱力学的エントロピーの最小化 知識グラフ"

    def test_unicode_content_arabic(self) -> None:
        """Arabic characters should pass validation."""
        proposal = self._make(content="الحد الأقصى للطاقة الحرة في النظام")
        assert proposal.content == "الحد الأقصى للطاقة الحرة في النظام"

    def test_max_valid_content_just_under_1mb(self) -> None:
        """Content at 1048575 bytes (1MB - 1) should pass."""
        # ASCII 'A' = 1 byte each
        content = "A" * 1_048_575
        proposal = self._make(content=content)
        assert len(proposal.content.encode("utf-8")) == 1_048_575

    def test_content_exceeds_1mb_fails(self) -> None:
        """Content at exactly 1MB + 1 byte should fail."""
        from pydantic import ValidationError

        content = "A" * 1_048_577
        with pytest.raises(ValidationError, match="Content exceeds maximum size"):
            self._make(content=content)

    @pytest.mark.parametrize("level", ["C1", "C2", "C3", "C4", "C5"])
    def test_all_confidence_levels(self, level: str) -> None:
        """All 5 confidence levels (C1-C5) should pass."""
        proposal = self._make(confidence=level)
        assert proposal.confidence == level

    @pytest.mark.parametrize(
        "fact_type",
        [
            "knowledge",
            "decision",
            "error",
            "observation",
            "ghost",
            "reflection",
            "pattern",
            "bridge",
            "diamond",
            "telemetry_batch",
            "mafia_node",
            "UI_ACTION",
            "task",
            "axiom",
            "metric",
            "session_summary",
            "causal_link",
            "episode",
            "enrichment",
            "compaction",
            "tombstone",
        ],
    )
    def test_all_valid_fact_types(self, fact_type: str) -> None:
        """Every fact type in _VALID_FACT_TYPES should pass."""
        proposal = self._make(fact_type=fact_type)
        assert proposal.fact_type == fact_type

    def test_tags_boundary_50_passes(self) -> None:
        """Exactly 50 tags should pass validation."""
        tags = [f"tag-{i}" for i in range(50)]
        proposal = self._make(tags=tags)
        assert len(proposal.tags) == 50

    def test_tags_boundary_51_fails(self) -> None:
        """51 tags should fail with ValidationError."""
        from pydantic import ValidationError

        tags = [f"tag-{i}" for i in range(51)]
        with pytest.raises(ValidationError, match="Too many tags"):
            self._make(tags=tags)

    def test_tenant_id_valid_chars(self) -> None:
        """tenant_id with alphanumeric, hyphens and underscores should pass."""
        proposal = self._make(tenant_id="valid-tenant_123")
        assert proposal.tenant_id == "valid-tenant_123"

    def test_tenant_id_invalid_chars_fails(self) -> None:
        """tenant_id with forbidden characters should fail."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="tenant_id contains forbidden characters"):
            self._make(tenant_id="bad tenant!@#")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# §3. TAINT ENGINE STRESS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestTaintEngineStress:
    """Stress the cryptographic taint system with sequential token generation."""

    def test_100_unique_taint_tokens(self, ed25519_key) -> None:
        """Generate 100 tokens sequentially; verify uniqueness and prefix."""
        from babylon60.engine.causal.taint_engine import generate_secure_taint_token

        private_key_b64, _ = ed25519_key
        tokens: list[str] = []

        t0 = time.perf_counter()
        for i in range(100):
            token = generate_secure_taint_token(
                agent_id="stress",
                session_id=f"s-{i}",
                content=f"taint-payload-{i}",
                private_key_b64=private_key_b64,
            )
            tokens.append(token)
        elapsed = time.perf_counter() - t0

        # All unique
        assert len(set(tokens)) == 100, "Taint tokens are not unique"

        # All start with moskv-taint:
        for t in tokens:
            assert t.startswith("moskv-taint:"), f"Token missing prefix: {t[:40]}"

        throughput = 100 / elapsed
        # Informational — print throughput for diagnostics
        logging.getLogger(__name__).info(f"\n[TAINT-STRESS] 100 tokens in {elapsed:.3f}s ({throughput:.0f} tokens/s)")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# §4. GUARD ADVERSARIAL BATTERY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestSecretGuardAdversarial:
    """SecretGuard must detect ALL known secret pattern types."""

    @pytest.mark.parametrize(
        "label,payload",
        [
            ("AWS", "config: AKIAIOSFODNN7EXAMPLE"),
            ("OpenAI", "key=sk-proj-abcdefghijklmnopqrstuvwxyz123456"),
            ("Stripe", "stripe_key: sk_test_abcdefghijklmnopqrstuvwx"),
            ("GitHub", "token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"),
            ("PEM", "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIB..."),
            ("Gemini", "api_key=AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ12345678"),
            ("Anthropic", "anthropic: sk-ant-abcdefghijklmnopqrstuvwxyz1234567890abcd"),
        ],
    )
    def test_secret_detection(self, label: str, payload: str) -> None:
        """Each secret pattern must raise PlaintextSecretError."""
        from babylon60.guards.secret_guard import PlaintextSecretError, SecretGuard

        with pytest.raises(PlaintextSecretError):
            SecretGuard.verify_clean(payload)

    def test_clean_content_passes(self) -> None:
        """Content without secrets should pass without exception."""
        from babylon60.guards.secret_guard import SecretGuard

        SecretGuard.verify_clean("This is a perfectly safe string with no secrets.")


class TestLandauerGuardAdversarial:
    """LandauerGuard boundary testing for entropy and byte limits."""

    def test_high_entropy_short_passes(self) -> None:
        """High-entropy content under 256 bytes should pass."""
        from babylon60.guards.landauer_guard import LandauerGuard

        content = "AX-049: Categorical Imperative of Exergy — zero anergy universal law."
        assert LandauerGuard.validate(content) is True

    def test_low_entropy_fails(self) -> None:
        """Repetitive low-entropy content should fail."""
        from babylon60.guards.landauer_guard import LandauerGuard

        content = "aaaaaaaaaa"
        assert LandauerGuard.validate(content) is False

    def test_exceeds_256_bytes_fails(self) -> None:
        """Content exceeding 256 bytes should fail even with high entropy."""
        from babylon60.guards.landauer_guard import LandauerGuard

        # 257 non-space printable chars (chr 33-126) — survives strip()
        content = "".join(chr(33 + (i % 94)) for i in range(257))
        assert len(content.strip().encode("utf-8")) > 256
        assert LandauerGuard.validate(content) is False

    def test_entropy_calculation_deterministic(self) -> None:
        """Entropy calculation must be deterministic for identical input."""
        from babylon60.guards.landauer_guard import LandauerGuard

        content = "Deterministic entropy test vector #42"
        e1 = LandauerGuard.calculate_entropy(content)
        e2 = LandauerGuard.calculate_entropy(content)
        assert e1 == e2
        assert isinstance(e1, float)
        assert e1 > 0.0

    def test_empty_content_zero_entropy(self) -> None:
        """Empty string should yield zero entropy."""
        from babylon60.guards.landauer_guard import LandauerGuard

        assert LandauerGuard.calculate_entropy("") == 0.0


class TestExergyGuardAdversarial:
    """ExergyGuard must reject decorative slop from both Spanish and English."""

    def test_spanish_slop_rejected(self) -> None:
        """Spanish conversational padding should be rejected."""
        from babylon60.guards.base import GuardViolation
        from babylon60.guards.exergy_guard import ExergyGuard

        slop = (
            "Por supuesto, aquí tienes la respuesta. Espero que te sea útil. "
            "Es importante notar que además en conclusión ciertamente claro que sí."
        )
        with pytest.raises(GuardViolation):
            ExergyGuard().evaluate(slop, fact_type="note")

    def test_english_slop_rejected(self) -> None:
        """English conversational padding should be rejected."""
        from babylon60.guards.base import GuardViolation
        from babylon60.guards.exergy_guard import ExergyGuard

        slop = (
            "Of course, here you go. Hope this is useful. In conclusion, "
            "furthermore, as an ai language model, proceed to explain."
        )
        with pytest.raises(GuardViolation):
            ExergyGuard().evaluate(slop, fact_type="note")

    def test_high_exergy_content_passes(self) -> None:
        """Dense technical content should pass the exergy guard."""
        from babylon60.guards.exergy_guard import ExergyGuard

        content = (
            "SQLite WAL mode uses write-ahead logging with shared-memory "
            "for concurrent readers. The B-tree page size is 4096 bytes. "
            "PRAGMA journal_mode=WAL enables non-blocking reads during writes."
        )
        result = ExergyGuard().evaluate(content, fact_type="note")
        assert result == content


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# §5. DATABASE CRASH RECOVERY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestDatabaseCrashRecovery:
    """Simulate crash (no close, GC) and verify WAL recovery."""

    def test_crash_recovery_committed_data_intact(self, tmp_path: Path) -> None:
        """Data committed before simulated crash must survive reopening."""
        from babylon60.database.core import causal_write, connect

        db_path = str(tmp_path / "crash_recovery.db")

        # Write data — do NOT close the connection (simulates crash)
        conn = connect(db_path)
        with causal_write(conn):
            conn.execute("CREATE TABLE recovery (id INTEGER PRIMARY KEY, val TEXT)")
            for i in range(50):
                conn.execute("INSERT INTO recovery (val) VALUES (?)", (f"crash-{i}",))
            conn.commit()

        # Simulate crash: drop reference, force GC
        del conn
        gc.collect()

        # Reopen and verify
        conn2 = connect(db_path, read_only=True)
        total = conn2.execute("SELECT COUNT(*) FROM recovery").fetchone()[0]
        conn2.close()
        assert total == 50, f"Expected 50 rows after crash recovery, got {total}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# §6. CONNECTION POOL EXHAUSTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestConnectionPoolExhaustion:
    """Open 50 connections, verify all work, close, and verify post-close access."""

    def test_50_connections_simultaneous(self, tmp_path: Path) -> None:
        """50 concurrent connections must all execute successfully."""
        from babylon60.database.core import causal_write, connect

        db_path = str(tmp_path / "pool_exhaust.db")

        # Setup
        setup_conn = connect(db_path)
        with causal_write(setup_conn):
            setup_conn.execute("CREATE TABLE pool_test (id INTEGER PRIMARY KEY, val TEXT)")
            setup_conn.execute("INSERT INTO pool_test (val) VALUES ('sentinel')")
            setup_conn.commit()
        setup_conn.close()

        # Open 50 connections
        connections = []
        for _ in range(50):
            c = connect(db_path, read_only=True)
            connections.append(c)

        # Verify all can execute
        for idx, c in enumerate(connections):
            row = c.execute("SELECT val FROM pool_test WHERE id = 1").fetchone()
            assert row is not None, f"Connection {idx} returned None"
            assert row[0] == "sentinel", f"Connection {idx} returned wrong value: {row[0]}"

        # Close all
        for c in connections:
            c.close()

        # Verify DB still accessible after mass close
        verify_conn = connect(db_path, read_only=True)
        row = verify_conn.execute("SELECT val FROM pool_test WHERE id = 1").fetchone()
        verify_conn.close()
        assert row[0] == "sentinel"
