"""Lot 1: real source modules, synthetic credentials and temporary evidence."""

import base64
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from babylon60.transducers.c5_mail_transducer import C5MailTransducer

ROOT = Path(__file__).absolute().parents[1]
TOKEN = "SYNTHETIC_LOT1_CREDENTIAL"


def load_source(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def attestation():
    return load_source("tools/tamkarum_attestation_engine.py", "lot1_attestation_fixture")


@pytest.mark.parametrize("kind", ["empty_stderr", "token_stderr", "generic", "bad_response", "http_failure"])
def test_mail_never_returns_credential_or_command(monkeypatch, kind):
    def run(cmd, **kwargs):
        if kind in {"empty_stderr", "token_stderr"}:
            raise subprocess.CalledProcessError(7, cmd, stderr="" if kind == "empty_stderr" else TOKEN)
        if kind == "generic":
            raise RuntimeError(f"Authorization: Bearer {TOKEN}; argv={cmd!r}")
        if kind == "bad_response":
            return SimpleNamespace(stdout=TOKEN)
        return SimpleNamespace(stdout=json.dumps({"message": f"Authorization: Bearer {TOKEN}"}) + "\n403")

    monkeypatch.setattr(subprocess, "run", run)
    result = C5MailTransducer(TOKEN).dispatch(["fixture@example.invalid"], "fixture", "fixture")
    rendered = json.dumps(result)
    assert TOKEN not in rendered
    assert "Authorization" not in rendered
    assert "curl" not in rendered
    assert result["status"] in {"ERROR", "FAILED"}
    assert result["code"]


def test_mail_no_key_and_success_preserve_expected_results(monkeypatch):
    monkeypatch.setattr(C5MailTransducer, "_get_keychain_secret", staticmethod(lambda: ""))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("No key must not dispatch"))
    assert C5MailTransducer().dispatch([], "", "")["code"] == "NO_API_KEY"
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: SimpleNamespace(stdout='{"id":"fixture-id"}\n200'))
    assert C5MailTransducer(TOKEN).dispatch([], "", "") == {
        "status": "DELIVERED",
        "id": "fixture-id",
        "http_code": 200,
    }


def canonical(value, *, allow_nan=False):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=allow_nan).encode()


def sign_statement(body, key, *, allow_nan=False):
    result = copy.deepcopy(body)
    signature = key.sign(b"BABYLON60:TAMKARUM:ATTESTATION:v2\0" + canonical(body, allow_nan=allow_nan))
    result["signature"] = {"algorithm": "Ed25519", "value": base64.b64encode(signature).decode()}
    return result


@pytest.fixture
def signed_evidence(tmp_path):
    paths = {name: tmp_path / f"{name}.json" for name in ["outreach_manifest", "social_calendar", "compliance_pack"]}
    for name, path in paths.items():
        path.write_text(
            json.dumps(
                {"global_consolidated_merkle_root": "a" * 64} if name == "outreach_manifest" else {"fixture": name}
            )
        )
    payload = {
        "git_commit": "b" * 40,
        "topology_sha256": "c" * 64,
        "outreach_root": "a" * 64,
        "evidence_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()},
    }
    payload["compound_attestation_hash"] = hashlib.sha256(
        b"BABYLON60:TAMKARUM:PAYLOAD:v2\0" + canonical(payload)
    ).hexdigest()
    body = {"header": {"schema": "tamkarum-evidence/v2", "algorithm": "Ed25519"}, "payload": payload}
    key = Ed25519PrivateKey.generate()
    path = tmp_path / "statement.json"
    path.write_text(json.dumps(sign_statement(body, key)))
    return SimpleNamespace(paths=paths, body=body, key=key, public=key.public_key().public_bytes_raw(), path=path)


def verify(module, fixture, **overrides):
    options = dict(
        statement_path=fixture.path,
        trusted_public_key=fixture.public,
        evidence_paths=fixture.paths,
        expected_commit="b" * 40,
        expected_topology_sha256="c" * 64,
    )
    options.update(overrides)
    return module.verify_attestation(**options)


