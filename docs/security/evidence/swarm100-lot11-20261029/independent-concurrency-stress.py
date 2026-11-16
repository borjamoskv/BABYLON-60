"""Bounded cooperation check: one warmup, eight calls, four threads, two projects."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[4]
SOURCE = ROOT / '01_KISH_ENGINE/babylon60/core/cortex_persist.py'
TEST = ROOT / 'tests/test_swarm100_lot11_regressions.py'
EXPECTED_SOURCE = '837faee40ae13b74cbb7b4d1e61fc6209285bb3362c23d2d2abd94c480b4b064'
EXPECTED_TEST = '9d4362da20dd1036a1eab183db8ccb6d00f1ff4f9caef0407958b412a1b9a06d'
sys.dont_write_bytecode = True


def hashes():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (SOURCE, TEST)}


def main():
    before = hashes()
    assert before[str(SOURCE.relative_to(ROOT))] == EXPECTED_SOURCE
    assert before[str(TEST.relative_to(ROOT))] == EXPECTED_TEST
    prohibited = []

    def forbidden(*args, **kwargs):
        prohibited.append('kill/network/subprocess')
        raise AssertionError('Protected operation forbidden in bounded fixture')

    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='lot11-cooperating-burst-') as temporary, \
            patch.object(os, 'kill', forbidden), patch.object(socket.socket, 'connect', forbidden), \
            patch.object(socket.socket, 'connect_ex', forbidden), patch.object(socket, 'getaddrinfo', forbidden), \
            patch.object(subprocess, 'Popen', forbidden), \
            patch.dict(os.environ, {'HOME': temporary, 'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1'}, clear=True):
        home = Path(temporary).resolve()
        os.environ['HOME'] = str(home)
        base = home / '.agent/memory'
        (base / 'projects').mkdir(parents=True)
        (base / 'snapshots').mkdir()
        for project in ('alpha', 'beta'):
            (base / 'projects' / (project + '.json')).write_text('{"meta":{},"recent_changes":[],"decisions":[]}')
        (base / 'ghosts.json').write_text('{}')
        (base / 'system.json').write_text('{"meta":{},"sessions_log":[]}')
        copied = home / 'fixture_persist.py'
        copied.write_bytes(SOURCE.read_bytes())
        spec = importlib.util.spec_from_file_location('lot11_independent_burst', copied)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        os.chdir(home)
        try:
            def delta(label):
                return module.SessionDelta('task-' + label, 'fixture.py', label, ['change-' + label], ['decision-' + label], 'fixture')

            with redirect_stdout(io.StringIO()):
                module.CortexOntologyLedger('alpha').crystallize_session(delta('warmup-alpha'))
                lock_path = base / '.cortex-persist.lock'
                lock_inode = lock_path.stat().st_ino
                barrier = threading.Barrier(4, timeout=10)
                instance_ids = []
                instances = []  # Keep identities alive so Python cannot recycle their IDs.
                recording = threading.Lock()

                def consolidate(index):
                    project = 'alpha' if index % 2 == 0 else 'beta'
                    label = f'burst-{index}-{project}'
                    ledger = module.CortexOntologyLedger(project)
                    with recording:
                        instances.append(ledger)
                        instance_ids.append(id(ledger))
                    barrier.wait()
                    ledger.crystallize_session(delta(label))
                    return project, label

                with ThreadPoolExecutor(max_workers=4, thread_name_prefix='lot11-owned-burst') as executor:
                    results = list(executor.map(consolidate, range(8)))
            assert len(set(instance_ids)) == 8
            assert lock_path.stat().st_ino == lock_inode
            expected = {'alpha': {'warmup-alpha'}, 'beta': set()}
            for project, label in results:
                expected[project].add(label)
            # Fresh objects reopen and reread the files after every writer has finished.
            reopened = {project: module.CortexOntologyLedger(project) for project in expected}
            ghosts = reopened['alpha']._read_json(str(base / 'ghosts.json'))
            system = reopened['beta']._read_json(str(base / 'system.json'))
            sessions = system['sessions_log']
            all_labels = expected['alpha'] | expected['beta']
            assert len(sessions) == 9 and {row['conversation_id'] for row in sessions} == all_labels
            assert set(ghosts) == {'alpha', 'beta'}
            retained = {}
            for project, labels in expected.items():
                data = reopened[project]._read_json(str(base / 'projects' / (project + '.json')))
                assert len(data['recent_changes']) == len(labels)
                assert {row['desc'] for row in data['recent_changes']} == {'change-' + label for label in labels}
                assert len(data['decisions']) == len(labels)
                assert {row['decision'] for row in data['decisions']} == {'decision-' + label for label in labels}
                newest = next(row for row in sessions if row['project'] == project)
                assert data['ghost']['last_conversation'] == ghosts[project]['last_conversation'] == newest['conversation_id']
                assert ghosts[project]['last_conversation'] in labels
                retained[project] = {'session_ids': sorted(labels), 'project_changes': len(data['recent_changes']), 'decisions': len(data['decisions']), 'latest_ghost_id': ghosts[project]['last_conversation']}
            assert not list(base.rglob('.cortex-persist-*.tmp'))
            assert not prohibited
        finally:
            os.chdir(original_cwd)
    after = hashes()
    assert before == after
    print(json.dumps({'status': 'PASS', 'control': 'warmup_then_eight_calls_four_threads_two_projects_distinct_instances_and_reopen', 'configuration': {'warmup_calls': 1, 'concurrent_calls': 8, 'worker_threads': 4, 'projects': 2, 'distinct_concurrent_instances': 8, 'barrier_parties': 4, 'unique_ids': 9, 'owned_fixtures': 1}, 'reopened_sessions': 9, 'retained_by_project': retained, 'persistent_lock_inode_unchanged': True, 'prohibited_calls': prohibited, 'source_sha256_before': before, 'source_sha256_after': after, 'limits': 'Bounded cooperating writers on this local POSIX filesystem; no throughput, physical stress, network filesystem, hostile-writer, power-cut or global three-file transaction claim.'}, indent=2))


if __name__ == '__main__':
    main()
