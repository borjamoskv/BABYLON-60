#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED - OPENROUTER HIGH-EXERGY MCP BRIDGE
# file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/src/06_apps/mcp_c5_abi_bridge/openrouter_client.py

import os
import sys
import json
import time
import urllib.request
import urllib.error

# Import local C-ABI MCP server engine
sys.path.insert(0, os.path.dirname(__file__))
from mcp_server import purge_semantic_anergy_ffi, generate_scitt_cose_receipt

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

class OpenRouterExergyBridge:
    def __init__(self, api_key: str | None = None, default_model: str = "anthropic/claude-3.5-sonnet"):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.default_model = default_model

    def get_mcp_tools_schema(self) -> list[dict]:
        """Returns OpenRouter/OpenAI-compatible tool declarations for mcp-c5-abi-bridge."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "c5_abi_execute",
                    "description": "Ejecución bare-metal C-ABI FFI (< 1 μs) con firma atómica SHA3 y atestación SCITT COSE.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command_id": {"type": "string"},
                            "payload": {"type": "string"}
                        },
                        "required": ["command_id", "payload"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "c5_purge_context",
                    "description": "Purga de Anergía Semántica (Filtro Sustantivo-Verbo Landauer FFI) recortando tokens inútiles en > 90%.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "raw_text": {"type": "string"}
                        },
                        "required": ["raw_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "c5_autopoiesis",
                    "description": "Auto-evaluación homeostática y resíntesis determinista de estado C-ABI.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "current_state": {"type": "string"}
                        },
                        "required": ["current_state"]
                    }
                }
            }
        ]

    def chat_completion(
        self,
        prompt: str,
        system_instruction: str = "Eres un asistente de alta exergía operando bajo la arquitectura BABYLON-60 C5-REAL.",
        model: str | None = None,
        apply_landauer_prefilter: bool = True
    ) -> dict:
        """Sends a high-exergy completion request to OpenRouter with automated pre-purged tokens."""
        target_model = model or self.default_model

        # Landauer Pre-Filter: Purge anergy from prompt before sending to OpenRouter
        if apply_landauer_prefilter:
            purged_prompt, digest_hex, lat_us = purge_semantic_anergy_ffi(prompt)
            print(f"[C5 Landauer Pre-Filter] Original: {len(prompt)} chars -> Purgado: {len(purged_prompt)} chars (Latencia: {lat_us:.2f} μs)")
            effective_prompt = purged_prompt
        else:
            effective_prompt = prompt

        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": effective_prompt}
            ],
            "tools": self.get_mcp_tools_schema(),
            "temperature": 0.2
        }

        if not self.api_key:
            return {
                "status": "OFFLINE_SIMULATION",
                "message": "OPENROUTER_API_KEY no configurada. Simulación de respuesta de alta exergía realizada.",
                "effective_prompt": effective_prompt,
                "tools_available": [t["function"]["name"] for t in payload["tools"]]
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/borjamoskv/BABYLON-60",
            "X-Title": "BABYLON-60 C5-REAL",
            "Content-Type": "application/json"
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OPENROUTER_API_URL, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            return {"error": f"OpenRouter HTTP {e.code}", "details": error_body}

if __name__ == "__main__":
    print("=== C5-REAL OPENROUTER MCP EXERGY BRIDGE ===")
    bridge = OpenRouterExergyBridge()
    test_prompt = (
        "IMPORTANTE: Por favor ejecuta una verificación muy rápida y fantástica de estado "
        "y comprueba básicamente que todo es excelente y totalmente funcional."
    )
    result = bridge.chat_completion(test_prompt)
    print(json.dumps(result, indent=2))
