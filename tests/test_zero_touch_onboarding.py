#!/usr/bin/env python3
"""
Tests for BABYLON-60 Zero-Touch Enterprise Onboarding Daemon
Verifies that pilot orders are provisioned autonomously with valid SHA-256 seals,
proforma invoices, and zero human friction in < 15ms.
"""

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import zero_touch_onboarding_daemon as onboarding
from scripts.zero_touch_onboarding_daemon import process_zero_touch_pilot_order

# Semilla exclusiva de test: derivada de una etiqueta pública, nunca válida en producción.
TEST_ONLY_LICENSE_SEED = hashlib.sha256(b"babylon60/tests/zero-touch/license-seed/v1").hexdigest()
SYNTHETIC_TEST_IBAN = "ES0099998888776655443322"
SYNTHETIC_TEST_BIC = "TESTBIC0XXX"


@pytest.fixture(autouse=True)
def _test_license_authority(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BABYLON_LICENSE_ED25519_SEED", TEST_ONLY_LICENSE_SEED)


def test_zero_touch_refuses_to_provision_without_license_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("BABYLON_LICENSE_ED25519_SEED", raising=False)
    payload = {"client_name": "Unsigned Co", "client_vat": "DE000000000", "tier": "pilot"}
    with pytest.raises(ValueError, match="Ed25519 seed"):
        process_zero_touch_pilot_order(payload, out_dir=tmp_path)
    assert not any(tmp_path.iterdir())


def test_zero_touch_pilot_provisioning(tmp_path: Path) -> None:
    client_payload = {
        "client_name": "Defense AI Systems GmbH",
        "client_vat": "DE123456789",
        "client_email": "ciso@defenseai.de",
        "client_address": "Industriestrasse 42, Munich, Germany",
        "host_os": "Linux-x86_64",
        "tier": "pilot",
    }

    receipt = process_zero_touch_pilot_order(client_payload, out_dir=tmp_path)

    # 1. Assert status and performance
    assert receipt["status"] == "PROVISIONED_AUTONOMOUSLY"
    assert receipt["processing_time_ms"] < 100.0  # Fast silicon execution

    # 2. Assert license certificate
    lic_meta = receipt["license_certificate"]
    assert lic_meta["tier"] == "pilot"
    assert lic_meta["entity"] == "Defense AI Systems GmbH"
    assert lic_meta["vat_id"] == "DE123456789"
    assert len(lic_meta["sha256"]) == 64  # Valid SHA-256 hex string
    assert Path(lic_meta["file_path"]).exists()

    # 3. Assert proforma invoice (International Reverse Charge = 15000.0)
    inv_meta = receipt["proforma_invoice"]
    assert inv_meta["amount_eur"] == 15000.0
    assert inv_meta["vat_rate"] == 0.00
    assert inv_meta["invoice_number"].startswith("B60-")
    assert Path(inv_meta["file_path"]).exists()

    # 4. Assert delivery bundle and air-gap guarantee
    bundle = receipt["delivery_bundle"]
    assert bundle["installer_command"].startswith("curl")
    assert bundle["support_channel"]["human_air_gap"] is True
    assert bundle["support_channel"]["meetings_required"] == 0

    # 5. Assert file permissions (WORM isolation 0600)
    lic_stat = os.stat(lic_meta["file_path"]).st_mode & 0o777
    inv_stat = os.stat(inv_meta["file_path"]).st_mode & 0o777
    assert lic_stat == 0o600
    assert inv_stat == 0o600


def test_zero_touch_spanish_vat_provisioning(tmp_path: Path) -> None:
    """Verifica que entidades españolas calculen correctamente el 21% de IVA (18.150,00 €)."""
    client_payload = {
        "client_name": "Sistemas Autónomos de Silicio S.L.",
        "client_vat": "ESB12345678",
        "client_email": "seguridad@silicio.es",
        "tier": "pilot",
    }

    receipt = process_zero_touch_pilot_order(client_payload, out_dir=tmp_path)
    inv_meta = receipt["proforma_invoice"]
    assert inv_meta["base_amount_eur"] == 15000.0
    assert inv_meta["vat_rate"] == 0.21
    assert inv_meta["total_due_eur"] == 18150.0
    assert inv_meta["amount_eur"] == 18150.0


def test_zero_touch_sanitization_against_injection(tmp_path: Path) -> None:
    """Verifica la purga estricta de saltos de línea para prevenir inyecciones en proforma."""
    client_payload = {
        "client_name": "Acme Corp\nINJECTED_LINE: HACK\rMALICIOUS_FIELD",
        "client_vat": "ESA11223344\nADMIN=TRUE",
        "tier": "pilot",
    }

    receipt = process_zero_touch_pilot_order(client_payload, out_dir=tmp_path)
    assert "\n" not in receipt["license_certificate"]["entity"]
    assert "\r" not in receipt["license_certificate"]["entity"]
    assert "\n" not in receipt["license_certificate"]["vat_id"]


def test_type_hints_and_schema_reflection() -> None:
    """Valida que typing.get_type_hints() resuelva sin NameError (ausencia de Optional)."""
    import typing

    hints = typing.get_type_hints(process_zero_touch_pilot_order)
    assert "out_dir" in hints
    assert "return" in hints


def test_zero_touch_daemon_does_not_import_raw_settlement_constants() -> None:
    """Verifica estáticamente que los flujos SARIF de DEFAULT_SETTLEMENT_IBAN/BIC estén rotos."""
    source_path = Path(__file__).resolve().parents[1] / "scripts" / "zero_touch_onboarding_daemon.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    forbidden = {"DEFAULT_SETTLEMENT_IBAN", "DEFAULT_SETTLEMENT_BIC"}
    imported_names: set[str] = set()
    referenced_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Name):
            referenced_names.add(node.id)
    assert imported_names.isdisjoint(forbidden)
    assert referenced_names.isdisjoint(forbidden)


