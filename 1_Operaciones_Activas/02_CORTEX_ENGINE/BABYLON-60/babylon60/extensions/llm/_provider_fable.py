# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
# This file is part of CORTEX. Apache-2.0.
# Reverse-Engineered Fable 5 Agentic Adapter
import asyncio
import logging
from typing import Any

import httpx

from babylon60.engine.causal.taint_engine import generate_secure_taint_token
from babylon60.extensions.llm._resilience import resilient_call
from babylon60.extensions.llm._stealth import apply_causal_jitter, sanitize_response
from babylon60.extensions.llm.fable_ffi import FableFFIClient

logger = logging.getLogger("babylon60_extensions.llm")


async def execute_fable_native(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    circuit_breaker: Any,
    provider_name: str,
    api_key: str,
    prompt: str,
    model_name: str = "claude-3-5-fable-20260609",
    system_prompt: str = "",
    tools: list[dict[str, Any]] | None = None,
    temperature: float = 0.0,
    max_tokens: int = 128000,
    cortex_private_key: str = "placeholder_key_b64",
) -> str:
    """
    Executes a deterministic call against Claude Fable 5, optimized for
    agentic tool orchestration and high steerability.
    Enforces CORTEX-TAINT structurally.
    """
    if tools is None:
        tools = []

    async def _call():
        ffi_client = FableFFIClient(api_key=api_key, client=client)

        # Inject structural Taint from CORTEX (Rule Ω3 / Axiom AX-045)
        # Binds the agentic workflow deterministically to the execution ledger
        taint_marker = generate_secure_taint_token(
            agent_id="fable-5-orchestrator",
            session_id="agentic_harness_01",
            content=prompt,
            private_key_b64=cortex_private_key,
        )

        payload: dict[str, Any] = {
            "model": model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": f"{system_prompt}\n\n[CORTEX-TAINT]: {taint_marker}",
            "messages": [{"role": "user", "content": prompt}],
        }

        if tools:
            payload["tools"] = tools
            # Force Steerability: Tool adherence mapping
            payload["tool_choice"] = {"type": "auto"}

        await apply_causal_jitter(tokens_estimate=100)

        async with semaphore:
            data = await ffi_client.invoke(payload, timeout=120.0)

        # Fable 5 Agentic Routing Verification
        if data["stop_reason"] == "tool_use":
            # Extract the deterministic AST from the agent (L1 invariant)
            tool_calls = [c for c in data["content"] if c["type"] == "tool_use"]
            logger.info("[CORTEX] Fable 5 orchestrated %s tool calls.", len(tool_calls))
            # Yield structured string; to be parsed by upstream causal engine
            return str(tool_calls)

        raw_content = next((c["text"] for c in data["content"] if c["type"] == "text"), "")
        return sanitize_response(raw_content)

    try:
        return await resilient_call(_call, provider_name, circuit_breaker)
    except httpx.HTTPStatusError as e:
        logger.error("Native Fable 5 API Failure: %s", e.response.text[:500])
        raise ValueError(f"HTTP {e.response.status_code} from native Fable 5") from e
