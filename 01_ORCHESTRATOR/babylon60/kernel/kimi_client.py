# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ KIMI K3 NATIVE CLIENT | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
kimi_client.py — Native Moonshot AI / Kimi K3 Client for BABYLON-60.
Transduced from CORTEX skills into native Python execution.
"""

import os
import json
import urllib.request
import urllib.error
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("babylon60.kernel.kimi_client")


class KimiClient:
    """Native API Client for Moonshot AI / Kimi K3 models."""

    BASE_URL = "https://api.moonshot.cn/v1"

    def __init__(self, api_key: Optional[str] = None, model: str = "kimi-k3-preview"):
        self.api_key = api_key or os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY")
        self.model = model

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def query(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 2048) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "success": False,
                "error": "Missing KIMI_API_KEY / MOONSHOT_API_KEY environment variable.",
                "remediation": "Set KIMI_API_KEY environment variable with a valid Moonshot AI token.",
            }

        url = f"{self.BASE_URL}/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": self.model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3}

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
                return {"success": True, "model": self.model, "content": content, "usage": result.get("usage", {})}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else str(e)
            logger.error("Kimi API HTTP error (%d): %s", e.code, err_body)
            return {
                "success": False,
                "code": e.code,
                "error": err_body,
                "remediation": "Verify API key permissions and endpoint status.",
            }
        except Exception as e:
            logger.error("Kimi API connection failure: %s", str(e))
            return {
                "success": False,
                "error": str(e),
                "remediation": "Check network connectivity to https://api.moonshot.cn.",
            }


def run_standalone_demo():
    client = KimiClient()
    if not client.is_configured():
        print("[KIMI_CLIENT] Unconfigured (KIMI_API_KEY missing). Ready for environment injection.")
    else:
        print("[KIMI_CLIENT] Configured. Querying Kimi K3 API...")
        res = client.query("Respond with 'C5-REAL Kimi Swarm Online'")
        print("[KIMI_CLIENT] Response:", res)


if __name__ == "__main__":
    run_standalone_demo()
