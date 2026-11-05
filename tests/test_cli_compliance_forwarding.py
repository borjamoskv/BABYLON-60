"""The root CLI delegates compliance options to the real report exporter."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from babylon60.attestation import MerkleCausalAnchor
from babylon60.cli import main_dispatcher


def _run_compliance(monkeypatch: pytest.MonkeyPatch, *arguments: str) -> int:
    monkeypatch.setattr(sys, "argv", ["babylon60", "compliance", *arguments])
    with pytest.raises(SystemExit) as stopped:
        main_dispatcher.main()
    code = stopped.value.code
    assert isinstance(code, int)
    return code


def test_compliance_help_exposes_exporter_options(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run_compliance(monkeypatch, "--help") == 0

    output = capsys.readouterr()
    assert output.err == ""
    for option in ("--bundle", "--output", "--format", "--allow-unverified"):
        assert option in output.out


@pytest.mark.parametrize("report_format", ["json", "md", "html"])
def test_compliance_forwards_report_options_and_writes_selected_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, report_format: str
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BABYLON60_SIGNING_SEED", "00" * 32)
    monkeypatch.setattr(
        MerkleCausalAnchor,
        "get_hardware_identity",
        lambda self: {
            "uuid": "TEST-SOFTWARE-UUID",
            "os": "Fixture",
            "machine": "Test",
            "enclave_type": "SOFTWARE_FIXTURE",
        },
    )
    bundle = tmp_path / "chosen evidence bundle"
    bundle.mkdir()
    root_hash = "ab" * 32
    (bundle / "manifest.json").write_text(json.dumps({"global_hash": root_hash}), encoding="utf-8")
    output = tmp_path / "chosen output" / f"report.{report_format}"

    assert (
        _run_compliance(
            monkeypatch,
            "--bundle",
            str(bundle),
            "--output",
            str(output),
            "--format",
            report_format,
            "--system-id",
            "CLI-FORWARDING-TEST",
            "--allow-unverified",
        )
        == 0
    )

    content = output.read_text(encoding="utf-8")
    assert "CLI-FORWARDING-TEST" in content
    assert root_hash in content
    assert not list(tmp_path.glob("compliance_cert_*"))
    if report_format == "json":
        report = json.loads(content)
        assert report["global_merkle_root"] == root_hash
        assert report["evidence_verification"]["verified"] is False
        assert report["publication_authorized"] is False
    elif report_format == "html":
        assert "<!DOCTYPE html>" in content
    else:
        assert content.startswith("# ")


def test_compliance_rejects_invalid_format_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    output = tmp_path / "must not exist" / "report.pdf"

    assert (
        _run_compliance(
            monkeypatch,
            "--bundle",
            str(tmp_path / "missing bundle"),
            "--output",
            str(output),
            "--format",
            "pdf",
        )
        == 2
    )

    assert "invalid choice" in capsys.readouterr().err
    assert not output.parent.exists()
    assert list(tmp_path.iterdir()) == []
