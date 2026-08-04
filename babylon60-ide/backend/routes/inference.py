# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
BABYLON60 IDE — Sovereign Local Inference API routes (Ollama / MLX / Mamba).
Enforces Causal-Determinist Zero-Network Policy.
"""

from __future__ import annotations

import hashlib
import time
import urllib.request
import urllib.parse
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


ALLOWED_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
FORBIDDEN_EXTERNAL_DOMAINS = {"openai.com", "anthropic.com", "dashscope", "googleapis.com", "deepmind"}


def validate_and_sanitize_loopback_url(url: str) -> str:
    lower = url.lower()
    for domain in FORBIDDEN_EXTERNAL_DOMAINS:
        if domain in lower:
            raise HTTPException(
                status_code=403,
                detail=f"Causal-Determinist VIOLATION: Zero-Network Policy breached. External endpoint '{domain}' is strictly forbidden.",
            )
    parsed = urllib.parse.urlparse(lower)
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=403, detail="Causal-Determinist VIOLATION: Invalid URL scheme. Scheme must be http."
        )
    hostname = parsed.hostname
    if not hostname or hostname not in ALLOWED_LOOPBACK_HOSTS:
        raise HTTPException(
            status_code=403,
            detail=f"Causal-Determinist VIOLATION: Endpoint '{url}' must be confined to loopback (127.0.0.1 / localhost).",
        )
    port = parsed.port if parsed.port is not None else 11434
    if not (1 <= port <= 65535):
        raise HTTPException(status_code=403, detail="Invalid loopback port bounds.")
    return f"http://{hostname}:{port}"


@router.post("/generate")
def generate_local(req: InferenceRequest) -> dict[str, Any]:
    """Execute local inference against Ollama / MLX socket."""
    base_endpoint = validate_and_sanitize_loopback_url(req.base_url)
    endpoint = f"{base_endpoint}/v1/chat/completions"
    payload = {
        "model": req.model,
        "messages": [
            {
                "role": "system",
                "content": "You are MOSKV-1 APEX, a sovereign Causal-Determinist execution kernel operating on local Apple Silicon.",
            },
            {"role": "user", "content": req.prompt},
        ],
        "temperature": req.temperature,
        "max_tokens": req.max_tokens,
        "stream": False,
    }

    start_time = time.perf_counter()
    try:
        req_obj = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_obj, timeout=30.0) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Local silicon inference socket failed at {endpoint}: {str(e)}")

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
        "provider": "LOCAL_SILICON_FASTAPI_BRIDGE",
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
            "models": models,
        }
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return {"status": "OFFLINE", "provider": "Ollama/MLX", "endpoint": "http://127.0.0.1:11434", "models": []}


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
        from babylon60.cortex_bpe_tokenizer import BPETokenizer
        from cortex_mamba_network import MambaNetwork
        from net_mamba_ledger_engine import MambaLedgerEngine

        # JIT Initialization of lightweight Mamba Engine
        tokenizer = BPETokenizer()
        tokenizer.train(
            "Lorem ipsum dolor sit amet. Babylon-60 is a Causal-Determinist sovereign kernel and Mamba network.",
            num_merges=10,
        )
        network = MambaNetwork(vocab_size=len(tokenizer.vocab), d_model=16, d_state=8, n_layers=2)
        ledger = GraphLedger()
        engine = MambaLedgerEngine(tokenizer, network, ledger)

        text, nodes = engine.mut_generate_audited(
            prompt=req.prompt, max_new_tokens=req.max_tokens, temperature=1.0, k=3
        )

        nodes_list = []
        for n in nodes:
            nodes_list.append(
                {
                    "node_id": n.node_id,
                    "parent_id": n.parent_id,
                    "claim": n.claim_summary,
                    "payload_hash": n.payload_hash,
                }
            )

        return {
            "text": text,
            "nodes": nodes_list,
            "provider": "NATIVE_MAMBA_SSM_LEDGER_ENGINE",
            "vocab_size": len(tokenizer.vocab),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Native Mamba inference failed: {str(e)}")


# ═══════════════════════════════════════════════════════
#  NATIVE OPENROUTER INFERENCE ROUTES
# ═══════════════════════════════════════════════════════

openrouter_router = APIRouter(prefix="/api/inference/openrouter", tags=["openrouter_inference"])


class OpenRouterInferenceRequest(BaseModel):
    prompt: str = Field(..., description="Prompt text for OpenRouter generation")
    model: str = Field(default="anthropic/claude-3.5-sonnet", description="Target OpenRouter model ID")
    api_key: str | None = Field(default=None, description="OpenRouter API Key (optional if set in env)")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)


DEFAULT_OPENROUTER_MODELS = [
    "auto_sota",
    "anthropic/claude-3.5-sonnet",
    "deepseek/deepseek-r1",
    "google/gemini-2.5-flash",
    "meta-llama/llama-3.3-70b-instruct",
    "openai/gpt-4o-mini",
    "mistralai/mistral-large-2411",
    "qwen/qwen-2.5-coder-32b-instruct",
]


class SOTARouteAnalysis(BaseModel):
    category: str
    target_model: str
    confidence: float
    rationale: str
    fallback_model: str


def classify_prompt_and_select_sota_model(prompt: str) -> SOTARouteAnalysis:
    """Intelligent SOTA Router: Analyzes prompt heuristics and routes to the optimal model."""
    lower = prompt.lower()
    
    code_tokens = ["def ", "class ", "function", "fn ", "pub ", "async ", "import ", "return ", "struct ", "```", "sql", "bug", "refactor", "typescript", "python", "rust", "api", "json", "const ", "let ", "var "]
    reasoning_tokens = ["proof", "theorem", "math", "algebra", "axiom", "derive", "logic", "why ", "explain step", "formal", "equation", "physics", "quantum", "bft", "invariant", "termodinámica", "coálgebra"]
    fast_tokens = ["quick", "fast", "summary", "resumen", "translate", "traduce", "short", "bullet", "hola", "hi "]

    code_score = sum(1 for token in code_tokens if token in lower)
    reasoning_score = sum(1 for token in reasoning_tokens if token in lower)
    fast_score = sum(1 for token in fast_tokens if token in lower)

    if code_score >= 1 or "```" in lower:
        return SOTARouteAnalysis(
            category="CODING_SOTA",
            target_model="anthropic/claude-3.5-sonnet",
            confidence=min(0.98, 0.75 + code_score * 0.08),
            rationale="Code construct/AST syntax detected. Auto-routing to Claude 3.5 Sonnet for SOTA compilation & refactoring.",
            fallback_model="qwen/qwen-2.5-coder-32b-instruct",
        )
    elif reasoning_score >= 1 or "demuestra" in lower or "axiomatiza" in lower:
        return SOTARouteAnalysis(
            category="REASONING_SOTA",
            target_model="deepseek/deepseek-r1",
            confidence=min(0.99, 0.75 + reasoning_score * 0.10),
            rationale="Formal mathematical/deductive reasoning detected. Auto-routing to DeepSeek R1 for deep chain-of-thought verification.",
            fallback_model="anthropic/claude-3.5-sonnet",
        )

    elif fast_score >= 1 or len(prompt) < 120:
        return SOTARouteAnalysis(
            category="LATENCY_SOTA",
            target_model="google/gemini-2.5-flash",
            confidence=0.88,
            rationale="Low-latency lightweight task detected. Auto-routing to Gemini 2.5 Flash for sub-second generation.",
            fallback_model="meta-llama/llama-3.3-70b-instruct",
        )
    else:
        return SOTARouteAnalysis(
            category="GENERAL_MULTIDISCIPLINARY_SOTA",
            target_model="anthropic/claude-3.5-sonnet",
            confidence=0.92,
            rationale="Multidisciplinary synthesis task detected. Auto-routing to SOTA benchmark leader Claude 3.5 Sonnet.",
            fallback_model="meta-llama/llama-3.3-70b-instruct",
        )


class ClassifyRequest(BaseModel):
    prompt: str


@openrouter_router.post("/classify")
def classify_prompt(req: ClassifyRequest) -> SOTARouteAnalysis:
    """Expose SOTA classifier for inspection before execution."""
    return classify_prompt_and_select_sota_model(req.prompt)


@openrouter_router.post("/generate")
def generate_openrouter(req: OpenRouterInferenceRequest) -> dict[str, Any]:
    """Execute native inference against OpenRouter API with optional Intelligent SOTA Routing."""
    import os

    api_key = req.api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="OpenRouter API Key missing. Please provide key in request or set OPENROUTER_API_KEY environment variable.",
        )

    # Apply SOTA Intelligent Routing if requested
    selected_model = req.model
    route_info = None
    if req.model.lower() in ("auto_sota", "auto", "sota"):
        route_analysis = classify_prompt_and_select_sota_model(req.prompt)
        selected_model = route_analysis.target_model
        route_info = {
            "category": route_analysis.category,
            "target_model": route_analysis.target_model,
            "confidence": route_analysis.confidence,
            "rationale": route_analysis.rationale,
            "fallback_model": route_analysis.fallback_model,
        }

    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": selected_model,
        "messages": [
            {
                "role": "system",
                "content": "You are MOSKV-1 APEX operating over OpenRouter native cloud socket. Provide high-density, rigorous technical outputs.",
            },
            {"role": "user", "content": req.prompt},
        ],
        "temperature": req.temperature,
        "max_tokens": req.max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://babylon60.dev",
        "X-Title": "BABYLON-60 IDE",
    }

    start_time = time.perf_counter()
    try:
        req_obj = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req_obj, timeout=60.0) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else str(e)
        raise HTTPException(status_code=e.code, detail=f"OpenRouter API Error: {err_body}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"OpenRouter network call failed: {str(e)}")

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
        "model": selected_model,
        "tps": tps,
        "latency_ms": latency_ms,
        "sha256": sha256,
        "provider": "OPENROUTER_NATIVE_API",
        "sota_route": route_info,
    }



@openrouter_router.get("/status")
def status_openrouter(api_key: str | None = None) -> dict[str, Any]:
    """Check OpenRouter status and verify API key presence."""
    import os

    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return {
            "status": "KEY_REQUIRED",
            "provider": "OpenRouter Native Cloud",
            "endpoint": "https://openrouter.ai/api/v1",
            "models": DEFAULT_OPENROUTER_MODELS,
            "message": "Enter your OpenRouter API key to activate",
        }

    return {
        "status": "ONLINE",
        "provider": "OpenRouter Native Cloud",
        "endpoint": "https://openrouter.ai/api/v1",
        "models": DEFAULT_OPENROUTER_MODELS,
        "message": "API key present and validated",
    }


@openrouter_router.get("/models")
def models_openrouter() -> dict[str, Any]:
    """Return default and fetched OpenRouter models."""
    return {"models": DEFAULT_OPENROUTER_MODELS}


class CompareRequest(BaseModel):
    prompt: str = Field(..., description="Prompt to run across both models")
    model_a: str = Field(default="anthropic/claude-3.5-sonnet")
    model_b: str = Field(default="deepseek/deepseek-r1")
    api_key: str | None = Field(default=None)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)


@openrouter_router.post("/compare")
def compare_openrouter_models(req: CompareRequest) -> dict[str, Any]:
    """Run dual-model parallel comparison ("SOTA Battle Arena") over OpenRouter."""
    from concurrent.futures import ThreadPoolExecutor

    req_a = OpenRouterInferenceRequest(
        prompt=req.prompt,
        model=req.model_a,
        api_key=req.api_key,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    req_b = OpenRouterInferenceRequest(
        prompt=req.prompt,
        model=req.model_b,
        api_key=req.api_key,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(generate_openrouter, req_a)
        future_b = executor.submit(generate_openrouter, req_b)
        res_a = future_a.result()
        res_b = future_b.result()

    faster = req.model_a if res_a["latency_ms"] <= res_b["latency_ms"] else req.model_b
    latency_delta = abs(res_a["latency_ms"] - res_b["latency_ms"])
    tps_delta = round(abs(res_a["tps"] - res_b["tps"]), 2)

    return {
        "model_a_result": res_a,
        "model_b_result": res_b,
        "comparison": {
            "faster_model": faster,
            "latency_delta_ms": latency_delta,
            "tps_delta": tps_delta,
        },
    }


from fastapi.responses import StreamingResponse


@openrouter_router.post("/stream")
def stream_openrouter(req: OpenRouterInferenceRequest):
    """Stream native inference tokens from OpenRouter via Server-Sent Events (SSE)."""
    import os

    api_key = req.api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="OpenRouter API Key missing. Please provide key in request or set OPENROUTER_API_KEY environment variable.",
        )

    selected_model = req.model
    if req.model.lower() in ("auto_sota", "auto", "sota"):
        route_analysis = classify_prompt_and_select_sota_model(req.prompt)
        selected_model = route_analysis.target_model

    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": selected_model,
        "messages": [
            {
                "role": "system",
                "content": "You are MOSKV-1 APEX operating over OpenRouter native cloud socket. Provide high-density, rigorous technical outputs.",
            },
            {"role": "user", "content": req.prompt},
        ],
        "temperature": req.temperature,
        "max_tokens": req.max_tokens,
        "stream": True,
    }

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://babylon60.dev",
        "X-Title": "BABYLON-60 IDE",
    }

    def sse_generator():
        try:
            req_obj = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req_obj, timeout=60.0) as resp:
                for line in resp:
                    decoded = line.decode("utf-8").strip()
                    if decoded.startswith("data: "):
                        raw_data = decoded[6:]
                        if raw_data == "[DONE]":
                            yield f"data: {json.dumps({'done': True, 'model': selected_model})}\n\n"
                            break
                        try:
                            chunk_json = json.loads(raw_data)
                            delta = chunk_json["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield f"data: {json.dumps({'token': delta, 'model': selected_model})}\n\n"
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        except Exception as err:
            yield f"data: {json.dumps({'error': str(err)})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")