def test_zero_touch_cli_and_receipt_never_leak_settlement_iban_cold_import(tmp_path: Path) -> None:
    """Con BABYLON_SETTLEMENT_IBAN en entorno antes de importar, stdout y receipt no filtran el IBAN crudo."""
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(
        os.environ,
        BABYLON_LICENSE_ED25519_SEED=TEST_ONLY_LICENSE_SEED,
        BABYLON_SETTLEMENT_IBAN=SYNTHETIC_TEST_IBAN,
        BABYLON_SETTLEMENT_BIC=SYNTHETIC_TEST_BIC,
    )
    runner = (
        "import sys; from pathlib import Path; "
        "from scripts import zero_touch_onboarding_daemon as d; "
        "d.OUTPUT_BASE_DIR = Path(sys.argv[1]); "
        "sys.argv = ['zero_touch_onboarding_daemon.py', '--client', 'Canary Entity S.L.', "
        "'--vat', 'ESB88776655', '--email', 'ciso-canary@example.invalid', "
        "'--address', 'Private Vault 404, Bilbao', '--tier', 'pilot']; "
        "d.run_cli()"
    )
    proc = subprocess.run(
        [sys.executable, "-c", runner, str(tmp_path)],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    assert SYNTHETIC_TEST_IBAN not in proc.stdout
    assert SYNTHETIC_TEST_BIC not in proc.stdout
    assert SYNTHETIC_TEST_IBAN not in proc.stderr
    assert SYNTHETIC_TEST_BIC not in proc.stderr
    assert "ciso-canary@example.invalid" not in proc.stdout
    assert "Private Vault 404" not in proc.stdout
    assert "ESB88776655" not in proc.stdout

    cli_payload = json.loads(proc.stdout)
    assert cli_payload["status"] == "PROVISIONED_AUTONOMOUSLY"
    assert cli_payload["order_id"]
    assert {"license_id", "tier", "file_path", "sha256"}.issubset(cli_payload["license_certificate"])
    assert cli_payload["proforma_invoice"]["payment_channels"]["sepa_swift_wire"] == "Provided upon proforma validation"
    assert {"installer_command", "compliance_pack_sample", "support_channel"}.issubset(cli_payload["delivery_bundle"])

    receipt_files = list(tmp_path.glob("ORDER_*_receipt.json"))
    assert len(receipt_files) == 1
    persisted_text = receipt_files[0].read_text(encoding="utf-8")
    assert SYNTHETIC_TEST_IBAN not in persisted_text
    assert SYNTHETIC_TEST_BIC not in persisted_text
    persisted = json.loads(persisted_text)
    assert persisted["status"] == "PROVISIONED_AUTONOMOUSLY"
    assert persisted["order_id"] == cli_payload["order_id"]
    assert persisted["proforma_invoice"]["payment_channels"]["sepa_swift_wire"] == "Provided upon proforma validation"
    assert {"installer_command", "compliance_pack_sample", "support_channel"}.issubset(persisted["delivery_bundle"])


def test_zero_touch_cli_sanitizes_stdout_and_preserves_receipt_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """run_cli() emite un resumen JSON sanitizado preservando el esquema sin filtrar IBAN ni PII."""
    monkeypatch.setenv("BABYLON_SETTLEMENT_IBAN", SYNTHETIC_TEST_IBAN)
    monkeypatch.setenv("BABYLON_SETTLEMENT_BIC", SYNTHETIC_TEST_BIC)
    monkeypatch.setattr(onboarding, "OUTPUT_BASE_DIR", tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "zero_touch_onboarding_daemon.py",
            "--client",
            "Redacted Corp GmbH",
            "--vat",
            "DE998877665",
            "--email",
            "private-ciso@example.invalid",
            "--address",
            "Confidential Ave 99",
            "--tier",
            "pilot",
        ],
    )

    onboarding.run_cli()
    captured = capsys.readouterr()

    assert SYNTHETIC_TEST_IBAN not in captured.out
    assert SYNTHETIC_TEST_BIC not in captured.out
    assert "private-ciso@example.invalid" not in captured.out
    assert "Confidential Ave 99" not in captured.out
    assert "DE998877665" not in captured.out

    summary = json.loads(captured.out)
    assert summary["status"] == "PROVISIONED_AUTONOMOUSLY"
    assert summary["order_id"]
    assert set(summary["license_certificate"]) == {"license_id", "tier", "file_path", "sha256"}
    assert summary["proforma_invoice"]["payment_channels"]["sepa_swift_wire"] == "Provided upon proforma validation"
    assert set(summary["delivery_bundle"]) == {"installer_command", "compliance_pack_sample", "support_channel"}

    receipt_files = list(tmp_path.glob("ORDER_*_receipt.json"))
    assert len(receipt_files) == 1
    receipt = json.loads(receipt_files[0].read_text(encoding="utf-8"))
    assert receipt["proforma_invoice"]["payment_channels"]["sepa_swift_wire"] == "Provided upon proforma validation"
    assert SYNTHETIC_TEST_IBAN not in json.dumps(receipt)


