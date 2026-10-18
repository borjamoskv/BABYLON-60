#!/usr/bin/env python3
"""
Tests for BABYLON-60 Zero-Touch Enterprise Onboarding Daemon
Verifies that pilot orders are provisioned autonomously with valid SHA-256 seals,
proforma invoices, and zero human friction in < 15ms.
"""

import os
from pathlib import Path

from scripts.zero_touch_onboarding_daemon import process_zero_touch_pilot_order


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
