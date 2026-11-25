"""Native loopback-only Ollama transport; fixture-tested independently of inference."""

from __future__ import annotations

from typing import cast

import httpx

from .store import PilotError, decode, integer, mapping, response_schema


class ModelBindingError(RuntimeError):
    """The registered model alias/digest was not observed; no inference admitted."""


async def _read(
    client: httpx.AsyncClient, method: str, url: str, payload: dict[str, object] | None = None
) -> dict[str, object]:
    async with client.stream(method, url, json=payload) as response:
        response.raise_for_status()
        raw = bytearray()
        async for chunk in response.aiter_bytes():
            raw.extend(chunk)
            if len(raw) > 1024 * 1024:
                raise PilotError("Ollama response exceeds 1 MiB")
    return decode(bytes(raw))


async def native_completion(
    config: dict[str, object], messages: list[dict[str, str]], timeout: float, remaining: int
) -> dict[str, object]:
    request_timeout = httpx.Timeout(
        timeout, connect=min(10.0, timeout), pool=min(10.0, timeout), write=min(10.0, timeout)
    )
    async with httpx.AsyncClient(timeout=request_timeout, follow_redirects=False, trust_env=False) as client:
        tags = await _read(client, "GET", "http://127.0.0.1:11434/api/tags")
        models = tags.get("models")
        if not isinstance(models, list):
            raise ModelBindingError("Registered Ollama model inventory unavailable")
        matches = [mapping(model) for model in models if mapping(model).get("name") == config["model"]]
        if len(matches) != 1 or matches[0].get("digest") != config["model_digest"]:
            raise ModelBindingError("Registered Ollama model alias or manifest digest changed")
        payload = {
            "model": config["model"],
            "messages": messages,
            "stream": False,
            "think": False,
            "format": "json",
            "options": {"num_ctx": 8192, "num_predict": min(2048, remaining), "temperature": config["temperature"]},
            "keep_alive": "5m",
        }
        if config["backend"] == "ollama_structured_v3":
            payload["format"] = response_schema(str(config["response_contract"]))
        data = await _read(client, "POST", str(config["endpoint"]), payload)
    if data.get("done") is not True or data.get("model") != config["model"]:
        raise ModelBindingError("Ollama completion model mismatch or incomplete response")
    prompt = integer(data.get("prompt_eval_count"), 0, 10**8, "Ollama prompt_eval_count")
    completion = integer(data.get("eval_count"), 0, 10**8, "Ollama eval_count")
    content = mapping(data.get("message")).get("content")
    if not isinstance(content, str):
        raise PilotError("Ollama returned no final content")
    normalized: dict[str, object] = {
        "model": data["model"],
        "model_digest": config["model_digest"],
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": prompt + completion},
    }
    if isinstance(data.get("id"), str):
        normalized["id"] = cast(str, data["id"])
    return normalized
