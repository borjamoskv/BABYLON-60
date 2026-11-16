"""Independent Lot6 review: synthetic environment, blocked dotenv/sockets, MockTransport."""
import asyncio
import hashlib
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import socket
import sys
import tempfile
import types

import httpx


ROOT = Path(__file__).absolute().parents[4]
SOURCE = ROOT / '01_KISH_ENGINE/babylon60/kernel/swarm_orchestrator.py'
EVIDENCE = Path(__file__).absolute().parent


def main():
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    results = []
    with tempfile.TemporaryDirectory(prefix='lot6-independent-') as temporary:
        os.environ.clear()
        os.environ.update(HOME=temporary, LC_ALL='C')
        os.chdir(temporary)
        dotenv_reads, sockets = [], []
        sys.modules['dotenv'] = types.SimpleNamespace(load_dotenv=lambda *a, **k: dotenv_reads.append('blocked'))

        def no_network(*args, **kwargs):
            sockets.append('blocked')
            raise AssertionError('Socket/DNS forbidden in independent fixture')

        socket.create_connection = no_network
        socket.getaddrinfo = no_network
        socket.socket.connect = no_network
        socket.socket.connect_ex = no_network
        name = 'lot6_independent_module'
        spec = importlib.util.spec_from_file_location(name, SOURCE)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        root_handlers = tuple(logging.getLogger().handlers)
        spec.loader.exec_module(module)
        environment = {'KIMI_API_KEY': 'fixture-moonshot-key', 'OPENROUTER_API_KEY': 'fixture-router-key'}
        reads, requests, clients, handlers = [], [], [], []

        def getenv(key, default=None):
            reads.append(key)
            return environment.get(key, default)

        module.os = types.SimpleNamespace(getenv=getenv)
        real_client = httpx.AsyncClient

        def handler(request):
            requests.append(request)
            if handlers:
                return handlers.pop(0)(request)
            return httpx.Response(200, json={'choices': [{'message': {'content': 'fixture-ok'}}]})

        def client_factory(*args, **kwargs):
            clients.append(dict(kwargs))
            kwargs['trust_env'] = False  # Independent confinement even if product validation regresses.
            kwargs['transport'] = httpx.MockTransport(handler)
            return real_client(*args, **kwargs)

        module.httpx.AsyncClient = client_factory
        logs = io.StringIO()
        log_handler = logging.StreamHandler(logs)
        module.log.addHandler(log_handler)
        module.log.setLevel(logging.DEBUG)
        Backend = module.InferenceBackend

        def reset():
            reads.clear()
            requests.clear()
            clients.clear()
            handlers.clear()
            logs.seek(0)
            logs.truncate(0)

        def refused(function):
            try:
                function()
            except module.SecurityError:
                return
            raise AssertionError('Expected SecurityError')

        async def refused_async(awaitable):
            try:
                await awaitable
            except module.SecurityError:
                return
            raise AssertionError('Expected SecurityError')

        async def import_and_selector():
            assert not dotenv_reads and root_handlers == tuple(logging.getLogger().handlers)
            for invalid in ('local_vlm', '', 'MOONSHOT', ' moonshot', None, True, [], {}):
                await refused_async(module.run_swarm_orchestrator('fixture-prompt', backend=invalid))
                refused(lambda invalid=invalid: module.SwarmConfig(backend=invalid))
            assert reads == [] and requests == [] and clients == []
            return 'No dotenv/global logging side effect; invalid public/direct selectors reject before any environment read or HTTP client.'

        async def endpoint_corpus():
            bad = [
                'http://api.moonshot.cn/v1/chat', 'https://api.moonshot.cn:444/v1/chat',
                'https://api.moonshot.cn:0/v1/chat', 'https://api.moonshot.cn:65536/v1/chat',
                'https://api.moonshot.cn:/v1/chat', 'https://api.moonshot.cn.evil.invalid/v1/chat',
                'https://api.moonshot.cn./v1/chat', 'https://evil.invalid@api.moonshot.cn/v1/chat',
                'https://@api.moonshot.cn/v1/chat', 'https://api.moonshot.cn/v1/chat?',
                'https://api.moonshot.cn/v1/chat#', 'https://api.moonshot.cn/v1/chat?secret=fixture',
                'https://api.moonshot.cn\\@evil.invalid/v1/chat', 'https://api.moonshot.cn/\x00chat',
                ' https://api.moonshot.cn/v1/chat', 'https://api.moonshot.cn/v1/chat\n',
                'https://openrouter.ai/api/v1/chat', '//api.moonshot.cn/v1/chat',
                'ftp://api.moonshot.cn/v1/chat', 'http://localhost.evil.invalid/v1/chat',
                'http://2130706433/v1/chat', 'http://127.000.000.001/v1/chat',
                'http://[::1%lo0]:8000/v1/chat', 'http://[::ffff:127.0.0.1]:8000/v1/chat',
            ]
            for url in bad:
                refused(lambda url=url: module.SwarmConfig(moonshot_url=url))
            assert reads == [] and clients == [] and requests == []
            return f'{len(bad)} malformed, ambiguous or unauthorized endpoint variants rejected before credentials/client.'

        async def routes():
            cases = [
                (Backend.MOONSHOT_REMOTE, {}, 'api.moonshot.cn', 'Bearer fixture-moonshot-key'),
                (Backend.OPENROUTER_REMOTE, {}, 'openrouter.ai', 'Bearer fixture-router-key'),
                (Backend.LOCAL_VLLM, {}, 'localhost', None),
                (Backend.LOCAL_MLX, {'local_url': 'http://[::1]:8912/v1/chat'}, '::1', None),
                (Backend.MOONSHOT_REMOTE, {'moonshot_url': 'http://127.0.0.1:8912/v1/chat'}, '127.0.0.1', 'Bearer fixture-moonshot-key'),
            ]
            for backend, fields, host, authorization in cases:
                reads.clear()
                config = module.SwarmConfig(backend=backend, **fields)
                assert await module.RobustLLMClient(config).call([{'role': 'user', 'content': 'fixture-prompt'}]) == 'fixture-ok'
                assert requests[-1].url.host == host
                assert requests[-1].headers.get('authorization') == authorization
                assert json.loads(requests[-1].content)['messages'][0]['content'] == 'fixture-prompt'
                if backend in (Backend.LOCAL_VLLM, Backend.LOCAL_MLX):
                    assert reads == []
            assert all(c.get('follow_redirects') is False and c.get('trust_env') is False for c in clients)
            return 'Both providers, both local backends and explicit remote loopback gateway follow the declared header/destination contract.'

        async def mutation_retry():
            config = module.SwarmConfig(moonshot_model='fixture-original-model', max_retries=2,
                                        retry_base_delay_s=0, request_timeout_s=7)
            client = module.RobustLLMClient(config)
            def change(request):
                config.backend = Backend.OPENROUTER_REMOTE
                config.openrouter_url = 'https://openrouter.ai/api/v1/chat/completions'
                config.openrouter_key = 'fixture-new-router-key'
                config.openrouter_model = 'fixture-new-model'
                config.request_timeout_s = 19
                return httpx.Response(429, headers={'Retry-After': '0'})
            handlers.append(change)
            assert await client.call([]) == 'fixture-ok'
            assert len(requests) == 2
            assert all(r.url.host == 'api.moonshot.cn' and r.headers['authorization'] == 'Bearer fixture-moonshot-key' for r in requests)
            assert all(json.loads(r.content)['model'] == 'fixture-original-model' for r in requests)
            assert all(c['timeout'] == 7 for c in clients)
            assert await client.call([]) == 'fixture-ok'
            assert requests[-1].url.host == 'openrouter.ai'
            assert requests[-1].headers['authorization'] == 'Bearer fixture-new-router-key'
            assert json.loads(requests[-1].content)['model'] == 'fixture-new-model'
            return 'Mutation during response/backoff cannot mix old credentials with the next provider; next call revalidates its new target.'

        async def redirects():
            for status in (301, 302, 303, 307, 308):
                handlers.append(lambda request, status=status: httpx.Response(status, headers={'Location': 'http://evil.invalid/fixture-key'}, text='fixture-error-secret'))
                before = len(requests)
                result = await module.RobustLLMClient(module.SwarmConfig()).call([])
                assert result == f'Error HTTP {status}' and len(requests) == before + 1
                assert 'fixture-error-secret' not in result
            return 'All five standard redirect statuses stop after the first mocked request.'

        async def dispatch_guards():
            invalid = [
                ('http://api.moonshot.cn/v1/chat', Backend.MOONSHOT_REMOTE, {}),
                ('https://openrouter.ai/v1/chat', Backend.MOONSHOT_REMOTE, {}),
                ('http://localhost:8912/v1/chat', Backend.LOCAL_VLLM, {'aUtHoRiZaTiOn': 'Bearer fixture'}),
                ('https://api.moonshot.cn/v1/chat', Backend.MOONSHOT_REMOTE, {'hOsT': 'evil.invalid'}),
                ('https://api.moonshot.cn/v1/chat', Backend.MOONSHOT_REMOTE, {'Proxy-Authorization': 'fixture'}),
                ('https://api.moonshot.cn/v1/chat', Backend.MOONSHOT_REMOTE, {'Authorization': 'fixture\r\nX: injected'}),
            ]
            for url, backend, headers in invalid:
                await refused_async(module._http_post_single_attempt(url, {}, headers, 1, backend))
            assert requests == [] and clients == []
            return 'Direct dispatch cannot bypass URL/backend checks or route using Host/proxy/local-Authorization headers.'

        async def changed_invalid():
            for field, value in (('backend', 'unknown'), ('moonshot_url', 'http://api.moonshot.cn/v1/chat')):
                config = module.SwarmConfig()
                client = module.RobustLLMClient(config)
                setattr(config, field, value)
                reads.clear()
                refused(lambda: config.api_key)
                await refused_async(client.call([]))
                assert not any('KEY' in name for name in reads)
            assert not clients and not requests
            return 'Invalid post-construction mutation is rejected by both api_key and call before credential lookup or transport.'

        async def diagnostics():
            canary = 'fixture-diagnostic-secret'
            for kind in ('http', 'connect', 'timeout', 'other'):
                def failed(request, kind=kind):
                    if kind == 'http':
                        return httpx.Response(401, text=canary)
                    if kind == 'connect':
                        raise httpx.ConnectError(canary, request=request)
                    if kind == 'timeout':
                        raise httpx.ReadTimeout(canary, request=request)
                    raise RuntimeError(canary)
                handlers.append(failed)
                result = await module.RobustLLMClient(module.SwarmConfig(max_retries=1)).call([])
                assert result.startswith('Error') and canary not in result
            assert canary not in logs.getvalue()
            return 'HTTP response body and exception text are omitted from module diagnostics.'

        async def cancellation():
            entered, closed = asyncio.Event(), asyncio.Event()
            async def held(request):
                entered.set()
                try:
                    await asyncio.Event().wait()
                finally:
                    closed.set()
            handlers.append(held)
            client = module.RobustLLMClient(module.SwarmConfig(max_retries=3))
            task = asyncio.create_task(client.call([]))
            await asyncio.wait_for(entered.wait(), 2)
            task.cancel()
            outcome = await asyncio.gather(task, return_exceptions=True)
            assert isinstance(outcome[0], asyncio.CancelledError)
            assert closed.is_set() and len(requests) == 1 and client._consecutive_failures == 0
            return 'Cancellation closes the mocked in-flight handler and is not retried or classified as provider failure.'

        for name, function in (
            ('import_and_invalid_selector', import_and_selector), ('endpoint_adversarial_corpus', endpoint_corpus),
            ('valid_routes_and_loopback_exception', routes), ('mutable_config_retry_snapshot', mutation_retry),
            ('redirects_refused', redirects), ('direct_dispatch_guards', dispatch_guards),
            ('invalid_mutation_revalidated', changed_invalid), ('sanitized_diagnostics', diagnostics),
            ('request_cancellation', cancellation)):
            reset()
            try:
                results.append(dict(name=name, status='PASS', detail=asyncio.run(function())))
            except Exception as error:
                results.append(dict(name=name, status='FAIL', error=repr(error)))
        assert not sockets
    final_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    report = dict(source_sha256=source_hash, final_source_sha256=final_hash,
                  source_stable=source_hash == final_hash, checks=results,
                  passed=sum(r['status'] == 'PASS' for r in results),
                  failed=sum(r['status'] == 'FAIL' for r in results), socket_attempts=len(sockets),
                  scope='Synthetic environment, dotenv blocked before module import, HTTPX MockTransport only; no real credentials, DNS, network, telemetry capture, native service, hardware or ATTESTED.')
    (EVIDENCE / 'independent-adversarial.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if not report['failed'] and report['source_stable'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
