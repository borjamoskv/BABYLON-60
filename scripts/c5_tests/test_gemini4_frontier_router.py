#!/usr/bin/env python3
"""
Deterministic unit tests for `scripts.c5_orchestrator.gemini4_frontier_router`.
Verifies:
  1. `CARBON_ACTIVE` resolution when `models/gemini-4-carbon` appears in catalog.
  2. `FALLBACK_ARGON` resolution when `models/gemini-4-carbon` is gated/absent.
  3. 24-hour local cache hit & key-rotation cache invalidation (SHA-256 scope digest).
  4. `INV_C5_ARGON_GOVERNANCE` locks:
     - `max_output_tokens` Guillotine bounds [32768, 65536].
     - `thinking_level` rejects `"minimal"` and maps `"low" | "medium" | "high"`.
     - `automatic_continuation=False` enforced.
     - `FAIL_CLOSED` when neither Carbon nor Argon is present.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from google.genai import types

from scripts.c5_orchestrator.gemini4_frontier_router import (
    FALLBACK_MODEL,
    FLASH_FALLBACK_MODEL,
    PRIMARY_MODEL,
    build_gemini4_config,
    generate_content_frontier,
    is_quota_zero_error,
    resolve_gemini4_frontier,
)


class _DummyModelsAPI:
    def __init__(self, model_names: list[str]) -> None:
        self._model_names = model_names
        self.calls = 0

    def list(self) -> list[SimpleNamespace]:
        self.calls += 1
        return [SimpleNamespace(name=name) for name in self._model_names]


class _DummyClient:
    def __init__(self, model_names: list[str]) -> None:
        self.models = _DummyModelsAPI(model_names)


def test_resolve_fallback_argon_and_24h_cache_hit(tmp_path: Path) -> None:
    cache_file = tmp_path / "gemini4_catalog_cache.json"
    dummy_client = _DummyClient(
        ["models/gemini-3.8-flash", "models/gemini-4-argon"]
    )

    # First call: live query (cache_hit=False) -> FALLBACK_ARGON
    _, model_id, cfg, res1 = resolve_gemini4_frontier(
        thinking_level="low",
        max_output_tokens=32768,
        api_key="synthetic-key-alpha",
        client=dummy_client,
        cache_path=cache_file,
    )
    assert model_id == FALLBACK_MODEL
    assert res1.status == "FALLBACK_ARGON"
    assert res1.requested_model == PRIMARY_MODEL
    assert res1.cache_hit is False
    assert res1.catalog_count == 2
    assert cfg.automatic_continuation is False
    assert cfg.max_output_tokens == 32768
    assert cfg.thinking_config is not None
    assert cfg.thinking_config.thinking_level == types.ThinkingLevel.LOW
    assert dummy_client.models.calls == 1

    # Verify raw key is never persisted in cache file
    raw_cache_text = cache_file.read_text(encoding="utf-8")
    assert "synthetic-key-alpha" not in raw_cache_text
    parsed_cache = json.loads(raw_cache_text)
    assert len(parsed_cache["key_digest"]) == 16

    # Second call with same key: 24h cache hit (zero extra network calls)
    _, model_id_2, _, res2 = resolve_gemini4_frontier(
        thinking_level="medium",
        max_output_tokens=65536,
        api_key="synthetic-key-alpha",
        client=dummy_client,
        cache_path=cache_file,
    )
    assert model_id_2 == FALLBACK_MODEL
    assert res2.status == "FALLBACK_ARGON"
    assert res2.cache_hit is True
    assert dummy_client.models.calls == 1


def test_resolve_carbon_active_when_provisioned(tmp_path: Path) -> None:
    cache_file = tmp_path / "gemini4_catalog_cache.json"
    dummy_client = _DummyClient(
        [
            "models/gemini-3.8-flash",
            "models/gemini-4-argon",
            "models/gemini-4-carbon",
        ]
    )

    _, model_id, cfg, res = resolve_gemini4_frontier(
        thinking_level="high",
        max_output_tokens=65536,
        api_key="synthetic-key-fairwind",
        client=dummy_client,
        cache_path=cache_file,
    )
    assert model_id == PRIMARY_MODEL
    assert res.resolved_model == "gemini-4-carbon"
    assert res.status == "CARBON_ACTIVE"
    assert res.cache_hit is False
    assert res.catalog_count == 3
    assert cfg.automatic_continuation is False
    assert cfg.max_output_tokens == 65536
    assert cfg.thinking_config is not None
    assert cfg.thinking_config.thinking_level == types.ThinkingLevel.HIGH


def test_key_rotation_invalidates_cache_automatically(tmp_path: Path) -> None:
    cache_file = tmp_path / "gemini4_catalog_cache.json"
    client_argon_only = _DummyClient(["models/gemini-4-argon"])
    client_with_carbon = _DummyClient(
        ["models/gemini-4-argon", "models/gemini-4-carbon"]
    )

    _, m1, _, r1 = resolve_gemini4_frontier(
        api_key="key-standard-tier",
        client=client_argon_only,
        cache_path=cache_file,
    )
    assert m1 == "gemini-4-argon"
    assert r1.status == "FALLBACK_ARGON"

    # Rotating to a Fairwind-enabled key invalidates the cached digest automatically
    _, m2, _, r2 = resolve_gemini4_frontier(
        api_key="key-fairwind-tier",
        client=client_with_carbon,
        cache_path=cache_file,
    )
    assert m2 == "gemini-4-carbon"
    assert r2.status == "CARBON_ACTIVE"
    assert r2.cache_hit is False
    assert client_with_carbon.models.calls == 1


def test_argon_governance_invariants_enforced(tmp_path: Path) -> None:
    # 1. Rejects thinking_level="minimal"
    with pytest.raises(ValueError, match="INV_C5_ARGON_GOVERNANCE"):
        build_gemini4_config(thinking_level="minimal")  # type: ignore[arg-type]

    # 2. Rejects max_output_tokens below Guillotine floor (< 32768)
    with pytest.raises(ValueError, match="Guillotine bounds"):
        build_gemini4_config(max_output_tokens=16384)

    # 3. Rejects max_output_tokens above 65536
    with pytest.raises(ValueError, match="Guillotine bounds"):
        build_gemini4_config(max_output_tokens=131072)

    # 4. Fails closed if neither Carbon nor Argon is present in catalog
    empty_frontier_client = _DummyClient(["models/gemini-3.8-flash"])
    with pytest.raises(RuntimeError, match="FAIL_CLOSED"):
        resolve_gemini4_frontier(
            api_key="key-no-g4",
            client=empty_frontier_client,
            cache_path=tmp_path / "cache.json",
        )


class _DummyGenClient:
    def __init__(self, simulate_quota_zero: bool = False) -> None:
        self.simulate_quota_zero = simulate_quota_zero
        self.calls: list[tuple[str, str, types.GenerateContentConfig]] = []

    class _Models:
        def __init__(self, outer: _DummyGenClient) -> None:
            self._outer = outer

        def generate_content(
            self, model: str, contents: str, config: types.GenerateContentConfig
        ) -> SimpleNamespace:
            self._outer.calls.append((model, contents, config))
            if self._outer.simulate_quota_zero and model != FLASH_FALLBACK_MODEL:
                raise RuntimeError(
                    "429 RESOURCE_EXHAUSTED. Quota exceeded for metric: "
                    "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, "
                    "limit: 0, model: gemini-4-argon"
                )
            return SimpleNamespace(text=f"response from {model}")

    @property
    def models(self) -> _Models:
        return self._Models(self)


def test_is_quota_zero_error_classification() -> None:
    assert is_quota_zero_error(RuntimeError("429 RESOURCE_EXHAUSTED limit: 0")) is True
    assert is_quota_zero_error(RuntimeError("429 Free Tier limit exceeded")) is True
    assert is_quota_zero_error(RuntimeError("400 INVALID_ARGUMENT")) is False
    assert is_quota_zero_error(RuntimeError("500 INTERNAL_SERVER_ERROR")) is False


def test_generate_content_frontier_nominal_success() -> None:
    client = _DummyGenClient(simulate_quota_zero=False)
    cfg = build_gemini4_config(thinking_level="low")
    resp, used_model, fell_back = generate_content_frontier(
        client, "gemini-4-argon", "ping", cfg, allow_flash_fallback=False
    )
    assert used_model == "gemini-4-argon"
    assert fell_back is False
    assert resp.text == "response from gemini-4-argon"
    assert len(client.calls) == 1
    assert client.calls[0][0] == "gemini-4-argon"


def test_generate_content_frontier_raises_429_when_fallback_disabled() -> None:
    client = _DummyGenClient(simulate_quota_zero=True)
    cfg = build_gemini4_config(thinking_level="low")
    with pytest.raises(RuntimeError, match="429 RESOURCE_EXHAUSTED"):
        generate_content_frontier(
            client, "gemini-4-argon", "ping", cfg, allow_flash_fallback=False
        )
    assert len(client.calls) == 1


def test_generate_content_frontier_switches_to_flash_on_quota_zero() -> None:
    client = _DummyGenClient(simulate_quota_zero=True)
    cfg = build_gemini4_config(thinking_level="low")
    resp, used_model, fell_back = generate_content_frontier(
        client, "gemini-4-argon", "ping", cfg, allow_flash_fallback=True
    )
    assert used_model == FLASH_FALLBACK_MODEL
    assert fell_back is True
    assert resp.text == f"response from {FLASH_FALLBACK_MODEL}"
    assert len(client.calls) == 2
    assert client.calls[0][0] == "gemini-4-argon"
    assert client.calls[1][0] == FLASH_FALLBACK_MODEL
    # Config passed to Flash should strip Argon thinking_config
    flash_call_cfg = client.calls[1][2]
    assert flash_call_cfg.thinking_config is None

