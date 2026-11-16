"""Reconcile the two routing/transport fixes with confined regression evidence."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]
HERE = Path(__file__).absolute().parent
ROUND3 = HERE.parent/'swarm100-round3-20261028'
SOURCE = '01_KISH_ENGINE/babylon60/kernel/swarm_orchestrator.py'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name, observation):
    tree = ast.parse((ROOT/SOURCE).read_text())
    names = name.split('.')
    nodes = tree.body
    for part in names:
        node = next(n for n in nodes if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == part)
        nodes = node.body
    return dict(path=SOURCE, start_line=node.lineno, end_line=node.end_lineno, observation=observation)


def main():
    records = {r['original']['candidate_id']:r for r in read(ROUND3/'registry.json')['records']}
    previous = read(ROUND3/'root-adjudications.json')
    if not (HERE/'root-adjudications-before-lot6.json').exists():
        write(HERE/'root-adjudications-before-lot6.json', previous)
    review = read(HERE/'independent-review.json')
    assert review['decision'] == 'APPROVED_WITH_EXPLICIT_SCOPE'
    assert review['open_actionable_findings'] == []
    for path, expected in {**review['source_sha256'], **review['test_source_sha256']}.items():
        assert sha(ROOT/path) == expected, path
    assert all(value['exit_code'] == 0 for value in read(HERE/'validation.json')['checks'].values())
    evidence = [str((HERE/name).relative_to(ROOT)) for name in
                ['before-tests.log', 'related-tests.log', 'independent-review.json', 'scope-check.json', 'validation.json']]
    guards = [
        'Known default moonshot remains remote; only unknown selectors lose the implicit remote fallback.',
        'Selected official provider hosts require HTTPS/443. Explicit loopback gateway overrides retain the old HTTP/HTTPS exception and may carry the selected remote Bearer.',
        'Local roles only select canonical loopback hosts and never attach Authorization or resolve remote keys.',
        'URL/key/model/timeout are fixed per call and retry; next call revalidates configuration. This is not a cross-thread configuration transaction or immutable caller-message snapshot.',
        'The HTTPX transport uses follow_redirects=False and trust_env=False. Operator proxy/CA environment is no longer an implicit routing input.',
        'API keys are lazy/hidden from repr; own errors do not echo URL, body, prompt or exception text. Arbitrary caller/third-party logging is outside this guarantee.',
        'HTTPX MockTransport/recorders only, synthetic HOME/env and dotenv blocked before import; sockets/DNS prohibited. No provider, real credential, native/hardware auth or ATTESTED.',
        'No real TLS handshake, DNS routing, service availability or OS network containment is certified.',
    ]
    descriptions = {
        'SW100-C0132': (
            'Unknown selectors now raise SecurityError before config/defaults/client/credential access, rather than selecting Moonshot. Direct configuration and mutated clients also revalidate backend/endpoint. Import no longer reads .env or configures global logging; only the selected provider resolves lazy URL/key/model values after validation, while local roles read no remote keys. Existing .api_key consumer compatibility is covered. Six original confined regressions failed; patched selector/order/local/known-route cases pass with zero attempts on rejection.',
            [('_parse_backend', 'Exact enum/known-string selection; invalid values never become a remote default.'),
             ('run_swarm_orchestrator', 'Validates the requested backend before constructing configuration or client.'),
             ('SwarmConfig.__post_init__', 'Inert defaults validate only the selected endpoint before any credential resolution.'),
             ('SwarmConfig._key_for', 'Resolves only selected credentials; local roles return no key.')]),
        'SW100-C0133': (
            'Endpoint policy validates raw syntax with urllib/HTTPX and exact role/host, rejecting official provider HTTP, non-443 external ports, userinfo, query/fragment, controls/backslash and ambiguous or unsupported hosts before credentials/headers/client creation. Explicit configs and the final HTTP helper share the guard. Per-call immutable target prevents retry-time config mutation from sending an old provider key to a new endpoint; redirects and ambient proxy routing are disabled. HTTP/exception diagnostics no longer echo response bodies or secret-bearing text. The original allowlist loopback gateway exception is retained and explicitly bounded; this is not a claim that every remote-role override uses HTTPS.',
            [('_validate_endpoint', 'Validates syntax, canonical host and selected-role HTTPS/loopback contract.'),
             ('SwarmConfig._request_target', 'Freezes URL/backend/key/model/timeout after URL validation.'),
             ('_http_post_single_attempt', 'Revalidates at dispatch, rejects local auth/Host/proxy overrides, and disables redirects/environment trust.'),
             ('RobustLLMClient.call', 'Uses one target for all retries and only safe diagnostic categories/codes.')]),
    }
    updates = []
    for cid, (rationale, checks) in descriptions.items():
        item = copy.deepcopy(records[cid]['current'])
        item.update(decision='ALREADY_FIXED', remediation_state='FIXED', current_source_sha256=sha(ROOT/SOURCE),
                    rationale=rationale, source_checks=[check(name, observation) for name, observation in checks],
                    guards=guards, runtime_executed=True,
                    runtime_scope='Actual HTTPX parser/client with MockTransport and controlled async retry barriers; synthetic env and TCP/DNS forbidden.',
                    evidence_paths=evidence, resolution_type='CODE_AND_CONFINED_REGRESSIONS_VERIFIED')
        updates.append(item)
    write(HERE/'candidate-status-updates.json', updates)
    ids = {i['candidate_id'] for i in updates}
    write(ROUND3/'root-adjudications.json', [i for i in previous if i['candidate_id'] not in ids]+updates)
    print('C0132/C0133 FIXED; no other candidates closed; explicit loopback exception retained.')


if __name__ == '__main__':
    main()