def test_http_handler_logging_redacts_query_unknown_paths_and_error_payloads() -> None:
    """ZeroTouchHttpHandler no registra query strings, rutas arbitrarias ni mensajes de error crudos."""
    recorded: list[str] = []
    handler = SimpleNamespace(
        path=f"{onboarding.ORDER_PATH}?iban={SYNTHETIC_TEST_IBAN}&token=secret-canary",
        command="POST",
        log_message=lambda fmt, *args: recorded.append(fmt % args),
    )
    onboarding.ZeroTouchHttpHandler.log_request(handler, 200, 128)  # type: ignore[arg-type]

    handler.path = f"/private/{SYNTHETIC_TEST_IBAN}/leak"
    handler.command = "DEBUG"
    onboarding.ZeroTouchHttpHandler.log_request(handler, 404, 0)  # type: ignore[arg-type]

    onboarding.ZeroTouchHttpHandler.log_error(
        handler,  # type: ignore[arg-type]
        "code %d, message %s",
        400,
        f"Bad request syntax ('POST /?iban={SYNTHETIC_TEST_IBAN}')",
    )

    joined = "\n".join(recorded)
    assert SYNTHETIC_TEST_IBAN not in joined
    assert "secret-canary" not in joined
    assert recorded == [
        f"POST {onboarding.ORDER_PATH} 200",
        "<redacted-method> <redacted-path> 404",
        "HTTP error status=400",
    ]
