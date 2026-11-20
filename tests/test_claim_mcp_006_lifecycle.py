"""CLAIM-MCP-006 end-to-end silicon suite: single-use broker commit, EffectTx quarantine,
O12/Seatbelt ProcSpawn confinement, and post-SIGKILL decoupled verification.

Automated CI uses an isolated software P-256 key; interactive Secure Enclave + Touch ID
human-presence prompting remains an operator hardware ceremony outside unattended runners.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
from typing import Any, cast

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
import pytest

from babylon60.kernel.mcp_lifecycle_manager import McpLifecycleManager
from babylon60.mcp.cortex_mcp_server import CortexMCPServer
from babylon60.verification.verification_gate import RiskLevel, VerificationGate

SANDBOX_EXEC = "/usr/bin/sandbox-exec"


@pytest.fixture(scope="module")
def native_library() -> Path:
    configured = os.environ.get("BABYLON60_TEST_CAPABILITY_LIBRARY")
    if configured:
        lib = Path(configured).absolute()
        if lib.is_file():
            return lib
    repo_root = Path(__file__).absolute().parents[1]
    ext = "dylib" if sys.platform == "darwin" else ("pyd" if os.name == "nt" else "so")
    default_lib = repo_root / "target" / "debug" / f"libbabylon60.{ext}"
    if default_lib.is_file():
        return default_lib
    pytest.skip("build babylon60_root with --features python to run CLAIM-MCP-006 suite")


def _load_native_module(library: Path) -> Any:
    import importlib.util
    from importlib.machinery import ExtensionFileLoader

    loader = ExtensionFileLoader("_babylon60_mcp", str(library))
    spec = importlib.util.spec_from_file_location("_babylon60_mcp", library, loader=loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _provision_software_p256(monkeypatch: pytest.MonkeyPatch) -> tuple[ec.EllipticCurvePrivateKey, str]:
    key = ec.generate_private_key(ec.SECP256R1())
    pub_hex = (
        key.public_key()
        .public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        .hex()
    )
    monkeypatch.setenv("BABYLON_ENCLAVE_PINNED_PUBKEY", pub_hex)
    return key, pub_hex


def _sign_approval(gate: VerificationGate, task: dict[str, object], key: ec.EllipticCurvePrivateKey) -> None:
    proof = json.dumps(
        {
            "version": 1,
            "task": task,
            "decision": "APPROVED",
            "nonce": secrets.token_hex(32),
            "issued_at": time.time() - 1.0,
            "expires_at": time.time() + 120.0,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    payload = proof.encode("utf-8")
    pub_bytes = key.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    evidence = json.dumps(
        {
            "status": "ATTESTED",
            "causal_hash": hashlib.sha256(payload).hexdigest(),
            "public_key": base64.b64encode(pub_bytes).decode("ascii"),
            "secure_enclave_signature": base64.b64encode(
                key.sign(payload, ec.ECDSA(hashes.SHA256()))
            ).decode("ascii"),
        }
    )
    gate.register_sign_off(str(task["execution_id"]), str(task["action"]), RiskLevel.CRITICAL, "APPROVED")
    ledger_id = gate._conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    with gate._conn:
        gate._conn.execute("INSERT INTO signed_approvals VALUES (?, ?, ?)", (ledger_id, proof, evidence))


def test_broker_issue_with_nonce_and_commit_once_zero_replay_window(native_library: Path) -> None:
    native = _load_native_module(native_library)
    broker = native.McpBroker()
    code_hash = hashlib.sha256(b"claim_mcp_006_tool_v1").digest()
    args = b'{"x":42}'
    scope = "mcp://cortex/detonate_ephemeral_mcp"

    broker.discover("detonate_ephemeral_mcp", code_hash, "ProcSpawn", scope)
    broker.authorize("detonate_ephemeral_mcp", code_hash, "ProcSpawn", scope)

    # Zero nonce is forbidden fail-closed.
    with pytest.raises(PermissionError, match="Zero invocation nonce"):
        broker.issue("detonate_ephemeral_mcp", code_hash, "ProcSpawn", args, scope, None, b"\x00" * 32)

    nonce_1 = hashlib.sha256(b"exec-id-001").digest()
    nonce_2 = hashlib.sha256(b"exec-id-002").digest()
    tok_1 = broker.issue("detonate_ephemeral_mcp", code_hash, "ProcSpawn", args, scope, None, nonce_1)
    tok_2 = broker.issue("detonate_ephemeral_mcp", code_hash, "ProcSpawn", args, scope, None, nonce_2)
    assert bytes(tok_1.token_id) != bytes(tok_2.token_id)

    ev_1 = broker.commit_once(tok_1, "detonate_ephemeral_mcp", code_hash, "ProcSpawn", args, scope)
    assert isinstance(ev_1, bytes) and len(ev_1) == 32

    # Replay of the consumed token OR re-issuance with the consumed nonce is rejected (window == 0).
    with pytest.raises(PermissionError, match="NonceAlreadyConsumed"):
        broker.commit_once(tok_1, "detonate_ephemeral_mcp", code_hash, "ProcSpawn", args, scope)
    with pytest.raises(PermissionError, match="NonceAlreadyConsumed"):
        broker.issue("detonate_ephemeral_mcp", code_hash, "ProcSpawn", args, scope, None, nonce_1)

    # Orthogonal invocation with distinct nonce succeeds independently.
    ev_2 = broker.commit_once(tok_2, "detonate_ephemeral_mcp", code_hash, "ProcSpawn", args, scope)
    assert isinstance(ev_2, bytes) and len(ev_2) == 32 and ev_2 != ev_1


def test_symlink_swap_and_sha256_tamper_abort_effect_tx_without_unlinking_victim(
    tmp_path: Path,
    native_library: Path,
) -> None:
    vault = tmp_path / "vault"
    bomb_root = tmp_path / "bomb_root"
    vault.mkdir()
    bomb_root.mkdir()

    victim = vault / "protected_secret.txt"
    victim_bytes = b"IMMUTABLE_SOVEREIGN_ASSET\n"
    victim.write_bytes(victim_bytes)
    victim_stat_before = victim.stat()

    mgr = McpLifecycleManager(db_path=str(tmp_path / "gate.db"), capability_library=native_library)

    # Vector 1: Symlink swap pointing outside bomb_root -> rejected, victim untouched.
    swapped = bomb_root / "mcp_swapped.py"
    swapped.symlink_to(victim)
    with pytest.raises(PermissionError, match="EffectTx quarantine rejected"):
        mgr._unlink_script(str(swapped), nonce_seed="symlink-attack")
    victim_stat_after = victim.stat()
    assert victim.read_bytes() == victim_bytes
    assert (victim_stat_after.st_dev, victim_stat_after.st_ino) == (
        victim_stat_before.st_dev,
        victim_stat_before.st_ino,
    )

    # Vector 2: Content mutation after SHA-256 witness capture -> rejected before destruction.
    tampered = bomb_root / "mcp_tampered.py"
    original_bytes = b"def run(): return 1\n"
    tampered.write_bytes(original_bytes)
    expected_sha256 = hashlib.sha256(original_bytes).digest()
    tampered.write_bytes(b"def run(): return 999\n")

    with pytest.raises(PermissionError, match="SECURITY_ABORT"):
        mgr._unlink_script(str(tampered), expected_sha256=expected_sha256, nonce_seed="tamper-attack")
    assert tampered.exists()


@pytest.mark.parametrize("bad_var", ["DYLD_INSERT_LIBRARIES", "LD_PRELOAD", "BABYLON_ENCLAVE_PRIVATE_KEY"])
def test_procspawn_rejects_o12_tainted_environment_before_effect(
    tmp_path: Path,
    native_library: Path,
    monkeypatch: pytest.MonkeyPatch,
    bad_var: str,
) -> None:
    key, _ = _provision_software_p256(monkeypatch)
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        causal_gate_path=tmp_path / "gate.db",
        capability_library=native_library,
    )
    call: dict[str, object] = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "detonate_ephemeral_mcp",
            "arguments": {
                "domain_name": "calc_sum",
                "implementation_body": "return {'sum': int(a) + int(b)}",
                "call_arguments": {"a": 2, "b": 3},
            },
            "_meta": {"babylon60/authorization": {"execution_id": f"o12-{bad_var}", "mode": "prepare"}},
        },
    }
    prep_resp = server.process_request(call)
    assert prep_resp is not None
    prep_res = cast(dict[str, object], prep_resp["result"])
    assert prep_res["isError"] is False
    task = cast(dict[str, object], prep_res["approval_task"])
    _sign_approval(server.verification_gate, task, key)

    monkeypatch.setenv(bad_var, "injected-value")
    cast(dict[str, object], call["params"])["_meta"] = {
        "babylon60/authorization": {"execution_id": f"o12-{bad_var}", "mode": "execute"}
    }
    exec_resp = server.process_request(call)
    assert exec_resp is not None
    exec_res = cast(dict[str, object], exec_resp["result"])
    assert exec_res["isError"] is True
    assert "O12 environment contamination rejected" in json.dumps(exec_res)
    # Approval was NOT consumed (table either not yet created or has 0 rows) and ledger remains empty.
    tables = {
        r[0]
        for r in server.verification_gate._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    consumed = (
        server.verification_gate._conn.execute("SELECT count(*) FROM consumed_mcp_effects").fetchone()[0]
        if "consumed_mcp_effects" in tables
        else 0
    )
    assert consumed == 0
    assert server.ledger.verify_integrity() is True
    assert server.ledger.query_events(limit=10) == []


@pytest.mark.skipif(
    sys.platform != "darwin" or not os.path.isfile(SANDBOX_EXEC),
    reason="macOS Seatbelt required for L3 confinement verification",
)
def test_ephemeral_mcp_detonation_links_effect_tx_wal_and_post_sigkill_decoupled_verify(
    tmp_path: Path,
    native_library: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = Path(__file__).absolute().parents[1]
    ledger_db = tmp_path / "ledger.db"
    gate_db = tmp_path / "gate.db"
    bomb_dir = tmp_path / "bomb_workspace"
    bomb_dir.mkdir(mode=0o700)

    priv_key = ec.generate_private_key(ec.SECP256R1())
    priv_pem = priv_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")
    pub_hex = (
        priv_key.public_key()
        .public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        .hex()
    )

    # 1. Subprocess A: Prepare -> Sign -> Execute (commit_once + Seatbelt + EffectTx) -> abrupt SIGKILL.
    worker_code = """
