"""The root CLI delegates compliance options to the real report exporter."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from babylon60.attestation import MerkleCausalAnchor
from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger
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


@pytest.mark.parametrize("configured_seed", [True, False], ids=["software-test-only-seed", "missing-seed"])
def test_user_guide_compliance_example_requires_configured_software_seed(
    tmp_path: Path, configured_seed: bool
) -> None:
    """Run the documented shell block with real CLI, ledger, signing and HTML export."""
    repository = Path(__file__).absolute().parents[1]
    guide = (repository / "docs/03_guides/USER_GUIDE.md").read_text(encoding="utf-8")
    section = guide.split("### 1. Auditoría y Cumplimiento EU AI Act (`babylon60 compliance`)", 1)[1]
    example = section.split("```bash\n", 1)[1].split("\n```", 1)[0]

    ledger_path = tmp_path / "evidence ledger.db"
    ledger = CortexPersistLedger(ledger_path)
    ledger.append_event(
        CortexEvent(
            agent_id="SOFTWARE_TEST_ONLY",
            event_type="INIT",
            payload={"action": "audit"},
            cortex_taint="T0",
            domain="compliance",
        )
    )
    root_hash = ledger.get_merkle_root()
    bundle = tmp_path / "evidence bundle"
    bundle.mkdir()
    (bundle / "manifest.json").write_text(json.dumps({"global_hash": root_hash}), encoding="utf-8")
    example = example.replace("/ruta/paquete_evidencia", shlex.quote(str(bundle)))
    example = example.replace("/ruta/ledger.db", shlex.quote(str(ledger_path)))

    # Only the platform identity observation is a fixture; no hardware identity or key is read.
    launcher_dir = tmp_path / "bin"
    launcher_dir.mkdir()
    invoked = tmp_path / "cli-invoked"
    driver = launcher_dir / "compliance_driver.py"
    driver.write_text(
        "from pathlib import Path\n"
        f"Path({str(invoked)!r}).touch()\n"
        "from babylon60.attestation import MerkleCausalAnchor\n"
        "from babylon60.cli.main_dispatcher import main\n"
        "MerkleCausalAnchor.get_hardware_identity = lambda self: {\n"
        "    'uuid': 'SOFTWARE_TEST_ONLY', 'os': 'Fixture',\n"
        "    'machine': 'Test', 'enclave_type': 'SOFTWARE_TEST_ONLY',\n"
        "}\n"
        "main()\n",
        encoding="utf-8",
    )
    launcher = launcher_dir / "babylon60"
    launcher.write_text(
        f'#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(driver))} "$@"\n', encoding="utf-8"
    )
    launcher.chmod(0o700)
    home = tmp_path / "home"
    home.mkdir()
    environment = {
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / "config"),
        "PATH": str(launcher_dir) + os.pathsep + os.defpath,
        "PYTHONPATH": str(repository / "01_KISH_ENGINE"),
        "PYTHONIOENCODING": "utf-8",
    }
    if configured_seed:
        environment["BABYLON60_SIGNING_SEED"] = bytes(range(32)).hex()  # SOFTWARE_TEST_ONLY

    result = subprocess.run(
        ["/bin/bash", "--noprofile", "--norc", "-c", example],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    output = tmp_path / "reporte_evidencia.html"
    if configured_seed:
        assert result.returncode == 0, result.stderr
        assert invoked.exists()
        report = output.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in report
        assert root_hash in report
        assert "Ed25519" in report
        assert "efímera: <code>False</code>" in report
        assert "Report generation does not authorize regulated approval or publication." in result.stdout
    else:
        assert result.returncode != 0
        assert "BABYLON60_SIGNING_SEED" in result.stderr
        assert "64 caracteres hexadecimales" in result.stderr
        assert "Traceback" not in result.stderr
        assert not invoked.exists()
        assert not output.exists()
