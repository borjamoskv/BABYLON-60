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
import re
from typing import NamedTuple


# A bridge owner contains two 60-character identifiers encoded as escaped JSON
# and base64 (up to 1,938 characters for astral Unicode). Keep bounded limits
# large enough for every identifier accepted by license_verifier.
MAX_OWNER_LENGTH = 2048
MAX_KEY_LENGTH = MAX_OWNER_LENGTH + 128


# Secret salt for verifying structural hash of commercial keys
def _license_salt() -> bytes:
    """HMAC salt for license signing. No static fallback: a hardcoded salt lets
    anyone forge licenses for any tier. Provision out-of-band via env/KMS."""
    _s = os.environ.get("BABYLON60_LICENSE_SALT")
    if not _s or len(_s.encode("utf-8")) < 32 or _s == "default_sovereign_hardened_salt_2026":
        raise RuntimeError(
            "BABYLON60_LICENSE_SALT must be an independently provisioned secret of at least 32 bytes; the historical public default is forbidden."
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
    if (
        not isinstance(owner, str)
        or not owner
        or len(owner) > MAX_OWNER_LENGTH
        or owner.strip() != owner
        or ":" in owner
        or any(ord(c) < 32 or ord(c) == 127 for c in owner)
    ):
        raise ValueError("Invalid licence owner")
    if tier not in ("pro", "enterprise"):
        raise ValueError("Unsupported licence tier")
    if type(expires_at) is not int or expires_at <= int(time.time()) or expires_at >= 2**53:
        raise ValueError("Licence expiry must be a future integer timestamp")

    payload = f"{owner}:{tier}:{expires_at}"
    sig = hmac.new(_license_salt(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def verify_license_key(key: str | None = None) -> LicenseStatus:
    """
    Pre: key string or None (if None, reads BABYLON60_LICENSE_KEY env var)
    Exec: validate structural integrity and HMAC signature
    Post: returns LicenseStatus tuple
    """
    if key is None:
        key = (os.getenv("BABYLON60_LICENSE_KEY") or os.getenv("BABYLON_LICENSE_KEY") or "").strip()

    if not key:
        return LicenseStatus(
            is_valid=False,
            tier="community",
            owner="sovereign_community",
            expires_at=0,
            message="Operating under Sovereign Community License (Free/Non-commercial).",
        )

    if not isinstance(key, str) or len(key) > MAX_KEY_LENGTH:
        return LicenseStatus(False, "invalid", "unknown", 0, "Invalid licence format.")

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
    if (
        not owner
        or len(owner) > MAX_OWNER_LENGTH
        or owner.strip() != owner
        or any(ord(c) < 32 or ord(c) == 127 for c in owner)
        or tier not in ("pro", "enterprise")
        or not re.fullmatch(r"[0-9]{1,16}", exp_str)
        or not re.fullmatch(r"(?:[0-9a-f]{16}|[0-9a-f]{64})", sig)
    ):
        return LicenseStatus(False, "invalid", "unknown", 0, "Invalid licence fields.")
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
    try:
        digest = hmac.new(_license_salt(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    except RuntimeError:
        return LicenseStatus(False, "invalid", owner, 0, "Licence verifier is not provisioned.")
    # Preserve verification of previously issued 16-hex signatures; new keys use all 64.
    expected_sig = digest[: len(sig)]

    if not hmac.compare_digest(sig, expected_sig):
        return LicenseStatus(
            is_valid=False,
            tier="invalid",
            owner=owner,
            expires_at=expires_at,
            message="Fail-fast: Invalid cryptographic signature for license key.",
        )

    current_time = int(time.time())
    if expires_at <= current_time or expires_at >= 2**53:
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
