"""
Unit tests for BABYLON-60 EU AI Act Compliance Exporter
Verifies multi-locale certificate generation, PII/API key sanitization,
evidence hash computation, and Markdown/HTML output formatting.
"""

import json
import os
import tempfile
from collections.abc import Iterator
import pytest
from babylon60.compliance_exporter.eu_ai_act import EUAIActComplianceExporter


@pytest.fixture
def temp_bundle_dir(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    monkeypatch.setenv("BABYLON60_ALLOW_EPHEMERAL_SIGNING", "1")
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


def test_redact_sensitive_data() -> None:
    raw_data = {
        "user_email": "operator@company.com",
        "api_key": "secret_token_1234567890",
        "nested": {"aws_key": "<REDACTED_AWS_KEY>", "safe_val": "hello_world"},
    }
    redacted = EUAIActComplianceExporter.redact_sensitive_data(raw_data)
    assert redacted["api_key"] == "[REDACTED_AUDIT_SAFE]"
    assert redacted["nested"]["aws_key"] == "[REDACTED_AWS_AKIA]"
    assert redacted["nested"]["safe_val"] == "hello_world"


def test_generate_certificate(temp_bundle_dir: str) -> None:
    exporter = EUAIActComplianceExporter(artifact_bundle_path=temp_bundle_dir)
    cert = exporter.generate_certificate(system_id="SYS-TEST-99", operator_name="Acme Corp", locale="es")

    assert cert["system_identifier"] == "SYS-TEST-99"
    assert cert["operator"] == "Acme Corp"
    assert "EU-AIA-CERT-" in cert["certificate_id"]
    assert "Article_9_Risk_Management" in cert["articles_compliance"]
    assert "Article_12_Record_Keeping_Logging" in cert["articles_compliance"]
    assert "Article_15_Robustness_Cybersecurity" in cert["articles_compliance"]
    assert len(cert["articles_compliance"]["Article_9_Risk_Management"]["evidence_hash"]) == 64
    assert len(cert["articles_compliance"]["Article_15_Robustness_Cybersecurity"]["evidence_hash"]) == 64


def test_export_markdown_and_html(temp_bundle_dir: str) -> None:
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


def test_certificate_lifecycle_and_expiration(temp_bundle_dir: str) -> None:
    """Verifica que el certificado incluye valid_until, hardware_anchor y validación de ciclo de vida."""
    exporter = EUAIActComplianceExporter(artifact_bundle_path=temp_bundle_dir)
    cert = exporter.generate_certificate(
        system_id="SYS-LIFECYCLE-01",
        operator_name="Acme Corp",
        validity_days=30,
    )

    assert "valid_until" in cert
    assert cert["validity_days"] == 30
    assert "hardware_anchor" in cert
    assert cert["hardware_anchor"]["pcr_index"] == "10"
    assert "hardware_uuid" in cert["hardware_anchor"]
    assert cert["revocation"]["status"] == "ACTIVE"

    # Verificación de ciclo de vida activo
    status = EUAIActComplianceExporter.verify_certificate_lifecycle(cert)
    assert status["valid"] is True
    assert status["status"] == "ACTIVE"

    # Simular expiración manipulando valid_until
    expired_cert = dict(cert)
    expired_cert["valid_until"] = "2020-01-01T00:00:00Z"
    status_expired = EUAIActComplianceExporter.verify_certificate_lifecycle(expired_cert)
    assert status_expired["valid"] is False
    assert status_expired["status"] == "EXPIRED"


def test_certificate_revocation(temp_bundle_dir: str) -> None:
    """Verifica el mecanismo de revocación de certificados contra lista CRL."""
    exporter = EUAIActComplianceExporter(artifact_bundle_path=temp_bundle_dir)
    cert = exporter.generate_certificate(system_id="SYS-REVOKE-01", operator_name="Acme Corp")
    cert_id = cert["certificate_id"]

    # Activo sin CRL
    assert EUAIActComplianceExporter.verify_certificate_lifecycle(cert)["valid"] is True

    # Revocar certificado incluyéndolo en la CRL
    crl = [cert_id, "SOME-OTHER-CERT-ID"]
    revocation_check = EUAIActComplianceExporter.verify_certificate_lifecycle(cert, crl=crl)
    assert revocation_check["valid"] is False
    assert revocation_check["status"] == "REVOKED"
    assert cert_id in revocation_check["reason"]


def test_decision_evidence_packet_dep(temp_bundle_dir: str) -> None:
    """Verifica la emisión de un Decision-Evidence Packet (DEP) con prueba de Merkle O(log N)."""
    from babylon60.bft.cortex_persist_ledger import CortexPersistLedger, CortexEvent

    with tempfile.TemporaryDirectory() as tmp_ledger_dir:
        ledger_file = os.path.join(tmp_ledger_dir, "dep_ledger.db")
        ledger = CortexPersistLedger(ledger_file)

        # Inserción de 5 eventos de prueba
        for i in range(1, 6):
            ledger.append_event(
                CortexEvent(
                    event_type="DECISION_ACTION",
                    payload={"action_id": f"act_{i}", "risk_score": 0.05 * i},
                    cortex_taint=f"taint:{i}",
                )
            )

        exporter = EUAIActComplianceExporter(artifact_bundle_path=temp_bundle_dir, ledger_path=ledger_file)
        dep = exporter.create_decision_evidence_packet(
            seq=3,
            decision_data={"action": "APPROVE_LOAN", "amount": 50000, "user_api_key": "secret_123"},
            ledger=ledger,
        )

        assert dep["seq"] == 3
        assert "dep_id" in dep
        assert dep["decision_data"]["user_api_key"] == "[REDACTED_AUDIT_SAFE]"
        assert "merkle_inclusion_proof" in dep
        assert dep["merkle_inclusion_proof"]["total_leaves"] == 5
        assert "hardware_anchor" in dep
        assert "signature" in dep

        # Verificar matemáticamente la prueba de inclusión del DEP
        is_verified = CortexPersistLedger.verify_event_proof(
            dep["merkle_inclusion_proof"],
            dep["global_merkle_root"],
        )
        assert is_verified is True


def test_export_evidence_dossier_includes_article_15(temp_bundle_dir: str) -> None:
    """Verifica que el dossier generado en Markdown exporta formalmente el Artículo 15."""
    exporter = EUAIActComplianceExporter(artifact_bundle_path=temp_bundle_dir)
    cert = exporter.generate_certificate(
        system_id="BABYLON-SVR-01",
        operator_name="Borja Moskv",
        locale="es",
    )
    with tempfile.TemporaryDirectory() as tmp_out:
        dossier_path = os.path.join(tmp_out, "dossier.md")
        exported = exporter.export_markdown_report(cert, dossier_path)
        assert os.path.exists(exported)
        with open(exported, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Art. 15: Precisión, Robustez y Ciberseguridad" in content
        assert "Aislamiento Ring-0 C-ABI" in content


def test_template_engine_jinja_rendering(temp_bundle_dir: str) -> None:
    """Verifica el renderizado desacoplado mediante Jinja2 con componentes modulares."""
    from babylon60.compliance_exporter.template_engine import ComplianceTemplateEngine

    exporter = EUAIActComplianceExporter(artifact_bundle_path=temp_bundle_dir)
    cert = exporter.generate_certificate(system_id="SYS-JINJA-01", operator_name="Acme AI", locale="es")

    engine = ComplianceTemplateEngine()
    assert engine.has_jinja is True

    html_out = engine.render_report(cert, locale="es", theme="dark")
    assert "<!DOCTYPE html>" in html_out
    assert "SYS-JINJA-01" in html_out
    assert "Acme AI" in html_out
    assert "Matriz de Cumplimiento Normativo EU AI Act" in html_out
    assert "Art. 9: Sistema de Gestión de Riesgos" in html_out
    assert "Art. 15: Precisión, Robustez y Ciberseguridad" in html_out
    assert "badge badge-" in html_out
    assert "--accent: #00F0FF" in html_out


def test_template_engine_fallback_rendering(temp_bundle_dir: str) -> None:
    """Verifica el motor de fallback determinista stdlib (string.Template) sin dependencias."""
    from babylon60.compliance_exporter.template_engine import ComplianceTemplateEngine

    exporter = EUAIActComplianceExporter(artifact_bundle_path=temp_bundle_dir)
    cert = exporter.generate_certificate(system_id="SYS-FALLBACK-01", operator_name="Acme AI", locale="es")

    # Forzar fallback para simular entorno sin Jinja2 instalado
    engine = ComplianceTemplateEngine(force_fallback=True)
    assert engine.has_jinja is False

    html_out = engine.render_report(cert, locale="es", theme="dark")
    assert "<!DOCTYPE html>" in html_out
    assert "SYS-FALLBACK-01" in html_out
    assert "Acme AI" in html_out
    assert "Matriz de Cumplimiento Normativo EU AI Act" in html_out
    assert "Art. 9: Sistema de Gestión de Riesgos" in html_out
    assert "Art. 15: Precisión, Robustez y Ciberseguridad" in html_out
    assert "badge badge-" in html_out
    assert "--accent: #00F0FF" in html_out


def test_template_engine_themes_dark_and_legal(temp_bundle_dir: str) -> None:
    """Verifica el soporte para temas visuales: HUD ciberpunk vs. informe imprimible legal."""
    from babylon60.compliance_exporter.template_engine import load_theme_css

    # Carga directa de CSS
    dark_css = load_theme_css("dark")
    legal_css = load_theme_css("legal")
    assert "#0b0f19" in dark_css or "--accent: #00F0FF" in dark_css
    assert "@media print" in legal_css
    assert "#f8fafc" in legal_css or "#1e3a8a" in legal_css

    exporter = EUAIActComplianceExporter(artifact_bundle_path=temp_bundle_dir)
    cert = exporter.generate_certificate(system_id="SYS-THEMES-01", operator_name="Acme Legal", locale="es")

    with tempfile.TemporaryDirectory() as out_dir:
        dark_path = os.path.join(out_dir, "report_dark.html")
        legal_path = os.path.join(out_dir, "report_legal.html")

        exporter.export_html_report(cert, dark_path, locale="es", theme="dark")
        exporter.export_html_report(cert, legal_path, locale="es", theme="legal")

        with open(dark_path, "r", encoding="utf-8") as f:
            dark_content = f.read()
            assert "#0b0f19" in dark_content or "#00F0FF" in dark_content

        with open(legal_path, "r", encoding="utf-8") as f:
            legal_content = f.read()
            assert "@media print" in legal_content
            assert "#f8fafc" in legal_content or "#1e3a8a" in legal_content
            assert "SYS-THEMES-01" in legal_content
            assert "Matriz de Cumplimiento Normativo EU AI Act" in legal_content


def test_dto_context_isolation(temp_bundle_dir: str) -> None:
    """Verifica la integridad del DTO de contexto y desacoplamiento de datos."""
    from babylon60.compliance_exporter.template_engine import ComplianceTemplateEngine, ReportContextDTO

    exporter = EUAIActComplianceExporter(artifact_bundle_path=temp_bundle_dir)
    cert = exporter.generate_certificate(system_id="SYS-DTO-01", operator_name="Acme DTO", locale="es")

    engine = ComplianceTemplateEngine()
    dto = engine.build_context(cert, locale="es", theme="legal")

    assert isinstance(dto, ReportContextDTO)
    assert dto.system_identifier == "SYS-DTO-01"
    assert dto.operator == "Acme DTO"
    assert dto.theme == "legal"
    assert len(dto.articles) > 0
    assert dto.compliance_matrix_title == "Matriz de Cumplimiento Normativo EU AI Act"

    d = dto.to_dict()
    assert d["system_identifier"] == "SYS-DTO-01"
    assert isinstance(d["articles"], list)
    assert d["articles"][0]["title"] is not None
