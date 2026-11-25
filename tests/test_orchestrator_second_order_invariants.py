"""Adversarial test suite for Second-Order Invariants (B1, B4, B5, B6) in BABYLON-60."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from babylon60.core.replay_kernel import EpistemicHalt, ReplayKernel
from babylon60.kernel.mcp_deductive_engine import McpCandidateContract
from babylon60.kernel.mcp_lifecycle_manager import McpLifecycleManager
from babylon60.verification import hardware_attestation as hardware
from babylon60.verification.verification_gate import RiskLevel, VerificationGate


@pytest.fixture
def pinned_authority(monkeypatch: pytest.MonkeyPatch) -> ec.EllipticCurvePrivateKey:
    key = ec.generate_private_key(ec.SECP256R1())
    public = key.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    monkeypatch.setenv("BABYLON_ENCLAVE_PINNED_PUBKEY", public.hex())
    return key


def _software_sign_helper(
    key: ec.EllipticCurvePrivateKey, cmd: list[str], **_kwargs: object
) -> subprocess.CompletedProcess[str]:
    payload = bytes.fromhex(cmd[cmd.index("--sign-hex") + 1])
    prehash = cmd[cmd.index("--causal-hash") + 1]
    assert prehash == hashlib.sha256(payload).hexdigest()
    public = key.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    data = {
        "status": "ATTESTED",
        "causal_hash": prehash,
        "public_key": base64.b64encode(public).decode(),
        "secure_enclave_signature": base64.b64encode(key.sign(payload, ec.ECDSA(hashes.SHA256()))).decode(),
    }
    return subprocess.CompletedProcess(cmd, 0, json.dumps(data), "")


@pytest.mark.parametrize("action", ["write", "patch", "commit", "refactor", "update", "apply_code_patch"])
def test_b1_high_risk_actions_require_signed_approval(action: str) -> None:
    """B1: HIGH-risk mutative actions must not pass is_allowed() without signed approval."""
    gate = VerificationGate(":memory:")
    try:
        task = {"execution_id": f"exec-{action}", "action": action}
        assert gate.evaluate_task(task) == RiskLevel.HIGH
        assert gate.is_allowed(task) is False
    finally:
        gate._conn.close()


def test_b6_second_order_toctou_resource_mutation_between_approval_and_commit(
    pinned_authority: ec.EllipticCurvePrivateKey,
    tmp_path: Path,
) -> None:
    """B6 (I_2.2): Mutating or replacing the target resource between approval and commit must fail closed."""
    target_file = tmp_path / "protected_config.json"
    initial_bytes = b'{"mode":"safe","limit":10}\n'
    target_file.write_bytes(initial_bytes)
    initial_digest = hashlib.sha256(initial_bytes).hexdigest()

    task: dict[str, object] = {
        "execution_id": "exec-b6-toctou-001",
        "action": "deploy_config",
        "is_mutative": True,
        "target_path": str(target_file),
        "pre_state_digest": initial_digest,
    }

    gate = VerificationGate(str(tmp_path / "gate.db"))
    try:
        with patch.object(
            hardware.subprocess,
            "run",
            side_effect=lambda cmd, **kw: _software_sign_helper(pinned_authority, cmd, **kw),
        ):
            assert gate.enforce_biometric_sign_off("exec-b6-toctou-001", "deploy_config", "Approve", task_payload=task)

        # Immediately after approval, pre-state matches -> allowed
        assert gate.is_allowed(task) is True

        # Adversarial TOCTOU: another process alters target_file before execute_once commits
        target_file.write_bytes(b'{"mode":"tampered_in_flight","limit":999999}\n')

        assert gate.is_allowed(task) is False
        effect_ran = False

        def mutating_effect() -> str:
            nonlocal effect_ran
            effect_ran = True
            return "COMMITTED"

        with pytest.raises(PermissionError, match="approval"):
            gate.execute_once(task, mutating_effect)
        assert effect_ran is False
    finally:
        gate._conn.close()


def test_b6_symlink_swap_rejected_by_o_nofollow(
    pinned_authority: ec.EllipticCurvePrivateKey,
    tmp_path: Path,
) -> None:
    """B6 (INV_C5_FS_DESCRIPTOR_NOFOLLOW): Replacing target_path with a symlink after signing must fail closed."""
    real_file = tmp_path / "real.txt"
    real_bytes = b"canonical-content"
    real_file.write_bytes(real_bytes)
    digest = hashlib.sha256(real_bytes).hexdigest()

    target_path = tmp_path / "guarded.txt"
    target_path.write_bytes(real_bytes)

    task: dict[str, object] = {
        "execution_id": "exec-b6-symlink-002",
        "action": "deploy_config",
        "is_mutative": True,
        "target_path": str(target_path),
        "pre_state_digest": digest,
    }

    gate = VerificationGate(str(tmp_path / "gate_symlink.db"))
    try:
        with patch.object(
            hardware.subprocess,
            "run",
            side_effect=lambda cmd, **kw: _software_sign_helper(pinned_authority, cmd, **kw),
        ):
            assert gate.enforce_biometric_sign_off("exec-b6-symlink-002", "deploy_config", "Approve", task_payload=task)

        assert gate.is_allowed(task) is True

        # Swap target_path with a symlink pointing to a file with the exact same bytes
        target_path.unlink()
        target_path.symlink_to(real_file)

        assert gate.is_allowed(task) is False
    finally:
        gate._conn.close()


class _AsyncSqliteAdapter:
    """Minimal async wrapper over sqlite3 for deterministic ReplayKernel testing."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> _AsyncCursorContext:
        return _AsyncCursorContext(self._conn, sql, params)


