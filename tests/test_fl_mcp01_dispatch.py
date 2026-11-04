"""Real Cortex dispatcher + independent SQLite reader on disposable fixtures.

Software signing keys used later in this suite do not attest Secure Enclave.
"""

import json
from pathlib import Path
import subprocess
import sys

from babylon60.mcp.cortex_mcp_server import CortexMCPServer

import base64
from itertools import product
import os
import secrets
import time
from typing import cast

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from babylon60.verification.verification_gate import RiskLevel, VerificationGate


def observe(path: Path) -> int:
    """A separate process reads the committed effect, never a dispatcher receipt."""
    code = (
        "import sqlite3,sys,os,json; "
        "c=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True); "
        'n=c.execute("SELECT count(*) FROM cortex_ledger '
        "WHERE event_type='FL_MCP01_WITNESS'\").fetchone()[0]; "
        "s=os.stat(sys.argv[1]); print(json.dumps({'count':n,'device':s.st_dev,'inode':s.st_ino}))"
    )
    observation = json.loads(subprocess.check_output([sys.executable, "-c", code, str(path)], text=True))
    identity = path.stat()
    assert (observation["device"], observation["inode"]) == (identity.st_dev, identity.st_ino)
    return int(observation["count"])


def request(name: str = "bft_append_event") -> dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": name,
            "arguments": {
                "event_type": "FL_MCP01_WITNESS",
                "payload": {"n": 1},
                "cortex_taint": "fl-mcp01-test",
            },
        },
    }


def test_unconfigured_dispatch_cannot_append(tmp_path: Path) -> None:
    path = tmp_path / "ledger.db"
    server = CortexMCPServer(ledger_path=path, causal_gate_path=tmp_path / "gate.db")
    before = observe(path)
    for _ in range(110):  # 10 warmups + 100 admission attempts
        response = server.process_request(request())
    after = observe(path)
    assert after == before, json.dumps({"before": before, "after": after, "response": response})


def test_direct_handler_cannot_bypass_dispatch(tmp_path: Path) -> None:
    server = CortexMCPServer(ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "gate.db")
    arguments = cast(dict[str, object], cast(dict[str, object], request()["params"])["arguments"])
    for _ in range(110):  # 10 warmups + 100 direct attempts
        try:
            server._tool_append_event(arguments)
        except PermissionError:
            pass
    assert observe(tmp_path / "ledger.db") == 0


def test_async_handler_finishes_before_dispatch_returns(tmp_path, native_library, signing_key):
    import asyncio
    import inspect

    class AsyncServer(CortexMCPServer):
        async def _tool_append_event(self, args):
            await asyncio.sleep(0)
            return super()._tool_append_event(args)

    server = AsyncServer(
        ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "gate.db",
        capability_library=native_library,
    )
    call = request()
    sign_task(server.verification_gate, prepare(server, call, "awaited"), signing_key)
    response = result(server, call)
    if inspect.iscoroutine(response):
        response.close()  # Old dispatcher returned an unexecuted coroutine.
    assert isinstance(response, dict)
    assert response["isError"] is False
    assert observe(tmp_path / "ledger.db") == 1
    assert result(server, call)["isError"] is True
    assert observe(tmp_path / "ledger.db") == 1


@pytest.mark.parametrize("failure", ["error", "cancel"])
def test_async_failure_after_effect_stays_unknown_and_consumed(tmp_path, native_library, signing_key, failure):
    import asyncio

    class AsyncFailure(CortexMCPServer):
        async def _tool_append_event(self, args):
            super()._tool_append_event(args)
            await asyncio.sleep(0)
            if failure == "cancel":
                raise asyncio.CancelledError("cancelled after effect")
            raise RuntimeError("error after effect")

    server = AsyncFailure(ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "gate.db", capability_library=native_library)
    call = request()
    sign_task(server.verification_gate, prepare(server, call, "async-failure"), signing_key)
    assert "EFFECT_OUTCOME_UNKNOWN" in json.dumps(result(server, call))
    assert observe(tmp_path / "ledger.db") == 1
    assert result(server, call)["isError"] is True
    assert observe(tmp_path / "ledger.db") == 1


