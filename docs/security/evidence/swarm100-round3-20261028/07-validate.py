"""Validate reviewer 07 coverage, schema, evidence paths, and source freshness."""

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
assignments = json.loads((BASE / 'assignments/07.json').read_text())
review = json.loads((BASE / 'reviews/07.json').read_text())
evidence = json.loads((BASE / '07-source-evidence.json').read_text())
fixtures = json.loads((BASE / '07-fixture-results.json').read_text())
assert review['reviewer'] == '07'
expected_ids = [c['candidate_id'] for c in assignments]
actual_ids = [c['candidate_id'] for c in review['candidates']]
assert len(actual_ids) == len(set(actual_ids)) == len(expected_ids) == 29
assert set(expected_ids) == set(actual_ids)
allowed_decisions = {'CONFIRMED_STATIC', 'REPRODUCED', 'REJECTED', 'DUPLICATE', 'ALREADY_FIXED', 'NEEDS_VALIDATION'}
allowed_states = {'OPEN', 'FIXED', 'MITIGATED', 'NOT_APPLICABLE', 'UNKNOWN'}
source_range_count = 0
for candidate in review['candidates']:
    assert candidate['decision'] in allowed_decisions
    assert candidate['remediation_state'] in allowed_states
    assert candidate['severity'] in {'P0', 'P1', 'P2', 'P3'}
    assert type(candidate['runtime_executed']) is bool
    source = ROOT / candidate['path']
    assert candidate['current_source_sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert candidate['rationale'] and candidate['guards'] and candidate['source_checks']
    for check in candidate['source_checks']:
        lines = (ROOT / check['path']).read_text().splitlines()
        assert 1 <= check['start_line'] <= check['end_line'] <= len(lines)
        assert check['observation']
        source_range_count += 1
    for path in candidate['evidence_paths']:
        assert (ROOT / path).is_file(), path
    if candidate['runtime_executed']:
        assert candidate['candidate_id'] in fixtures['results']
    if candidate['decision'] == 'DUPLICATE':
        assert candidate.get('canonical_id')
for item in evidence['source_ranges']:
    source = ROOT / item['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == item['sha256']
    lines = source.read_text().splitlines()
    excerpt = '\n'.join(f'{i + 1}: {lines[i]}' for i in range(item['start_line'] - 1, item['end_line']))
    assert excerpt == item['excerpt']
for path, expected in evidence['path_checks'].items():
    assert (ROOT / path).exists() == expected
print(json.dumps({
    'reviewer': '07',
    'status': 'PASS',
    'candidates': len(actual_ids),
    'decisions': dict(Counter(c['decision'] for c in review['candidates'])),
    'remediation_states': dict(Counter(c['remediation_state'] for c in review['candidates'])),
    'source_checks_validated': source_range_count,
    'distinct_source_ranges_validated': len(evidence['source_ranges']),
    'fixture_cases_present': len(fixtures['results']),
    'review_sha256': hashlib.sha256((BASE / 'reviews/07.json').read_bytes()).hexdigest(),
    'limits': ['Schema/freshness checks do not prove adjudications correct.',
               'No production source change or protected runtime execution.'],
}, indent=2))
