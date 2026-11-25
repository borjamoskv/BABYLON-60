"""Security regression tests for tools/tamkarum_license_provisioner.py (CodeQL #2)."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from types import ModuleType

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tools" / "tamkarum_license_provisioner.py"
SAMPLE_IBAN = "ES9121000418450200051332"
SAMPLE_IBAN_SPACED = "ES91 2100 0418 4502 0005 1332"


def _load_fresh_module(name: str = "tamkarum_security_test_module") -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ephemeral_seed_hex() -> str:
    key = Ed25519PrivateKey.generate()
    raw = key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return raw.hex()


def test_exported_interface_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BABYLON_SETTLEMENT_IBAN", raising=False)
    monkeypatch.delenv("BABYLON_SETTLEMENT_BIC", raising=False)
    mod = _load_fresh_module("tamkarum_contract")

    assert hasattr(mod, "DEFAULT_SETTLEMENT_IBAN")
    assert hasattr(mod, "DEFAULT_SETTLEMENT_BIC")
    assert callable(mod.generate_license_certificate)
    assert callable(mod.generate_proforma_invoice)
    assert set(mod.TIERS) >= {"pilot", "enterprise"}


@pytest.mark.parametrize("iban_value", [SAMPLE_IBAN, SAMPLE_IBAN_SPACED])
def test_configured_iban_never_leaks_in_proforma_or_module_constant(
    monkeypatch: pytest.MonkeyPatch, iban_value: str
) -> None:
    monkeypatch.setenv("BABYLON_SETTLEMENT_IBAN", iban_value)
    mod = _load_fresh_module("tamkarum_with_iban")

    assert SAMPLE_IBAN not in mod.DEFAULT_SETTLEMENT_IBAN
    assert iban_value not in mod.DEFAULT_SETTLEMENT_IBAN
    assert "21000418450200051332" not in mod.DEFAULT_SETTLEMENT_IBAN
    assert mod.DEFAULT_SETTLEMENT_IBAN == mod.DEFAULT_SETTLEMENT_CONFIGURED_MARKER

    _, proforma_text = mod.generate_proforma_invoice(
        "Acme Silicon GmbH",
        "DE123456789",
        "Industriestrasse 1, Munich",
        "pilot",
        "11111111-2222-3333-4444-555555555555",
        "a" * 64,
    )

    assert SAMPLE_IBAN not in proforma_text
    assert iban_value not in proforma_text
    assert "21000418450200051332" not in proforma_text
    assert "1332" not in proforma_text
    assert mod.DEFAULT_SETTLEMENT_CONFIGURED_MARKER in proforma_text


def test_env_iban_set_after_import_is_still_redacted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BABYLON_SETTLEMENT_IBAN", raising=False)
    mod = _load_fresh_module("tamkarum_late_env")

    monkeypatch.setenv("BABYLON_SETTLEMENT_IBAN", SAMPLE_IBAN)
    _, proforma_text = mod.generate_proforma_invoice(
        "Late Env Corp",
        "ESB12345678",
        "Calle Mayor 1, Madrid",
        "enterprise",
        "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "b" * 64,
    )

    assert SAMPLE_IBAN not in proforma_text
    assert mod.DEFAULT_SETTLEMENT_CONFIGURED_MARKER in proforma_text


def test_overridden_default_settlement_iban_is_redacted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BABYLON_SETTLEMENT_IBAN", raising=False)
    mod = _load_fresh_module("tamkarum_override_attr")
    monkeypatch.setattr(mod, "DEFAULT_SETTLEMENT_IBAN", SAMPLE_IBAN)

    _, proforma_text = mod.generate_proforma_invoice(
        "Override Corp",
        "DE987654321",
        "Berlin",
        "pilot",
        "22222222-3333-4444-5555-666666666666",
        "c" * 64,
    )

    assert SAMPLE_IBAN not in proforma_text
    assert mod.DEFAULT_SETTLEMENT_CONFIGURED_MARKER in proforma_text


@pytest.mark.parametrize("env_value", [None, "", "   "])
def test_default_mode_without_iban_env_var(monkeypatch: pytest.MonkeyPatch, env_value: str | None) -> None:
    if env_value is None:
        monkeypatch.delenv("BABYLON_SETTLEMENT_IBAN", raising=False)
    else:
        monkeypatch.setenv("BABYLON_SETTLEMENT_IBAN", env_value)
    monkeypatch.delenv("BABYLON_SETTLEMENT_BIC", raising=False)
    mod = _load_fresh_module("tamkarum_default_mode")

    assert mod.DEFAULT_SETTLEMENT_IBAN == "Provided upon proforma validation"
    assert mod.DEFAULT_SETTLEMENT_BIC == "Provided upon proforma validation"

    inv_num, proforma_text = mod.generate_proforma_invoice(
        "Default Client Ltd",
        "GB123456789",
        "London",
        "pilot",
        "33333333-4444-5555-6666-777777777777",
        "d" * 64,
    )

    assert inv_num.startswith("B60-")
    assert "IBAN:           Provided upon proforma validation" in proforma_text


def test_cli_main_redacts_iban_on_disk_and_enforces_0600_permissions(tmp_path: Path) -> None:
    out_dir = tmp_path / "issued"
    env = dict(os.environ)
    env["BABYLON_LICENSE_ED25519_SEED"] = _ephemeral_seed_hex()
    env["BABYLON_SETTLEMENT_IBAN"] = SAMPLE_IBAN
    env.pop("BABYLON_SETTLEMENT_BIC", None)

    result = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "--client",
            "Sovereign Client S.L.",
            "--vat",
            "ESB12345678",
            "--tier",
            "pilot",
            "--out-dir",
            str(out_dir),
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert SAMPLE_IBAN not in result.stdout
    assert SAMPLE_IBAN not in result.stderr

    invoices = list(out_dir.glob("*_invoice.txt"))
    licenses = list(out_dir.glob("*_license.json"))
    assert len(invoices) == 1
    assert len(licenses) == 1

    invoice_text = invoices[0].read_text(encoding="utf-8")
    license_text = licenses[0].read_text(encoding="utf-8")

    assert SAMPLE_IBAN not in invoice_text
    assert "21000418450200051332" not in invoice_text
    assert "1332" not in invoice_text
    assert "Configured via authenticated settlement channel (IBAN redacted)" in invoice_text
    assert SAMPLE_IBAN not in license_text

    assert stat.S_IMODE(os.stat(invoices[0]).st_mode) == 0o600
    assert stat.S_IMODE(os.stat(licenses[0]).st_mode) == 0o600
    assert stat.S_IMODE(os.stat(out_dir).st_mode) == 0o700


def test_cli_main_default_mode_without_iban_enforces_0600(tmp_path: Path) -> None:
    out_dir = tmp_path / "issued_default"
    env = dict(os.environ)
    env["BABYLON_LICENSE_ED25519_SEED"] = _ephemeral_seed_hex()
    env.pop("BABYLON_SETTLEMENT_IBAN", None)
    env.pop("BABYLON_SETTLEMENT_BIC", None)

    result = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "--client",
            "Default Co GmbH",
            "--vat",
            "DE123456789",
            "--tier",
            "enterprise",
            "--out-dir",
            str(out_dir),
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    invoices = list(out_dir.glob("*_invoice.txt"))
    licenses = list(out_dir.glob("*_license.json"))
    assert len(invoices) == 1
    assert len(licenses) == 1

    invoice_text = invoices[0].read_text(encoding="utf-8")
    assert "IBAN:           Provided upon proforma validation" in invoice_text
    assert json.loads(licenses[0].read_text(encoding="utf-8"))["licensee"]["entity"] == "Default Co GmbH"
    assert stat.S_IMODE(os.stat(invoices[0]).st_mode) == 0o600
    assert stat.S_IMODE(os.stat(licenses[0]).st_mode) == 0o600


def test_write_restricted_text_hardens_existing_file_and_rejects_symlinks(tmp_path: Path) -> None:
    mod = _load_fresh_module("tamkarum_write_helper")

    existing = tmp_path / "existing.txt"
    existing.write_text("stale", encoding="utf-8")
    os.chmod(existing, 0o644)
    mod._write_restricted_text(str(existing), "updated")
    assert existing.read_text(encoding="utf-8") == "updated"
    assert stat.S_IMODE(os.stat(existing).st_mode) == 0o600

    if hasattr(os, "O_NOFOLLOW"):
        target = tmp_path / "victim.txt"
        target.write_text("intact", encoding="utf-8")
        link = tmp_path / "invoice_link.txt"
        link.symlink_to(target)
        with pytest.raises(OSError):
            mod._write_restricted_text(str(link), "overwrite")
        assert target.read_text(encoding="utf-8") == "intact"


def test_default_output_dir_is_repo_relative() -> None:
    mod = _load_fresh_module("tamkarum_default_dir")
    assert mod.DEFAULT_OUTPUT_DIR == REPO_ROOT / "contracts" / "issued_licenses"
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    assert "/Users/" not in source_text
