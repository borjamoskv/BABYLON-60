import base64
import json
import logging
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger("babylon60.crypto.rekor")
REKOR_URL = "https://rekor.sigstore.dev"


class RekorClient:
    def __init__(self, rekor_url: str = REKOR_URL):
        self.rekor_url = rekor_url

    def anchor_payload(self, payload_hash: str, signature_b64: str, public_key_pem: str) -> dict[str, Any] | None:
        data = {
            "kind": "hashedrekord",
            "apiVersion": "0.0.1",
            "spec": {
                "signature": {
                    "content": signature_b64,
                    "publicKey": {"content": base64.b64encode(public_key_pem.encode("utf-8")).decode("utf-8")},
                },
                "data": {"hash": {"algorithm": "sha256", "value": payload_hash}},
            },
        }
        req = urllib.request.Request(
            f"{self.rekor_url}/api/v1/log/entries",
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in (201, 200):
                    response_body = response.read().decode("utf-8")
                    resp_json = json.loads(response_body)
                    if resp_json:
                        uuid = list(resp_json.keys())[0]
                        entry = resp_json[uuid]
                        logger.info(
                            "Successfully anchored to Rekor. UUID: %s, LogIndex: %s", uuid, entry.get("logIndex")
                        )
                        return {
                            "uuid": uuid,
                            "logIndex": entry.get("logIndex"),
                            "integratedTime": entry.get("integratedTime"),
                        }
        except urllib.error.HTTPError as e:
            logger.error("HTTPError anchoring to Rekor: %s - %s", e.code, e.read().decode("utf-8"))
        except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:
            logger.error("Failed to anchor to Rekor: %s", e)
        return None
