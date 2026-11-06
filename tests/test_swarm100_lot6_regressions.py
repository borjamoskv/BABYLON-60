"""Inference routing in isolated environments and HTTPX MockTransport only."""

from collections.abc import Callable
import importlib.util
import os
from pathlib import Path
import sys
import socket
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest

ROOT = Path(__file__).absolute().parents[1]
SOURCE = ROOT / "01_KISH_ENGINE/babylon60/kernel/swarm_orchestrator.py"


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    environment = {
        "HOME": str(tmp_path),
        "PATH": "/usr/bin:/bin",
        "LC_ALL": "C",
        "KIMI_API_KEY": "fixture-moonshot-secret",
        "OPENROUTER_API_KEY": "fixture-openrouter-secret",
    }

    def blocked_connect(*args, **kwargs):
        raise AssertionError("network sockets forbidden in this fixture")

    monkeypatch.setattr(socket.socket, "connect", blocked_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked_connect)
    monkeypatch.setattr(socket, "getaddrinfo", blocked_connect)
    dotenv_reads = []
    module_name = "swarm_lot6_fixture"
    with (
        patch.dict(os.environ, environment, clear=True),
        patch.dict(sys.modules, {"dotenv": SimpleNamespace(load_dotenv=lambda: dotenv_reads.append("blocked"))}),
    ):
        spec = importlib.util.spec_from_file_location(module_name, SOURCE)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, module_name, module)
        spec.loader.exec_module(module)
        env_reads = []

        def getenv(name, default=None):
            env_reads.append(name)
            return environment.get(name, default)

        monkeypatch.setattr(module, "os", SimpleNamespace(getenv=getenv))
        posts = []
        clients = []
        responses: list[Callable[[httpx.Request], httpx.Response]] = []

        def handler(request):
            posts.append(request)
            if responses:
                value = responses.pop(0)
                return value(request)
            return httpx.Response(200, json={"choices": [{"message": {"content": "fixture-ok"}}]})

        real_client = httpx.AsyncClient

        def factory(*args, **kwargs):
            clients.append(dict(kwargs))
            # This confinement also protects red tests against an unsafe ambient proxy.
            kwargs["trust_env"] = False
            kwargs["transport"] = httpx.MockTransport(handler)
            return real_client(*args, **kwargs)

        monkeypatch.setattr(module.httpx, "AsyncClient", factory)
        monkeypatch.setattr(module, "capture_kernel_snapshot", lambda: (None, None))
        original_decompose = module.task_decomposer

        async def decompose(client, prompt, max_tasks):
            await client.call([{"role": "user", "content": prompt}])
            return []

        monkeypatch.setattr(module, "task_decomposer", decompose)
        yield SimpleNamespace(
            module=module,
            env=environment,
            reads=env_reads,
            posts=posts,
            clients=clients,
            responses=responses,
            dotenv_reads=dotenv_reads,
            original_decompose=original_decompose,
        )


@pytest.mark.asyncio
async def test_c0132_unknown_selector_rejects_before_credentials_or_client(fixture):
    m = fixture.module
    with pytest.raises(m.SecurityError):
        await m.run_swarm_orchestrator("fixture-private-prompt", backend="local_vlm_typo")
    assert fixture.reads == []
    assert fixture.clients == [] and fixture.posts == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "backend,variable,url",
    [
        ("MOONSHOT_REMOTE", "MOONSHOT_API_URL", "http://api.moonshot.cn/v1/chat/completions"),
        ("OPENROUTER_REMOTE", "OPENROUTER_API_URL", "http://openrouter.ai/api/v1/chat/completions"),
    ],
)
async def test_c0133_http_provider_override_rejects_before_credentials(fixture, backend, variable, url):
    m = fixture.module
    fixture.env[variable] = url
    with pytest.raises(m.SecurityError):
        config = m.SwarmConfig(backend=getattr(m.InferenceBackend, backend))
        await m.RobustLLMClient(config).call([{"role": "user", "content": "fixture-private-prompt"}])
    assert not any("KEY" in name for name in fixture.reads)
    assert fixture.clients == [] and fixture.posts == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "backend,field,url",
    [
        ("MOONSHOT_REMOTE", "moonshot_url", "http://api.moonshot.cn/v1/chat/completions"),
        ("OPENROUTER_REMOTE", "openrouter_url", "http://openrouter.ai/api/v1/chat/completions"),
    ],
)
async def test_explicit_endpoint_cannot_bypass_provider_validation(fixture, backend, field, url):
    m = fixture.module
    with pytest.raises(m.SecurityError):
        config = m.SwarmConfig(backend=getattr(m.InferenceBackend, backend), **{field: url})
        await m.RobustLLMClient(config).call([])
    assert fixture.clients == [] and fixture.posts == []


