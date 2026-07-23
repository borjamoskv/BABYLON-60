"""
BABYLON60 IDE — Sovereign Local Inference API routes (Ollama / MLX / Mamba).
Enforces C5-REAL Zero-Network Policy.
"""

from __future__ import annotations

import hashlib
import time
import urllib.request
import json
from pathlib import Path
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
    except (urllib.error.URLError, json.JSONDecodeError, OSError, ConnectionError):
        return {
            "status": "OFFLINE",
            "provider": "Ollama/MLX",
            "endpoint": "http://127.0.0.1:11434",
            "models": []
        }


class MambaInferenceRequest(BaseModel):
    prompt: str = Field(..., description="Prompt text for local Mamba SSM generation")
    max_tokens: int = Field(default=10, ge=1, le=100)


@router.post("/mamba/generate")
def generate_mamba(req: MambaInferenceRequest) -> dict[str, Any]:
    """Execute local Mamba SSM inference integrated with GraphLedger."""
    try:
        # Import primitives from parent workspace dynamically
        import sys
        parent_dir = str(Path(__file__).resolve().parent.parent.parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        from core_graph_ledger import GraphLedger
        from cortex_bpe_tokenizer import BPETokenizer
        from cortex_mamba_network import MambaNetwork
        from net_mamba_ledger_engine import MambaLedgerEngine

        # JIT Initialization of lightweight Mamba Engine
        tokenizer = BPETokenizer()
        tokenizer.train("Lorem ipsum dolor sit amet. Babylon-60 is a C5-REAL sovereign kernel and Mamba network.", num_merges=10)
        network = MambaNetwork(vocab_size=len(tokenizer.vocab), d_model=16, d_state=8, n_layers=2)
        ledger = GraphLedger()
        engine = MambaLedgerEngine(tokenizer, network, ledger)

        text, cert = engine.mut_generate_audited(
            prompt=req.prompt,
            max_new_tokens=req.max_tokens,
            temperature=1.0,
            k=3
        )

        return {
            "text": text,
            "certificate": {
                "evidence_hash": cert.evidence_hash,
                "ruleset_hash": cert.ruleset_hash,
                "cert_hash": cert.cert_hash,
                "residual_microbits": cert.residual_microbits,
                "nodes_count": len(ledger.crdt.state)
            },
            "provider": "NATIVE_MAMBA_SSM_LEDGER_ENGINE",
            "vocab_size": len(tokenizer.vocab)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Native Mamba inference failed: {str(e)}"
        )
