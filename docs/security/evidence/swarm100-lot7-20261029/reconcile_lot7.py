"""Reconcile false gate success and fabricated receipt fixes, not SMT claims."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]
HERE = Path(__file__).absolute().parent
ROUND3 = HERE.parent/'swarm100-round3-20261028'
SOURCE = 'scripts/c5_verifiers/fast_smt_gate.py'


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
    if not (HERE/'root-adjudications-before-lot7.json').exists():
        write(HERE/'root-adjudications-before-lot7.json', previous)
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
        'FIXED refers to unsupported success and fabricated/unbound receipts. No solver/checker was added: all 25 properties remain NOT_EXECUTED/NOT_IMPLEMENTED and are not certified.',
        'FAIL/UNKNOWN are reported caller statuses, not proof. PASS and legacy boolean tuples are rejected; no inventory state makes this gate return zero.',
        'JSON v3 and legacy --scitt/API names emit unsigned reports. Old boolean receipt inputs are incompatible and explicitly rejected; historical receipts were not rewritten.',
        'BLAKE3 binds the complete canonical body/configuration with a domain, excluding only its own digest. It provides content consistency, not signature, authenticity or tamper resistance against recomputation.',
        'Observations are typed directory-entry metadata only, never invariant checks. Exported observations remain REPORTED_OBSERVATIONS_NOT_PROOF; path roots are not an OS sandbox.',
        'No Ed25519 key, SCITT issuance, hardware approval, legal assessment or ATTESTED occurs. Timing is report latency, never SMT verification latency.',
        'Only copied source and synthetic HOME/root, sockets/DNS prohibited; consumer phase extracted alone with subprocess doubles. No full maintenance, auto-fixer or native solver executed.',
        'Present-gate nonzero makes the observed consumer phase fail. The separate consumer missing-script default-success branch remains outside this single-file fix.',
    ]
    descriptions = {
        'SW100-C0556': (
            'Replaced literal True/path-existence pseudo-verification with a complete, validated 25-ID catalogue of NOT_EXECUTED records. Directory-entry observations are separate and cannot authorize a PASS. Absent checkers, UNKNOWN, FAIL and invalid/missing inventories all block gate success in default, JSON, legacy --scitt and strict modes. The present-script maintenance consumer rejects that nonzero status in isolated function tests. Seven original reproductions failed before the patch; the final regression suite covers exit codes and honest statuses. This fixes false success without implementing or proving the underlying invariants.',
            [('_not_executed','All catalogue entries explicitly lack an executable checker.'),
             ('_validated_results','Requires every unique known ID, explicit fields and supported non-PASS statuses.'),
             ('observe_workspace','Read-only typed metadata observations remain separate from invariants.'),
             ('run_fast_smt_verification','No supported inventory can produce a zero gate exit; invalid data also blocks.')]),
        'SW100-C0557': (
            'Replaced the ID-only digest, formatted pseudo-Ed25519 signature and literal compliance with a versioned UNSIGNED report. Strict canonical JSON and domain-separated BLAKE3 bind all body fields, including ID/status/description/detail, configuration, observations, metrics and local timestamp. Mutation tests with fixed IDs/time and an independently recomputed digest verify content binding. The report expressly says signature None/UNSIGNED, SCITT NOT_ISSUED, certification NONE, legal NOT_ASSESSED and hardware UNVERIFIED. Legacy boolean receipt inputs are rejected; no authenticator or signer is claimed.',
            [('_canonical','Canonical sorted UTF-8 JSON rejects NaN/infinity in serialized values.'),
             ('_validated_configuration','Allows only the explicit supported unsigned catalogue profile.'),
             ('generate_scitt_receipt','Legacy API alias exports unsigned full-content report with no fabricated signature or compliance.')]),
    }
    updates = []
    for cid, (rationale, checks) in descriptions.items():
        item = copy.deepcopy(records[cid]['current'])
        item.update(decision='ALREADY_FIXED', remediation_state='FIXED', current_source_sha256=sha(ROOT/SOURCE),
                    rationale=rationale, source_checks=[check(name, observation) for name, observation in checks],
                    guards=guards, runtime_executed=True,
                    runtime_scope='Copied CLI/report functions and owned temporary paths; consumer function only with subprocess doubles. No SMT proof or real maintenance/signing.',
                    evidence_paths=evidence, resolution_type='CODE_AND_CONFINED_REGRESSIONS_VERIFIED')
        updates.append(item)
    write(HERE/'candidate-status-updates.json', updates)
    ids = {i['candidate_id'] for i in updates}
    write(ROUND3/'root-adjudications.json', [i for i in previous if i['candidate_id'] not in ids]+updates)
    print('C0556/C0557 FIXED for false gate success and fabricated/unbound receipt; 25 invariant checks remain NOT_IMPLEMENTED.')


if __name__ == '__main__':
    main()
