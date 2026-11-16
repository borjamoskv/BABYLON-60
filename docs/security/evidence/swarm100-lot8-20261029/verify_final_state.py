"""Check final inventory, source evidence and links without executing production."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).absolute().parents[4]
HERE = Path(__file__).absolute().parent
ROUND3 = HERE.parent/'swarm100-round3-20261028'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    summary = read(ROUND3/'registry-summary.json')
    assert summary['original_candidates'] == 598
    assert summary['round3_reviewed'] == summary['round3_assigned'] == 582
    assert summary['all_remediation_states'] == dict(OPEN=545, FIXED=45, MITIGATED=4, NOT_APPLICABLE=4)
    assert summary['round3_remediation_states'] == dict(OPEN=540, FIXED=35, MITIGATED=3, NOT_APPLICABLE=4)
    assert summary['unique_open_findings'] == 539
    assert summary['unique_open_severity'] == dict(P1=57, P2=472, P3=10)
    assert summary['needs_validation_ids'] == []
    registry = read(ROUND3/'registry.json')['records']
    assert len(registry) == len({item['original']['candidate_id'] for item in registry}) == 598
    fixed = {'SW100-C0499','SW100-C0500'}
    updates = read(HERE/'candidate-status-updates.json')
    assert {item['candidate_id'] for item in updates} == fixed
    for item in updates:
        assert item['remediation_state'] == 'FIXED'
        assert sha(ROOT/item['path']) == item['current_source_sha256']
        assert all((ROOT/path).exists() for path in item['evidence_paths'])
    assert not fixed & {item['candidate_id'] for item in read(ROUND3/'remediation-queue.json')}
    before = {item['candidate_id']:item for item in read(HERE/'root-adjudications-before-lot8.json')}
    after = {item['candidate_id']:item for item in read(ROUND3/'root-adjudications.json')}
    assert set(after)-set(before) <= fixed
    assert all(after[cid] == item for cid, item in before.items() if cid not in fixed)
    review = read(HERE/'independent-review.json')
    assert review['decision'] == 'APPROVED_WITH_EXPLICIT_SCOPE' and review['open_actionable_findings'] == []
    for path, value in {**review['source_sha256'], **review['test_source_sha256']}.items():
        assert sha(ROOT/path) == value
    for item in read(HERE/'validation.json')['checks'].values():
        assert item['exit_code'] == 0
        assert sha(ROOT/item['log']) == item['log_sha256']
        for path, digest in item.get('source_sha256_before_and_after', {}).items():
            assert sha(ROOT/path) == digest
    before_sources = read(HERE/'before-source-manifest.json')['source_sha256']
    for path, digest in before_sources.items():
        if path != 'scripts/c5_cortex/cortex_objectives_transducer.py':
            assert sha(ROOT/path) == digest
    for item in read(HERE/'lot9-selection.json'):
        assert sha(ROOT/item['path']) == item['source_sha256']
        current = next(row['current'] for row in registry if row['original']['candidate_id'] == item['candidate_id'])
        assert current['remediation_state'] == 'OPEN' and current['decision'] == 'CONFIRMED_STATIC'
    link_counts = {}
    for name in ['PLAN_SWARM100_LOTE8_2026-10-29.md','PLAN_SWARM100_LOTE9_2026-10-29.md',
                 'REMEDIATION_SWARM100_LOTE8_2026-10-29.md','AUDIT_SWARM100_ROUND3_2026-10-28.md']:
        path = ROOT/'docs/security'/name
        links = re.findall(r'\]\(([^)]+)\)',path.read_text())
        local = [value for value in links if not value.startswith(('https://','http://','#'))]
        assert all((path.parent/value.split('#')[0]).exists() for value in local), name
        link_counts[name] = len(local)
    result = dict(status='PASS', original_ids=598, round3_ids=582, unique_open=539,
                  unique_open_severity=summary['unique_open_severity'], fixed_in_lot=sorted(fixed),
                  unrelated_root_adjudications_unchanged=True, lot9_not_applied=True, local_links_checked=link_counts,
                  limits='Static reconciliation and local link/hash checks, not certification of runtime or Git/hook sandbox or global concurrency transaction.')
    (HERE/'final-state-check.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
