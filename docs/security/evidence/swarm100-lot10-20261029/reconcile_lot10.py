"""Reconcile scoped purge preservation, not physical erasure or atomic unlink."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]
HERE = Path(__file__).absolute().parent
ROUND3 = HERE.parent/'swarm100-round3-20261028'
SOURCE = 'scripts/c5_verifiers/purge_residuals.py'


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
    if not (HERE/'root-adjudications-before-lot10.json').exists():
        write(HERE/'root-adjudications-before-lot10.json', previous)
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
    guards = [
        'Only current Python .pyc headers in __pycache__ are deletion candidates; directories, opaque .DS_Store/cache data and unknown artifacts are preserved. Legacy broad cleanup compatibility is intentionally narrowed.',
        'Database/lock-name filtering is conservative; scratch and metadata/dependency/cache subtrees are excluded, not recursively certified. No database cleanup/checkpoint/ownership override is implemented.',
        'MAGIC/header/flags recognition is not provenance or bytecode validity. A caller-controlled file with a recognized header can still meet the scoped policy.',
        'Descriptor-relative O_NOFOLLOW/O_NONBLOCK and stat/fstat revalidation detect tested substitutions, preserve hardlinks/foreign owners and avoid following links. Python stat-to-unlink is not atomic against hostile concurrent pathname replacement.',
        'No OS sandbox, bind-mount containment, hostile ancestor/directory-rename isolation, complete filesystem inventory or physical-space/erasure claim is certified.',
        'The report records deletion only after successful unlink; failures/budgets are errors and CLI nonzero. SCOPED_OK means completion within this narrow scope, not all caches removed or repository safety.',
        'verify_va is no longer invoked automatically. Cleanup emits no 0-percent entropy, signature, hardware attestation or certification.',
        'Actual cleanup/SQLite/Git effects only in owned temporary fixtures, synthetic HOME/config; original verifier stubbed and patched runtime has no verifier import. No real project purge/operator database, signing, protected runtime, network, publication or ATTESTED.',
        'Data preservation was observed by inode/content, live SQLite/WAL/SHM and Git exclusion with a lock fd open. This is not evidence of actual Git corruption, power-loss resilience or physical deletion. Global telemetry omitted.'
    ]
    descriptions = {
        'SW100-C0574': (
            'Removed suffix-based operational lock deletion and all recursive directory removal. Git entries/recognized bare and worktree metadata structures are excluded without following outside pointers; lock-like names are preserved even inside candidate caches. Nine initial red reproductions included index.lock/packed-refs.lock pathname removal with descriptors still open and a competing Git update succeeding after unlink. The patched fixtures preserve lock inode/content and Git exclusion while its descriptor stays open, irrespective of old timestamp. No corruption of an operator repository is claimed.',
            [('_protected_name','Conservative database/lock filtering precedes candidate selection.'),
             ('_git_metadata','Recognizes Git/bare/worktree metadata shapes without following destinations.'),
             ('_scan','Excludes protected subtrees, never rmtree/rmdir and only dispatches regular scoped bytecode candidates.'),
             ('purge_repository_residuals','Descriptor-rooted cleanup and factual structured outcome, no other verifier.')]),
        'SW100-C0575': (
            'Removed unconditional scratch/*.db* deletion and broad cache-directory removal. Scratch, database/auxiliary/lock names and unknown cache data are outside deletion scope; a SQLite file disguised as .pyc is preserved when its header is unrecognized. Only owned single-link regular current-Python header candidates inside __pycache__ can be unlinked after identity revalidation. Live temporary database/WAL/SHM, lookalikes, cached database and hardlink/symlink cases remain intact. This fixes unauthorized data selection by removing that cleanup path; it does not implement authorized database disposal or prove bytecode provenance.',
            [('_protected_name','Database/SQLite/journal/WAL/SHM names cannot select a deletion.'),
             ('_delete_bytecode','Own single-link header recognition with descriptor access and identity rechecks before unlink.'),
             ('_scan','Scratch/opaque caches are excluded and special/unknown files preserved.'),
             ('main','JSON/text report and nonzero error result replace unsupported blanket success.')]),
    }
    updates = []
    for cid, (rationale, checks) in descriptions.items():
        item = copy.deepcopy(records[cid]['current'])
        item.update(decision='ALREADY_FIXED', remediation_state='FIXED', current_source_sha256=sha(ROOT/SOURCE),
                    rationale=rationale, source_checks=[check(name, observation) for name, observation in checks],
                    guards=guards, runtime_executed=True,
                    runtime_scope='Owned temporary cleanup roots, compiled fixture bytecode, live temporary SQLite/WAL and real fixture Git locking; no operator data/purge/protected runtime.',
                    evidence_paths=evidence, resolution_type='CODE_AND_CONFINED_REGRESSIONS_VERIFIED')
        updates.append(item)
    write(HERE/'candidate-status-updates.json', updates)
    ids = {item['candidate_id'] for item in updates}
    write(ROUND3/'root-adjudications.json', [item for item in previous if item['candidate_id'] not in ids]+updates)
    print('C0574/C0575 FIXED for unsafe deletion selection; narrow bytecode scope and concurrency/header limits retained.')


if __name__ == '__main__':
    main()