def test_child_tasks_finish_before_policy_and_approval_locks_release(tmp_path, native_library, signing_key):
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from babylon60.bft.cortex_persist_ledger import CortexEvent

    entered, attempting, updated = Event(), Event(), Event()

    class ChildEffect(CortexMCPServer):
        async def _tool_append_event(self, args):
            async def later():
                entered.set()
                for _ in range(2000):
                    if attempting.is_set():
                        break
                    await asyncio.sleep(0.001)
                assert attempting.is_set()
                assert not updated.is_set()
                self.ledger.append_event(CortexEvent(
                    event_type="FL_MCP01_WITNESS", payload={"child": True}, cortex_taint="isolated-async-fixture",
                ))
            asyncio.create_task(later())
            return {"content": [], "isError": False}

    server = ChildEffect(ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "gate.db", capability_library=native_library)
    call = request()
    sign_task(server.verification_gate, prepare(server, call, "child-effect"), signing_key)

    def update():
        assert entered.wait(3)
        attempting.set()
        server.effect_dispatcher.update_external_policy("Disabled", "Disabled")
        updated.set()

    with ThreadPoolExecutor(max_workers=1) as pool:
        worker = pool.submit(update)
        assert result(server, call)["isError"] is False
        assert observe(tmp_path / "ledger.db") == 1
        worker.result(timeout=3)
    assert updated.is_set()


@pytest.mark.parametrize("hop", ["child", "thread", "different_tool", "policy"])
def test_invocation_authority_does_not_transfer(tmp_path, native_library, signing_key, hop):
    import asyncio

    class Attempt(CortexMCPServer):
        async def _tool_append_event(self, args):
            if hop == "child":
                asyncio.create_task(self._tool_append_event(args))
                return {"isError": False}
            if hop == "thread":
                return await asyncio.to_thread(CortexMCPServer._tool_append_event, self, args)
            if hop == "different_tool":
                return self._tool_royal_rumble_dispatch({})
            self.effect_dispatcher.update_external_policy("Enabled", "Enabled")
            return {"isError": False}

    server = Attempt(ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "gate.db", capability_library=native_library)
    call = request()
    sign_task(server.verification_gate, prepare(server, call, "no-transfer"), signing_key)
    assert "EFFECT_OUTCOME_UNKNOWN" in json.dumps(result(server, call))
    assert observe(tmp_path / "ledger.db") == 0
    assert result(server, call)["isError"] is True


def test_copied_context_expires_after_completion(tmp_path, native_library, signing_key):
    from contextvars import copy_context

    saved = []

    class Capturing(CortexMCPServer):
        def _tool_append_event(self, args):
            saved.append(copy_context())
            return super()._tool_append_event(args)

    server = Capturing(ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "gate.db", capability_library=native_library)
    call = request()
    sign_task(server.verification_gate, prepare(server, call, "context-expires"), signing_key)
    assert result(server, call)["isError"] is False
    arguments = cast(dict[str, object], cast(dict[str, object], call["params"])["arguments"])
    with pytest.raises(PermissionError):
        saved[0].run(CortexMCPServer._tool_append_event, server, arguments)
    assert observe(tmp_path / "ledger.db") == 1


def test_unclassified_direct_handler_defaults_to_denied(tmp_path):
    class FutureServer(CortexMCPServer):
        def _tool_future_effect(self, args):
            pytest.fail("unclassified handler body ran")

    server = FutureServer(ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "gate.db")
    with pytest.raises(PermissionError):
        server._tool_future_effect({})


def test_mail_handler_direct_access_is_guarded(tmp_path):
    from babylon60.mcp.mail_integration import BabylonMailIntegration

    mail = BabylonMailIntegration(tmp_path / "mail.db")
    with pytest.raises(PermissionError):
        mail.send({"to": "fixture@example.invalid", "subject": "fixture", "body": "synthetic"})
    with mail.ledger._get_connection() as conn:
        assert conn.execute("SELECT count(*) FROM cortex_ledger").fetchone()[0] == 0