class _AsyncCursorContext:
    def __init__(self, conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> None:
        self._conn = conn
        self._sql = sql
        self._params = params
        self._cursor: sqlite3.Cursor | None = None

    async def __aenter__(self) -> _AsyncCursorContext:
        await asyncio.sleep(0)
        self._cursor = self._conn.execute(self._sql, self._params)
        self._conn.commit()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._cursor is not None:
            self._cursor.close()

    def __await__(self) -> Any:
        async def _run() -> sqlite3.Cursor:
            await asyncio.sleep(0)
            cur = self._conn.execute(self._sql, self._params)
            self._conn.commit()
            return cur

        return _run().__await__()

    async def fetchone(self) -> Any:
        await asyncio.sleep(0)
        assert self._cursor is not None
        return self._cursor.fetchone()


def test_b4_replay_kernel_serializes_concurrent_admissions_and_verifies_proposal() -> None:
    """B4: Concurrent admit_event calls must form a linear parent_hash chain and reject phantom proposals."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE model_proposals (
            proposal_hash TEXT PRIMARY KEY,
            provider TEXT,
            model TEXT,
            prompt TEXT,
            params_json TEXT,
            output TEXT,
            context_hash TEXT,
            created_at INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE ledger_events (
            sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_hash TEXT UNIQUE,
            parent_hash TEXT,
            kind TEXT,
            payload_json TEXT,
            source_proposal_hash TEXT,
            policy_version TEXT,
            created_at INTEGER
        )
        """
    )

    kernel = ReplayKernel(_AsyncSqliteAdapter(conn), policy_version="v1.0")

    async def _scenario() -> None:
        # 1. Phantom source_proposal_hash must be rejected with EpistemicHalt
        with pytest.raises(EpistemicHalt, match="inexistente"):
            await kernel.admit_event(
                kind="STATE_MUTATION",
                payload={"x": 1},
                source_proposal_hash="deadbeef" * 8,
            )

        # 2. Registered proposal must be accepted
        prop_hash = await kernel.propose_model_output(
            provider="local",
            model="test-model",
            prompt="hello",
            params={"temperature": 0},
            output="world",
            context_hash="00" * 32,
        )

        # 3. Concurrent admissions must serialize without parent_hash forking
        await asyncio.gather(
            kernel.admit_event(kind="EVT_1", payload={"seq": 1}, source_proposal_hash=prop_hash),
            kernel.admit_event(kind="EVT_2", payload={"seq": 2}, source_proposal_hash=prop_hash),
            kernel.admit_event(kind="EVT_3", payload={"seq": 3}, source_proposal_hash=prop_hash),
        )

    asyncio.run(_scenario())

    rows = conn.execute("SELECT event_hash, parent_hash FROM ledger_events ORDER BY sequence_id ASC").fetchall()
    assert len(rows) == 3
    assert rows[0][1] == "GENESIS"
    assert rows[1][1] == rows[0][0]
    assert rows[2][1] == rows[1][0]
    conn.close()


def test_b5_mcp_lifecycle_re_registration_unlinks_replaced_ephemeral_script(tmp_path: Path) -> None:
    """B5: Re-registering the same server_name with a new script_path must unlink the old script first."""
    manager = McpLifecycleManager(str(tmp_path / "causal_gate.db"))
    first_script = tmp_path / "mcp_first_instance.py"
    second_script = tmp_path / "mcp_second_instance.py"
    first_script.write_text("# first ephemeral instance\n")
    second_script.write_text("# second ephemeral instance\n")

    contract = McpCandidateContract("dup_server", "dup_tool", "Duplicate registration test")
    res1 = manager.register_mcp(contract, str(first_script), scope="EPH_EPHEMERAL")
    assert res1["status"] == "SUCCESS"
    assert first_script.exists()

    res2 = manager.register_mcp(contract, str(second_script), scope="EPH_EPHEMERAL")
    assert res2["status"] == "SUCCESS"
    # First script must not be orphaned on disk when replaced
    assert not first_script.exists()
    assert second_script.exists()

    assert manager.detonate_mcp("dup_server") is True
    assert not second_script.exists()


