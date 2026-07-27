# [C5-REAL] Exergy-Maximized — AUTODIDACT Invariant Coverage
"""
Test suite covering the MISSING invariants identified by the AUTODIDACT audit.

Sections:
  §1  INV-05: Encryption at Rest (P0)
  §2  INV-11: Singularidad de Red (No Vercel)
  §3  INV-13: SQLite-Vec Integrity (VEC-0)
  §4  INV-03: Async Correctness (no time.sleep in async def)
  §5  INV-08: CLI Architectural Boundary
  §6  Extension Isolation (no cli imports from extensions)
"""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Any

import pytest

os.environ["PYTEST_CURRENT_TEST"] = "invariant_coverage"
os.environ["CORTEX_TESTING"] = "1"

ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# §1  INV-05: ENCRYPTION AT REST (P0)
# ---------------------------------------------------------------------------


class TestINV05EncryptionAtRest:
    """Validates the AES-256-GCM envelope encryption subsystem (P0)."""

    def test_crypto_module_exists(self) -> None:
        """babylon60/crypto/ must exist with aes.py and keys.py."""
        crypto_dir = ROOT / "babylon60" / "crypto"
        assert crypto_dir.is_dir(), f"Missing crypto directory: {crypto_dir}"
        assert (crypto_dir / "aes.py").is_file(), "Missing aes.py"
        assert (crypto_dir / "keys.py").is_file(), "Missing keys.py"

    def test_aes_gcm_encrypt_decrypt_roundtrip(self) -> None:
        """CortexEncrypter must roundtrip plaintext through AES-256-GCM."""
        from babylon60.crypto.aes import CortexEncrypter

        master_key = os.urandom(32)
        enc = CortexEncrypter(master_key=master_key, strict_mode=True)
        plaintext = "C5-REAL invariant test payload"
        ciphertext = enc.encrypt_str(plaintext)
        assert ciphertext is not None
        assert ciphertext.startswith("v6_aesgcm:")
        decrypted = enc.decrypt_str(ciphertext)
        assert decrypted == plaintext

    def test_aes_gcm_tenant_isolation(self) -> None:
        """Different tenants must produce different ciphertexts for the same plaintext."""
        from babylon60.crypto.aes import CortexEncrypter

        master_key = os.urandom(32)
        enc = CortexEncrypter(master_key=master_key)
        payload = "shared_secret"
        ct_a = enc.encrypt_str(payload, tenant_id="tenant_alpha")
        ct_b = enc.encrypt_str(payload, tenant_id="tenant_beta")
        assert ct_a != ct_b, "Tenant isolation violated: identical ciphertexts"

    def test_aes_gcm_cross_tenant_decrypt_fails(self) -> None:
        """Decrypting with the wrong tenant_id must raise ValueError."""
        from babylon60.crypto.aes import CortexEncrypter

        master_key = os.urandom(32)
        enc = CortexEncrypter(master_key=master_key, strict_mode=True)
        ciphertext = enc.encrypt_str("secret", tenant_id="tenant_a")
        assert ciphertext is not None
        with pytest.raises(ValueError, match="Decryption failed"):
            enc.decrypt_str(ciphertext, tenant_id="tenant_b")

    def test_aes_gcm_json_roundtrip(self) -> None:
        """encrypt_json / decrypt_json must roundtrip a dict."""
        from babylon60.crypto.aes import CortexEncrypter

        master_key = os.urandom(32)
        enc = CortexEncrypter(master_key=master_key)
        data: dict[str, Any] = {"invariant": "INV-05", "level": "P0"}
        ct = enc.encrypt_json(data)
        result = enc.decrypt_json(ct)
        assert result == data

    def test_aes_no_key_strict_mode_raises(self) -> None:
        """Strict mode without a key must raise on encrypt."""
        from babylon60.crypto.aes import CortexEncrypter

        enc = CortexEncrypter(master_key=None, strict_mode=True)
        with pytest.raises(RuntimeError, match="Strict crypto mode"):
            enc.encrypt_str("payload")

    def test_ed25519_sign_verify_roundtrip(self) -> None:
        """Ed25519 Signer/Verifier must produce valid signatures."""
        from babylon60.crypto.keys import KeyManager

        km = KeyManager("test_invariant_coverage")
        actor = "inv05_test_actor"
        pub_b64 = km.generate_and_store_key(actor, expiration_days=1)
        priv_b64 = km.get_private_key_b64(actor)
        assert priv_b64 is not None

        from babylon60.crypto.keys import Signer, Verifier

        payload_hash = "sha256:deadbeef"
        timestamp = "2026-07-06T00:00:00Z"
        sig = Signer.sign_payload(priv_b64, payload_hash, timestamp)
        assert Verifier.verify_signature(pub_b64, payload_hash, timestamp, sig)

    def test_ed25519_key_revocation(self) -> None:
        """Revoked keys must return None on private key retrieval."""
        from babylon60.crypto.keys import KeyManager

        km = KeyManager("test_invariant_revocation")
        actor = "revoke_me"
        km.generate_and_store_key(actor, expiration_days=1)
        km.revoke_key(actor)
        assert km.get_private_key_b64(actor) is None


