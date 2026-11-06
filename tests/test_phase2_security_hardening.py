"""Executable regressions for the compliance export redaction boundary."""

import json
from pathlib import Path

from babylon60.compliance_exporter.eu_ai_act import EUAIActComplianceExporter


def test_redaction_layer_sanitizes_nested_secrets() -> None:
    raw = {
        "api_key": "sensitive-value",
        "nested": [{"password": "private-password"}],
        "message": "token=secret_token_value",
        "event": "audit",
        "count": 3,
    }
    result = EUAIActComplianceExporter.redact_sensitive_data(raw)
    assert result == {
        "api_key": "[REDACTED_AUDIT_SAFE]",
        "nested": [{"password": "[REDACTED_AUDIT_SAFE]"}],
        "message": "token=[REDACTED_AUDIT_SAFE]",
        "event": "audit",
        "count": 3,
    }
    assert raw["api_key"] == "sensitive-value"


def test_manifest_load_applies_redaction(tmp_path: Path) -> None:
    (tmp_path / "manifest.json").write_text(json.dumps({"api_key": "private-secret", "event": "audit"}))
    result = EUAIActComplianceExporter(str(tmp_path)).load_manifest()
    assert result["api_key"] == "[REDACTED_AUDIT_SAFE]"
    assert result["event"] == "audit"
    assert "private-secret" not in json.dumps(result)