def test_async_direct_handler_requires_its_own_invocation(tmp_path):
    import asyncio

    class AsyncDirect(CortexMCPServer):
        async def _tool_append_event(self, args):
            return super()._tool_append_event(args)

    server = AsyncDirect(ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "gate.db")
    arguments = cast(dict[str, object], cast(dict[str, object], request()["params"])["arguments"])
    with pytest.raises(PermissionError):
        asyncio.run(server._tool_append_event(arguments))
    assert observe(tmp_path / "ledger.db") == 0


def test_existing_application_loop_is_not_reentered_or_consumed(tmp_path, native_library, signing_key):
    import asyncio

    server = make_server(tmp_path, native_library)
    call = request()
    sign_task(server.verification_gate, prepare(server, call, "existing-loop"), signing_key)

    async def attempt():
        return result(server, call)

    assert "DENIED" in json.dumps(asyncio.run(attempt()))
    assert observe(tmp_path / "ledger.db") == 0
    # The unsupported ingress was rejected before durable consumption.
    assert result(server, call)["isError"] is False
    assert observe(tmp_path / "ledger.db") == 1


def test_failed_async_parent_cancels_its_pending_effects(tmp_path, native_library, signing_key):
    import asyncio
    from babylon60.bft.cortex_persist_ledger import CortexEvent

    class CancelPending(CortexMCPServer):
        async def _tool_append_event(self, args):
            async def pending():
                await asyncio.sleep(0.02)
                self.ledger.append_event(CortexEvent(
                    event_type="FL_MCP01_WITNESS", payload={"escaped": True}, cortex_taint="isolated-pending",
                ))
            asyncio.create_task(pending())
            raise RuntimeError("parent failed before child effect")

    server = CancelPending(ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "gate.db", capability_library=native_library)
    call = request()
    sign_task(server.verification_gate, prepare(server, call, "cancel-pending"), signing_key)
    assert "EFFECT_OUTCOME_UNKNOWN" in json.dumps(result(server, call))
    time.sleep(0.04)
    assert observe(tmp_path / "ledger.db") == 0
    assert result(server, call)["isError"] is True


def test_signed_mail_handler_still_records_once(tmp_path, native_library, signing_key):
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db", mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "gate.db", capability_library=native_library,
    )
    call = request("bft_send_sovereign_mail")
    cast(dict[str, object], call["params"])["arguments"] = {
        "to": "fixture@example.invalid", "subject": "local fixture", "body": "synthetic",
    }
    sign_task(server.verification_gate, prepare(server, call, "mail-once"), signing_key)
    assert result(server, call)["isError"] is False
    assert result(server, call)["isError"] is True
    code = "import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute('SELECT count(*) FROM cortex_ledger').fetchone()[0])"
    assert subprocess.check_output([sys.executable, "-c", code, str(tmp_path / "mail.db")]).strip() == b"1"


@pytest.fixture
def signing_key(monkeypatch: pytest.MonkeyPatch) -> ec.EllipticCurvePrivateKey:
    # Isolated test authority. Never presented as a hardware/biometric result.
    key = ec.generate_private_key(ec.SECP256R1())
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    monkeypatch.setenv("BABYLON_ENCLAVE_PINNED_PUBKEY", public.hex())
    return key


@pytest.fixture
def native_library() -> Path:
    value = os.environ.get("BABYLON60_TEST_CAPABILITY_LIBRARY")
    if value is None:
        pytest.skip("build kernel with --features python and set BABYLON60_TEST_CAPABILITY_LIBRARY")
    library = Path(value).absolute()
    assert library.is_file(), library
    return library


def make_server(tmp_path: Path, library: Path) -> CortexMCPServer:
    return CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        causal_gate_path=tmp_path / "gate.db",
        capability_library=library,
    )