import base64, hashlib, json, os, secrets, signal, sys, time
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from babylon60.mcp.cortex_mcp_server import CortexMCPServer
from babylon60.kernel.mcp_lifecycle_manager import McpLifecycleManager
from babylon60.verification.verification_gate import RiskLevel

ledger_db, gate_db, bomb_dir, lib_path, out_json = sys.argv[1:6]
key = serialization.load_pem_private_key(os.environ["TEST_EPHEMERAL_PRIV_PEM"].encode(), password=None)
del os.environ["TEST_EPHEMERAL_PRIV_PEM"]

# Verify EffectTx WAL persistence directly in bomb_dir as well as full CortexMCPServer dispatch:
mgr = McpLifecycleManager(db_path=gate_db, capability_library=lib_path)
direct_receipt = mgr.synthesize_and_detonate_bomb(
    domain_name="adder_tx",
    implementation_body="return {'total': int(x) + int(y)}",
    call_arguments={"x": 19, "y": 41},
    output_dir=bomb_dir,
)
assert direct_receipt["status"] == "SUCCESS", direct_receipt
assert direct_receipt["self_destruct_verified"] is True, direct_receipt
assert direct_receipt["self_destruct_evidence"]["effect_tx_quarantine"]["protocol"] == "RUST_EFFECT_TX_V2"

