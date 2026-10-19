"""Exercise portable signatures through the actual CLI in isolated subprocesses."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).absolute().parents[1]
CLI = ROOT / "01_KISH_ENGINE" / "babylon60" / "cli" / "main_dispatcher.py"
OBSERVED_AT = "2026-10-18T12:00:00+02:00"


def run_signature(*args: str, payload: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), "signature", *args],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


def sample_payload() -> str:
    return json.dumps(
        {
            "schema_version": 1,
            "observed_at": OBSERVED_AT,
            "fields": {"LLM": "Modelo de prueba (metadatos del turno; No evaluable)"},
            "sources": {"LLM": "Metadatos de sesión de prueba"},
        },
        ensure_ascii=False,
    )


def test_schema_is_json_without_input_or_banner() -> None:
    result = run_signature("--schema")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["type"] == "object"
    assert result.stderr == ""


def test_default_auto_is_plain_text_and_does_not_infer_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEX_MODEL", "must-not-be-current")
    result = run_signature("--input", "-", payload=sample_payload())
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("[ LLM ]:") == 1
    assert "must-not-be-current" not in result.stdout
    assert "MOSKV-1" in result.stdout
    assert "\x1b[" not in result.stdout
    assert result.stderr == ""


def test_json_accepts_file_input_and_preserves_observation(tmp_path: Path) -> None:
    source = tmp_path / "observation.json"
    source.write_text(sample_payload(), encoding="utf-8")
    result = run_signature("--input", str(source), "--format", "json")
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["observed_at"] == OBSERVED_AT
    assert output["fields"]["TOPOLOGÍA ACTIVA"] == "MOSKV-1"
    assert output["sources"]["LLM"] == "Metadatos de sesión de prueba"
    assert result.stderr == ""


@pytest.mark.parametrize("format_name", ["html", "markdown", "text", "json"])
def test_each_format_renders_once(format_name: str) -> None:
    result = run_signature("--input", "-", "--format", format_name, payload=sample_payload())
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("Modelo de prueba") == 1
    if format_name == "html":
        assert result.stdout.startswith("<!DOCTYPE html>")
        assert '<html lang="es">' in result.stdout
        assert 'name="viewport"' in result.stdout
        assert 'name="color-scheme"' in result.stdout
        assert "</html>" in result.stdout


@pytest.mark.parametrize(
    "payload",
    [
        "{",
        "[]",
        '{"observed_at":"2026-10-18T12:00:00+02:00","fields":{},"fields":{}}',
        '{"observed_at":"2026-10-18T12:00:00+02:00","fields":{"LLM":"A","LLM":"B"}}',
        '{"observed_at":"2026-10-18T12:00:00+02:00","fields":{"LLM":NaN}}',
        '{"observed_at":"2026-10-18T12:00:00","fields":{}}',
    ],
)
def test_invalid_input_fails_without_stdout_or_traceback(payload: str) -> None:
    result = run_signature("--input", "-", payload=payload)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "signature:" in result.stderr
    assert "Traceback" not in result.stderr


def test_requires_input_or_schema() -> None:
    result = run_signature()
    assert result.returncode == 2
    assert result.stdout == ""


def test_missing_input_is_a_clean_error(tmp_path: Path) -> None:
    result = run_signature("--input", str(tmp_path / "absent.json"))
    assert result.returncode == 2
    assert result.stdout == ""
    assert "signature:" in result.stderr
    assert "Traceback" not in result.stderr


def test_invalid_observation_does_not_create_an_output_file(tmp_path: Path) -> None:
    output = tmp_path / "response.html"
    result = run_signature("--input", "-", "--format", "html", "--output", str(output), payload="{}")
    assert result.returncode == 2
    assert not output.exists()


def test_file_output_is_private_exclusive_and_stdout_stays_empty(tmp_path: Path) -> None:
    output = tmp_path / "response.html"
    first = run_signature("--input", "-", "--format", "html", "--output", str(output), payload=sample_payload())
    assert first.returncode == 0, first.stderr
    assert first.stdout == ""
    content = output.read_bytes()
    assert content.startswith(b"<!DOCTYPE html>")
    if os.name == "posix":
        assert output.stat().st_mode & 0o777 == 0o600
    second = run_signature("--input", "-", "--output", str(output), payload=sample_payload())
    assert second.returncode == 2
    assert second.stdout == ""
    assert output.read_bytes() == content


def test_output_cannot_follow_symlink(tmp_path: Path) -> None:
    target = tmp_path / "existing.txt"
    target.write_text("keep", encoding="utf-8")
    output = tmp_path / "link.txt"
    output.symlink_to(target)
    result = run_signature("--input", "-", "--output", str(output), payload=sample_payload())
    assert result.returncode == 2
    assert target.read_text(encoding="utf-8") == "keep"


@pytest.mark.skipif(not hasattr(os, "O_NOFOLLOW"), reason="OS lacks O_NOFOLLOW")
def test_input_cannot_follow_symlink(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    source.write_text(sample_payload(), encoding="utf-8")
    link = tmp_path / "link.json"
    link.symlink_to(source)
    result = run_signature("--input", str(link))
    assert result.returncode == 2
    assert result.stdout == ""
