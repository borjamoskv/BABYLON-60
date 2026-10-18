"""Credential scanning must distinguish assignments from code identifiers."""

from pathlib import Path

from scripts.c5_cli.opsec_sentinel_c5 import OpsecSentinelC5


def test_aws_credential_assignment_is_detected(tmp_path: Path) -> None:
    scanner = OpsecSentinelC5(str(tmp_path), str(tmp_path / "audit.sqlite"))
    candidate = tmp_path / "config.txt"
    candidate.write_text('aws_secret_access_key = "' + "A" * 20 + "g" * 20 + '"\n')
    assert [finding["violation_type"] for finding in scanner.audit_file(candidate)] == ["AWS_SECRET_KEY"]


def test_long_source_identifier_is_not_an_aws_secret(tmp_path: Path) -> None:
    scanner = OpsecSentinelC5(str(tmp_path), str(tmp_path / "audit.sqlite"))
    candidate = tmp_path / "source.rs"
    candidate.write_text("pub struct " + "A" * 20 + "g" * 20 + ";\n")
    assert scanner.audit_file(candidate) == []
