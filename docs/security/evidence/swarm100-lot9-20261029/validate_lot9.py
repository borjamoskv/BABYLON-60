"""Run scoped verification and record command/log/source digests."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).absolute().parents[4]
HERE = Path(__file__).absolute().parent
SOURCE = 'scripts/c5_thermo/c5_exergy_optimizer_monitor.py'
TEST = 'tests/test_swarm100_lot9_regressions.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--documents', action='store_true')
    args = parser.parse_args()
    output = HERE/'validation.json'
    value = json.loads(output.read_text()) if output.exists() else dict(
        date='2026-10-29', timezone='Europe/Madrid',
        scope='Only c5_exergy_optimizer_monitor.py production edited. Actual Git commits/hooks only in owned temporary repositories; synthetic HOME/identity and isolated config. Inert failing signer recorder, no signing key. Monitor producers/database/audits/tests replaced in fixtures; real TCP/DNS/SQLite prohibited there. No actual monitor run, commit/amend on real checkout, protected runtime, network, hardware, dependencies/lockfiles/publication or ATTESTED. Git/config/hooks trusted; no global transaction against concurrent STATUS writers. Global telemetry omitted.',
        checks={})
    prefix = ['uv', 'run', '--locked', '--no-sync']
    if args.documents:
        commands = {
            'semantic-gate':['python3', 'scripts/c5_quality_gates/audit_semantic_contracts.py', '--workspace-only'],
            'budget-gate':['python3', 'scripts/c5_quality_gates/audit_token_budget.py', '--workspace-only', '--skip-ghost-listeners'],
            'topology-gate':['python3', 'scripts/guards/verify_active_topology.py'],
            'diff-check':['git', 'diff', '--check'],
            'ruff':prefix+['ruff', 'check', SOURCE, TEST, *[str(path.relative_to(ROOT)) for path in sorted(HERE.glob('*.py'))]],
        }
    else:
        previous = json.loads((HERE.parent/'swarm100-lot8-20261029/validation.json').read_text())
        old = previous['checks']['related-tests']['command']
        index = old.index('-c')
        bootstrap = old[index+1].replace('b60-lot8-tests-', 'b60-lot9-tests-')
        commands = {
            'related-tests':prefix+['python', '-c', bootstrap, TEST, *old[index+2:]],
            'mypy':prefix+['mypy', '--follow-imports=silent', '--check-untyped-defs', SOURCE],
        }
    frozen = {path:sha(ROOT/path) for path in [SOURCE, TEST]}
    for name, command in commands.items():
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=360)
        log = HERE/(name+'.log')
        log.write_text(result.stdout+result.stderr)
        assert all(sha(ROOT/path)==digest for path, digest in frozen.items()), 'Sources changed during verification'
        value['checks'][name] = dict(command=command, exit_code=result.returncode,
                                    log=str(log.relative_to(ROOT)), log_sha256=sha(log),
                                    source_sha256_before_and_after=frozen)
        output.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
        print(f'{name}: exit={result.returncode}\n{(result.stdout+result.stderr)[-1800:]}', flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