def test_legacy_editable_self_checksum_is_not_authentication(attestation, tmp_path, monkeypatch):
    payload = {
        "git_commit": "arbitrary-edited-value",
        "agent_topology": {"topology_sha256": "t"},
        "outreach_campaigns": {"global_merkle_root": "o"},
        "social_dissemination": {"calendar_sha256": "c"},
        "eu_ai_act_compliance": {"evidence_pack_sha256": "e"},
    }
    payload["compound_attestation_hash"] = hashlib.sha256(b"arbitrary-edited-value:t:o:c:e").hexdigest()
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps({"payload": payload}))
    monkeypatch.setattr(attestation, "ATTESTATION_STATEMENT_PATH", path)
    assert not attestation.verify_attestation()


def test_authorized_signed_current_evidence_verifies(attestation, signed_evidence, capsys):
    assert verify(attestation, signed_evidence)
    output = capsys.readouterr().out
    assert "100%" not in output
    assert "hardware" not in output.lower()


@pytest.mark.parametrize("name", ["outreach_manifest", "social_calendar", "compliance_pack"])
@pytest.mark.parametrize("change", ["modify", "delete"])
def test_stale_or_missing_evidence_is_rejected(attestation, signed_evidence, name, change):
    path = signed_evidence.paths[name]
    path.write_text('{"changed":true}') if change == "modify" else path.unlink()
    assert not verify(attestation, signed_evidence)


@pytest.mark.parametrize(
    "change",
    [
        "untrusted_key",
        "missing_key",
        "unsigned",
        "bad_signature",
        "commit",
        "topology",
        "outreach_root",
        "schema",
        "edited_rehashed",
    ],
)
def test_attestation_rejects_authentication_or_state_mismatch(attestation, signed_evidence, change):
    fixture = signed_evidence
    body = copy.deepcopy(fixture.body)
    options: dict[str, bytes | str | None] = {}
    if change == "untrusted_key":
        options["trusted_public_key"] = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
    elif change == "missing_key":
        options["trusted_public_key"] = None
    elif change == "commit":
        options["expected_commit"] = "d" * 40
    elif change == "topology":
        options["expected_topology_sha256"] = "d" * 64
    elif change == "outreach_root":
        body["payload"]["outreach_root"] = "d" * 64
        value = body["payload"].pop("compound_attestation_hash")
        assert value
        body["payload"]["compound_attestation_hash"] = hashlib.sha256(
            b"BABYLON60:TAMKARUM:PAYLOAD:v2\0" + canonical(body["payload"])
        ).hexdigest()
        fixture.path.write_text(json.dumps(sign_statement(body, fixture.key)))
    elif change == "schema":
        body["header"]["schema"] = "unrecognized/v0"
        fixture.path.write_text(json.dumps(sign_statement(body, fixture.key)))
    else:
        document = json.loads(fixture.path.read_text())
        if change == "unsigned":
            del document["signature"]
        elif change == "bad_signature":
            document["signature"]["value"] = base64.b64encode(b"0" * 64).decode()
        else:
            document["payload"]["git_commit"] = "d" * 40
            document["payload"].pop("compound_attestation_hash")
            document["payload"]["compound_attestation_hash"] = hashlib.sha256(
                b"BABYLON60:TAMKARUM:PAYLOAD:v2\0" + canonical(document["payload"])
            ).hexdigest()
        fixture.path.write_text(json.dumps(document))
    assert not verify(attestation, fixture, **options)


def test_duplicate_json_keys_are_rejected_even_with_matching_effective_signature(attestation, signed_evidence):
    document = json.loads(signed_evidence.path.read_text())
    encoded = json.dumps(document)
    signed_evidence.path.write_text('{"payload":{},' + encoded[1:])
    assert not verify(attestation, signed_evidence)