def test_import_does_not_load_dotenv(fixture):
    assert fixture.dotenv_reads == []


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["", None, True, [], {}, "MOONSHOT", "local", "local_mlx_typo"])
async def test_invalid_backend_does_not_resolve_any_environment_value(fixture, backend):
    m = fixture.module
    with pytest.raises(m.SecurityError):
        await m.run_swarm_orchestrator("fixture-private-prompt", backend=backend)
    assert fixture.reads == [] and fixture.posts == [] and fixture.clients == []


@pytest.mark.parametrize("backend", ["", None, False, [], {}, "unknown"])
def test_direct_config_invalid_backend_fails_before_defaults(fixture, backend):
    with pytest.raises(fixture.module.SecurityError):
        fixture.module.SwarmConfig(backend=backend)
    assert fixture.reads == [] and fixture.clients == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "backend,host,field",
    [("MOONSHOT_REMOTE", "api.moonshot.cn", "moonshot_url"), ("OPENROUTER_REMOTE", "openrouter.ai", "openrouter_url")],
)
@pytest.mark.parametrize(
    "pattern",
    [
        "http://{host}/v1/chat",
        "ftp://{host}/v1/chat",
        "//{host}/v1/chat",
        "https://user:fixture-pass@{host}/v1/chat",
        "https://{host}.evil.invalid/v1/chat",
        "https://{host}@evil.invalid/v1/chat",
        "https://{host}:8443/v1/chat",
        "https://{host}:0/v1/chat",
        "https://{host}:65536/v1/chat",
        "https://{host}:bad/v1/chat",
        "https://{host}:/v1/chat",
        "https://{host}/v1/chat?token=fixture-secret",
        "https://{host}/v1/chat#fragment",
        " https://{host}/v1/chat",
        "https://{host}/v1/chat\n",
        "https://{host}\\evil/v1/chat",
        "https://%61{host}/v1/chat",
        "https://{host}./v1/chat",
    ],
)
async def test_invalid_provider_urls_reject_without_credentials_or_transport(fixture, backend, host, field, pattern):
    m = fixture.module
    url = pattern.format(host=host)
    with pytest.raises(m.SecurityError) as failure:
        config = m.SwarmConfig(backend=getattr(m.InferenceBackend, backend), **{field: url})
        await m.RobustLLMClient(config).call([])
    assert not any("KEY" in name for name in fixture.reads)
    assert fixture.clients == [] and fixture.posts == []
    assert "fixture-pass" not in str(failure.value) and "fixture-secret" not in str(failure.value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "backend,field,url,secret",
    [
        ("MOONSHOT_REMOTE", "moonshot_url", "https://api.moonshot.cn/v1/chat/completions", "fixture-moonshot-secret"),
        (
            "OPENROUTER_REMOTE",
            "openrouter_url",
            "https://openrouter.ai/api/v1/chat/completions",
            "fixture-openrouter-secret",
        ),
    ],
)
async def test_valid_remote_routes_preserve_exact_payload_and_selected_key(fixture, backend, field, url, secret):
    import json

    m = fixture.module
    config = m.SwarmConfig(backend=getattr(m.InferenceBackend, backend), **{field: url})
    assert not any("KEY" in name for name in fixture.reads)
    messages = [{"role": "user", "content": "fixture-private-prompt"}]
    assert await m.RobustLLMClient(config).call(messages) == "fixture-ok"
    (request,) = fixture.posts
    assert str(request.url) == url
    assert request.headers["Authorization"] == "Bearer " + secret
    body = json.loads(request.content)
    assert body["messages"] == messages
    assert body["model"] == ("moonshot-v1-auto" if backend == "MOONSHOT_REMOTE" else "openrouter/auto")
    assert fixture.clients[0]["follow_redirects"] is False
    assert fixture.clients[0]["trust_env"] is False
    reads = set(fixture.reads)
    if backend == "MOONSHOT_REMOTE":
        assert "OPENROUTER_API_KEY" not in reads
    else:
        assert not {"KIMI_API_KEY", "MOONSHOT_API_KEY"} & reads
    assert secret not in repr(config)


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["LOCAL_VLLM", "LOCAL_MLX"])
@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8000/v1/chat/completions",
        "http://127.0.0.1:8080/v1/chat/completions",
        "http://[::1]:8080/v1/chat/completions",
    ],
)
async def test_local_backend_never_reads_remote_keys_or_sends_bearer(fixture, backend, url):
    m = fixture.module
    fixture.env["MOONSHOT_API_URL"] = "http://unsafe.invalid"
    fixture.env["OPENROUTER_API_URL"] = "http://unsafe.invalid"
    config = m.SwarmConfig(
        backend=getattr(m.InferenceBackend, backend),
        local_url=url,
        moonshot_key="fixture-unselected-moonshot",
        openrouter_key="fixture-unselected-openrouter",
    )
    assert config.api_key == ""
    assert await m.RobustLLMClient(config).call([]) == "fixture-ok"
    assert fixture.reads == []
    (request,) = fixture.posts
    assert str(request.url) == url
    assert "Authorization" not in request.headers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "http://evil.invalid/v1/chat",
        "https://api.moonshot.cn/v1/chat",
        "http://user:pass@localhost/v1/chat",
        "http://127.0.0.1:0/v1/chat",
    ],
)
async def test_local_role_cannot_select_external_or_ambiguous_url(fixture, url):
    m = fixture.module
    with pytest.raises(m.SecurityError):
        config = m.SwarmConfig(backend=m.InferenceBackend.LOCAL_VLLM, local_url=url)
        await m.RobustLLMClient(config).call([])
    assert fixture.clients == [] and fixture.posts == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "backend,field", [("MOONSHOT_REMOTE", "moonshot_url"), ("OPENROUTER_REMOTE", "openrouter_url")]
)
async def test_explicit_remote_loopback_gateway_remains_supported(fixture, backend, field):
    m = fixture.module
    url = "http://127.0.0.1:9876/v1/chat/completions"
    config = m.SwarmConfig(backend=getattr(m.InferenceBackend, backend), **{field: url})
    assert await m.RobustLLMClient(config).call([]) == "fixture-ok"
    assert str(fixture.posts[0].url) == url
    assert fixture.posts[0].headers["Authorization"].startswith("Bearer fixture-")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "destination",
    ["http://api.moonshot.cn/v1/chat", "https://evil.invalid/v1/chat", "https://openrouter.ai/api/v1/chat"],
)
async def test_redirect_never_forwards_credentials_or_prompt(fixture, destination):
    m = fixture.module
    fixture.responses.append(
        lambda request: httpx.Response(
            307, headers={"Location": destination}, text="fixture-moonshot-secret fixture-private-prompt"
        )
    )
    client = m.RobustLLMClient(m.SwarmConfig())
    result = await client.call([{"role": "user", "content": "fixture-private-prompt"}])
    assert result == "Error HTTP 307"
    assert len(fixture.posts) == 1 and len(fixture.clients) == 1
    assert fixture.clients[0]["follow_redirects"] is False
    assert "fixture-moonshot-secret" not in result and "fixture-private-prompt" not in result


