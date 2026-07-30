# C5-REAL EXERGY CERTIFIED — LicenseManager Engine Test Suite
# Invariantes: INV_C5_17 (Dual Licensing & Monetization), Ω11 (Immutable Ledger),
#              Ω23 (Dynamic Resolution), Ω_BFT_04 (Idempotency Bizantina)

from __future__ import annotations

import importlib.util
import time
from pathlib import Path
from typing import Generator

import pytest

# Dynamic module loading to handle leading numbers in folder structure (Ω23)
_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parents[1]
_ENGINE_PATH = (
    _REPO_ROOT
    / "1_Operaciones_Activas"
    / "02_CORTEX_ENGINE"
    / "cortex"
    / "engines"
    / "license_manager_engine.py"
)
_TEST_DB_PATH = _REPO_ROOT / ".cortex" / "test_license_manager.db"

spec = importlib.util.spec_from_file_location("license_manager_engine", _ENGINE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Failed to load spec for {_ENGINE_PATH}")
license_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(license_mod)

LicenseManagerEngine = license_mod.LicenseManagerEngine
LicenseTier = license_mod.LicenseTier
LicenseState = license_mod.LicenseState
LicenseToken = license_mod.LicenseToken


@pytest.fixture(autouse=True)
def clean_test_db() -> Generator[Path, None, None]:
    """Provisiona un SQLite ledger de pruebas limpio."""
    _TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-shm", "-wal"):
        p = Path(str(_TEST_DB_PATH) + suffix)
        if p.exists():
            p.unlink(missing_ok=True)

    yield _TEST_DB_PATH

    for suffix in ("", "-shm", "-wal"):
        p = Path(str(_TEST_DB_PATH) + suffix)
        if p.exists():
            p.unlink(missing_ok=True)


def test_community_tier_default() -> None:
    """Verifica que sin token la licencia por defecto es COMMUNITY (AGPLv3 core exergy)."""
    engine = LicenseManagerEngine(db_path=_TEST_DB_PATH)
    assert engine.active_tier() == LicenseTier.COMMUNITY
    assert engine.state == LicenseState.COMMUNITY

    # Community features accessible
    allowed, msg = engine.can_access_feature("mcts_basic")
    assert allowed is True
    assert "COMMUNITY" in msg

    # Enterprise features denied for community tier
    allowed_ent, msg_ent = engine.can_access_feature("swarm_1000_agents")
    assert allowed_ent is False
    assert "DENEGADO" in msg_ent


def test_enterprise_token_validation() -> None:
    """Verifica token de licencia comercial ENTERPRISE válido con firma HMAC SHA3-256."""
    engine = LicenseManagerEngine(db_path=_TEST_DB_PATH)

    token = LicenseToken(
        license_id="LIC-ENT-2026-001",
        holder="Enterprise Corp",
        tier=LicenseTier.ENTERPRISE,
        expires_at=time.time() + 86400,  # Valid for 24h
    )

    state = engine.load_license_token(token.to_dict())
    assert state == LicenseState.VALID_ONLINE
    assert engine.active_tier() == LicenseTier.ENTERPRISE

    # Enterprise features authorized
    allowed, msg = engine.can_access_feature("swarm_1000_agents")
    assert allowed is True
    assert "ENTERPRISE" in msg


def test_invalid_signature_token_rejected() -> None:
    """Verifica rechazo inmediato de tokens con firmas falsificadas (Fail-Fast)."""
    engine = LicenseManagerEngine(db_path=_TEST_DB_PATH)

    token_dict = {
        "license_id": "LIC-TAMPERED-001",
        "holder": "Attacker",
        "tier": LicenseTier.ENTERPRISE.value,
        "expires_at": time.time() + 86400,
        "signature": "DEADBEEF_INVALID_HASH",
    }

    state = engine.load_license_token(token_dict)
    assert state == LicenseState.INVALID_SIGNATURE
    assert engine.active_tier() == LicenseTier.COMMUNITY

    allowed, _ = engine.can_access_feature("swarm_1000_agents")
    assert allowed is False


def test_expired_token_rejected() -> None:
    """Verifica que tokens expirados degradan al tier COMMUNITY."""
    engine = LicenseManagerEngine(db_path=_TEST_DB_PATH)

    token = LicenseToken(
        license_id="LIC-EXPIRED-001",
        holder="Past Subscriber",
        tier=LicenseTier.ENTERPRISE,
        expires_at=time.time() - 3600,  # Expired 1 hour ago
    )

    state = engine.load_license_token(token.to_dict())
    assert state == LicenseState.EXPIRED
    assert engine.active_tier() == LicenseTier.COMMUNITY


def test_429_rate_limit_resilience_and_offline_staging() -> None:
    """
    Verifica resiliencia ante Error 429:
    Transiciona a DEGRADED_OFFLINE_VALID manteniendo la operatividad ENTERPRISE
    y registrando la auditoría en el offline staging ledger.
    """
    engine = LicenseManagerEngine(db_path=_TEST_DB_PATH)

    # Valid enterprise token
    token = LicenseToken(
        license_id="LIC-ENT-RESILIENT-429",
        holder="Robust Corp",
        tier=LicenseTier.ENTERPRISE,
        expires_at=time.time() + 86400,
    )
    engine.load_license_token(token.to_dict())

    # Simular colapso por HTTP 429
    new_state = engine.handle_network_429(feature_name="swarm_1000_agents", error_msg="HTTP 429 Rate Limit")
    assert new_state == LicenseState.DEGRADED_OFFLINE_VALID
    assert engine.active_tier() == LicenseTier.ENTERPRISE

    # Enterprise feature remains accessible under degraded offline status
    allowed, msg = engine.can_access_feature("swarm_1000_agents")
    assert allowed is True
    assert "DEGRADED_OFFLINE" in msg

    # Recovery: Flush staging ledger after network 429 clears
    flushed_count = engine.flush_staging_ledger()
    assert flushed_count == 1
    assert engine.state == LicenseState.VALID_ONLINE
