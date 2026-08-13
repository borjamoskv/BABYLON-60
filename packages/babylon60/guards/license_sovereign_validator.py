# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# Causal-Determinist: LICENSE SOVEREIGN VALIDATOR
# =================================================================================
# Verification Protocol: Cryptographic / HMAC License Transducer for Cortex Persist
# Domain Transducer Primitive: [720-895]
# Nominal Density Invariant: INV_C5_NOMINAL_DENSITY

import os
import hmac
import hashlib
import time
from typing import NamedTuple

# Secret salt for verifying structural hash of commercial keys
def _license_salt() -> bytes:
    """HMAC salt for license signing. No static fallback: a hardcoded salt lets
    anyone forge licenses for any tier. Provision out-of-band via env/KMS."""
    _s = os.environ.get("BABYLON60_LICENSE_SALT")
    if not _s:
        raise RuntimeError(
            "FATAL: BABYLON60_LICENSE_SALT env var required for license signing "
            "(zero static salt permitted)."
        )
    return _s.encode("utf-8")


class LicenseStatus(NamedTuple):
    is_valid: bool
    tier: str
    owner: str
    expires_at: int
    message: str


def generate_license_key(owner: str, tier: str, expires_at: int) -> str:
    """
    Pre: non-empty owner, valid tier str, future unix timestamp
    Exec: Generate HMAC-SHA256 signature payload formatted as owner:tier:expires_at:signature
    Post: returns deterministic license key string
    """
    assert len(owner) > 0, "Fail-fast: owner cannot be empty"
    assert tier in ("pro", "enterprise"), f"Fail-fast: invalid tier '{tier}'"
    assert expires_at > 0, "Fail-fast: expires_at must be positive int"

    payload = f"{owner}:{tier}:{expires_at}"
    sig = hmac.new(_license_salt(), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    return f"{payload}:{sig}"


def verify_license_key(key: str | None = None) -> LicenseStatus:
    """
    Pre: key string or None (if None, reads CORTEX_LICENSE_KEY env var)
    Exec: validate structural integrity and HMAC signature
    Post: returns LicenseStatus tuple
    """
    if key is None:
        key = (
            os.getenv("BABYLON60_LICENSE_KEY")
            or os.getenv("BABYLON_LICENSE_KEY")
            or os.getenv("CORTEX_LICENSE_KEY", "")
        ).strip()

    if not key:
        return LicenseStatus(
            is_valid=False,
            tier="community",
            owner="sovereign_community",
            expires_at=0,
            message="Operating under Sovereign Community License (Free/Non-commercial).",
        )

    parts = key.split(":")
    if len(parts) != 4:
        return LicenseStatus(
            is_valid=False,
            tier="invalid",
            owner="unknown",
            expires_at=0,
            message="Fail-fast: Invalid license key structure.",
        )

    owner, tier, exp_str, sig = parts
    try:
        expires_at = int(exp_str)
    except ValueError:
        return LicenseStatus(
            is_valid=False,
            tier="invalid",
            owner="unknown",
            expires_at=0,
            message="Fail-fast: Invalid license expiration format.",
        )

    payload = f"{owner}:{tier}:{exp_str}"
    expected_sig = hmac.new(_license_salt(), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:16]

    if not hmac.compare_digest(sig, expected_sig):
        return LicenseStatus(
            is_valid=False,
            tier="invalid",
            owner=owner,
            expires_at=expires_at,
            message="Fail-fast: Invalid cryptographic signature for license key.",
        )

    current_time = int(time.time())
    if expires_at < current_time:
        return LicenseStatus(
            is_valid=False,
            tier=tier,
            owner=owner,
            expires_at=expires_at,
            message=f"License expired at unix timestamp {expires_at}.",
        )

    return LicenseStatus(
        is_valid=True,
        tier=tier,
        owner=owner,
        expires_at=expires_at,
        message=f"Valid commercial license verified for {owner} [{tier.upper()}].",
    )
