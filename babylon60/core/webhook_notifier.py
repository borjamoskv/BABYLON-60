"""
BABYLON-60 ENTERPRISE WEBHOOK NOTIFIER ENGINE (C5-REAL)
======================================================
Cryptographically signed webhook dispatcher for Enterprise BFT state events and billing notifications.
"""

import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request
from typing import Any

WEBHOOK_SIGNING_SALT = "CORTEX_WEBHOOK_SIGNATURE_SALT_2026"

class EnterpriseWebhookNotifier:
    """Dispatches cryptographically signed webhook notifications to Enterprise endpoints."""

    def __init__(self, secret_salt: str | None = None) -> None:
        self.secret_salt = secret_salt or WEBHOOK_SIGNING_SALT

    def sign_payload(self, payload_json: str, timestamp: int) -> str:
        """Generate HMAC-SHA256 signature for webhook payload verification."""
        signed_data = f"{timestamp}.{payload_json}"
        return hmac.new(self.secret_salt.encode(), signed_data.encode(), hashlib.sha256).hexdigest()

    def create_event(self, event_type: str, org_name: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create structured BFT webhook event."""
        now = int(time.time())
        payload = {
            "event_type": event_type,
            "org_name": org_name,
            "timestamp": now,
            "data": data,
        }
        payload_str = json.dumps(payload, sort_keys=True)
        signature = self.sign_payload(payload_str, now)
        return {
            "payload": payload,
            "headers": {
                "Content-Type": "application/json",
                "X-B60-Timestamp": str(now),
                "X-B60-Signature": signature,
                "X-C5-REAL": "Verified"
            }
        }

    def dispatch(self, url: str, event_type: str, org_name: str, data: dict[str, Any], timeout: float = 3.0) -> bool:
        """Send HTTP POST webhook payload to target enterprise server."""
        event_dict = self.create_event(event_type, org_name, data)
        body_bytes = json.dumps(event_dict["payload"], sort_keys=True).encode('utf-8')
        
        req = urllib.request.Request(url, data=body_bytes, headers=event_dict["headers"], method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return 200 <= response.status < 300
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            return False
