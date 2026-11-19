"""Regresión: ambos motores (Jinja2 y fallback stdlib) deben escapar datos del ledger."""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "01_KISH_ENGINE"))
from babylon60.compliance_exporter.template_engine import ComplianceTemplateEngine  # noqa: E402

PAYLOAD = '<script>alert(1)</script>"><img src=x onerror=1>'


def _cert() -> dict[str, object]:
    keys = [
        "title",
        "compliance_standard",
        "supervisory_authority",
        "report_id",
        "certificate_id",
        "system_identifier",
        "operator",
        "issued_at",
        "quarantine_status",
        "valid_until",
        "global_merkle_root",
        "legal_disclaimer",
    ]
    cert: dict[str, object] = {k: PAYLOAD for k in keys}
    cert["evidence_verification"] = {
        k: PAYLOAD for k in ["ledger_path", "integrity_verified", "ledger_merkle_root", "evidence_match", "detail"]
    }
    cert["signature"] = {
        k: PAYLOAD for k in ["algorithm", "public_key", "signed_payload_sha256", "signature", "ephemeral"]
    }
    cert["cryptographic_attestation"] = {
        k: PAYLOAD for k in ["fingerprint", "hardware_enclave", "hardware_uuid", "platform"]
    }
    cert["revocation_check"] = {k: PAYLOAD for k in ["status", "check_hash", "revocation_authority"]}
    cert["compliance_matrix"] = {"a": {k: PAYLOAD for k in ["title", "mechanism", "status", "evidence_hash"]}}
    return cert


@pytest.mark.parametrize("force_fallback", [True, False])
def test_html_report_escapes_ledger_data(force_fallback: bool) -> None:
    out = ComplianceTemplateEngine(force_fallback=force_fallback).render_report(_cert())
    body = re.sub(r"<style.*?</style>", "", out, flags=re.S)
    assert "<script>alert" not in body
    assert "<img src=x" not in body
    assert "&lt;script&gt;" in body
