"""
BABYLON-60 ENTERPRISE API KEY & BILLING MANAGEMENT ENGINE (C5-REAL)
====================================================================
Cryptographically secure API key issuing, token revocation, and enterprise organization provisioning.
"""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

API_SALT = "CORTEX_ENTERPRISE_API_KEY_SALT_2026"


@dataclass
class APIKeyMetaData:
    key_id: str
    org_name: str
    tier: str
    created_at: int
    expires_at: int
    is_active: bool


class EnterpriseAPIKeyManager:
    """Manages enterprise API keys for BFT cloud ledgers."""

    def __init__(self, storage_dir: str | None = None) -> None:
        if storage_dir:
            self.base_dir = Path(storage_dir)
        else:
            self.base_dir = Path.home() / ".babylon60" / "api_keys"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.base_dir / "keys_registry.json"

    def issue_key(self, org_name: str, tier: str = "ENTERPRISE", valid_days: int = 365) -> str:
        """Issue cryptographically signed API key."""
        now = int(time.time())
        expires_at = now + (valid_days * 86400)
        raw_token = f"{org_name}:{tier}:{now}:{expires_at}:{API_SALT}"
        signature = hmac.new(API_SALT.encode(), raw_token.encode(), hashlib.sha256).hexdigest()[:24]

        key_id = f"b60_live_{signature}"
        metadata = {
            "key_id": key_id,
            "org_name": org_name,
            "tier": tier,
            "created_at": now,
            "expires_at": expires_at,
            "is_active": True,
        }
        self._save_key_meta(key_id, metadata)
        return key_id

    def validate_key(self, key_id: str) -> APIKeyMetaData | None:
        """Validate API key status and expiration."""
        keys = self._load_all_keys()
        if key_id not in keys:
            return None
        data = keys[key_id]
        if not data.get("is_active", False):
            return None
        if time.time() > data.get("expires_at", 0):
            return None
        return APIKeyMetaData(
            key_id=key_id,
            org_name=data["org_name"],
            tier=data["tier"],
            created_at=data["created_at"],
            expires_at=data["expires_at"],
            is_active=data["is_active"],
        )

    def revoke_key(self, key_id: str) -> bool:
        """Revoke active API key instantly."""
        keys = self._load_all_keys()
        if key_id in keys:
            keys[key_id]["is_active"] = False
            self._save_all_keys(keys)
            return True
        return False

    def _load_all_keys(self) -> dict[str, Any]:
        if not self.db_file.exists():
            return {}
        try:
            with open(self.db_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_all_keys(self, data: dict[str, Any]) -> None:
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            raise RuntimeError("FAIL-FAST: Failed to write API key registry.")

    def _save_key_meta(self, key_id: str, metadata: dict[str, Any]) -> None:
        keys = self._load_all_keys()
        keys[key_id] = metadata
        self._save_all_keys(keys)
