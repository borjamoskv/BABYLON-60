"""
Unit tests for BABYLON-60 EU AI Act Compliance Exporter
Verifies multi-locale certificate generation, PII/API key sanitization,
evidence hash computation, and Markdown/HTML output formatting.
"""

import json
import os
import tempfile
import pytest
from babylon60.compliance_exporter.eu_ai_act import EUAIActComplianceExporter


@pytest.fixture
def temp_bundle_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "manifest.json")
        sample_manifest = {
            "global_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "agent_id": "test_agent_alpha",
            "api_key": "secret_key_1234567890_do_not_leak",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...\n-----END PRIVATE KEY-----",
            "events_count": 42,
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(sample_manifest, f)
        yield tmpdir


def test_redact_sensitive_data():
    raw_data = {
        "user_email": "operator@company.com",
        "api_key": "secret_token_1234567890",
        "nested": {"aws_key": "<REDACTED_AWS_KEY>", "safe_val": "hello_world"},
    }
    redacted = EUAIActComplianceExporter.redact_sensitive_data(raw_data)
    assert redacted["api_key"] == "[REDACTED_AUDIT_SAFE]"
    assert redacted["nested"]["aws_key"] == "[REDACTED_AWS_AKIA]"
    assert redacted["nested"]["safe_val"] == "hello_world"


def test_generate_certificate(temp_bundle_dir):
    exporter = EUAIActComplianceExporter(artifact_bundle_path=temp_bundle_dir)
    cert = exporter.generate_certificate(system_id="SYS-TEST-99", operator_name="Acme Corp", locale="es")

    assert cert["system_identifier"] == "SYS-TEST-99"
    assert cert["operator"] == "Acme Corp"
    assert "EU-AIA-CERT-" in cert["certificate_id"]
    assert "Article_9_Risk_Management" in cert["articles_compliance"]
    assert "Article_12_Record_Keeping_Logging" in cert["articles_compliance"]
    assert len(cert["articles_compliance"]["Article_9_Risk_Management"]["evidence_hash"]) == 64


def test_export_markdown_and_html(temp_bundle_dir):
    exporter = EUAIActComplianceExporter(artifact_bundle_path=temp_bundle_dir)
    cert = exporter.generate_certificate(system_id="SYS-TEST-99", operator_name="Acme Corp", locale="es")

    with tempfile.TemporaryDirectory() as out_dir:
        md_file = os.path.join(out_dir, "report.md")
        html_file = os.path.join(out_dir, "report.html")

        exporter.export_markdown_report(cert, md_file, locale="es")
        exporter.export_html_report(cert, html_file, locale="es")

        assert os.path.exists(md_file)
        assert os.path.exists(html_file)

        with open(md_file, "r", encoding="utf-8") as f:
            md_content = f.read()
            assert "Conformidad" in md_content or "Certificado" in md_content or "Informe" in md_content
            assert "SYS-TEST-99" in md_content

        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
            assert "<!DOCTYPE html>" in html_content
            assert "SYS-TEST-99" in html_content
            assert "Matriz de Cumplimiento Normativo EU AI Act" in html_content
