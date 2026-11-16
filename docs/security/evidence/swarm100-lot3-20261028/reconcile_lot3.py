"""Reconcile publication fixes; retain original inventories and historical evidence."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]
HERE = Path(__file__).absolute().parent
ROUND3 = HERE.parent/'swarm100-round3-20261028'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(path, literal, observation):
    lines = (ROOT/path).read_text().splitlines()
    index = next(i for i, line in enumerate(lines, 1) if (line.strip() == literal[1:] if literal.startswith('^') else literal in line))
    return dict(path=path, start_line=index, end_line=index, observation=observation)


def main():
    records = {r['original']['candidate_id']:r for r in read(ROUND3/'registry.json')['records']}
    previous = read(ROUND3/'root-adjudications.json')
    additional = read(ROUND3/'additional-findings.json')
    for name, data in [('root-adjudications-before-lot3.json', previous),
                       ('additional-findings-before-lot3.json', additional)]:
        target = HERE/name
        if not target.exists():
            write(target, data)
    review = read(HERE/'independent-review.json')
    assert review['decision'] == 'APPROVED_WITH_EXPLICIT_SCOPE'
    assert review['open_actionable_findings'] == []
    for path, digest in review['source_sha256'].items():
        assert sha(ROOT/path) == digest, path
    assert all(item['exit_code'] == 0 for item in read(HERE/'validation.json')['checks'].values())
    evidence = [str((HERE/name).relative_to(ROOT)) for name in
                ['before-tests.log', 'related-tests.log', 'independent-review.json', 'validation.json']]
    distill = 'scripts/c5_git_utils/c5_distill_public_mirror.sh'
    ship = 'scripts/c5_git_utils/c5_ship.sh'
    guards = [
        'All Git/scanner/gate executable effects observed only through owned temporary doubles; no ATTESTED fixture.',
        'Software field/signature checks do not attest hardware provenance independently of the trusted selected local gate.',
        'Active pre-push hooks, LFS pointers and submodules are explicitly unsupported and rejected; no hook bypass.',
        'Host transport binaries/configuration, hardware integration and real remote publication are outside this verification.',
        'Ship atomically retains the verified receipt plus its effect descriptor at last_ship_receipt.json with mode 0600; no prior receipt is reused. Public projection receipt remains attempt-local.',
    ]
    updates = []
    details = {
        'SW100-C0413': (distill,
            'Mandatory Gitleaks availability/failure now aborts. The scanner receives raw blobs from the selected immutable tree, including export-ignored paths and raw symlink data, with tracked policy/ignores and no Git replacement objects. A real serialized snapshot tar enforces the strict 20 MiB budget. Baseline fake publisher ran without Gitleaks; patched temporary regressions reject it. Zero scanner findings is not proof of absence of secrets.',
            [('mandatory Gitleaks unavailable', 'Missing mandatory scanner exits before local preparation or authorization.'),
             ('git(\'ls-tree\', \'-rz\'', 'Snapshot is built from raw Git blobs, never worktree/archive filtering.'),
             ('gitleaks dir --config', 'Gitleaks runs on snapshot with frozen policy/ignore scope; any nonzero status aborts.')]),
        'SW100-C0418': (ship,
            'Missing both native and usable Swift gate aborts before aliases or local Git mutations. One selected gate attempt must return a bounded, fresh, effect-bound ATTESTED receipt with exact hash/action/scope, normalized agent, session operator and DER P256 signature; failure/cancellation/timeout/invalid output never dispatches or falls back. The baseline fixture dispatched without any gate. Rejection and pure software contract checks pass; no real hardware approval/publication was performed.',
            [('FATAL: c5_biometric_gate unavailable', 'Gate selection has an explicit abort when no provider exists.'),
             ('^select_gate', 'Gate preflight runs before aliases and mutation workflow.'),
             ('publication_tool gate "$WORK/receipt.json"', 'Gate must finish successfully before the immutable dispatcher is called.')]),
    }
    for cid, (path, rationale, checks) in details.items():
        item = copy.deepcopy(records[cid]['current'])
        item.update(decision='ALREADY_FIXED', remediation_state='FIXED', rationale=rationale,
                    current_source_sha256=sha(ROOT/path), runtime_executed=True,
                    runtime_scope='Copied shell entrypoints with fake effect executables; pure binding/crypto functions and temporary snapshots.',
                    guards=guards, evidence_paths=evidence, resolution_type='CODE_AND_CONFINED_REGRESSIONS_VERIFIED',
                    source_checks=[check(path, literal.strip(), observation) for literal, observation in checks])
        updates.append(item)
    cid = 'SW100-C0414'
    item = copy.deepcopy(records[cid]['current'])
    rationale = ('Re-reviewed after Lot3: dry-run still explicitly permits local orphan commit/convenience branch preparation and exits before authorization or remote dispatch. Its prior-tip preservation was not part of the existing contract. This rejection is unchanged; the separate mutable-dispatch finding SW100-R3-0001 is fixed independently using the saved immutable commit.')
    item.update(current_source_sha256=sha(ROOT/distill), rationale=rationale,
                guards=['Preview local preparation remains allowed; authorization/push are explicitly NOT_CHECKED.',
                        'Convenience ref is no longer a dispatch source; the separate additional finding is handled independently.'],
                source_checks=[check(distill, 'git branch -f release/v5.0-clean', 'Local convenience branch preparation remains permitted.'),
                               check(distill, 'Authorization/push NOT_CHECKED.', 'Preview exits before gate or publisher and states verification limits.')],
                evidence_paths=list(dict.fromkeys(item['evidence_paths']+evidence)))
    assert item['decision'] == 'REJECTED' and item['remediation_state'] == 'NOT_APPLICABLE'
    updates.append(item)
    write(HERE/'candidate-status-updates.json', updates)
    ids = {item['candidate_id'] for item in updates}
    write(ROUND3/'root-adjudications.json', [item for item in previous if item['candidate_id'] not in ids]+updates)
    extra = next(item for item in additional if item['candidate_id']=='SW100-R3-0001')
    extra.update(decision='ALREADY_FIXED', remediation_state='FIXED',
                 adjudication_status='FIXED_WITH_CONFINED_REGRESSIONS', current_source_sha256=sha(ROOT/distill),
                 runtime_executed=True, runtime_scope='Two scheduled copied invocations, warmup plus four overlapping attempts and no-op dispatcher selection; no actual authorization/push.',
                 rationale='Baseline fixture A selected the C2 convenience ref after B changed it while A waited. The patched flow signs SHA256 of a per-attempt nonce, immutable commit/tree, destination digest, full target ref, force policy, action/scope/agent and frozen transport-config digest. The isolated dispatcher uses the saved commit and literal destination in a private bare repository without mutable remote rewrites; ls-remote independently checks the target. Patched invalid fixture receipts never dispatch, while direct no-op dispatch tests retain C1 despite branch/config changes. This closes mutable-reference selection, not an end-to-end hardware or transport identity certification.',
                 source_checks=[check(distill, 'effect = dict(schema=', 'Authorization effect includes immutable commit/tree and target/policy metadata.'),
                                check(distill, 'refspec = effect[\'commit\']', 'Dispatcher source is the saved commit and full target ref.'),
                                check(distill, 'GIT_CONFIG_SYSTEM=os.devnull', 'Private bare dispatch omits mutable source/global rewrites.'),
                                check(distill, 'publication_tool prepare "$CLEAN_COMMIT"', 'Entrypoint passes the prepared immutable commit, not convenience ref.')],
                 guards=guards, evidence_paths=evidence)
    write(ROUND3/'additional-findings.json', additional)
    print('C0413/C0418 FIXED; additional SW100-R3-0001 FIXED; C0414 remains NOT_APPLICABLE.')


if __name__ == '__main__':
    main()
