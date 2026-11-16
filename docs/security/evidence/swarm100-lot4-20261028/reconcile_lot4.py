"""Close bundle defects with confined evidence; retain historical v2 findings."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]
HERE = Path(__file__).absolute().parent
ROUND3 = HERE.parent/'swarm100-round3-20261028'
CORE = 'proof/bundles/attestation_bundle_v1/verify'
V1 = 'scripts/generate_attestation_bundle.py'
V2 = 'scripts/generate_attestation_bundle_v2.py'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(path, name, observation):
    tree = ast.parse((ROOT/path).read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return dict(path=path, start_line=node.lineno, end_line=node.end_lineno, observation=observation)


def main():
    records = {r['original']['candidate_id']:r for r in read(ROUND3/'registry.json')['records']}
    previous = read(ROUND3/'root-adjudications.json')
    before = HERE/'root-adjudications-before-lot4.json'
    if not before.exists():
        write(before, previous)
    review = read(HERE/'independent-review.json')
    assert review['decision'] == 'APPROVED_WITH_EXPLICIT_SCOPE'
    assert review['open_actionable_findings'] == []
    for path, expected in review['source_sha256'].items():
        assert sha(ROOT/path) == expected, path
    assert all(value['exit_code'] == 0 for value in read(HERE/'validation.json')['checks'].values())
    evidence = [str((HERE/name).relative_to(ROOT)) for name in
                ['before-tests.log', 'related-tests.log', 'independent-review.json', 'validation.json']]
    guards = [
        'Legacy signatures cannot authenticate new metadata retroactively; legacy/unknown schemas are rejected.',
        'Generators emit only unsigned NOT_EXECUTED/UNVERIFIED snapshots and never load/generate private keys.',
        'Integrity-only is explicitly unauthenticated; a signature is checked only against an external P256 key.',
        'Signature math does not establish hardware provenance, test execution or physical operator approval.',
        'Scope is the exact SELECTED_FILES inventory, not the entire repository or a consistent live-worktree transaction.',
        'All generation/signing/verification here used owned temporary fixtures and software-only test keys; no ATTESTED object.',
        'Historical materials and the separate v2 verifier remain unchanged; C0135/C0136 remain OPEN.',
    ]
    descriptions = {
        'SW100-C0060': ('verify_bundle',
            'The old v1 verifier returned exit0 after failed hash/signature checks. It now rejects unsupported legacy input and all integrity/signature failures with nonzero status; unsigned default is NOT_AUTHENTICATED/exit2. Valid new-format signed integrity against an explicit external software fixture anchor succeeds without certifying execution or hardware.'),
        'SW100-C0061': ('verify_bundle',
            'New schema binds every manifest field (including commit/time/schema/producer), component path/type/size/BLAKE3 and the exact selected artifact inventory. Bytes are re-read from the explicit external root through nofollow descriptors. Domain-separated ECDSA P256/SHA256 covers the full canonical manifest, checked only with an external trust key. Legacy causal-hash signatures cannot establish this binding and are rejected, not upgraded. Tampered metadata, rehashed manifests, source changes and wrong signature representations are rejected in confined tests.'),
        'SW100-C0083': ('build_snapshot',
            'The v1 entrypoint is import-safe and requires a new explicit output. Its common builder emits suites NOT_EXECUTED, hardware UNVERIFIED and certification NONE; hard-coded PASS/counts, copied signature/key and fixed historical timestamp are removed. Missing inputs fail before output and existing output is never overwritten. No automatic signing or empirical attestation is offered by the unsigned snapshot builder.'),
        'SW100-C0086': ('build_snapshot',
            'The v2 entrypoint no longer fabricates trial/pass counts, loads a persistent private key or signs invented results. The builder has no execution-evidence ingestion contract and always emits NOT_EXECUTED; even externally signed PASS-like fixture payloads are rejected by the new verifier. This is an honest unsigned snapshot workflow, not implemented test execution or hardware attestation.'),
        'SW100-C0087': ('verify_bundle',
            'Newly generated bundles copy the canonical portable verifier, whose selected-file checks read actual external artifact bytes and validate path/type/size/BLAKE3 and the bound claims snapshot. A changed/deleted/FIFO/symlink artifact fails even if stored digest strings remain unchanged. The historical v2 verifier is not regenerated and its separate C0135/C0136 stay OPEN.'),
        'SW100-C0088': ('build_snapshot',
            'Environment fields come from observed platform/Python APIs, with empty/unavailable text recorded as UNKNOWN; provenance is OBSERVED_PLATFORM_ONLY and hardware remains UNVERIFIED. Fixed Apple chip/runtime/filesystem/TRNG certification strings are removed from generation. Fake FixtureOS and empty-platform regressions prove the output is derived from the observation provider, without asserting real hardware certification.'),
    }
    updates = []
    for cid, (function, rationale) in descriptions.items():
        item = copy.deepcopy(records[cid]['current'])
        path = records[cid]['original']['path']
        checks = [check(CORE, function, rationale)]
        if path != CORE:
            checks.insert(0, check(path, 'main', 'Import-safe wrapper delegates to the canonical new-format builder only on explicit CLI execution.'))
        item.update(decision='ALREADY_FIXED', remediation_state='FIXED', current_source_sha256=sha(ROOT/path),
                    rationale=rationale, source_checks=checks, guards=guards, evidence_paths=evidence,
                    runtime_executed=True, runtime_scope='Copied CLI entrypoints, portable verifier and bounded pure helpers in temporary fixtures; only software test signatures.',
                    resolution_type='CODE_AND_CONFINED_REGRESSIONS_VERIFIED')
        updates.append(item)
    item = copy.deepcopy(records['SW100-C0135']['current'])
    item['rationale'] = item['rationale'].split(' Re-reviewed after Lot4:')[0]+(
        ' Re-reviewed after Lot4: the new producer emits v3 selected-file snapshots with a new portable verifier; it does not regenerate or fix this historical v2 verifier. Its string-only artifact check remains and C0135 stays OPEN/P2. The cross-source reference is refreshed because the old producer was replaced, not because this copy was fixed.')
    item['source_checks'] = [c for c in item['source_checks'] if c['path'] != V2]
    item['source_checks'].append(check(V2, 'main', 'Current wrapper produces a different contract; the separately stored historical v2 verifier is unchanged.'))
    item['evidence_paths'] = list(dict.fromkeys(item['evidence_paths']+evidence))
    assert item['remediation_state'] == 'OPEN' and item['severity'] == 'P2'
    updates.append(item)
    write(HERE/'candidate-status-updates.json', updates)
    ids = {i['candidate_id'] for i in updates}
    write(ROUND3/'root-adjudications.json', [i for i in previous if i['candidate_id'] not in ids]+updates)
    print('Four planned IDs and collateral C0060/C0088 FIXED; C0135/C0136 historical copy remains OPEN.')


if __name__ == '__main__':
    main()
