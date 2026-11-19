"""HTTP and AI-review fixtures only: no network, model inference or efficacy claims."""

import asyncio
import json
from pathlib import Path
from typing import cast

import httpx
import pytest

from babylon60.cognitive_pilot import execution, judging, store


@pytest.fixture
def config() -> dict[str, object]:
    return {
        "backend": "gemini_compat",
        "model": "gemini-3.1-flash-lite",
        "reasoning_effort": "minimal",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "max_tokens": 6000,
        "max_calls": 1,
        "timeout": 120,
        "temperature": 0.3,
        "memory_bytes": 8192,
    }


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions?key=fixture",
        "https://generativelanguage.googleapis.com/v1beta/models",
        "https://generativelanguage.googleapis.com:8443/v1beta/openai/chat/completions",
        "https://example.com/v1beta/openai/chat/completions",
    ],
)
def test_gemini_rejects_wrong_authority_or_endpoint(config: dict[str, object], endpoint: str) -> None:
    with pytest.raises(store.PilotError):
        execution.Provider({**config, "endpoint": endpoint})


def test_gemini_explicit_effort_and_policy_are_frozen(tmp_path: Path, config: dict[str, object]) -> None:
    with pytest.raises(store.PilotError, match="cannot be disabled"):
        store.validate_config({**config, "reasoning_effort": "none"})
    directory = tmp_path / "frozen"
    plan = store.prepare(directory, config, repetitions=1)
    assert store.mapping(plan["provider_policy"])["reasoning_effort"] == "minimal"
    assert store.canonical(store.load(directory)) == store.canonical(plan)
    plan["provider_policy"] = {**store.mapping(plan["provider_policy"]), "reasoning_effort": "high"}
    plan.pop("plan_digest")
    plan["plan_digest"] = store.digest(plan)
    store.write(directory / "plan.json", plan, replace=True)
    with pytest.raises(store.PilotError, match="policy changed"):
        store.load(directory)


def test_gemini_http_fixture_uses_env_auth_explicit_effort_and_usage(
    config: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "id": "fixture-response-123",
                "model": "gemini-3.1-flash-lite",
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 23,
                    "total_tokens": 123,
                    "thought_text": "NOT-RETAINED-FIXTURE",
                },
                "choices": [{"message": {"content": '{"fixture":true}', "reasoning_content": "NOT-RETAINED-FIXTURE"}}],
            },
        )

    original = httpx.AsyncClient

    def client(**kwargs: object) -> httpx.AsyncClient:
        assert kwargs["follow_redirects"] is False and kwargs["trust_env"] is False
        timeout = kwargs["timeout"]
        assert isinstance(timeout, httpx.Timeout)
        assert timeout.read == 120 and timeout.connect == timeout.pool == timeout.write == 10
        return original(transport=httpx.MockTransport(respond), follow_redirects=False, trust_env=False)

    monkeypatch.setenv("GEMINI_API_KEY", "not-a-real-key-fixture")
    monkeypatch.setattr(httpx, "AsyncClient", client)
    provider = execution.Provider(config)
    assert asyncio.run(provider.call([{"role": "user", "content": "Public fixture only"}], 120)) == {"fixture": True}
    request = seen[0]
    assert request.headers["Authorization"] == "Bearer not-a-real-key-fixture"
    payload = json.loads(request.content)
    assert payload["model"] == "gemini-3.1-flash-lite"
    assert payload["reasoning_effort"] == "minimal"
    assert payload["response_format"] == {"type": "json_object"}
    assert "tools" not in payload and "extra_body" not in payload
    assert provider.calls == 1 and provider.tokens == 123
    assert provider.observations == [
        {
            "call": 1,
            "id": "fixture-response-123",
            "model": "gemini-3.1-flash-lite",
            "usage": {"prompt_tokens": 100, "completion_tokens": 23, "total_tokens": 123},
        }
    ]