def test_skill_proposal_cannot_replace_signed_dispatch_approval(tmp_path, native_library):
    from babylon60.mcp.skills_snapshot import GATEWAY_EXPECTED_AUDIENCE

    server = make_server(tmp_path, native_library)
    skill = server._skills_snapshot.resolve("c5-neural-face-swap-cuadrilla")
    assert skill is not None
    proposal = server._skills_snapshot.propose_skill_effect({
        "skill_id": skill.name, "version": skill.version, "tool_identity_hash": skill.tool_identity_hash,
        "arguments": {"target_path": "workspace://state", "expected_pre_hash": "a" * 64},
        "precondition_snapshot": {"allowed_roots": ["workspace://"], "observed_pre_hash": "a" * 64},
        "credential": {"audience": GATEWAY_EXPECTED_AUDIENCE, "project_id": "fixture", "nonce": "proposal"},
    })
    assert proposal["status"] == "AUTHORIZED"
    capability = proposal["action_capability"]
    call = request()
    call["params"]["_meta"] = {
        "babylon60/authorization": {"execution_id": capability["capability_id"], "mode": "execute"},
    }
    assert result(server, call)["isError"] is True
    assert observe(tmp_path / "ledger.db") == 0


def result(server: CortexMCPServer, call: dict[str, object]) -> dict[str, object]:
    response = server.process_request(call)
    assert response is not None
    return cast(dict[str, object], response["result"])


def prepare(server: CortexMCPServer, call: dict[str, object], execution_id: str) -> dict[str, object]:
    params = cast(dict[str, object], call["params"])
    params["_meta"] = {"babylon60/authorization": {"execution_id": execution_id, "mode": "prepare"}}
    prepared = result(server, call)
    assert prepared.get("isError") is False, prepared
    params["_meta"] = {"babylon60/authorization": {"execution_id": execution_id}}
    return cast(dict[str, object], prepared["approval_task"])


