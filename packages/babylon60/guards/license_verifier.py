"""
BABYLON-60 License Verifier (Hybrid License Verifier Bridge).
Connects legacy test harness to license_sovereign_validator primitives.
"""

import time
import json
from typing import Tuple, Dict, Any
from babylon60.guards.license_sovereign_validator import (
    generate_license_key,
    verify_license_key,
    LicenseStatus
)


class LicenseValidationError(Exception):
    pass


class HybridLicenseVerifier:
    @staticmethod
    def generate_license_payload(org: str, node: str, expires_at: int) -> Dict[str, Any]:
        tier = "enterprise"
        key = generate_license_key(f"{org}_{node}", tier, expires_at)
        return {
            "org": org,
            "node": node,
            "tier": tier,
            "expires_at": expires_at,
            "key": key
        }

    @staticmethod
    def verify_license_offline(license_json: str, expected_node: str) -> Tuple[bool, Dict[str, Any]]:
        try:
            data = json.loads(license_json)
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            raise LicenseValidationError(f"Invalid JSON format: {e}")

        key = data.get("key")
        status = verify_license_key(key)

        if not status.is_valid:
            raise LicenseValidationError(status.message)

        if expected_node and data.get("node") != expected_node:
            raise LicenseValidationError(f"Node mismatch: expected {expected_node}, got {data.get('node')}")

        return True, data

    @staticmethod
    def check_heartbeat_attestation(last_heartbeat_ts: int, max_offline_sec: int = 604800) -> Tuple[bool, str]:
        now = int(time.time())
        if (now - last_heartbeat_ts) > max_offline_sec:
            return False, "HEARTBEAT_EXPIRED_FALLBACK_QUARANTINE"
        return True, "HEARTBEAT_NOMINAL_ACTIVE"