server = CortexMCPServer(ledger_path=ledger_db, causal_gate_path=gate_db, capability_library=Path(lib_path))
call = {
    "jsonrpc": "2.0",
    "id": 7,
    "method": "tools/call",
    "params": {
        "name": "detonate_ephemeral_mcp",
        "arguments": {
            "domain_name": "mul_tx",
            "implementation_body": "return {'prod': int(a) * int(b)}",
            "call_arguments": {"a": 6, "b": 10},
        },
        "_meta": {"babylon60/authorization": {"execution_id": "mcp006-sigkill-1", "mode": "prepare"}},
    },
}
prep = server.process_request(call)["result"]
task = prep["approval_task"]
proof = json.dumps(
    {
        "version": 1,
        "task": task,
        "decision": "APPROVED",
        "nonce": secrets.token_hex(32),
        "issued_at": time.time() - 1.0,
        "expires_at": time.time() + 120.0,
    },
    sort_keys=True,
    separators=(",", ":"),
)
payload = proof.encode()
pub = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
evidence = json.dumps(
    {
        "status": "ATTESTED",
        "causal_hash": hashlib.sha256(payload).hexdigest(),
        "public_key": base64.b64encode(pub).decode(),
        "secure_enclave_signature": base64.b64encode(key.sign(payload, ec.ECDSA(hashes.SHA256()))).decode(),
    }
)
server.verification_gate.register_sign_off(task["execution_id"], task["action"], RiskLevel.CRITICAL, "APPROVED")
lid = server.verification_gate._conn.execute("SELECT last_insert_rowid()").fetchone()[0]
with server.verification_gate._conn:
    server.verification_gate._conn.execute("INSERT INTO signed_approvals VALUES (?, ?, ?)", (lid, proof, evidence))

