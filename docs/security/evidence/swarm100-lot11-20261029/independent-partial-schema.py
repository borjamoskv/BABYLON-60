"""Observe public error metadata for malformed nested fixture data."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[4]
SOURCE = ROOT / '01_KISH_ENGINE/babylon60/core/cortex_persist.py'
sys.dont_write_bytecode = True
payload = SOURCE.read_bytes()
records = []

def forbidden(*args, **kwargs):
    raise AssertionError('kill/network/subprocess forbidden')

with tempfile.TemporaryDirectory(prefix='lot11-schema-') as temporary, \
        patch.object(os, 'kill', forbidden), patch.object(socket.socket, 'connect', forbidden), \
        patch.object(socket.socket, 'connect_ex', forbidden), patch.object(socket, 'getaddrinfo', forbidden), \
        patch.object(subprocess, 'Popen', forbidden), patch.dict(os.environ, {'HOME': temporary, 'PATH': '/usr/bin:/bin'}, clear=True):
    boundary = Path(temporary)
    copied = boundary / 'fixture.py'
    copied.write_bytes(payload)
    spec = importlib.util.spec_from_file_location('lot11_schema_fixture', copied)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    for case in ('ghosts-non-object', 'session-non-object'):
        home = boundary / case
        os.environ['HOME'] = str(home)
        base = home / '.agent/memory'
        (base / 'projects').mkdir(parents=True)
        (base / 'snapshots').mkdir()
        project = base / 'projects/alpha.json'
        project.write_text('{"meta":{},"recent_changes":[],"decisions":[]}')
        (base / 'ghosts.json').write_text('{"alpha":null}' if case.startswith('ghosts') else '{}')
        (base / 'system.json').write_text('{"meta":{},"sessions_log":[null]}' if case.startswith('session') else '{"meta":{},"sessions_log":[]}')
        ledger = module.CortexOntologyLedger('alpha')
        try:
            ledger.crystallize_session(module.SessionDelta('fixture', 'fixture.py', case, ['new fixture'], []))
        except Exception as error:
            records.append({'case': case, 'error_type': type(error).__name__, 'structured_partial': isinstance(error, module.ConsolidationError), 'completed_files': [Path(p).name for p in getattr(error, 'completed_files', [])], 'project_committed': json.loads(project.read_text())['recent_changes'] != [], 'cause_type': type(error.__cause__).__name__ if error.__cause__ else None})
        else:
            raise AssertionError('Malformed fixture unexpectedly succeeded')
print(json.dumps({'source_sha256': hashlib.sha256(payload).hexdigest(), 'observations': records, 'scope': 'Owned temporary memory only, kill/network/process creation blocked before import'}, indent=2))

if '--expect-fixed' in sys.argv:
    assert all(row['structured_partial'] and row['error_type'] == 'ConsolidationError' and row['cause_type'] == 'AttributeError' for row in records)
    assert records[0]['completed_files'] == ['alpha.json']
    assert records[1]['completed_files'] == ['alpha.json', 'ghosts.json']
