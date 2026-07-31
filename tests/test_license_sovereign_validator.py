# test_license_sovereign_validator.py
# Empirical falsification for Sovereign Dual-Licensing (INV_C5_17) & License Transducer
# Authorship: Telmo Dinámico de Moskv (borjamoskv)

import time
import pytest
from license_sovereign_validator import (
    generate_license_key,
    verify_license_key,
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


def test_community_tier_throughput_limit(tmp_path: object) -> None:
    """Verifica que el tier community falla rápido al intentar persistir > 100 nodos."""
    from core_graph_ledger import GraphLedger, core_calc_sha256

    db_file = str(tmp_path) + "/test_community_limit.db"  # type: ignore[operator]
    persist = LedgerPersist(db_file)

    ledger = GraphLedger()
    curr_parent = ledger.genesis_id
    for i in range(101):
        node = ledger.mut_append_node(
            parent_id=curr_parent,
            claim=f"Node {i}",
            payload_hash=core_calc_sha256(f"payload_{i}"),
        )
        curr_parent = node.node_id

    with pytest.raises(ValueError, match="Community tier limits batch inserts to 100 nodes"):
        persist.io_persist_ledger(ledger)

    persist.close()


def test_commercial_tier_unbounded_throughput(tmp_path: object) -> None:
    """Verifica que un tier comercial permite persistir > 100 nodos sin restricciones."""
    from core_graph_ledger import GraphLedger, core_calc_sha256

    db_file = str(tmp_path) + "/test_commercial_unbounded.db"  # type: ignore[operator]
    future_exp = int(time.time()) + 86400
    key = generate_license_key(owner="enterprise_corp", tier="enterprise", expires_at=future_exp)
    persist = LedgerPersist(db_file, license_key=key)

    ledger = GraphLedger()
    curr_parent = ledger.genesis_id
    for i in range(105):
        node = ledger.mut_append_node(
            parent_id=curr_parent,
            claim=f"Node {i}",
            payload_hash=core_calc_sha256(f"payload_{i}"),
        )
        curr_parent = node.node_id

    inserted = persist.io_persist_ledger(ledger)
    assert inserted == 105
    assert persist.io_node_count() == 105
    persist.close()
