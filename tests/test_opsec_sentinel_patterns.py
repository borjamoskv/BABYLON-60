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


def test_decimal_mantissas_and_zero_padded_loopback_do_not_trigger_opsec(tmp_path: Path) -> None:
    scanner = OpsecSentinelC5(str(tmp_path), str(tmp_path / "audit.sqlite"))
    timing_json = tmp_path / "results.json"
    # Same prefix form as pytest JSON durations (0.<16-digit float>)
    luhn_float_digits = "5286" + "0" * 11 + "7"
    timing_json.write_text(f'{{"seconds": 0.{luhn_float_digits}}}\n')
    assert scanner.audit_file(timing_json) == []

    ssrf_test = tmp_path / "ssrf_vectors.py"
    ssrf_test.write_text("URLS = ['http://127.000.000.001/v1/chat', 'http://000.000.000.000/x']\n")
    assert scanner.audit_file(ssrf_test) == []


def test_real_c2_and_webhook_patterns_still_trigger(tmp_path: Path) -> None:
    scanner = OpsecSentinelC5(str(tmp_path), str(tmp_path / "audit.sqlite"))
    c2 = tmp_path / "c2.py"
    c2.write_text("url = '" + "http://" + "198.51.100.42/beacon'\n")
    assert [f["violation_type"] for f in scanner.audit_file(c2)] == ["PLAIN_HTTP_C2"]

    hook = tmp_path / "hook.ts"
    hook.write_text("fetch('" + "https://webhook" + ".site/00000000-0000-0000-0000-000000000000')\n")
    assert [f["violation_type"] for f in scanner.audit_file(hook)] == ["CANARY_WEBHOOK"]


def test_credit_card_with_sentence_period_still_triggers_opsec(tmp_path: Path) -> None:
    scanner = OpsecSentinelC5(str(tmp_path), str(tmp_path / "audit.sqlite"))
    card_note = tmp_path / "note.txt"
    # Luhn-valid synthetic test card followed by a grammatical sentence period must not bypass detection.
    synthetic_visa = "4532" + "0151" + "1283" + "0366"
    card_note.write_text(f"Customer card on file is {synthetic_visa}.\n")
    assert [f["violation_type"] for f in scanner.audit_file(card_note)] == ["PLAINTEXT_CREDIT_CARD"]

    float_suffix = tmp_path / "float_metric.json"
    float_suffix.write_text(f'{{"metric": {synthetic_visa}.0}}\n')
    assert scanner.audit_file(float_suffix) == []
