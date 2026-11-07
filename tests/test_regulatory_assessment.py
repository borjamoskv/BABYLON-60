"""Adversarial evidence and release verification. Synthetic keys never attest hardware."""

import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time

import blake3
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from babylon60.compliance_exporter.regulatory import (
    BLOCKING_IDS,
    CATALOGUE,
    assess,
    canonical,
    digest,
    evidence_hash,
    load_json,
)
from babylon60.compliance_exporter.regulatory_gate import authorization, verify_receipt
from babylon60.compliance_exporter.regulatory_cli import render
from scripts.guards.verify_regulated_release import verify

ROOT = Path(__file__).absolute().parents[1]


@pytest.fixture
def dossier(tmp_path):
    key = ed25519.Ed25519PrivateKey.generate()
    evidence = tmp_path / "proof.txt"
    evidence.write_text("Test fixture: signed acceptance is not legal or hardware certification.")
    policy = {
        "reviewers": {
            "reviewer-1": {
                "name": "Test accountable reviewer",
                "scopes": ["assessment"],
                "system_ids": ["SYS-1"],
                "public_key_hex": key.public_key().public_bytes_raw().hex(),
            }
        },
        "revoked_reviews": [],
        "revoked_authorizations": [],
    }
    profile = {
        "schema": "babylon60.euai.profile.v1",
        "system_id": "SYS-1",
        "system_version": "1.0",
        "configuration_digest": "ab" * 32,
        "intended_purpose": "Test only",
        "context": "Isolated test",
        "responsible_entity": "Fixture",
        "roles": ["provider"],
        "classification": "high_risk",
        "classification_reason": "Fixture for a regulated release",
    }
    entries = {
        rid: {
            "applicability": "applicable",
            "owner": "Test reviewer",
            "decision": "accepted",
            "evidence": [{"path": "proof.txt", "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest()}],
        }
        for rid in BLOCKING_IDS
    }
    assessment = {
        "schema": "babylon60.euai.assessment.v1",
        "requirements": entries,
        "review": {"statement": {"reviewer": "reviewer-1", "expires_at": int(time.time()) + 3600}},
    }
    statement = assess(profile, assessment, tmp_path, policy)["review_statement"]
    assessment["review"] = {
        "statement": statement,
        "signature": base64.b64encode(key.sign(canonical(statement))).decode(),
    }
    return profile, assessment, policy, tmp_path, key


def test_signed_review_enables_only_defined_gate(dossier):
    p, a, trust, root, _ = dossier
    result = assess(p, a, root, trust)
    assert result["gate_eligible"]
    assert result["review_valid"]
    assert result["legal_conformity"] == "NOT_DETERMINED"
    assert not result["publication_authorized"]
    assert any(r["status"] == "MISSING" for r in result["requirements"] if not r.get("blocking"))


@pytest.mark.parametrize("requirement", BLOCKING_IDS)
def test_every_missing_core_requirement_blocks(dossier, requirement):
    p, a, trust, root, _ = dossier
    del a["requirements"][requirement]
    result = assess(p, a, root, trust)
    assert not result["gate_eligible"]
    assert not result["review_valid"]


@pytest.mark.parametrize(
    "change",
    [
        "evidence",
        "version",
        "configuration",
        "assessment_metadata",
        "role",
        "catalogue",
        "signature",
        "scope",
        "revoked",
        "expired",
        "not_applicable",
        "owner",
        "decision",
    ],
)
def test_changes_and_untrusted_decisions_cannot_authorize(dossier, change):
    p, a, trust, root, _ = dossier
    if change == "evidence":
        (root / "proof.txt").write_text("Changed bytes")
    elif change == "version":
        p["system_version"] = "2"
    elif change == "configuration":
        p["configuration_digest"] = "cd" * 32
    elif change == "assessment_metadata":
        a["context"] = "Changed dossier metadata"
    elif change == "role":
        p["roles"] = ["deployer"]
    elif change == "catalogue":
        a["review"]["statement"]["catalogue_digest"] = "00" * 32
    elif change == "signature":
        a["review"]["signature"] = base64.b64encode(bytes(64)).decode()
    elif change == "scope":
        trust["reviewers"]["reviewer-1"]["system_ids"] = ["OTHER"]
    elif change == "revoked":
        trust["revoked_reviews"] = [digest(a["review"])]
    elif change == "expired":
        a["review"]["statement"]["expires_at"] = 1
    elif change == "not_applicable":
        a["requirements"][BLOCKING_IDS[0]].update(applicability="not_applicable", justification="Shortcut")
    elif change == "owner":
        a["requirements"][BLOCKING_IDS[0]]["owner"] = ""
    elif change == "decision":
        a["requirements"][BLOCKING_IDS[0]]["decision"] = "pending"
    assert not assess(p, a, root, trust)["gate_eligible"]


@pytest.mark.parametrize("classification", [None, "", "unknown", "infrastructure", "not_high_risk"])
def test_unknown_or_nonregulated_profile_cannot_be_promoted(dossier, classification):
    p, a, trust, root, _ = dossier
    p["classification"] = classification
    assert not assess(p, a, root, trust)["gate_eligible"]


def test_diagnostic_generation_does_not_require_review(dossier):
    p, a, trust, root, _ = dossier
    a.pop("review")
    result = assess(p, a, root, trust)
    assert not result["gate_eligible"]
    assert "PENDING_REVIEW" in render(result, "json", "es")


def test_evidence_paths_cannot_escape_or_follow_symlinks(dossier):
    _, _, _, root, _ = dossier
    (root / "link").symlink_to(root / "proof.txt")
    for path in ("../proof.txt", str(root / "proof.txt"), "link", "./proof.txt"):
        with pytest.raises((ValueError, OSError)):
            evidence_hash(root, path)


def test_duplicate_keys_and_floating_metadata_rejected(tmp_path):
    p = tmp_path / "json"
    for data in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1.0}'):
        p.write_text(data)
        with pytest.raises(ValueError):
            load_json(p)


def synthetic_receipt(dossier):
    """Cryptographic fixture only: never evidence of a real Secure Enclave run."""
    profile, assessment, policy, root, _ = dossier
    artifact = root / "image.tar"
    artifact.write_bytes(b"fixture OCI archive")
    key = ec.generate_private_key(ec.SECP256R1())
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    policy.update(
        hardware_public_key_hex=public.hex(),
        hardware_backend={"test_only": True},
        native_validation={
            "status": "VERIFIED",
            "binary_sha256": "11" * 32,
            "evidence_sha256": "22" * 32,
            "backend_digest": digest({"test_only": True}),
        },
        release_profile="eu_ai_act_high_risk",
        release_profile_digest=digest(profile),
    )
    result = assess(profile, assessment, root, policy)
    auth = authorization(
        "authorize-release",
        result,
        commit="ab" * 20,
        artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
        destination="ghcr.io/example/repo",
        run_id="123",
        run_attempt="1",
    )
    envelope = (
        struct.pack(">Q", 1)
        + bytes(32)
        + bytes.fromhex(auth["source_fact_hash"])
        + bytes.fromhex(digest(auth))
        + bytes([0, 0, 2])
    )
    msg = blake3.blake3(envelope, derive_key_context="BABYLON-60::RING0::CAUSAL_ENVELOPE::V1").digest()
    r, s = decode_dss_signature(key.sign(msg, ec.ECDSA(hashes.SHA256())))
    sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    merkle = blake3.blake3(
        envelope + sig + hashlib.sha256(public).digest() + bytes(32),
        derive_key_context="BABYLON-60::L0::MERKLE_NODE::V1",
    ).hexdigest()
    receipt = {
        "schema": "babylon60.euai.receipt.v1",
        "authorization": auth,
        "envelope_hex": envelope.hex(),
        "signature_hex": sig.hex(),
        "public_key_hex": public.hex(),
        "merkle_root": merkle,
        "backend": "apple_secure_enclave",
        "simulated": False,
        "measurement_status": "UNAVAILABLE",
        "source_record": assessment["review"],
        "native_validation": copy.deepcopy(policy["native_validation"]),
    }
    expected = {
        k: auth[k]
        for k in ("action", "profile_digest", "commit", "artifact_sha256", "destination", "run_id", "run_attempt")
    }
    return receipt, policy, expected, artifact


def test_independent_crypto_verifier_with_synthetic_key(dossier):
    receipt, policy, expected, _ = synthetic_receipt(dossier)
    verify_receipt(receipt, policy, expected)


def test_native_validation_cannot_be_relabelled_on_old_receipt(dossier):
    receipt, policy, expected, _ = synthetic_receipt(dossier)
    policy["native_validation"]["binary_sha256"] = "33" * 32
    receipt["native_validation"] = copy.deepcopy(policy["native_validation"])
    with pytest.raises(ValueError, match="different native validation"):
        verify_receipt(receipt, policy, expected)


@pytest.mark.parametrize(
    "field", ["commit", "artifact_sha256", "profile_digest", "destination", "run_id", "run_attempt", "action"]
)
def test_receipt_cannot_be_reused_for_other_release(dossier, field):
    receipt, policy, expected, _ = synthetic_receipt(dossier)
    expected[field] = "OTHER"
    with pytest.raises(ValueError):
        verify_receipt(receipt, policy, expected)


@pytest.mark.parametrize(
    "change", ["mock", "tier", "signature", "key", "expiry", "revoked", "native", "root", "source"]
)
def test_invalid_or_simulated_receipt_rejected(dossier, change):
    receipt, policy, expected, _ = synthetic_receipt(dossier)
    if change == "mock":
        receipt["simulated"] = True
    elif change == "tier":
        receipt["envelope_hex"] = receipt["envelope_hex"][:-2] + "01"
    elif change == "signature":
        receipt["signature_hex"] = "00" * 64
    elif change == "key":
        policy["hardware_public_key_hex"] = "04" + "00" * 64
    elif change == "expiry":
        receipt["authorization"]["expires_at"] = 1
    elif change == "revoked":
        policy["revoked_authorizations"] = [digest(receipt["authorization"])]
    elif change == "native":
        policy["native_validation"]["status"] = "NO_VERIFICADO"
    elif change == "root":
        receipt["merkle_root"] = "00" * 32
    elif change == "source":
        receipt["source_record"]["statement"]["profile_digest"] = "00" * 32
    with pytest.raises(Exception):
        verify_receipt(receipt, policy, expected)


def test_publication_rechecks_actual_archive_and_execution(dossier):
    receipt, policy, _, artifact = synthetic_receipt(dossier)
    env = {
        "GITHUB_SHA": "ab" * 20,
        "GITHUB_REPOSITORY": "Example/Repo",
        "GITHUB_RUN_ID": "123",
        "GITHUB_RUN_ATTEMPT": "1",
    }
    assert "AUTHORIZED" in verify(artifact, policy, receipt, env)
    artifact.write_bytes(b"Rebuilt after approval")
    with pytest.raises(ValueError):
        verify(artifact, policy, receipt, env)
    assert "INFRASTRUCTURE_ONLY" in verify(artifact, {"release_profile": "infrastructure"}, None, env)
    with pytest.raises(ValueError):
        verify(artifact, {}, None, env)


@pytest.mark.parametrize("mode,returncode", [("report", 0), ("assess", 2), ("approve", 2), ("authorize-release", 2)])
def test_incomplete_dossier_keeps_diagnostics_available(tmp_path, mode, returncode):
    for name in ("profile", "assessment"):
        (tmp_path / f"{name}.json").write_text("{}")
    out = tmp_path / "out.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "babylon60.compliance_exporter.eu_ai_act",
            "--mode",
            mode,
            "--profile",
            str(tmp_path / "profile.json"),
            "--assessment",
            str(tmp_path / "assessment.json"),
            "--bundle",
            str(tmp_path),
            "--output",
            str(out),
        ],
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "01_KISH_ENGINE")},
    )
    assert result.returncode == returncode, result.stderr
    assert out.exists() == (mode in {"report", "assess"})