def test_missing_gemini_key_fails_without_http(config: dict[str, object], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(store.PilotError, match="GEMINI_API_KEY"):
        asyncio.run(execution.Provider(config).call([], 1))


@pytest.mark.parametrize("status", [None, 503])
def test_provider_failure_receipt_has_safe_class_and_status_only(
    tmp_path: Path, config: dict[str, object], monkeypatch: pytest.MonkeyPatch, status: int | None
) -> None:
    directory = tmp_path / "failed-http"
    store.prepare(directory, config, repetitions=1)
    plan = store.load(directory)
    run = next(item for item in cast(list[dict[str, object]], plan["runs"]) if item["stage"] == "quality")
    request = httpx.Request(
        "POST", "https://example.com/?private=SECRET-CANARY", headers={"Authorization": "Bearer SECRET-CANARY"}
    )

    async def failed(self: execution.Provider, messages: list[dict[str, str]], timeout: float) -> dict[str, object]:
        if status is None:
            raise httpx.ReadTimeout("SECRET-CANARY", request=request)
        raise httpx.HTTPStatusError(
            "SECRET-CANARY", request=request, response=httpx.Response(status, text="SECRET-CANARY")
        )

    monkeypatch.setattr(execution.Provider, "call", failed)
    record = asyncio.run(execution.run_one(directory, plan, run))
    assert record["status"] == "blocked"
    assert record["provider_error_type"] == ("ReadTimeout" if status is None else "HTTPStatusError")
    assert record.get("provider_http_status") == status
    assert b"SECRET-CANARY" not in store.canonical(record)


@pytest.fixture
def anonymous(tmp_path: Path, config: dict[str, object]) -> Path:
    directory = tmp_path / "anonymous"
    store.prepare(directory, config, repetitions=1)
    judging.prepare_judging(directory, config, ["AI-fresh-1", "AI-fresh-2", "AI-fresh-3"], 18000)
    packet_id = "a" * 24
    store.write(
        directory / "blind" / packet_id / "packet.json",
        {
            "packet_id": packet_id,
            "specification": "Return a constant: test fixture only",
            "candidates": [{"source": "def solve(p):\n    return 0", "mechanism": "fixture constant"}],
            "grades": [{"quality": 100}],
            "selected": 0,
            "reference": "def solve(p): pass",
            "rubric": "Fixture mechanism labels only",
        },
    )
    return directory


def test_judging_freezes_before_first_attempt(tmp_path: Path, config: dict[str, object]) -> None:
    directory = tmp_path / "late"
    store.prepare(directory, config, repetitions=1)
    store.write(directory / "claims" / "fixture.json", {"attempted": True})
    with pytest.raises(store.PilotError, match="before the first"):
        judging.prepare_judging(directory, config, ["a", "b", "c"], 18000)


def test_three_fresh_ai_judgments_only_receive_blind_packet(anonymous: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    providers: list[execution.Provider] = []
    messages_seen: list[list[dict[str, str]]] = []

    async def fixture(self: execution.Provider, messages: list[dict[str, str]], timeout: float) -> dict[str, object]:
        providers.append(self)
        messages_seen.append(messages)
        self.tokens = 6000
        self.calls = 1
        return {
            "families": ["constant"],
            "originality": 0,
            "critical_violation": False,
            "evidence": "Returns a constant.",
        }

    monkeypatch.setattr(execution.Provider, "call", fixture)
    summary = asyncio.run(judging.run_judging(anonymous))
    assert summary["attempted_now"] == 3 and summary["provider_reported_tokens"] == 18000
    assert len({id(provider) for provider in providers}) == 3
    for messages in messages_seen:
        packet = store.decode(messages[1]["content"])
        assert set(packet) == {"packet_id", "specification", "candidates", "grades", "selected", "reference", "rubric"}
        assert "arm" not in packet and "public_cases" not in packet and "hidden" not in packet
    identities = [store.read(path)["reviewer_id"] for path in sorted((anonymous / "blind").glob("*/review[123].json"))]
    assert identities == ["AI-fresh-1", "AI-fresh-2", "AI-fresh-3"]
    assert asyncio.run(judging.run_judging(anonymous))["attempted_now"] == 0


def test_failed_ai_judgment_is_retained_without_silent_retry(anonymous: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def malformed(self: execution.Provider, messages: list[dict[str, str]], timeout: float) -> dict[str, object]:
        self.tokens = 100
        self.calls = 1
        return {"families": []}

    monkeypatch.setattr(execution.Provider, "call", malformed)
    assert asyncio.run(judging.run_judging(anonymous))["attempted_now"] == 3
    assert asyncio.run(judging.run_judging(anonymous))["attempted_now"] == 0
    receipts = [store.read(path) for path in (anonymous / "judge_receipts").glob("*.json")]
    assert all(receipt["status"] == "failed" for receipt in receipts)
    assert not list((anonymous / "blind").glob("*/review[123].json"))


def test_ai_judgment_http_failure_retains_safe_diagnostic(anonymous: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def failed(self: execution.Provider, messages: list[dict[str, str]], timeout: float) -> dict[str, object]:
        request = httpx.Request("POST", "https://example.com/?secret=SECRET-CANARY")
        raise httpx.HTTPStatusError(
            "SECRET-CANARY", request=request, response=httpx.Response(429, text="SECRET-CANARY")
        )

    monkeypatch.setattr(execution.Provider, "call", failed)
    assert asyncio.run(judging.run_judging(anonymous))["attempted_now"] == 2
    receipts = [store.read(path) for path in (anonymous / "judge_receipts").glob("*.json")]
    assert len(receipts) == 2
    for receipt in receipts:
        assert receipt["status"] == "blocked"
        assert receipt["provider_error_type"] == "HTTPStatusError" and receipt["provider_http_status"] == 429
        assert b"SECRET-CANARY" not in store.canonical(receipt)
