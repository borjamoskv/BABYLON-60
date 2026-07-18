"""
BABYLON60 IDE — Sovereign Local Inference API routes (Ollama / MLX / Mamba).
Enforces C5-REAL Zero-Network Policy.
"""

from __future__ import annotations

import hashlib
import time
import urllib.request
import json
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/inference/local", tags=["inference"])


class InferenceRequest(BaseModel):
    prompt: str = Field(..., description="Prompt text for local silicon generation")
    model: str = Field(default="qwen2.5-coder:32b", description="Target model ID")
    base_url: str = Field(default="http://127.0.0.1:11434/v1", description="Local socket endpoint")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)


def validate_zero_network(url: str) -> None:
    lower = url.lower()
    forbidden = ["openai.com", "anthropic.com", "dashscope", "googleapis.com", "deepmind"]
    for domain in forbidden:
        if domain in lower:
            raise HTTPException(
                status_code=403,
                detail=f"C5-REAL VIOLATION: Zero-Network Policy breached. External endpoint '{domain}' is strictly forbidden."
            )
    if not lower.startswith("http://127.0.0.1") and not lower.startswith("http://localhost"):
        raise HTTPException(
            status_code=403,
            detail=f"C5-REAL VIOLATION: Endpoint '{url}' must be confined to loopback (127.0.0.1 / localhost)."
        )


@router.post("/generate")
def generate_local(req: InferenceRequest) -> dict[str, Any]:
    """Execute local inference against Ollama / MLX socket."""
    validate_zero_network(req.base_url)

    endpoint = f"{req.base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": req.model,
        "messages": [
            {
                "role": "system",
                "content": "You are MOSKV-1 APEX, a sovereign C5-REAL execution kernel operating on local Apple Silicon."
            },
            {
                "role": "user",
                "content": req.prompt
            }
        ],
        "temperature": req.temperature,
        "max_tokens": req.max_tokens,
        "stream": False
    }

    start_time = time.perf_counter()
    try:
        req_obj = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req_obj, timeout=30.0) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Local silicon inference socket failed at {endpoint}: {str(e)}"
        )

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    
    try:
        text = resp_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        text = ""

    token_count = max(1, len(text.split())) * 1.33
    tps = round(token_count / (latency_ms / 1000.0), 2) if latency_ms > 0 else 0.0
    sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()

    return {
        "text": text,
        "model": req.model,
        "tps": tps,
        "latency_ms": latency_ms,
        "sha256": sha256,
        "provider": "LOCAL_SILICON_FASTAPI_BRIDGE"
    }


@router.get("/status")
def status_local() -> dict[str, Any]:
    """Check if Ollama / MLX local inference daemon is running."""
    try:
        req_obj = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
        with urllib.request.urlopen(req_obj, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = [m.get("name") for m in data.get("models", []) if "name" in m]
        return {
            "status": "ONLINE",
            "provider": "Ollama/MLX Local Silicon",
            "endpoint": "http://127.0.0.1:11434",
            "models": models
        }
    except Exception:
        return {
            "status": "OFFLINE",
            "provider": "Ollama/MLX",
            "endpoint": "http://127.0.0.1:11434",
            "models": []
        }