@pytest.mark.asyncio
async def test_environment_proxy_is_explicitly_disabled(fixture, monkeypatch):
    m = fixture.module
    monkeypatch.setenv("HTTP_PROXY", "http://fixture-proxy.invalid:8000")
    monkeypatch.setenv("HTTPS_PROXY", "http://fixture-proxy.invalid:8000")
    client = m.RobustLLMClient(m.SwarmConfig())
    assert await client.call([]) == "fixture-ok"
    assert fixture.clients[0]["trust_env"] is False
    assert len(fixture.posts) == 1


@pytest.mark.asyncio
async def test_retry_keeps_original_provider_key_model_and_timeout(fixture, monkeypatch):
    import json

    m = fixture.module
    config = m.SwarmConfig(
        moonshot_model="fixture-moonshot-model", request_timeout_s=5, max_retries=2, retry_base_delay_s=0
    )
    client = m.RobustLLMClient(config)
    entered, release = m.asyncio.Event(), m.asyncio.Event()

    async def backoff(delay):
        entered.set()
        await release.wait()

    monkeypatch.setattr(m.asyncio, "sleep", backoff)
    fixture.responses.append(lambda request: httpx.Response(429, headers={"Retry-After": "0"}))
    task = m.asyncio.create_task(client.call([{"role": "user", "content": "fixture-private-prompt"}]))
    await m.asyncio.wait_for(entered.wait(), timeout=2)
    config.backend = m.InferenceBackend.OPENROUTER_REMOTE
    config.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
    config.openrouter_key = "fixture-rotated-key"
    config.openrouter_model = "fixture-new-model"
    config.request_timeout_s = 99
    release.set()
    assert await m.asyncio.wait_for(task, timeout=2) == "fixture-ok"
    assert len(fixture.posts) == 2
    assert all(str(request.url) == "https://api.moonshot.cn/v1/chat/completions" for request in fixture.posts)
    assert all(request.headers["Authorization"] == "Bearer fixture-moonshot-secret" for request in fixture.posts)
    assert all(json.loads(request.content)["model"] == "fixture-moonshot-model" for request in fixture.posts)
    assert all(item["timeout"] == 5 for item in fixture.clients)
    assert await client.call([]) == "fixture-ok"
    assert str(fixture.posts[-1].url) == "https://openrouter.ai/api/v1/chat/completions"
    assert fixture.posts[-1].headers["Authorization"] == "Bearer fixture-rotated-key"
    assert json.loads(fixture.posts[-1].content)["model"] == "fixture-new-model"


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["backend", "url", "local-url"])
async def test_mutated_invalid_config_rejected_before_next_call_transport(fixture, mode):
    m = fixture.module
    config = m.SwarmConfig()
    client = m.RobustLLMClient(config)
    fixture.reads.clear()
    if mode == "backend":
        config.backend = "unknown"
    elif mode == "url":
        config.moonshot_url = "http://api.moonshot.cn/v1/chat"
    else:
        config.backend = m.InferenceBackend.LOCAL_MLX
        config.local_url = "http://evil.invalid/v1/chat"
    with pytest.raises(m.SecurityError):
        await client.call([])
    assert not any("KEY" in name for name in fixture.reads)
    assert fixture.posts == [] and fixture.clients == []


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["url", "backend"])
async def test_client_construction_revalidates_mutated_config(fixture, mode):
    m = fixture.module
    config = m.SwarmConfig()
    fixture.reads.clear()
    if mode == "url":
        config.moonshot_url = "http://api.moonshot.cn/v1/chat"
    else:
        config.backend = "unknown"
    with pytest.raises(m.SecurityError):
        m.RobustLLMClient(config)
    assert not any("KEY" in name for name in fixture.reads)
    assert fixture.posts == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url,backend,headers",
    [
        ("http://api.moonshot.cn/v1/chat", "MOONSHOT_REMOTE", {}),
        ("https://openrouter.ai/api/v1/chat", "MOONSHOT_REMOTE", {}),
        ("http://localhost:8000/v1/chat", "LOCAL_VLLM", {"authorization": "Bearer fixture-secret"}),
        ("https://api.moonshot.cn/v1/chat", "MOONSHOT_REMOTE", {"Host": "evil.invalid"}),
        ("https://api.moonshot.cn/v1/chat", "MOONSHOT_REMOTE", {"Proxy-Authorization": "fixture-secret"}),
        (
            "https://api.moonshot.cn/v1/chat",
            "MOONSHOT_REMOTE",
            {"Authorization": "Bearer fixture-secret\r\nX: injected"},
        ),
    ],
)
async def test_low_level_transport_rejects_bypass_attempts(fixture, url, backend, headers):
    m = fixture.module
    with pytest.raises(m.SecurityError):
        await m._http_post_single_attempt(url, {}, headers, 1, getattr(m.InferenceBackend, backend))
    assert fixture.clients == [] and fixture.posts == []


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["connect", "read-timeout", "unexpected", "http-error"])
async def test_error_diagnostics_do_not_echo_secrets(fixture, mode):
    m = fixture.module
    secret = "fixture-moonshot-secret fixture-private-prompt"

    def failure(request):
        if mode == "connect":
            raise httpx.ConnectError(secret, request=request)
        if mode == "read-timeout":
            raise httpx.ReadTimeout(secret, request=request)
        if mode == "unexpected":
            raise RuntimeError(secret)
        return httpx.Response(401, text=secret)

    fixture.responses.append(failure)
    result = await m.RobustLLMClient(m.SwarmConfig(max_retries=1)).call([])
    assert result.startswith("Error")
    assert "fixture-moonshot-secret" not in result and "fixture-private-prompt" not in result