def test_nonfinite_signed_json_is_rejected(attestation, signed_evidence):
    body = copy.deepcopy(signed_evidence.body)
    body["payload"]["unexpected"] = float("nan")
    signed_evidence.path.write_text(json.dumps(sign_statement(body, signed_evidence.key, allow_nan=True)))
    assert not verify(attestation, signed_evidence)


@pytest.mark.parametrize("content", ["not-json", "[]", "null", '{"header":[],"payload":{}}'])
def test_malformed_statement_rejects_without_raising(attestation, signed_evidence, content):
    signed_evidence.path.write_text(content)
    assert not verify(attestation, signed_evidence)


def test_cli_failure_returns_nonzero(attestation, tmp_path, monkeypatch):
    path = tmp_path / "bad.json"
    path.write_text('{"payload":{}}')
    monkeypatch.setattr(attestation, "ATTESTATION_STATEMENT_PATH", path)
    monkeypatch.setattr(sys, "argv", ["tamkarum", "--verify"])
    assert attestation.main() == 1


def test_cli_accepts_explicit_trusted_fixture(attestation, signed_evidence, monkeypatch, tmp_path):
    key_path = tmp_path / "public.raw"
    key_path.write_bytes(signed_evidence.public)
    args = [
        "tamkarum",
        "--verify",
        "--statement",
        str(signed_evidence.path),
        "--trusted-key",
        str(key_path),
        "--expected-commit",
        "b" * 40,
        "--expected-topology-sha256",
        "c" * 64,
    ]
    for name, path in signed_evidence.paths.items():
        args.extend(["--" + name.replace("_", "-"), str(path)])
    monkeypatch.setattr(sys, "argv", args)
    assert attestation.main() == 0


@pytest.mark.parametrize(
    "flag",
    [
        "--statement",
        "--trusted-key",
        "--outreach-manifest",
        "--social-calendar",
        "--compliance-pack",
        "--expected-commit",
        "--expected-topology-sha256",
    ],
)
def test_emit_rejects_verify_only_options_before_writing(attestation, monkeypatch, flag):
    monkeypatch.setattr(attestation, "generate_attestation_statement", lambda: pytest.fail("Must not emit"))
    monkeypatch.setattr(sys, "argv", ["tamkarum", "--emit", flag, "unused-fixture"])
    with pytest.raises(SystemExit) as error:
        attestation.main()
    assert error.value.code == 2


def test_unsigned_emitter_labels_scope_and_uses_only_fixtures(attestation, signed_evidence, monkeypatch, capsys):
    fixture = signed_evidence
    monkeypatch.setattr(attestation, "OUTREACH_MANIFEST", fixture.paths["outreach_manifest"])
    monkeypatch.setattr(attestation, "SOCIAL_CALENDAR", fixture.paths["social_calendar"])
    monkeypatch.setattr(attestation, "COMPLIANCE_PACK", fixture.paths["compliance_pack"])
    monkeypatch.setattr(attestation, "ATTESTATION_STATEMENT_PATH", fixture.path)
    monkeypatch.setattr(attestation, "get_git_head_commit", lambda: "b" * 40)
    monkeypatch.setattr(attestation, "compute_topology_sha256", lambda: "c" * 64)
    document = attestation.generate_attestation_statement()
    assert document["header"] == {"schema": "tamkarum-evidence/v2", "algorithm": "UNSIGNED"}
    assert "signature" not in document
    assert not verify(attestation, fixture)
    output = capsys.readouterr().out
    assert "UNSIGNED" in output and "100%" not in output


def test_default_current_state_fails_when_git_lookup_fails(attestation, signed_evidence, monkeypatch):
    monkeypatch.setattr(attestation, "get_git_head_commit", lambda: "")
    monkeypatch.setattr(attestation, "compute_topology_sha256", lambda: "c" * 64)
    assert not verify(attestation, signed_evidence, expected_commit=None, expected_topology_sha256=None)
