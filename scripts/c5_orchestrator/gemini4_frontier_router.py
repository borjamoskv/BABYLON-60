#!/usr/bin/env python3
"""
C5-REAL · Gemini 4 Frontier Router (Carbon -> Argon Deterministic Fallback)
Compatible with google-genai SDK v2.31.0+

Enforces INV_C5_ARGON_GOVERNANCE:
  1. Resolves `gemini-4-carbon` against the active project catalog (`v1beta/models`)
     using an atomic 24-hour local cache (key-scoped via SHA-256 digest, zero secret leakage).
  2. Falls back deterministically to `gemini-4-argon` while `gemini-4-carbon` remains gated.
  3. Applies strict Gemini 4 safety locks on `types.GenerateContentConfig`:
     - `max_output_tokens` bounded in [32768, 65536] (default 32768 Guillotine floor).
     - `thinking_level` restricted to {"low", "medium", "high"} ("minimal" and `thinking_budget` vetoed).
     - `automatic_continuation=False` to prevent multi-turn billing runaway.
     - Zero `temperature`/`top_p`/`top_k`/`cached_content` injection (Implicit Caching preserved).
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Literal

from google import genai
from google.genai import types

ThinkingTier = Literal["low", "medium", "high"]

PRIMARY_MODEL = "gemini-4-carbon"
FALLBACK_MODEL = "gemini-4-argon"
FLASH_FALLBACK_MODEL = "gemini-3.8-flash"
DEFAULT_CACHE_TTL_SECONDS = 86_400  # 24 hours
MIN_SAFE_OUTPUT_TOKENS = 32_768
MAX_SAFE_OUTPUT_TOKENS = 65_536

_LEVEL_MAP: dict[str, types.ThinkingLevel] = {
    "low": types.ThinkingLevel.LOW,
    "medium": types.ThinkingLevel.MEDIUM,
    "high": types.ThinkingLevel.HIGH,
}

DEFAULT_CACHE_PATH = (
    Path.home() / ".cache" / "c5_gemini" / "gemini4_catalog_cache.json"
)


@dataclasses.dataclass(frozen=True)
class ModelResolution:
    resolved_model: str
    requested_model: str
    status: Literal["CARBON_ACTIVE", "FALLBACK_ARGON"]
    cache_hit: bool
    cache_age_seconds: float
    catalog_count: int
    thinking_level: str
    max_output_tokens: int
    automatic_continuation: bool


def _resolve_api_key(explicit_key: str | None = None) -> str:
    key = (
        explicit_key
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    if not key:
        raise RuntimeError(
            "FAIL_CLOSED: Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set in environment."
        )
    return key


def _key_scope_digest(api_key: str) -> str:
    """Returns a non-reversible 16-hex-char SHA-256 fingerprint of the credential."""
    return hashlib.sha256(f"c5-gemini4-scope:{api_key}".encode("utf-8")).hexdigest()[:16]


def _read_catalog_cache(
    cache_path: Path, key_digest: str, ttl_seconds: int
) -> tuple[list[str], float] | None:
    if not cache_path.is_file():
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        if payload.get("key_digest") != key_digest:
            return None
        fetched_at = float(payload.get("fetched_at", 0.0))
        age = time.time() - fetched_at
        if age < 0 or age > ttl_seconds:
            return None
        models = payload.get("models")
        if not isinstance(models, list) or not models:
            return None
        return [str(m) for m in models], age
    except Exception:
        return None


def _write_catalog_cache(
    cache_path: Path, key_digest: str, models: list[str]
) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "key_digest": key_digest,
        "fetched_at": time.time(),
        "models": sorted(set(models)),
    }
    fd, tmp_name = tempfile.mkstemp(
        prefix=".gemini4_cache_", dir=str(cache_path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, cache_path)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def fetch_available_models(
    client: Any,
    *,
    api_key: str,
    cache_path: Path = DEFAULT_CACHE_PATH,
    ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    force_refresh: bool = False,
) -> tuple[list[str], bool, float]:
    """
    Returns (model_names, cache_hit, cache_age_seconds) using zero-token metadata listing.
    """
    digest = _key_scope_digest(api_key)
    if not force_refresh:
        cached = _read_catalog_cache(cache_path, digest, ttl_seconds)
        if cached is not None:
            models, age = cached
            return models, True, age

    models: list[str] = []
    for item in client.models.list():
        name = getattr(item, "name", None)
        if name:
            models.append(str(name).removeprefix("models/"))

    if not models:
        raise RuntimeError("FAIL_CLOSED: Empty model catalog returned by endpoint.")

    _write_catalog_cache(cache_path, digest, models)
    return models, False, 0.0


def build_gemini4_config(
    *,
    thinking_level: ThinkingTier = "low",
    max_output_tokens: int = MIN_SAFE_OUTPUT_TOKENS,
    include_thoughts: bool = False,
    response_schema: Any | None = None,
    system_instruction: str | None = None,
) -> types.GenerateContentConfig:
    """
    Constructs a GenerateContentConfig strictly adhering to INV_C5_ARGON_GOVERNANCE.
    """
    norm_level = thinking_level.strip().lower()
    if norm_level not in _LEVEL_MAP:
        raise ValueError(
            f"INV_C5_ARGON_GOVERNANCE violation: Invalid thinking_level={thinking_level!r}. "
            f"Allowed values for Gemini 4 series: {sorted(_LEVEL_MAP.keys())} ('minimal' is forbidden)."
        )

    if not (MIN_SAFE_OUTPUT_TOKENS <= max_output_tokens <= MAX_SAFE_OUTPUT_TOKENS):
        raise ValueError(
            f"INV_C5_ARGON_GOVERNANCE violation: max_output_tokens={max_output_tokens} "
            f"violates Guillotine bounds [{MIN_SAFE_OUTPUT_TOKENS}, {MAX_SAFE_OUTPUT_TOKENS}]."
        )

    kwargs: dict[str, Any] = {
        "max_output_tokens": max_output_tokens,
        "automatic_continuation": False,
        "thinking_config": types.ThinkingConfig(
            thinking_level=_LEVEL_MAP[norm_level],
            include_thoughts=include_thoughts,
        ),
    }
    if system_instruction is not None:
        kwargs["system_instruction"] = system_instruction
    if response_schema is not None:
        kwargs["response_mime_type"] = "application/json"
        kwargs["response_schema"] = response_schema

    return types.GenerateContentConfig(**kwargs)


def resolve_gemini4_frontier(
    *,
    thinking_level: ThinkingTier = "low",
    max_output_tokens: int = MIN_SAFE_OUTPUT_TOKENS,
    include_thoughts: bool = False,
    response_schema: Any | None = None,
    system_instruction: str | None = None,
    api_key: str | None = None,
    client: Any | None = None,
    cache_path: Path = DEFAULT_CACHE_PATH,
    ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    force_refresh: bool = False,
) -> tuple[Any, str, types.GenerateContentConfig, ModelResolution]:
    """
    Resolves `gemini-4-carbon` if enabled in the active catalog, falling back
    deterministically to `gemini-4-argon`, and returns:
        (client, model_id, generate_content_config, resolution_telemetry)
    """
    resolved_key = _resolve_api_key(api_key)
    active_client = client if client is not None else genai.Client(api_key=resolved_key)
    config = build_gemini4_config(
        thinking_level=thinking_level,
        max_output_tokens=max_output_tokens,
        include_thoughts=include_thoughts,
        response_schema=response_schema,
        system_instruction=system_instruction,
    )

    catalog, cache_hit, age = fetch_available_models(
        active_client,
        api_key=resolved_key,
        cache_path=cache_path,
        ttl_seconds=ttl_seconds,
        force_refresh=force_refresh,
    )
    catalog_set = set(catalog)

    if PRIMARY_MODEL in catalog_set:
        chosen = PRIMARY_MODEL
        status: Literal["CARBON_ACTIVE", "FALLBACK_ARGON"] = "CARBON_ACTIVE"
    elif FALLBACK_MODEL in catalog_set:
        chosen = FALLBACK_MODEL
        status = "FALLBACK_ARGON"
    else:
        raise RuntimeError(
            f"FAIL_CLOSED: Neither {PRIMARY_MODEL!r} nor {FALLBACK_MODEL!r} "
            "is available in the authenticated catalog."
        )

    resolution = ModelResolution(
        resolved_model=chosen,
        requested_model=PRIMARY_MODEL,
        status=status,
        cache_hit=cache_hit,
        cache_age_seconds=round(age, 3),
        catalog_count=len(catalog_set),
        thinking_level=thinking_level.lower(),
        max_output_tokens=max_output_tokens,
        automatic_continuation=bool(config.automatic_continuation),
    )
    return active_client, chosen, config, resolution


def is_quota_zero_error(exc: Exception) -> bool:
    """Detects whether an exception corresponds to a Free Tier 0-quota exhaustion."""
    msg = str(exc).lower()
    return "429" in msg and (
        "limit: 0" in msg
        or "free_tier" in msg
        or "free tier" in msg
        or "resource_exhausted" in msg
    )


def generate_content_frontier(
    client: Any,
    model_id: str,
    contents: Any,
    config: types.GenerateContentConfig,
    *,
    allow_flash_fallback: bool = False,
) -> tuple[Any, str, bool]:
    """
    Executes client.models.generate_content.
    If `allow_flash_fallback=True` and a 429 quota-zero error (Free Tier limit: 0)
    occurs on a Gemini 4 model, seamlessly falls back to `gemini-3.8-flash`
    with a sanitized GenerateContentConfig.

    Returns:
        (response, model_used, fallback_triggered)
    """
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=contents,
            config=config,
        )
        return response, model_id, False
    except Exception as exc:
        if allow_flash_fallback and is_quota_zero_error(exc):
            flash_config = types.GenerateContentConfig(
                max_output_tokens=min(config.max_output_tokens or 65536, 65536),
                automatic_continuation=False,
                response_mime_type=config.response_mime_type,
                response_schema=config.response_schema,
                system_instruction=config.system_instruction,
            )
            response = client.models.generate_content(
                model=FLASH_FALLBACK_MODEL,
                contents=contents,
                config=flash_config,
            )
            return response, FLASH_FALLBACK_MODEL, True
        raise


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="C5-REAL Gemini 4 Frontier Router (Carbon -> Argon deterministic fallback)"
    )
    parser.add_argument(
        "--level",
        default="low",
        choices=["low", "medium", "high"],
        help="Thinking effort level for Gemini 4 (default: low)",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=MIN_SAFE_OUTPUT_TOKENS,
        help=f"Safety Guillotine cap in [{MIN_SAFE_OUTPUT_TOKENS}, {MAX_SAFE_OUTPUT_TOKENS}]",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Bypass the 24h local catalog cache and query v1beta/models",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Execute a test generate_content call with the resolved model",
    )
    parser.add_argument(
        "--allow-flash-fallback",
        action="store_true",
        help="Fallback to gemini-3.8-flash if Gemini 4 returns 429 limit: 0",
    )
    args = parser.parse_args(argv)

    client, chosen, cfg, res = resolve_gemini4_frontier(
        thinking_level=args.level,
        max_output_tokens=args.max_output_tokens,
        force_refresh=args.force_refresh,
    )
    print(json.dumps(dataclasses.asdict(res), indent=2))

    if args.prompt:
        resp, used_model, fell_back = generate_content_frontier(
            client,
            chosen,
            args.prompt,
            cfg,
            allow_flash_fallback=args.allow_flash_fallback,
        )
        print(f"INFERENCE_MODEL_USED: {used_model}")
        print(f"FLASH_FALLBACK_TRIGGERED: {fell_back}")
        print(f"OUTPUT:\n{getattr(resp, 'text', str(resp))}")

    return 0


if __name__ == "__main__":
    sys.exit(_main())
