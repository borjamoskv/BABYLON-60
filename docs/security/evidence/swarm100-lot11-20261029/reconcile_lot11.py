"""Reconcile per-file JSON atomicity, cooperative session locking and UTC time."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]
HERE = Path(__file__).absolute().parent
ROUND3 = HERE.parent/'swarm100-round3-20261028'
SOURCE = '01_KISH_ENGINE/babylon60/core/cortex_persist.py'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name, observation):
    nodes = ast.parse((ROOT/SOURCE).read_text()).body
    for part in name.split('.'):
        node = next(n for n in nodes if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == part)
        nodes = node.body
    return dict(path=SOURCE, start_line=node.lineno, end_line=node.end_lineno, observation=observation)


def main():
    records = {r['original']['candidate_id']:r for r in read(ROUND3/'registry.json')['records']}
    previous = read(ROUND3/'root-adjudications.json')
    if not (HERE/'root-adjudications-before-lot11.json').exists():
        write(HERE/'root-adjudications-before-lot11.json', previous)
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
        'Atomicity is per file. Project, ghosts and system are three sequential commits; no journal, recovery protocol or indivisible multi-file transaction is claimed.',
        'PersistenceWriteError distinguishes NOT_ATTEMPTED/NOT_REPLACED/REPLACED/UNKNOWN. Directory fsync failure after replace leaves new JSON visible with durability unconfirmed; no blind rollback occurs.',
        'ConsolidationError preserves ordinary failure cause and completed_files, including AttributeError from malformed containers after earlier files committed. No success is printed on failure.',
        'Fresh flock descriptor per public session serializes cooperating writers sharing base_dir across instances/projects. Private _write_json is per-file atomic only, not independently protected RMW.',
        'Lock is persistent, never deleted/truncated or recovered by age/PID. Logical memory-directory and lock identities are revalidated; no atomic compare/replace against hostile noncooperators or ancestor renames is certified.',
        'Only existing owned single-link regular memory JSON files and no-follow directories are supported. Read-only destinations reject. Basic permission bits are retained; ACLs/xattrs are not guaranteed preserved.',
        'UTC aware timestamps preserve new instants; historical timestamp strings and inherited schema/retention transformations are not migrated.',
        'fsync and replace executed on local POSIX fixtures; this is not a physical power-cut or network-filesystem durability/locking proof. Abrupt child termination can leave an uncommitted temporary, which is neither read nor deleted by guesswork.',
        'Original os.kill was inert in baseline fixtures; patched ordinary errors raise exceptions. Owned fixture children only, synthetic HOME seeded before import, TCP/DNS blocked. No operator memory/process, protected runtime, real keys/hardware/ATTESTED or publication.',
        'This is core/cortex_persist.py, not the separate BFT cortex_persist_ledger implementation. Previous lot sources/dependencies/lockfiles remain unchanged. Global telemetry omitted.'
    ]
    descriptions = {
        'SW100-C0167': (
            'Replaced live truncation with a validated finite JSON payload, exclusive same-directory temporary, write-all loop, file fsync, descriptor-relative atomic replace and parent fsync. Identity checks and cleanup only of the created temporary avoid rewriting unrelated targets. Faults before/after replace report observed replacement state instead of fabricated success; per-session completed files and original causes remain explicit. Original partial-write reproduction lost the prior JSON; final fixtures preserve old or new valid content by commit boundary, including controlled abrupt child exit. This closes per-file truncation/durability mechanics, not a transaction across the three files.',
            [('CortexOntologyLedger._write_json','Exclusive temporary/full write/fsync/replace/parent sync and explicit failure state.'),
             ('PersistenceWriteError','Replacement visibility is distinct from durability confirmation.'),
             ('ConsolidationError','Reports completed files and current replacement state without rollback.'),
             ('CortexOntologyLedger.crystallize_session','Wraps ordinary errors with partial progress and never announces failure as success.')]),
        'SW100-C0168': (
            'A persistent base_dir operation lock with a new flock descriptor per public call now covers the entire read/modify/write sequence for project, ghosts and system. Same and different project instances/threads/processes share that lock; no per-project split or lockfile deletion is used. Fresh base/lock identity checks reject directory substitution so a prior lock cannot authorize writes to a new memory directory. Deterministic old-code interleavings lost project/ghost/session updates; patched thread/process fixtures retain them, with inherited bounded retention unchanged. The guarantee is cooperative, local POSIX locking, not arbitrary writer or multi-file reader isolation.',
            [('CortexOntologyLedger._exclusive_session','Fresh descriptor and persistent common flock cover all public session updates.'),
             ('CortexOntologyLedger._base_handle','No-follow directory chain and active base identity comparison.'),
             ('CortexOntologyLedger._check_operation_lock','Revalidates logical base and bound lock before data accesses/replacement.'),
             ('CortexOntologyLedger._crystallize_locked','Original data transforms/retention run within common exclusion.')]),
        'SW100-C0169': (
            'Removed the literal +02:00 suffix applied to UTC clock fields. New timestamps use datetime.now(timezone.utc).isoformat(), retaining the actual aware instant and precision. Fixed summer and winter UTC instants compare equal after parsing, and historical strings remain unchanged under normal retained data. This changes storage timestamps, not operator presentation timezone or consensus logical-clock claims.',
            [('CortexOntologyLedger._get_iso_now','Explicit UTC-aware ISO timestamp for new data.')]),
    }
    updates = []
    for cid, (rationale, checks) in descriptions.items():
        item = copy.deepcopy(records[cid]['current'])
        item.update(decision='ALREADY_FIXED', remediation_state='FIXED', current_source_sha256=sha(ROOT/SOURCE),
                    rationale=rationale, source_checks=[check(name, observation) for name, observation in checks],
                    guards=guards, runtime_executed=True,
                    runtime_scope='Owned synthetic HOME memory; actual JSON/fcntl/fsync/replace, deterministic threads and controlled Python children; no operator memory/process or protected runtime.',
                    evidence_paths=evidence, resolution_type='CODE_AND_CONFINED_REGRESSIONS_VERIFIED')
        updates.append(item)
    write(HERE/'candidate-status-updates.json', updates)
    ids = {item['candidate_id'] for item in updates}
    write(ROUND3/'root-adjudications.json', [item for item in previous if item['candidate_id'] not in ids]+updates)
    print('C0167/C0168/C0169 FIXED: per-file replacement, cooperative whole-session locking and UTC timestamps; multi-file transaction not claimed.')


if __name__ == '__main__':
    main()
