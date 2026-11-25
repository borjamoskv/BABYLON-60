"""Isolated model fixtures and real native-broker admission tests.

Software P-256 fixture keys do not attest Secure Enclave. A native broker test
requires the explicitly selected existing library; missing native coverage skips.
"""

import base64
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import time

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from babylon60.verification.verification_gate import RiskLevel
from tools.babylon_work.effects import ProtectedChecks
from tools.babylon_work.providers import ModelClient, command_warnings, source_excerpt
from tools.babylon_work.runs import Runs
from tools.babylon_work.runtime import Runtime
from tools.babylon_work.workspace import Workspace, WorkspaceError


@pytest.fixture
def workspace(tmp_path):
    return Workspace(tmp_path / "work.sqlite")


def task(workspace):
    return workspace.create({"title": "Encargo real", "prompt": "Redactar una guía breve.", "kind": "document"})


@pytest.fixture
def models(monkeypatch):
    def discover(self):
        self.catalog = [{"id": "ollama", "label": "Fixture local", "status": "ready", "models": ["fixture-model"]}]
        return self.catalog

    monkeypatch.setattr(ModelClient, "discover", discover)
    return ModelClient()


def test_model_context_response_and_no_reasoning_persistence(models, workspace, monkeypatch):
    models.discover()
    requests = []

    def request(url, body=None, **kwargs):
        requests.append((url, body))
        return {
            "done": True,
            "done_reason": "stop",
            "message": {"content": "# Resultado real", "thinking": "PRIVATE"},
            "eval_count": 5,
            "prompt_eval_count": 30,
        }

    monkeypatch.setattr(models, "request", request)
    document, sources, metadata = models.generate(task(workspace), "ollama", "fixture-model", "Sé breve")
    assert document == "# Resultado real\n"
    assert sources[0]["path"] == "README.md"
    assert metadata["usage"] == {"input_tokens": 30, "output_tokens": 5}
    assert "PRIVATE" not in json.dumps([document, sources, metadata])
    assert requests[0][1]["think"] is False
    assert "tools" not in requests[0][1]
    assert "Sé breve" in requests[0][1]["messages"][1]["content"]
    assert requests[0][0] == "http://127.0.0.1:11434/api/chat"


@pytest.mark.parametrize("model", ["unknown", "http://untrusted.example", "../../secrets"])
def test_unknown_model_cannot_select_endpoint(models, workspace, model):
    models.discover()
    with pytest.raises(WorkspaceError, match="no figura disponible"):
        models.generate(task(workspace), "ollama", model, "")


def test_partial_response_does_not_replace_document(models, workspace, monkeypatch):
    models.discover()
    monkeypatch.setattr(
        models, "request", lambda *a, **k: {"done": True, "done_reason": "length", "message": {"content": "Parcial"}}
    )
    current = task(workspace)
    current = workspace.update(current["id"], {"action": "save", "revision": 1, "document": "Original"})
    runs = Runs(workspace)
    job = runs.create(current["id"], current["revision"], "generation", {})
    runs.move(job["id"], "running", "Fixture")
    output, sources, metadata = models.generate(current, "ollama", "fixture-model", "")
    runs.complete_generation(job["id"], output, sources, metadata)
    assert workspace.get(current["id"])["document"] == "Original"
    assert runs.get(job["id"])["state"] == "incomplete"
    assert runs.get(job["id"])["result"]["document"] == "Parcial\n"


def test_retrieval_selects_installation_beyond_file_prefix():
    content = "# Overview\n" + "General context. " * 800 + "\n## Instalación\n\n```bash\nbash install.sh\n```\n"
    excerpt = source_excerpt(content, "Guía de instalación y requisitos")
    assert "bash install.sh" in excerpt
    assert len(excerpt) <= 6500