@pytest.mark.asyncio
async def test_cancelled_call_is_not_retried(fixture, monkeypatch):
    m = fixture.module
    entered = m.asyncio.Event()

    async def request(*args):
        entered.set()
        await m.asyncio.Event().wait()

    monkeypatch.setattr(m, "_http_post_single_attempt", request)
    client = m.RobustLLMClient(m.SwarmConfig(max_retries=3))
    task = m.asyncio.create_task(client.call([]))
    await m.asyncio.wait_for(entered.wait(), timeout=2)
    task.cancel()
    with pytest.raises(m.asyncio.CancelledError):
        await task
    assert client._consecutive_failures == 0


def test_api_key_property_resolves_only_selected_valid_provider(fixture):
    m = fixture.module
    local = m.SwarmConfig(backend=m.InferenceBackend.LOCAL_MLX)
    assert local.api_key == "" and fixture.reads == []
    router = m.SwarmConfig(backend=m.InferenceBackend.OPENROUTER_REMOTE)
    assert router.api_key == "fixture-openrouter-secret"
    assert not {"KIMI_API_KEY", "MOONSHOT_API_KEY"} & set(fixture.reads)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "selector,host",
    [
        "moonshot api.moonshot.cn".split(),
        "openrouter openrouter.ai".split(),
        "local_vllm localhost".split(),
        "local_mlx localhost".split(),
    ],
)
async def test_public_entrypoint_preserves_known_selector_routes(fixture, selector, host):
    m = fixture.module
    result = await m.run_swarm_orchestrator("fixture-private-prompt", backend=selector)
    assert result == "El Planner no pudo descomponer la tarea."
    assert len(fixture.posts) == 1
    assert fixture.posts[0].url.host == host
    if selector.startswith("local_"):
        assert "Authorization" not in fixture.posts[0].headers
        assert fixture.reads == []