def sign_task(gate: VerificationGate, task: dict[str, object], key: ec.EllipticCurvePrivateKey) -> None:
    # Real P-256 verifier and persisted approval path; no patched authorization methods.
    import hashlib

    proof = json.dumps(
        {
            "version": 1,
            "task": task,
            "decision": "APPROVED",
            "nonce": secrets.token_hex(32),
            "issued_at": time.time() - 1,
            "expires_at": time.time() + 120,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    payload = proof.encode()
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    evidence = json.dumps(
        {
            "status": "ATTESTED",
            "causal_hash": hashlib.sha256(payload).hexdigest(),
            "public_key": base64.b64encode(public).decode(),
            "secure_enclave_signature": base64.b64encode(key.sign(payload, ec.ECDSA(hashes.SHA256()))).decode(),
        }
    )
    gate.register_sign_off(str(task["execution_id"]), str(task["action"]), RiskLevel.CRITICAL, "APPROVED")
    ledger_id = gate._conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    with gate._conn:
        gate._conn.execute("INSERT INTO signed_approvals VALUES (?, ?, ?)", (ledger_id, proof, evidence))


def test_native_signed_effect_and_alias_have_independent_witness(tmp_path, native_library, signing_key):
    server = make_server(tmp_path, native_library)
    call = request("cortex_event_append")
    task = prepare(server, call, "positive")
    assert task["action"] == "mcp:bft_append_event"
    assert observe(tmp_path / "ledger.db") == 0  # preparation never executes
    sign_task(server.verification_gate, task, signing_key)
    assert result(server, call)["isError"] is False
    assert observe(tmp_path / "ledger.db") == 1
    assert result(server, call)["isError"] is True
    assert observe(tmp_path / "ledger.db") == 1  # replay produced no second effect
    consumed = server.verification_gate._conn.execute("SELECT count(*) FROM consumed_mcp_effects").fetchone()[0]
    assert consumed == 1


@pytest.mark.parametrize(
    "vector", ["arguments", "execution_id", "forged_boolean", "wrong_key", "revoked", "aba", "grant_revoked"]
)
def test_denials_preserve_physical_fixture(tmp_path, native_library, signing_key, vector):
    server = make_server(tmp_path, native_library)
    call = request()
    task = prepare(server, call, "deny")
    sign_task(server.verification_gate, task, signing_key)
    params = cast(dict[str, object], call["params"])
    if vector == "arguments":
        cast(dict[str, object], params["arguments"])["payload"] = {"n": 999}
    elif vector == "execution_id":
        params["_meta"] = {"babylon60/authorization": {"execution_id": "different"}}
    elif vector == "forged_boolean":
        params["_meta"] = {"babylon60/authorization": {"execution_id": "deny", "approved": True}}
    elif vector == "wrong_key":
        other = ec.generate_private_key(ec.SECP256R1())
        sign_task(server.verification_gate, task, other)
    elif vector == "revoked":
        server.verification_gate.register_sign_off("deny", "mcp:bft_append_event", RiskLevel.CRITICAL, "REJECTED")
    elif vector == "grant_revoked":
        server.effect_dispatcher.revoke_tool("bft_append_event")
    else:
        server.effect_dispatcher.update_external_policy("Disabled", "Enabled")
        server.effect_dispatcher.update_external_policy("Enabled", "Unconfigured")
    assert result(server, call)["isError"] is True
    assert observe(tmp_path / "ledger.db") == 0


def test_external_policy_matrix_with_signed_calls(tmp_path, native_library, signing_key):
    server = make_server(tmp_path, native_library)
    states = ("Enabled", "Disabled", "Unconfigured")
    effects = 0
    stale_bypasses = 0
    positive = 0
    for index, (f0, g0, f1, g1) in enumerate(product(states, repeat=4)):
        server.effect_dispatcher.update_external_policy(f0, g0)
        call = request()
        cast(dict[str, object], cast(dict[str, object], call["params"])["arguments"])["payload"] = {"n": index}
        task = prepare(server, call, f"matrix-{index}")
        sign_task(server.verification_gate, task, signing_key)
        server.effect_dispatcher.update_external_policy(f1, g1)
        accepted = not result(server, call)["isError"]
        expected = (f0, g0) == (f1, g1) and (f1 == "Enabled" or (f1 == "Unconfigured" and g1 == "Enabled"))
        stale_bypasses += int(accepted and not expected)
        positive += int(accepted and expected)
        assert accepted == expected, (f0, g0, f1, g1)
        effects += int(expected)
        assert observe(tmp_path / "ledger.db") == effects
    assert stale_bypasses == 0
    assert positive == 4


def test_crash_after_consumption_never_replays(tmp_path, native_library, signing_key):
    server = make_server(tmp_path, native_library)
    task = prepare(server, request(), "crash")
    sign_task(server.verification_gate, task, signing_key)
    task_path = tmp_path / "task.json"
    task_path.write_text(json.dumps(task))
    code = (
        "import json,os,sys; from babylon60.verification.verification_gate import VerificationGate; "
        "g=VerificationGate(sys.argv[1]); t=json.load(open(sys.argv[2])); "
        "g.execute_once(t,lambda:os._exit(19))"
    )
    child = subprocess.run([sys.executable, "-c", code, str(tmp_path / "gate.db"), str(task_path)], check=False)
    assert child.returncode == 19
    gate = VerificationGate(str(tmp_path / "gate.db"))
    with pytest.raises(PermissionError, match="already been consumed"):
        gate.execute_once(task, lambda: pytest.fail("replayed effect"))
    assert observe(tmp_path / "ledger.db") == 0
    gate._conn.close()


def test_policy_update_waits_for_actual_handler(tmp_path, native_library, signing_key):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    entered = Event()
    attempting = Event()
    updated = Event()

    class BlockingServer(CortexMCPServer):
        def _tool_append_event(self, args: dict[str, object]) -> dict[str, object]:
            entered.set()
            assert attempting.wait(2)
            assert not updated.wait(0.05)
            return cast(dict[str, object], super()._tool_append_event(args))

    server = BlockingServer(
        ledger_path=tmp_path / "ledger.db",
        causal_gate_path=tmp_path / "gate.db",
        capability_library=native_library,
    )
    call = request()
    sign_task(server.verification_gate, prepare(server, call, "serial"), signing_key)

    def update() -> None:
        assert entered.wait(2)
        attempting.set()
        server.effect_dispatcher.update_external_policy("Disabled", "Disabled")
        updated.set()

    with ThreadPoolExecutor(max_workers=1) as pool:
        worker = pool.submit(update)
        assert result(server, call)["isError"] is False
        worker.result(timeout=3)
    assert updated.is_set()
    assert observe(tmp_path / "ledger.db") == 1
    assert result(server, call)["isError"] is True


def test_stdio_roundtrip_independent_observer(tmp_path, native_library, signing_key):
    import selectors

    child = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "babylon60.mcp.cortex_mcp_server",
            "--ledger",
            str(tmp_path / "ledger.db"),
            "--causal-gate",
            str(tmp_path / "gate.db"),
            "--capability-library",
            str(native_library),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    assert child.stdin is not None and child.stdout is not None
    stdin, stdout = child.stdin, child.stdout

    def exchange(call: dict[str, object]) -> dict[str, object]:
        stdin.write(json.dumps(call) + "\n")
        stdin.flush()
        with selectors.DefaultSelector() as selector:
            selector.register(stdout, selectors.EVENT_READ)
            assert selector.select(10), "stdio dispatcher timed out"
        response = json.loads(stdout.readline())
        return cast(dict[str, object], response["result"])

    gate = None
    try:
        call = request()
        params = cast(dict[str, object], call["params"])
        params["_meta"] = {"babylon60/authorization": {"execution_id": "stdio", "mode": "prepare"}}
        task = cast(dict[str, object], exchange(call)["approval_task"])
        assert observe(tmp_path / "ledger.db") == 0
        gate = VerificationGate(str(tmp_path / "gate.db"))
        sign_task(gate, task, signing_key)
        params["_meta"] = {"babylon60/authorization": {"execution_id": "stdio"}}
        assert exchange(call)["isError"] is False
        assert observe(tmp_path / "ledger.db") == 1
        assert exchange(call)["isError"] is True
        assert observe(tmp_path / "ledger.db") == 1
    finally:
        child.stdin.close()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)
        child.stdout.close()
        if gate is not None:
            gate._conn.close()


def test_handler_failure_is_unknown_not_a_false_denial(tmp_path, native_library, signing_key):
    class FailingServer(CortexMCPServer):
        def _tool_append_event(self, args: dict[str, object]) -> dict[str, object]:
            super()._tool_append_event(args)
            raise ValueError("failure after committed fixture effect")

    server = FailingServer(
        ledger_path=tmp_path / "ledger.db",
        causal_gate_path=tmp_path / "gate.db",
        capability_library=native_library,
    )
    call = request()
    sign_task(server.verification_gate, prepare(server, call, "unknown"), signing_key)
    response = result(server, call)
    assert "EFFECT_OUTCOME_UNKNOWN" in json.dumps(response)
    assert observe(tmp_path / "ledger.db") == 1
    assert result(server, call)["isError"] is True
    assert observe(tmp_path / "ledger.db") == 1


def test_native_availability_cannot_replace_pinned_authority(tmp_path, native_library, monkeypatch):
    monkeypatch.delenv("BABYLON_ENCLAVE_PINNED_PUBKEY", raising=False)
    server = make_server(tmp_path, native_library)
    for _ in range(10):  # warmup
        server.process_request(request())
    for index in range(100):
        server.effect_dispatcher.update_external_policy("Unconfigured", "Enabled")
        call = request()
        prepare(server, call, f"unapproved-{index}")
        assert result(server, call)["isError"] is True
    assert observe(tmp_path / "ledger.db") == 0


# Live hardware acceptance has a single manual entry point, outside pytest
# discovery: tests/manual/hardware_mcp_cycle.py. This suite never prompts.