def test_invented_installation_command_is_retained_for_review(workspace):
    warnings = command_warnings("```bash\npip install babylon60\n```", [{"excerpt": "bash install.sh"}], "instalación")
    assert warnings
    current = task(workspace)
    runs = Runs(workspace)
    job = runs.create(current["id"], 1, "generation", {})
    runs.move(job["id"], "running", "Fixture")
    runs.complete_generation(
        job["id"], "pip install babylon60", [], {"model": "fixture", "complete": True, "warnings": warnings}
    )
    assert runs.get(job["id"])["state"] == "needs_review"
    assert workspace.get(current["id"])["document"] == ""
    assert not command_warnings("```bash\nbash install.sh\n```", [{"excerpt": "bash install.sh"}], "instalación")


def test_generation_preserves_concurrent_edit_and_result(workspace):
    current = task(workspace)
    runs = Runs(workspace)
    job = runs.create(current["id"], current["revision"], "generation", {})
    runs.move(job["id"], "running", "Fixture")
    workspace.update(current["id"], {"action": "save", "revision": 1, "document": "Cambio del usuario"})
    runs.complete_generation(job["id"], "Texto de IA", [], {"model": "fixture", "complete": True})
    assert workspace.get(current["id"])["document"] == "Cambio del usuario"
    assert runs.get(job["id"])["state"] == "conflict"
    assert runs.get(job["id"])["result"]["document"] == "Texto de IA"


def test_running_job_is_not_replayed_after_restart(workspace):
    current = task(workspace)
    runs = Runs(workspace)
    job = runs.create(current["id"], 1, "generation", {})
    runs.move(job["id"], "running", "Fixture")
    recovered = Runs(Workspace(workspace.path))
    recovered.recover()
    assert recovered.get(job["id"])["state"] == "interrupted"
    assert workspace.get(current["id"])["document"] == ""


def test_concurrent_duplicate_job_is_rejected(workspace):
    current = task(workspace)
    runs = Runs(workspace)
    runs.create(current["id"], 1, "generation", {})
    with pytest.raises(WorkspaceError, match="en curso"):
        runs.create(current["id"], 1, "generation", {})


def test_background_runtime_produces_document(models, workspace, monkeypatch):
    monkeypatch.setattr(
        ModelClient,
        "generate",
        lambda *a: ("# Documento generado", [], {"provider": "ollama", "model": "fixture-model", "complete": True}),
    )
    runtime = Runtime(workspace, None)
    try:
        assert runtime.ready.wait(3)
        current = task(workspace)
        job = runtime.start(
            current["id"], {"kind": "generation", "revision": 1, "provider": "ollama", "model": "fixture-model"}
        )
        runtime.worker.submit(lambda: None).result(timeout=3)
        assert runtime.runs.get(job["id"])["state"] == "succeeded"
        assert workspace.get(current["id"])["document"] == "# Documento generado"
        with pytest.raises(WorkspaceError):
            runtime.start(
                current["id"],
                {"kind": "generation", "revision": 2, "provider": "ollama", "model": "fixture-model", "command": "rm"},
            )
    finally:
        runtime.close()


@pytest.fixture
def effects(tmp_path, monkeypatch, workspace):
    selected = os.environ.get("BABYLON60_TEST_CAPABILITY_LIBRARY")
    if not selected:
        pytest.skip("set BABYLON60_TEST_CAPABILITY_LIBRARY for real native-broker coverage")
    private = ec.generate_private_key(ec.SECP256R1())
    public = private.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    monkeypatch.setenv("BABYLON_ENCLAVE_PINNED_PUBKEY", public.hex())
    host = ProtectedChecks(tmp_path / "approvals.sqlite", Path(selected).absolute(), workspace=workspace)
    witness = tmp_path / "witness.txt"
    host.commands["witness"] = {
        "label": "Isolated witness",
        "argv": [sys.executable, "-c", f"from pathlib import Path; Path({str(witness)!r}).write_text('observed')"],
    }
    try:
        yield host, private, witness
    finally:
        host.close()


