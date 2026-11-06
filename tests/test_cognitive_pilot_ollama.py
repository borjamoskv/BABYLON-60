"""Native Ollama transport fixtures: no model loading, inference or network."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from babylon60.cognitive_pilot import __main__ as runner
from babylon60.cognitive_pilot import execution, judging, ollama, store


@pytest.fixture
def config() -> dict[str, object]:
    return {
        "backend": "ollama_native",
        "model": "cognitive-fixture:latest",
        "model_digest": "a" * 64,
        "parallelism": 1,
        "endpoint": "http://127.0.0.1:11434/api/chat",
        "max_tokens": 6000,
        "max_calls": 1,
        "timeout": 120,
        "temperature": 0.3,
        "memory_bytes": 8192,
    }


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://localhost:11434/api/chat",
        "https://127.0.0.1:11434/api/chat",
        "http://127.0.0.1:11435/api/chat",
        "http://127.0.0.1:11434/api/chat?key=fixture",
        "http://127.0.0.1:11434/v1/chat/completions",
    ],
)
def test_native_endpoint_is_exact(config: dict[str, object], endpoint: str) -> None:
    with pytest.raises(store.PilotError):
        execution.Provider({**config, "endpoint": endpoint})


@pytest.mark.parametrize("change", [{"parallelism": 0}, {"parallelism": 3}, {"model_digest": "sha256:" + "a" * 64}])
def test_native_registration_rejects_invalid_binding(config: dict[str, object], change: dict[str, object]) -> None:
    with pytest.raises(store.PilotError):
        store.validate_config({**config, **change})


def test_native_v2_policy_and_serial_execution_are_frozen(tmp_path: Path, config: dict[str, object]) -> None:
    directory = tmp_path / "serial"
    runner.register(directory, config, 42, 1, 720000)
    plan = store.load(directory)
    assert plan["schema"] == "cognitive-pilot-v2"
    assert store.mapping(plan["provider_policy"])["think"] is False
    assert runner.registration(directory, plan)["parallelism"] == 1
    frozen = judging.prepare_judging(directory, config, ["AI-1", "AI-2", "AI-3"], 432000)
    assert frozen["parallelism"] == 1 and frozen["schema"] == "cognitive-pilot-ai-judging-v2"
    assert judging._load(directory)["parallelism"] == 1


@pytest.mark.parametrize("change_on_second", [False, True])
def test_native_checks_manifest_before_every_call_and_never_sends_credentials(
    config: dict[str, object], monkeypatch: pytest.MonkeyPatch, change_on_second: bool
) -> None:
    requests: list[httpx.Request] = []
    inventories = 0

    def response(request: httpx.Request) -> httpx.Response:
        nonlocal inventories
        requests.append(request)
        assert "authorization" not in request.headers and "x-api-key" not in request.headers
        if request.method == "GET":
            inventories += 1
            value = "b" * 64 if change_on_second and inventories == 2 else config["model_digest"]
            return httpx.Response(200, json={"models": [{"name": config["model"], "digest": value}]})
        payload = json.loads(request.content)
        assert payload == {
            "model": config["model"],
            "messages": [{"role": "user", "content": "Public fixture"}],
            "stream": False,
            "think": False,
            "format": "json",
            "keep_alive": "5m",
            "options": {"num_ctx": 8192, "num_predict": 2048, "temperature": 0.3},
        }
        return httpx.Response(
            200,
            json={
                "model": config["model"],
                "done": True,
                "message": {"content": '{"fixture":true}', "thinking": "NOT-RETAINED-FIXTURE"},
                "prompt_eval_count": 100,
                "eval_count": 23,
            },
        )

    original = httpx.AsyncClient

    def client(**kwargs: object) -> httpx.AsyncClient:
        assert kwargs["follow_redirects"] is False and kwargs["trust_env"] is False
        return original(transport=httpx.MockTransport(response), follow_redirects=False, trust_env=False)

    monkeypatch.setenv("GEMINI_API_KEY", "NEVER-SEND-FIXTURE")
    monkeypatch.setenv("OPENROUTER_API_KEY", "NEVER-SEND-FIXTURE")
    monkeypatch.setattr(httpx, "AsyncClient", client)
    provider = execution.Provider(config)
    assert asyncio.run(provider.call([{"role": "user", "content": "Public fixture"}], 120)) == {"fixture": True}
    if change_on_second:
        with pytest.raises(ollama.ModelBindingError):
            asyncio.run(provider.call([{"role": "user", "content": "Public fixture"}], 120))
        assert [request.method for request in requests] == ["GET", "POST", "GET"]
        assert provider.tokens == 123 and provider.calls == 1
    else:
        assert asyncio.run(provider.call([{"role": "user", "content": "Public fixture"}], 120)) == {"fixture": True}
        assert [request.method for request in requests] == ["GET", "POST", "GET", "POST"]
        assert provider.tokens == 246 and provider.calls == 2
    assert b"NOT-RETAINED-FIXTURE" not in store.canonical(provider.observations)
    assert provider.observations[0]["model_digest"] == config["model_digest"]


def test_serial_runner_never_overlaps_provider_calls(
    tmp_path: Path, config: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "serial-run"
    runner.register(directory, config, 42, 1, 12000)
    active = 0
    maximum = 0

    async def fixture(self: execution.Provider, messages: list[dict[str, str]], timeout: float) -> dict[str, object]:
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        await asyncio.sleep(0.001)
        active -= 1
        self.calls = 1
        self.tokens = 6000
        source = "def solve(p):\n    return 0"
        return {
            "action": "final",
            "source": source,
            "candidates": [{"source": source, "mechanism": "fixture"}],
            "selected": 0,
            "memory": "fixture",
        }

    async def evaluator(source: str, tests: list[dict[str, object]], timeout: float = 10) -> dict[str, object]:
        return {"quality": 0.0, "passed": 0, "total": len(tests), "source_digest": store.digest(source)}

    monkeypatch.setattr(execution.Provider, "call", fixture)
    monkeypatch.setattr(execution, "evaluate", evaluator)
    assert asyncio.run(runner.run_batch(directory))["attempted_now"] == 2
    assert maximum == 1


def test_v3_role_binding_and_v2_compatibility(tmp_path: Path, config: dict[str, object]) -> None:
    agent = {**config, "backend": "ollama_structured_v3", "response_contract": "agent"}
    judge = {**agent, "response_contract": "judge"}
    with pytest.raises(store.PilotError, match="agent structured-response"):
        store.prepare(tmp_path / "wrong", judge, repetitions=1)
    path = tmp_path / "v3"
    runner.register(path, agent, 42, 1, 720000)
    plan = store.load(path)
    assert plan["schema"] == "cognitive-pilot-v3"
    assert store.mapping(plan["provider_policy"])["format"] == store.response_schema("agent")
    with pytest.raises(store.PilotError, match="judge structured-response"):
        judging.prepare_judging(path, agent, ["AI-1", "AI-2", "AI-3"], 432000)
    frozen = judging.prepare_judging(path, judge, ["AI-1", "AI-2", "AI-3"], 432000)
    assert frozen["schema"] == "cognitive-pilot-ai-judging-v3"
    assert store.mapping(judging._load(path)["provider_policy"])["format"] == store.response_schema("judge")
    old = tmp_path / "v2"
    store.prepare(old, config, repetitions=1)
    assert store.load(old)["schema"] == "cognitive-pilot-v2"
    assert store.mapping(store.load(old)["provider_policy"])["format"] == "json"


@pytest.mark.parametrize("contract", ["", "completion", 3, None])
def test_v3_rejects_unknown_role(config: dict[str, object], contract: object) -> None:
    with pytest.raises(store.PilotError):
        store.validate_config({**config, "backend": "ollama_structured_v3", "response_contract": contract})


@pytest.mark.parametrize("contract", ["agent", "judge"])
def test_v3_http_fixture_binds_exact_role_schema(
    config: dict[str, object], monkeypatch: pytest.MonkeyPatch, contract: str
) -> None:
    config = {**config, "backend": "ollama_structured_v3", "response_contract": contract}
    action: dict[str, object] = (
        {"action": "test", "source": "def solve(p): return 0"}
        if contract == "agent"
        else {"families": ["constant"], "originality": 0, "critical_violation": False, "evidence": "Fixture constant."}
    )

    def respond(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json={"models": [{"name": config["model"], "digest": config["model_digest"]}]})
        payload = json.loads(request.content)
        assert payload["format"] == store.response_schema(contract)
        assert payload["think"] is False and payload["options"]["num_predict"] == 2048
        return httpx.Response(
            200,
            json={
                "model": config["model"],
                "done": True,
                "message": {"content": json.dumps(action)},
                "prompt_eval_count": 100,
                "eval_count": 40,
            },
        )

    original = httpx.AsyncClient

    def client(**kwargs: object) -> httpx.AsyncClient:
        return original(transport=httpx.MockTransport(respond), follow_redirects=False, trust_env=False)

    monkeypatch.setattr(httpx, "AsyncClient", client)
    assert asyncio.run(execution.Provider(config).call([{"role": "user", "content": "Fixture only"}], 120)) == action


def test_v3_schemas_with_standard_validator_and_semantic_guards() -> None:
    # Optional transitive MCP dependency; semantic guards are exercised in the core suite too.
    jsonschema = pytest.importorskip("jsonschema")
    agent = store.response_schema("agent")
    judge = store.response_schema("judge")
    jsonschema.Draft202012Validator.check_schema(agent)
    jsonschema.Draft202012Validator.check_schema(judge)
    validator = jsonschema.Draft202012Validator(agent)
    validator.validate({"action": "test", "source": "def solve(p): return 0"})
    source = "def solve(p): return 0"
    final: dict[str, object] = {
        "action": "final",
        "source": source,
        "candidates": [{"source": source, "mechanism": "fixture"}],
        "selected": 0,
        "memory": "fixture",
    }
    validator.validate(final)
    with pytest.raises(jsonschema.ValidationError):
        validator.validate({"action": "other", "source": source})
    with pytest.raises(jsonschema.ValidationError):
        validator.validate({"action": "test", "source": source, "unexpected": True})
    for changed in ({**final, "selected": 4}, {**final, "source": "different"}, {**final, "memory": "x" * 8193}):
        validator.validate(changed)  # Cross-field equality, index and UTF-8 budgets stay semantic.
        with pytest.raises(store.PilotError):
            execution.final_artifact(changed, 8192)