@pytest.mark.asyncio
async def test_explicit_empty_key_suppresses_environment_fallback(fixture):
    m = fixture.module
    config = m.SwarmConfig(moonshot_key="")
    fixture.reads.clear()
    assert await m.RobustLLMClient(config).call([]) == "fixture-ok"
    assert not any("KEY" in name for name in fixture.reads)
    assert "Authorization" not in fixture.posts[0].headers


@pytest.mark.asyncio
async def test_open_circuit_does_not_resolve_credentials(fixture):
    m = fixture.module
    client = m.RobustLLMClient(m.SwarmConfig(circuit_breaker_threshold=1))
    client._consecutive_failures = 1
    fixture.reads.clear()
    assert (await client.call([])).startswith("🔴 Circuit breaker")
    assert not any("KEY" in name for name in fixture.reads)
    assert fixture.clients == []


@pytest.mark.asyncio
@pytest.mark.parametrize("key", [b"fixture-secret", "fixture-secret\r\nInjected: true"])
async def test_invalid_credential_format_rejects_before_client(fixture, key):
    m = fixture.module
    client = m.RobustLLMClient(m.SwarmConfig(moonshot_key=key))
    with pytest.raises(m.SecurityError) as failure:
        await client.call([])
    assert "fixture-secret" not in str(failure.value)
    assert fixture.clients == []