call["params"]["_meta"] = {"babylon60/authorization": {"execution_id": "mcp006-sigkill-1", "mode": "execute"}}
exec_res = server.process_request(call)["result"]
assert exec_res["isError"] is False, exec_res
assert len(exec_res.get("broker_evidence_id", "")) == 64
Path(out_json).write_text(json.dumps({"call": call, "exec_res": exec_res}))
os.kill(os.getpid(), signal.SIGKILL)
"""
    out_json = tmp_path / "worker_out.json"
    env_a = os.environ.copy()
    env_a["PYTHONPATH"] = f"{repo_root}:{repo_root / '01_KISH_ENGINE'}:{repo_root / '02_EDIN_SWARMS'}"
    env_a["BABYLON_ENCLAVE_PINNED_PUBKEY"] = pub_hex
    env_a["BABYLON60_TEST_CAPABILITY_LIBRARY"] = str(native_library)
    env_a["TEST_EPHEMERAL_PRIV_PEM"] = priv_pem
    for bad in ("DYLD_INSERT_LIBRARIES", "DYLD_LIBRARY_PATH", "LD_PRELOAD", "PYTHONINSPECT"):
        env_a.pop(bad, None)

    proc_a = subprocess.run(
        [sys.executable, "-c", worker_code, str(ledger_db), str(gate_db), str(bomb_dir), str(native_library), str(out_json)],
        env=env_a,
        capture_output=True,
        text=True,
    )
    assert proc_a.returncode == -9, f"Expected SIGKILL (-9), got {proc_a.returncode}: {proc_a.stderr}"
    saved = json.loads(out_json.read_text(encoding="utf-8"))
    bomb_payload = json.loads(saved["exec_res"]["content"][0]["text"])
    assert bomb_payload["self_destruct_verified"] is True
    assert bomb_payload["self_destruct_evidence"]["effect_tx_quarantine"]["protocol"] == "RUST_EFFECT_TX_V2"

    # Physical witness 1: EffectTx WAL in bomb_dir recorded AttemptReserved + OutcomeKnown (2 * 154 = 308 bytes)
    # and zero script files remain in bomb_dir or quarantine.
    wal_file = bomb_dir / ".babylon" / "quarantine" / ".effect_wal.bin"
    assert wal_file.is_file()
    assert wal_file.stat().st_size == 308
    assert list(bomb_dir.glob("*.py")) == []
    assert list((bomb_dir / ".babylon" / "quarantine").glob("del_*")) == []

    # 2. Subprocess B (Cold Post-Restart Verification): NO private key present; verifies ledger & rejects replay.
    verifier_code = """
