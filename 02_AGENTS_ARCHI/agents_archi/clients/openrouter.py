#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ OPENROUTER GATEWAY CLIENT | DOMAIN: agents.archi | STATE: C5-REAL
# ============================================================================
"""
Unified OpenRouter Gateway Client for hybrid model routing.
"""

import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any, Dict, Optional, List

logger = logging.getLogger("agents_archi.clients.openrouter")


class OpenRouterClient:
    """Unified OpenRouter API Gateway for frontier inference."""

    BASE_URL = "https://openrouter.ai/api/v1"

    DEFAULT_FALLBACK_MODELS = [
        "deepseek/deepseek-r1",
        "qwen/qwen-2.5-72b-instruct",
        "meta-llama/llama-3.3-70b-instruct",
    ]

    def __init__(self, api_key: Optional[str] = None, primary_model: str = "openrouter/auto"):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.environ.get("OPENROUTER_API_KEY") or ""
        self.primary_model = primary_model

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def query(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "success": False,
                "error": "Missing OPENROUTER_API_KEY environment variable.",
                "remediation": "Set OPENROUTER_API_KEY with a valid token or run in air-gapped local mode.",
            }

        target_model = model or self.primary_model
        url = f"{self.BASE_URL}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/borjamoskv/BABYLON-60",
            "X-Title": "BABYLON-60 Sovereign Kernel",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": target_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=45.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "model": target_model,
                    "content": content,
                    "usage": result.get("usage", {}),
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else str(e)
            logger.error("OpenRouter API error (%d): %s", e.code, err_body)
            return {"success": False, "error": f"HTTP {e.code}: {err_body}"}
        except Exception as e:
            logger.error("OpenRouter unexpected error: %s", str(e))
            return {"success": False, "error": str(e)}