def test_allow_unverified_cannot_bypass_approval(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "babylon60.compliance_exporter.eu_ai_act", "--mode", "approve", "--allow-unverified"],
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "01_KISH_ENGINE")},
    )
    assert result.returncode == 2
    assert b"restricted" in result.stderr


@pytest.mark.parametrize("locale", ["es", "en", "de", "fr", "it"])
def test_article_13_present_in_all_locales_and_outputs(dossier, locale):
    from babylon60.compliance_exporter.i18n import get_translation

    p, a, trust, root, _ = dossier
    result = assess(p, a, root, trust)
    assert "Article_13" in get_translation(locale)["article_titles"]
    for fmt in ("json", "md", "html"):
        assert "A13.instructions" in render(result, fmt, locale)
    assert all(r.get("phase") and r.get("roles") for r in CATALOGUE["requirements"])


def test_html_report_escapes_assessment_metadata(dossier):
    p, a, trust, root, _ = dossier
    a["requirements"][BLOCKING_IDS[0]]["owner"] = '<img src=x onerror="alert(1)">'
    rendered = render(assess(p, a, root, trust), "html", "es")
    assert "<img src=x" not in rendered
    assert "&lt;img" in rendered


def test_native_anchor_is_separate_and_invalid_lineage_never_signs(dossier):
    import sqlite3

    p, a, policy, root, _ = dossier
    binary = Path(os.environ.get("BABYLON60_TEST_GATE_BINARY", ROOT / "target/debug/babylon60_regulatory_gate"))
    if not binary.is_file():
        pytest.skip("Run cargo build --locked --bin babylon60_regulatory_gate for native integration")
    policy_file = root / "policy.json"
    policy_file.write_text(json.dumps(policy))
    ledger = root / "l0.sqlite"

    def call(request):
        return subprocess.run(
            [str(binary), "--policy", str(policy_file), "--ledger", str(ledger)],
            input=canonical(request),
            capture_output=True,
            timeout=10,
        )

    assert call({"mode": "init"}).returncode == 0
    result = assess(p, a, root, policy)
    intent = authorization(
        "approve",
        result,
        commit="ab" * 20,
        artifact_sha256="cd" * 32,
        destination="dossier:SYS-1",
        run_id="123",
        run_attempt="1",
    )
    request = {"mode": "approve", "source_record": a["review"], "authorization": intent}
    rejected = call(request)
    assert rejected.returncode == 2
    assert b"UnanchoredCausalLineage" in rejected.stderr
    with sqlite3.connect(ledger) as conn:
        assert conn.execute("SELECT count(*) FROM l0_anchored_facts").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM l0_causal_ledger").fetchone()[0] == 0
    assert call({"mode": "anchor", "source_record": a["review"]}).returncode == 0
    # Idempotent explicit anchoring; still no approval and no biometric request.
    assert call({"mode": "anchor", "source_record": a["review"]}).returncode == 0
    rejected = call(request)
    assert rejected.returncode == 2 and b"NO_VERIFICADO" in rejected.stderr
    # These checks belong in the native boundary too, before a hardware call.
    for field, value, error in (
        ("unexpected", "value", b"Invalid authorization schema"),
        ("commit", "not-a-commit", b"Invalid commit digest"),
        ("expires_at", 0, b"Authorization binding or validity invalid"),
    ):
        altered = copy.deepcopy(request)
        altered["authorization"][field] = value
        rejected = call(altered)
        assert rejected.returncode == 2 and error in rejected.stderr
    policy["revoked_authorizations"] = [digest(intent)]
    policy_file.write_text(json.dumps(policy))
    rejected = call(request)
    assert rejected.returncode == 2 and b"Authorization revoked" in rejected.stderr
    with sqlite3.connect(ledger) as conn:
        assert conn.execute("SELECT count(*) FROM l0_anchored_facts").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM l0_causal_ledger").fetchone()[0] == 0


