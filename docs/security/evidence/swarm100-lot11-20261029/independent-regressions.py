"""Run the reviewed Lot 11 tests with synthetic HOME and temporary cwd."""
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[4]
SOURCE = ROOT / '01_KISH_ENGINE/babylon60/core/cortex_persist.py'
TEST = ROOT / 'tests/test_swarm100_lot11_regressions.py'
FILES = (SOURCE, TEST)
sys.dont_write_bytecode = True


def hashes():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in FILES}


def forbidden(*args, **kwargs):
    raise AssertionError('Network forbidden in isolated regression run')


def main():
    before = hashes()
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='lot11-independent-pytest-') as temporary, \
            patch.dict(os.environ, {'HOME': temporary, 'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'}, clear=True), \
            patch.object(socket.socket, 'connect', forbidden), patch.object(socket.socket, 'connect_ex', forbidden), \
            patch.object(socket, 'getaddrinfo', forbidden):
        os.chdir(temporary)
        print('SOURCE_HASHES_BEFORE ' + json.dumps(before), flush=True)
        try:
            import pytest
            result = pytest.main([str(TEST), '-q', '-p', 'pytest_asyncio.plugin', '-p', 'no:cacheprovider', '--basetemp', str(Path(temporary) / 'cases')])
        finally:
            os.chdir(original_cwd)
    after = hashes()
    print('SOURCE_HASHES_AFTER ' + json.dumps(after), flush=True)
    assert before == after, 'Sources changed during regression execution'
    return result


if __name__ == '__main__':
    raise SystemExit(main())