def test_third_order_global_gate_post_merge_identity_preservation(
    pinned_authority: ec.EllipticCurvePrivateKey,
    tmp_path: Path,
) -> None:
    """3rd-Order Invariant: Execute(a) => H(a) == H(a_verified_post_merge) ^ Authorized(a)."""
    merged_artifact = tmp_path / "merged_release_bundle.tar"
    verified_bytes = b"post-merge-verified-artifact-v2"
    merged_artifact.write_bytes(verified_bytes)
    verified_digest = hashlib.sha256(verified_bytes).hexdigest()

    task: dict[str, object] = {
        "execution_id": "exec-3rd-order-001",
        "action": "deploy_merged_bundle",
        "is_mutative": True,
        "executed_artifact_path": str(merged_artifact),
        "verified_post_merge_digest": verified_digest,
    }

    gate = VerificationGate(str(tmp_path / "gate_3rd.db"))
    try:
        with patch.object(
            hardware.subprocess,
            "run",
            side_effect=lambda cmd, **kw: _software_sign_helper(pinned_authority, cmd, **kw),
        ):
            assert gate.enforce_biometric_sign_off(
                "exec-3rd-order-001", "deploy_merged_bundle", "Approve Post-Merge", task_payload=task
            )

        # 1. Valid post-merge tree and matching artifact digest -> allowed
        assert (
            gate.verify_global_gate_post_merge(
                task,
                executed_artifact_path=merged_artifact,
                verified_post_merge_digest=verified_digest,
                is_post_merge_tree=True,
            )
            is True
        )

        # 2. Pre-merge isolated branch check -> rejected even with valid signature and digest
        assert (
            gate.verify_global_gate_post_merge(
                task,
                executed_artifact_path=merged_artifact,
                verified_post_merge_digest=verified_digest,
                is_post_merge_tree=False,
            )
            is False
        )

        # 3. Post-verification swap of executed artifact -> rejected by both GlobalGate and execute_once
        merged_artifact.write_bytes(b"unverified-tampered-post-merge-artifact")
        assert (
            gate.verify_global_gate_post_merge(
                task,
                executed_artifact_path=merged_artifact,
                verified_post_merge_digest=verified_digest,
                is_post_merge_tree=True,
            )
            is False
        )
        with pytest.raises(PermissionError, match="approval"):
            gate.execute_once(task, lambda: "DEPLOYED")
    finally:
        gate._conn.close()


def test_o12_verifier_escape_and_scope_isolation_enforced(tmp_path: Path) -> None:
    """O12 (Verifier Escape): Verifier must be isolated from generator write scope, TCB secrets, and writable oracles."""
    gen_dir = tmp_path / "generator_workspace"
    ver_dir = tmp_path / "verifier_snapshot"
    tcb_dir = tmp_path / "tcb_secrets"
    oracle_dir = tmp_path / "immutable_oracles"
    for d in (gen_dir, ver_dir, tcb_dir, oracle_dir):
        d.mkdir()

    oracle_file = oracle_dir / "test_suite.bundle"
    oracle_bytes = b"immutable-independent-oracle-v1"
    oracle_file.write_bytes(oracle_bytes)
    oracle_file.chmod(0o400)
    oracle_digest = hashlib.sha256(oracle_bytes).hexdigest()

    try:
        # 1. Clean disjoint scopes + read-only oracle (0400) + clean env -> accepted
        assert (
            VerificationGate.verify_verifier_isolation(
                generator_write_paths=[gen_dir],
                verifier_read_paths=[ver_dir],
                tcb_secret_paths=[tcb_dir],
                oracle_path=oracle_file,
                expected_oracle_digest=oracle_digest,
                verifier_env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
                require_readonly_oracle=True,
            )
            is True
        )

        # 2. Generator write scope overlaps verifier read scope -> rejected (C5-07)
        assert (
            VerificationGate.verify_verifier_isolation(
                generator_write_paths=[gen_dir, ver_dir],
                verifier_read_paths=[ver_dir],
                tcb_secret_paths=[tcb_dir],
                oracle_path=oracle_file,
                expected_oracle_digest=oracle_digest,
            )
            is False
        )

        # 3. Verifier attempts to read TCB secrets directory -> rejected (O12 escape)
        assert (
            VerificationGate.verify_verifier_isolation(
                generator_write_paths=[gen_dir],
                verifier_read_paths=[ver_dir, tcb_dir / "enclave_key.pem"],
                tcb_secret_paths=[tcb_dir],
                oracle_path=oracle_file,
                expected_oracle_digest=oracle_digest,
            )
            is False
        )

        # 4. Dynamic library injection in verifier env (DYLD_INSERT_LIBRARIES) -> rejected (O12)
        assert (
            VerificationGate.verify_verifier_isolation(
                generator_write_paths=[gen_dir],
                verifier_read_paths=[ver_dir],
                tcb_secret_paths=[tcb_dir],
                oracle_path=oracle_file,
                expected_oracle_digest=oracle_digest,
                verifier_env={"DYLD_INSERT_LIBRARIES": "/tmp/evil.dylib"},
            )
            is False
        )

        # 5. Writable oracle file (0600) when require_readonly_oracle=True -> rejected
        oracle_file.chmod(0o600)
        assert (
            VerificationGate.verify_verifier_isolation(
                generator_write_paths=[gen_dir],
                verifier_read_paths=[ver_dir],
                tcb_secret_paths=[tcb_dir],
                oracle_path=oracle_file,
                expected_oracle_digest=oracle_digest,
                require_readonly_oracle=True,
            )
            is False
        )
    finally:
        oracle_file.chmod(0o600)