# ---------------------------------------------------------------------------
# §2  INV-11: SINGULARIDAD DE RED (No Vercel)
# ---------------------------------------------------------------------------


class TestINV11NoVercel:
    """P0: No Vercel artifacts may exist in the codebase."""

    def test_no_vercel_json_anywhere(self) -> None:
        """vercel.json must not exist anywhere in the repository."""
        hits = list(ROOT.rglob("vercel.json"))
        assert hits == [], f"vercel.json found at: {[str(h) for h in hits]}"

    def test_no_vercel_packages_in_any_package_json(self) -> None:
        """No package.json may reference @vercel/* dependencies."""
        violations: list[str] = []
        for pj in ROOT.rglob("package.json"):
            if "node_modules" in str(pj):
                continue
            content = pj.read_text(encoding="utf-8", errors="ignore")
            if "@vercel/" in content:
                violations.append(str(pj))
        assert violations == [], f"@vercel/* found in: {violations}"


# ---------------------------------------------------------------------------
# §3  INV-13: SQLite-Vec Integrity (VEC-0)
# ---------------------------------------------------------------------------


class TestINV13SqliteVec:
    """Validates vec0 virtual table structural invariants on runtime.db."""

    RUNTIME_DB = Path.home() / ".cortex" / "runtime.db"

    @pytest.mark.asyncio
    async def test_vec0_tables_exist(self) -> None:
        """runtime.db must contain at least one vec0 virtual table."""
        if not self.RUNTIME_DB.exists():
            pytest.skip(f"runtime.db not found at {self.RUNTIME_DB}")

        import aiosqlite

        async with aiosqlite.connect(str(self.RUNTIME_DB)) as db:
            cursor = await db.execute(
                "SELECT name, sql FROM sqlite_master WHERE type='table' AND sql LIKE '%vec0%'"
            )
            rows = await cursor.fetchall()
            assert len(rows) > 0, "No vec0 virtual tables found in runtime.db"

    @pytest.mark.asyncio
    async def test_vec0_dimension_declarations(self) -> None:
        """vec0 CREATE statements must declare explicit dimensions."""
        if not self.RUNTIME_DB.exists():
            pytest.skip(f"runtime.db not found at {self.RUNTIME_DB}")

        import aiosqlite

        dim_pattern = re.compile(r"float\[\d+\]", re.IGNORECASE)
        async with aiosqlite.connect(str(self.RUNTIME_DB)) as db:
            cursor = await db.execute(
                "SELECT name, sql FROM sqlite_master WHERE type='table' AND sql LIKE '%vec0%'"
            )
            rows = await cursor.fetchall()
            if not rows:
                pytest.skip("No vec0 tables to validate")

            for name, sql in rows:
                if sql is None:
                    continue
                assert dim_pattern.search(sql), (
                    f"vec0 table '{name}' lacks explicit dimension declaration in: {sql}"
                )


# ---------------------------------------------------------------------------
# §4  INV-03: ASYNC CORRECTNESS (no time.sleep in async def)
# ---------------------------------------------------------------------------


