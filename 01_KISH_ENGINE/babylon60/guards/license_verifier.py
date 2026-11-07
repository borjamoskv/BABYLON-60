"""Bind signed licence fields to the organisation and node of the legacy bridge."""

import base64
import json
import time
from typing import TypedDict

from babylon60.guards.license_sovereign_validator import generate_license_key, verify_license_key


class LicenseValidationError(Exception):
    pass


class LicensePayload(TypedDict):
    org: str
    node: str
    tier: str
    expires_at: int
    key: str


def _owner(org: str, node: str) -> str:
    # Length-delimited JSON avoids the ambiguous legacy org_node concatenation.
    value = json.dumps([org, node], ensure_ascii=True, separators=(",", ":")).encode()
    return "node-v2." + base64.urlsafe_b64encode(value).decode().rstrip("=")


def _identifier(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 60
        or value.strip() != value
        or any(ord(c) < 32 or ord(c) == 127 for c in value)
    ):
        raise LicenseValidationError("Invalid organisation or node")
    return value


class HybridLicenseVerifier:
    @staticmethod
    def generate_license_payload(org: str, node: str, expires_at: int) -> LicensePayload:
        org = _identifier(org)
        node = _identifier(node)
        tier = "enterprise"
        key = generate_license_key(_owner(org, node), tier, expires_at)
        return {"org": org, "node": node, "tier": tier, "expires_at": expires_at, "key": key}

    @staticmethod
    def verify_license_offline(license_json: str, expected_node: str) -> tuple[bool, LicensePayload]:
        if not isinstance(license_json, str) or len(license_json) > 8192:
            raise LicenseValidationError("Invalid licence document")
        try:
            data = json.loads(license_json)
        except (json.JSONDecodeError, ValueError) as error:
            raise LicenseValidationError("Invalid JSON format") from error
        if not isinstance(data, dict):
            raise LicenseValidationError("Licence must be an object")
        org = _identifier(data.get("org"))
        node = _identifier(data.get("node"))
        key = data.get("key")
        if not isinstance(key, str) or not key:
            raise LicenseValidationError("Explicit signed licence key required")
        status = verify_license_key(key)
        if not status.is_valid:
            raise LicenseValidationError(status.message)
        legacy_owner = f"{org}_{node}" if "_" not in org and "_" not in node else None
        if status.owner != _owner(org, node) and status.owner != legacy_owner:
            raise LicenseValidationError("Signed organisation/node mismatch")
        if (
            data.get("tier") != status.tier
            or type(data.get("expires_at")) is not int
            or data.get("expires_at") != status.expires_at
        ):
            raise LicenseValidationError("Unsigned licence fields differ from signed payload")
        if expected_node and node != expected_node:
            raise LicenseValidationError("Node mismatch")
        return True, {"org": org, "node": node, "tier": status.tier, "expires_at": status.expires_at, "key": key}

    @staticmethod
    def check_heartbeat_attestation(last_heartbeat_ts: int, max_offline_sec: int = 604800) -> tuple[bool, str]:
        now = int(time.time())
        if last_heartbeat_ts > now or (now - last_heartbeat_ts) > max_offline_sec:
            return False, "HEARTBEAT_EXPIRED_FALLBACK_QUARANTINE"
        return True, "HEARTBEAT_NOMINAL_ACTIVE"
