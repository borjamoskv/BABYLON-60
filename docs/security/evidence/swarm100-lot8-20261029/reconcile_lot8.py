"""Reconcile scoped Git Sentinel fixes without claiming a Git/hook sandbox."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]
HERE = Path(__file__).absolute().parent
ROUND3 = HERE.parent/'swarm100-round3-20261028'
SOURCE = 'scripts/c5_cortex/cortex_objectives_transducer.py'


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
    if not (HERE/'root-adjudications-before-lot8.json').exists():
        write(HERE/'root-adjudications-before-lot8.json', previous)
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
        'Commits/hooks ran only in owned temporary repositories with synthetic HOME/identity and isolated Git config. No helper/commit/amend on the real checkout, real signing, network, hardware or ATTESTED.',
        'Normal Git hooks and signing configuration are retained. No --no-verify, hooksPath override, implicit git add, reset, clean, stash or retry bypass is issued.',
        'Whole-file selection only: previous unstaged edits inside a selected generated output are not separated by hunk. Unselected PROJECT.md edits are excluded from YAML-only consumers.',
        'Selected outputs must already be tracked regular files. New/untracked outputs and unsupported index/repository states are explicitly rejected, not silently staged.',
        'Index preparation present at preflight, including intent-to-add and special flags, is rejected without refreshing/writing it. Git --only manages its own temporary staging/rollback for ordinary hook rejection.',
        'Concurrent writers of the SAME selected output are outside the transaction guarantee: late partial staging can be superseded by --only. This limitation was reproduced and is not claimed fixed.',
        'Git/config/hooks are trusted executable code. A hook may expand the commit tree or move refs before postvalidation; the helper detects an unexpected result but does not prevent or roll back that effect. This limitation was reproduced.',
        'Preflight/interleaved staging of unrelated paths is preserved/excluded in fixtures; no OS-level sandbox or global multi-process Git transaction is certified.',
        'Consumers propagate Git failure before printing success, but YAML/PROJECT already written by their producers remain dirty for review; persistence rollback is outside these IDs.',
    ]
    descriptions = {
        'SW100-C0499': (
            'Removed automatic hook-disabled retry. Git commit --only runs once with normal hooks and configured signing; nonzero Git/hook results raise rather than returning an old HEAD or localized diagnostic as success. No-op is decided by a successful scoped binary diff and stable HEAD/index before any commit. Parent, branch and committed-path postvalidation reject unexpected results without undoing another actor. Seven original red reproductions are now covered by the final confined regression suite; normal and rejecting hooks are both observed. Git/config/hooks remain a trust boundary, not a sandbox.',
            [('run_git_sentinel','One scoped commit with normal hooks; failures/no-op/postconditions do not become fabricated success.'),
             ('cmd_add_objective','Git rejection propagates before success output.'),
             ('cmd_add_milestone','Git rejection propagates before success output.'),
             ('cmd_update_status','Git rejection propagates before success output.'),
             ('cmd_iter','Git rejection propagates before success output; selects only actual producer outputs.')]),
        'SW100-C0500': (
            'Replaced repository-wide add/full-index commit with explicit per-consumer output selection and Git --only, without manual staging/reset. YAML-only commands exclude unrelated PROJECT edits; iteration passes only outputs whose producers reported changes. The helper validates root, selector environment, Git state, clean ordinary index including intent-to-add, and tracked regular allowlisted paths. Existing staged/partial content is rejected byte-for-byte; unrelated dirty/untracked data and late staging remain outside the commit. Native fixtures include spaces, binary content, repeated commits and a linked worktree. Guarantees are at whole-file/preflight granularity; concurrent writers of selected outputs and hook-created effects remain documented limitations.',
            [('run_git_sentinel','Allowlist, clean-index/flags/state preflight, no git add and path-restricted commit.'),
             ('_sentinel_regular_bytes','Reads regular index through O_NOFOLLOW without implicit refresh.'),
             ('_sentinel_regular_output','Checks selected path components/type without following symlinks.'),
             ('cmd_add_objective','Only YAML is selected.'),
             ('cmd_add_milestone','Only YAML is selected.'),
             ('cmd_update_status','Only YAML is selected.'),
             ('cmd_iter','Selects YAML and/or PROJECT according to producer mutation flags.')]),
    }
    updates = []
    for cid, (rationale, checks) in descriptions.items():
        item = copy.deepcopy(records[cid]['current'])
        item.update(decision='ALREADY_FIXED', remediation_state='FIXED', current_source_sha256=sha(ROOT/SOURCE),
                    rationale=rationale, source_checks=[check(name, observation) for name, observation in checks],
                    guards=guards, runtime_executed=True,
                    runtime_scope='Actual Git/harmless hooks only in owned temporary repositories, isolated HOME/config; no real-checkout mutation/signing/network/protected runtime.',
                    evidence_paths=evidence, resolution_type='CODE_AND_CONFINED_REGRESSIONS_VERIFIED')
        updates.append(item)
    write(HERE/'candidate-status-updates.json', updates)
    ids = {i['candidate_id'] for i in updates}
    write(ROUND3/'root-adjudications.json', [i for i in previous if i['candidate_id'] not in ids]+updates)
    print('C0499/C0500 FIXED for automatic bypass and broad staging; hook/same-output concurrent-writer limits retained.')


if __name__ == '__main__':
    main()