import json, sqlite3, sys
from pathlib import Path
from babylon60.bft.cortex_persist_ledger import CortexPersistLedger
from babylon60.mcp.cortex_mcp_server import CortexMCPServer

ledger_db, gate_db, lib_path, saved_path = sys.argv[1:5]
saved = json.loads(Path(saved_path).read_text())

ledger = CortexPersistLedger(ledger_db)
assert ledger.verify_integrity() is True
events = ledger.query_events(limit=10)
assert len(events) == 1, events

server = CortexMCPServer(ledger_path=ledger_db, causal_gate_path=gate_db, capability_library=Path(lib_path))
replay = server.process_request(saved["call"])["result"]
assert replay["isError"] is True, replay

ro = sqlite3.connect("file:" + ledger_db + "?mode=ro", uri=True)
count_after = ro.execute("SELECT count(*) FROM cortex_ledger WHERE event_type='MCP_BOMB_DETONATED'").fetchone()[0]
assert count_after == 1
print("POST_RESTART_DECOUPLED_OK")
"""
    env_b = {k: v for k, v in env_a.items() if k != "TEST_EPHEMERAL_PRIV_PEM"}
    proc_b = subprocess.run(
        [sys.executable, "-c", verifier_code, str(ledger_db), str(gate_db), str(native_library), str(out_json)],
        env=env_b,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "POST_RESTART_DECOUPLED_OK" in proc_b.stdout

    # 3. Subprocess C (L3_ISOLATION Cut): Confined agent process under Seatbelt cannot mutate or unlink
    # ledger.db or gate.db directly (EPERM), preserving physical (dev, ino, sha256) witnesses.
    ledger_before = (ledger_db.stat().st_dev, ledger_db.stat().st_ino, hashlib.sha256(ledger_db.read_bytes()).hexdigest())
    gate_before = (gate_db.stat().st_dev, gate_db.stat().st_ino, hashlib.sha256(gate_db.read_bytes()).hexdigest())

    protected_subpath = json.dumps(str(tmp_path.resolve()))
    sbpl = (
        "(version 1) (allow default)\n"
        f"(deny file-write* (subpath {protected_subpath}))\n"
    )
    attack_code = """
import os, sys
errors = 0
for target in sys.argv[1:]:
    try:
        with open(target, "ab") as fh:
            fh.write(b"BYPASS")
    except PermissionError:
        errors += 1
    try:
        os.unlink(target)
    except PermissionError:
        errors += 1
assert errors == 4, f"Expected 4 EPERM denials, got {errors}"
print("SEATBELT_CUT_VERIFIED")
"""
    python_bin = shutil.which("python3") or sys.executable
    base = os.path.realpath(sys.base_prefix)
    fw_bin = os.path.join(base, "Resources/Python.app/Contents/MacOS/Python")
    exec_bin = fw_bin if os.path.isfile(fw_bin) else os.path.realpath(python_bin)
    proc_c = subprocess.run(
        [SANDBOX_EXEC, "-p", sbpl, exec_bin, "-c", attack_code, str(ledger_db.resolve()), str(gate_db.resolve())],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "SEATBELT_CUT_VERIFIED" in proc_c.stdout

    ledger_after = (ledger_db.stat().st_dev, ledger_db.stat().st_ino, hashlib.sha256(ledger_db.read_bytes()).hexdigest())
    gate_after = (gate_db.stat().st_dev, gate_db.stat().st_ino, hashlib.sha256(gate_db.read_bytes()).hexdigest())
    assert ledger_after == ledger_before
    assert gate_after == gate_before
