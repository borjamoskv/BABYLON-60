# test_license_manager.py
# Empirical falsification for Sovereign Dual-Licensing (INV_C5_17) & License Manager
# Authorship: Telmo Dinámico de Moskv (borjamoskv)

import os
import time
import pytest
from babylon60.license_manager import (
    generate_license_key,
    verify_license_key,
    LicenseStatus,
)
from io_persist_ledger import LedgerPersist


def test_community_mode_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifica que sin CORTEX_LICENSE_KEY opera en modo Sovereign Community gratis."""
    monkeypatch.delenv("CORTEX_LICENSE_KEY", raising=False)
    status = verify_license_key()
    assert status.is_valid is False
    assert status.tier == "community"
    assert status.owner == "sovereign_community"
    assert "Sovereign Community" in status.message


def test_valid_commercial_pro_license() -> None:
    """Verifica la generación y validación de una clave de licencia comercial Pro."""
    future_exp = int(time.time()) + 86400 * 30  # 30 días
    key = generate_license_key(owner="acme_corp", tier="pro", expires_at=future_exp)

    status = verify_license_key(key)
    assert status.is_valid is True
    assert status.tier == "pro"
    assert status.owner == "acme_corp"
    assert status.expires_at == future_exp
    assert "Valid commercial license" in status.message


def test_valid_commercial_enterprise_license() -> None:
    """Verifica la generación y validación de una clave Enterprise."""
    future_exp = int(time.time()) + 86400 * 365
    key = generate_license_key(owner="megacorp_inc", tier="enterprise", expires_at=future_exp)

    status = verify_license_key(key)
    assert status.is_valid is True
    assert status.tier == "enterprise"
    assert status.owner == "megacorp_inc"


def test_expired_license_fails() -> None:
    """Verifica que una licencia expirada es invalidada inmediatamente."""
    past_exp = int(time.time()) - 1000
    key = generate_license_key(owner="expired_co", tier="pro", expires_at=past_exp)

    status = verify_license_key(key)
    assert status.is_valid is False
    assert "expired" in status.message.lower()


def test_tampered_signature_fails() -> None:
    """Verifica que alterar la firma HMAC o los datos invalida la licencia."""
    future_exp = int(time.time()) + 86400
    key = generate_license_key(owner="hacker_org", tier="enterprise", expires_at=future_exp)

    # Alter owner in string payload
    tampered_key = key.replace("hacker_org", "legit_org")
    status = verify_license_key(tampered_key)

    assert status.is_valid is False
    assert status.tier == "invalid"
    assert "Invalid cryptographic signature" in status.message


def test_ledger_persist_license_integration(tmp_path: object) -> None:
    """Verifica la integración de LicenseStatus en LedgerPersist."""
    db_file = str(tmp_path) + "/test_lic_persist.db"  # type: ignore[operator]

    future_exp = int(time.time()) + 86400
    key = generate_license_key(owner="fintech_lab", tier="pro", expires_at=future_exp)

    persist = LedgerPersist(db_file, license_key=key)
    assert persist.license_status.is_valid is True
    assert persist.license_status.owner == "fintech_lab"
    persist.close()