@pytest.mark.asyncio
async def test_low_level_helper_requires_backend_contract(fixture):
    m = fixture.module
    with pytest.raises(m.SecurityError):
        await m._http_post_single_attempt("https://api.moonshot.cn/v1/chat", {}, {}, 1, "unknown")
    with pytest.raises(TypeError):
        await m._http_post_single_attempt("https://api.moonshot.cn/v1/chat", {}, {}, 1)
    assert fixture.posts == [] and fixture.clients == []


@pytest.mark.asyncio
async def test_selected_key_alias_keeps_previous_precedence(fixture):
    m = fixture.module
    fixture.env.pop("KIMI_API_KEY")
    fixture.env["MOONSHOT_API_KEY"] = "fixture-alternate-moonshot-key"
    client = m.RobustLLMClient(m.SwarmConfig())
    assert await client.call([]) == "fixture-ok"
    assert fixture.posts[0].headers["Authorization"] == "Bearer fixture-alternate-moonshot-key"
    assert "OPENROUTER_API_KEY" not in fixture.reads


@pytest.mark.asyncio
async def test_private_prompt_is_not_logged_by_planner_or_subagent(fixture, caplog):
    m = fixture.module
    client = m.RobustLLMClient(m.SwarmConfig(backend=m.InferenceBackend.LOCAL_VLLM))
    caplog.set_level("INFO")
    prompt = "fixture-sensitive-prompt-do-not-log"
    assert await fixture.original_decompose(client, prompt, 1) == [prompt]
    pager = m.AgentPager()
    pager.beep()
    result = await m.execute_subagent(0, prompt, client, pager, m.asyncio.Semaphore(1), 0)
    assert result["status"] == "OK"
    assert prompt not in caplog.text
    assert "fixture-moonshot-secret" not in caplog.text


@pytest.mark.asyncio
async def test_warmup_and_parallel_provider_calls_keep_credentials_separate(fixture):
    m = fixture.module
    first = m.RobustLLMClient(m.SwarmConfig())
    second = m.RobustLLMClient(m.SwarmConfig(backend=m.InferenceBackend.OPENROUTER_REMOTE))
    assert await first.call([]) == "fixture-ok"  # Warmup, no network/performance claim.
    assert (
        await m.asyncio.gather(*[client.call([]) for _ in range(16) for client in (first, second)])
        == ["fixture-ok"] * 32
    )
    assert len(fixture.posts) == 33
    for request in fixture.posts:
        key = "fixture-moonshot-secret" if request.url.host == "api.moonshot.cn" else "fixture-openrouter-secret"
        assert request.headers["Authorization"] == "Bearer " + key
