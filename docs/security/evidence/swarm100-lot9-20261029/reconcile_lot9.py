"""Reconcile C0438's Git defect, not monitor metrics or hook containment."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]
HERE = Path(__file__).absolute().parent
ROUND3 = HERE.parent/'swarm100-round3-20261028'
SOURCE = 'scripts/c5_thermo/c5_exergy_optimizer_monitor.py'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name, observation):
    tree = ast.parse((ROOT/SOURCE).read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return dict(path=SOURCE, start_line=node.lineno, end_line=node.end_lineno, observation=observation)


def main():
    records = {r['original']['candidate_id']:r for r in read(ROUND3/'registry.json')['records']}
    previous = read(ROUND3/'root-adjudications.json')
    if not (HERE/'root-adjudications-before-lot9.json').exists():
        write(HERE/'root-adjudications-before-lot9.json', previous)
    review = read(HERE/'independent-review.json')
    assert review['decision'] == 'APPROVED_WITH_EXPLICIT_SCOPE'
    assert review['open_actionable_findings'] == []
    for path, expected in {**review['source_sha256'], **review['test_source_sha256']}.items():
        assert sha(ROOT/path) == expected, path
    validation = read(HERE/'validation.json')['checks']
    assert {'related-tests','mypy','ruff','semantic-gate','budget-gate','topology-gate','diff-check'} <= set(validation)
    assert all(value['exit_code'] == 0 for value in validation.values())
    assert read(HERE/'scope-check.json')['result'] == 'PASS'
    evidence = [str((HERE/name).relative_to(ROOT)) for name in
                ['before-tests.log','related-tests.log','independent-review.json','scope-check.json','validation.json']]
    item = copy.deepcopy(records['SW100-C0438']['current'])
    item.update(decision='ALREADY_FIXED', remediation_state='FIXED', current_source_sha256=sha(ROOT/SOURCE),
        rationale='The monitor no longer swallows failed Git results, disables signing, bypasses hooks, stages its obsolete/current source or consumes the full index. A STATUS-only preflight precedes all producers and is repeated before a single commit --only, with parent/branch/path postvalidation. Existing prepared/intent/special index entries and unsupported states reject without refresh; normal hook/signer rejection propagates without COMPLETE, retries or manual rollback. No-op is None/NO_CHANGE, not an old hash presented as a new commit. The caller no longer amends or rewrites historical PENDING markers: the actual commit OID is output only after validation. Eight initial red reproductions and final native-Git fixtures verify the specific defect. Monitor metrics, pre-append SHA3 and report persistence remain unverified outside this fix.',
        source_checks=[
            check('_git_bytes','Normal Git/config/hooks, binary subprocess and check=True; no signing override or swallowed error.'),
            check('_git','Explicit filesystem decoding for presentation; raw paths/diffs stay bytes.'),
            check('_git_preflight','Exact root/STATUS, regular tracked file and ordinary clean index/state, without implicit refresh.'),
            check('git_sentinel_commit','Single STATUS-only commit or None; stable baseline/parent/branch/path validation and no destructive rollback.'),
            check('c5_real_colapso','Preflight before all producers; neutral row and one verified commit; no amend/historical replacement; NO_CHANGE or non-success on failure.')],
        guards=[
            'Git/config/hooks/clean filters are trusted executable code, not sandboxed. Unexpected effects can occur before postvalidation; they are not automatically undone.',
            'Whole-file selection includes earlier unstaged edits in STATUS.md. No global transaction against concurrent writers/partial staging of the same output is certified.',
            'Unrelated staging present at preflight rejects intact; late unrelated staging is preserved/excluded in fixtures. No arbitrary multi-process Git isolation claim.',
            'STATUS.md must already be tracked/regular. New outputs and unsupported repository/index states fail explicitly before producer execution.',
            'Ordinary failed commits discard Git temporary preparation. Hook/signer failures never trigger --no-verify, signature override, reset/clean/stash or retry.',
            'No-op returns None and consumer prints NO_CHANGE; only a validated new commit can print COMPLETE with its full OID.',
            'Producer writes can remain dirty on later Git failure. This is not a filesystem persistence rollback or an attestation of generated metrics.',
            'Existing crystallize_status still hashes pre-append STATUS with SHA3 and ignores report. It does not bind the complete report/final row; these facts remain outside C0438.',
            'Actual Git/harmless hooks/failing signer recorder only in owned temporary repositories with synthetic HOME/identity/config. All monitor database/audit/test producers are controlled in fixtures.',
            'No monitor, helper/commit/amend on real checkout, operator database, real signing key, protected runtime, hardware, network, publication or ATTESTED. Global telemetry omitted.'
        ], runtime_executed=True,
        runtime_scope='Actual Git only in owned temporary repositories; monitor producers and signer recorder controlled, no real project execution/signing/network.',
        evidence_paths=evidence, resolution_type='CODE_AND_CONFINED_REGRESSIONS_VERIFIED')
    write(HERE/'candidate-status-updates.json', [item])
    write(ROUND3/'root-adjudications.json', [r for r in previous if r['candidate_id'] != 'SW100-C0438']+[item])
    print('C0438 FIXED for monitor Git integrity; metrics/SHA3 and hook/concurrency limits retained.')


if __name__ == '__main__':
    main()