def test_native_init_migrates_legacy_unique_fact_ticks_without_changing_facts(dossier):
    import sqlite3

    _, _, policy, root, _ = dossier
    binary = Path(os.environ.get("BABYLON60_TEST_GATE_BINARY", ROOT / "target/debug/babylon60_regulatory_gate"))
    if not binary.is_file():
        pytest.skip("Native binary required")
    ledger = root / "legacy.sqlite"
    schema = (
        (ROOT / "scripts/ring0_l0_schema.sql")
        .read_text()
        .replace("anchored_tick   INTEGER NOT NULL CHECK", "anchored_tick   INTEGER NOT NULL UNIQUE CHECK")
    )
    with sqlite3.connect(ledger) as conn:
        conn.executescript(schema)
        conn.execute("INSERT INTO l0_anchored_facts VALUES(?,0,1,?)", (bytes([1]) * 32, bytes([2]) * 32))
    policy_file = root / "policy.json"
    policy_file.write_text(json.dumps(policy))
    result = subprocess.run(
        [str(binary), "--policy", str(policy_file), "--ledger", str(ledger)],
        input=canonical({"mode": "init"}),
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    with sqlite3.connect(ledger) as conn:
        assert conn.execute("SELECT * FROM l0_anchored_facts").fetchall() == [(bytes([1]) * 32, 0, 1, bytes([2]) * 32)]
        conn.execute("INSERT INTO l0_anchored_facts VALUES(?,0,1,?)", (bytes([3]) * 32, bytes([4]) * 32))
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE l0_anchored_facts SET domain_tag=2")


def test_mock_compiled_binary_refuses_hardware_validation_and_approval(dossier):
    p, a, policy, root, _ = dossier
    binary = os.environ.get("BABYLON60_TEST_MOCK_GATE_BINARY")
    if not binary:
        pytest.skip("CI supplies an independently built mock-enabled binary")
    policy_file = root / "policy.json"
    policy_file.write_text(json.dumps(policy))
    ledger = root / "mock.sqlite"
    args = [binary, "--policy", str(policy_file), "--ledger", str(ledger)]
    for mode in ("init", "anchor"):
        result = subprocess.run(
            args, input=canonical({"mode": mode, "source_record": a["review"]}), capture_output=True
        )
        assert result.returncode == 0, result.stderr
    evaluated = assess(p, a, root, policy)
    intent = authorization(
        "approve",
        evaluated,
        commit="ab" * 20,
        artifact_sha256="cd" * 32,
        destination="dossier:SYS-1",
        run_id="1",
        run_attempt="1",
    )
    for request in (
        {"mode": "approve", "source_record": a["review"], "authorization": intent},
        {"mode": "validate-hardware", "nonce": "00" * 32},
    ):
        result = subprocess.run(args, input=canonical(request), capture_output=True)
        assert result.returncode == 2 and b"Mock-enabled" in result.stderr


def test_preparation_cannot_fall_back_from_unknown_or_missing_regulated_receipt(tmp_path, monkeypatch):
    from scripts.guards.prepare_regulated_release import prepare

    def no_network(*args, **kwargs):
        raise AssertionError("Unexpected network")

    monkeypatch.setattr("urllib.request.OpenerDirector.open", no_network)
    prepare(tmp_path / "infra", {"POLICY_JSON": '{"release_profile":"infrastructure"}'})
    for raw in ("{}", '{"release_profile":"unknown"}', '{"release_profile":"eu_ai_act_high_risk"}'):
        with pytest.raises(ValueError):
            prepare(tmp_path / "regulated", {"POLICY_JSON": raw})


def test_http_redirect_cannot_change_authorization_origin():
    from scripts.guards.prepare_regulated_release import NoRedirect

    with pytest.raises(ValueError):
        NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://other.invalid/")


@pytest.mark.parametrize("locale", ["es", "en", "de", "fr", "it"])
def test_legacy_report_article13_is_rendered_and_never_authorizes(tmp_path, monkeypatch, locale):
    from babylon60.compliance_exporter.eu_ai_act import EUAIActComplianceExporter
    from babylon60.attestation.merkle_anchor import MerkleCausalAnchor

    monkeypatch.setenv("BABYLON60_ALLOW_EPHEMERAL_SIGNING", "1")
    monkeypatch.setattr(MerkleCausalAnchor, "generate_hardware_pcr_quote", lambda *args: {"status": "NO_VERIFICADO"})
    (tmp_path / "manifest.json").write_text(json.dumps({"global_hash": "ab" * 32}))
    exporter = EUAIActComplianceExporter(str(tmp_path))
    cert = exporter.generate_certificate("test", "test", locale=locale)
    assert cert["publication_authorized"] is False and cert["legal_conformity"] == "NOT_DETERMINED"
    title = cert["articles_compliance"]["Article_13_Transparency"]["title"]
    for fmt in ("md", "html"):
        target = tmp_path / f"report.{fmt}"
        method = exporter.export_markdown_report if fmt == "md" else exporter.export_html_report
        method(cert, str(target), locale=locale)
        assert title in target.read_text()