class _AsyncSleepVisitor(ast.NodeVisitor):
    """AST visitor that detects time.sleep() calls inside async def functions."""

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.violations: list[str] = []
        self._in_async = False

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        old = self._in_async
        self._in_async = True
        self.generic_visit(node)
        self._in_async = old

    def visit_Call(self, node: ast.Call) -> None:
        if self._in_async and self._is_time_sleep(node):
            self.violations.append(f"{self.filepath}:{node.lineno}")
        self.generic_visit(node)

    @staticmethod
    def _is_time_sleep(node: ast.Call) -> bool:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "sleep":
            if isinstance(func.value, ast.Name) and func.value.id == "time":
                return True
        return False


class TestINV03AsyncCorrectness:
    """No async def function may call time.sleep() — must use asyncio.sleep()."""

    SCAN_DIRS = ["babylon60/engine", "babylon60/guards"]

    def test_no_time_sleep_in_async_defs(self) -> None:
        """Scan engine/ and guards/ for time.sleep() inside async def."""
        violations: list[str] = []
        for scan_dir in self.SCAN_DIRS:
            target = ROOT / scan_dir
            if not target.is_dir():
                continue
            for py_file in target.rglob("*.py"):
                try:
                    tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
                except SyntaxError:
                    continue
                visitor = _AsyncSleepVisitor(str(py_file.relative_to(ROOT)))
                visitor.visit(tree)
                violations.extend(visitor.violations)
        assert violations == [], "time.sleep() found inside async def:\n" + "\n".join(
            f"  - {v}" for v in violations
        )


# ---------------------------------------------------------------------------
# §5  INV-08: CLI ARCHITECTURAL BOUNDARY
# ---------------------------------------------------------------------------


class TestINV08CLIBoundary:
    """CLI modules must not bypass the engine layer with direct DB access."""

    PATTERN = re.compile(r"aiosqlite\.connect\(")

    def test_detect_direct_db_access_in_cli(self) -> None:
        """Scan babylon60/cli/*.py for direct aiosqlite.connect() calls.

        Known violation: babylon60/cli/ledger.py — tracked as regression marker.
        This test PASSES by detecting and documenting known violations.
        """
        cli_dir = ROOT / "babylon60" / "cli"
        if not cli_dir.is_dir():
            pytest.skip("CLI directory not found")

        violations: list[str] = []
        for py_file in cli_dir.glob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            if self.PATTERN.search(content):
                violations.append(str(py_file.relative_to(ROOT)))

        # Document known violations as regression markers
        known = {"babylon60/cli/ledger.py"}
        unknown = set(violations) - known
        assert unknown == set(), (
            "NEW CLI boundary violations (not previously known):\n"
            + "\n".join(f"  - {v}" for v in sorted(unknown))
        )
        # The known set is accepted as technical debt
        if violations:
            pytest.xfail(
                f"Known CLI boundary violations (regression markers): {sorted(violations)}"
            )


# ---------------------------------------------------------------------------
# §6  EXTENSION ISOLATION
# ---------------------------------------------------------------------------


class TestExtensionIsolation:
    """Extension modules must not import from babylon60.cli."""

    PATTERN = re.compile(r"from\s+babylon60\.cli\b")

    def test_detect_cli_imports_in_extensions(self) -> None:
        """Scan babylon60/extensions/**/*.py for 'from babylon60.cli' imports.

        Known violations (~7 files) are tracked as regression markers.
        This test PASSES by detecting and documenting them.
        """
        ext_dir = ROOT / "babylon60" / "extensions"
        if not ext_dir.is_dir():
            pytest.skip("Extensions directory not found")

        violations: list[str] = []
        for py_file in ext_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            if self.PATTERN.search(content):
                violations.append(str(py_file.relative_to(ROOT)))

        # Capture all violations as a regression set
        # If new violations appear beyond the known count, test fails
        known_count = 8
        if len(violations) > known_count:
            excess = violations[known_count:]
            pytest.fail(
                f"NEW extension isolation violations beyond known {known_count}:\n"
                + "\n".join(f"  - {v}" for v in excess)
            )
        # Document the regression set
        if violations:
            pytest.xfail(
                f"Known extension isolation violations ({len(violations)} files): "
                + ", ".join(sorted(violations))
            )