def signed(host, private, approval, *, age=0):
    issued = time.time() - age
    payload = json.dumps(
        {
            "version": 1,
            "task": approval,
            "decision": "APPROVED",
            "nonce": secrets.token_hex(32),
            "issued_at": issued,
            "expires_at": issued + 300,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    public = private.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    evidence = json.dumps(
        {
            "status": "ATTESTED",
            "success": True,
            "causal_hash": hashlib.sha256(payload).hexdigest(),
            "public_key": base64.b64encode(public).decode(),
            "secure_enclave_signature": base64.b64encode(private.sign(payload, ec.ECDSA(hashes.SHA256()))).decode(),
        }
    )
    gate = host.gate
    gate.register_sign_off(approval["execution_id"], approval["action"], RiskLevel.CRITICAL, "APPROVED")
    ledger_id = gate._conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    with gate._conn:
        gate._conn.execute("INSERT INTO signed_approvals VALUES(?,?,?)", (ledger_id, payload.decode(), evidence))


def test_native_unsigned_and_direct_calls_have_no_effect(effects, workspace):
    host, _, witness = effects
    args, approval = host.prepare("unsigned", task(workspace), "witness")
    for _ in range(110):  # 10 warmups + 100 admission attempts; independent file witness.
        denied = host.execute(args, approval, request_signature=False)
        assert denied["isError"] is True
    with pytest.raises(PermissionError):
        host.run_checks(args)
    assert not witness.exists()


def test_native_signed_effect_observed_once_and_replay_denied(effects, workspace):
    host, private, witness = effects
    args, approval = host.prepare("signed-once", task(workspace), "witness")
    signed(host, private, approval)
    result = host.execute(args, approval, request_signature=False)
    assert result["isError"] is False
    assert result["returncode"] == 0
    assert witness.read_text() == "observed"
    before = witness.stat().st_mtime_ns
    # The native broker also advances its revision after consumption.
    with pytest.raises(WorkspaceError):
        host.execute(args, approval, request_signature=False)
    assert witness.stat().st_mtime_ns == before


def test_signed_arbitrary_command_is_rejected_by_fixed_catalog(effects, workspace):
    host, private, witness = effects
    args, _ = host.prepare("catalog", task(workspace), "witness")
    args["argv"] = ["/bin/sh", "-c", "exit 0"]
    prepared = host.effect_dispatcher.dispatch(
        "work_run_checks", args, {"execution_id": "catalog", "mode": "prepare"}, host.run_checks
    )
    approval = prepared["approval_task"]
    signed(host, private, approval)
    response = host.execute(args, approval, request_signature=False)
    assert response["isError"] is True
    assert not witness.exists()


@pytest.mark.parametrize("mutation", ["expired", "arguments", "revoked"])
def test_native_rejects_expiry_rebinding_and_revocation(effects, workspace, mutation):
    host, private, witness = effects
    args, approval = host.prepare("invalid", task(workspace), "witness")
    signed(host, private, approval, age=400 if mutation == "expired" else 0)
    if mutation == "arguments":
        args = {**args, "task_revision": 777}
        with pytest.raises(WorkspaceError, match="solicitud"):
            host.execute(args, approval, request_signature=False)
    else:
        if mutation == "revoked":
            host.effect_dispatcher.revoke_tool("work_run_checks")
            with pytest.raises(WorkspaceError):
                host.execute(args, approval, request_signature=False)
        else:
            assert host.execute(args, approval, request_signature=False)["isError"] is True
    assert not witness.exists()


def test_missing_trust_key_never_invokes_biometry(effects, workspace, monkeypatch):
    host, _, witness = effects
    host.gate._trusted_key = None
    monkeypatch.setattr(host.gate, "enforce_biometric_sign_off", lambda *a, **k: pytest.fail("Biometry must not run"))
    args, approval = host.prepare("no-pin", task(workspace), "witness")
    with pytest.raises(WorkspaceError, match="PINNED_PUBKEY"):
        host.execute(args, approval)
    assert not witness.exists()


def test_task_changed_after_signature_never_spawns(effects, workspace):
    host, private, witness = effects
    current = task(workspace)
    args, approval = host.prepare("changed-task", current, "witness")
    signed(host, private, approval)
    workspace.update(current["id"], {"action": "save", "revision": 1, "document": "Cambio posterior"})
    response = host.execute(args, approval, request_signature=False)
    assert response["isError"] is True
    assert not witness.exists()
