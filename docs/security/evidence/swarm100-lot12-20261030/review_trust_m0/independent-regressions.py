"""Run the frozen trust/M0 suites and preserved CRL controls in a synthetic HOME."""
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[5]
EVIDENCE = Path(__file__).absolute().parent
SOURCES = ['01_KISH_ENGINE/babylon60/attestation/conformal_tree.py', '01_KISH_ENGINE/babylon60/attestation/merkle_anchor.py', 'tools/tamkarum_license_provisioner.py', '01_KISH_ENGINE/babylon60/verifier/standalone_verify.py']
TESTS = ['tests/test_swarm100_lot12_s2_trust_regressions.py', 'tests/test_swarm100_lot12_m0_regressions.py', 'tests/test_swarm100_round2_regressions.py']
sys.dont_write_bytecode = True


def hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCES + TESTS}


def forbidden(*args, **kwargs):
    raise AssertionError('Network or kill forbidden in regression fixture')


def main():
    before = hashes()
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='lot12-review-regressions-') as temporary, \
            patch.dict(os.environ, {'HOME': temporary, 'BABYLON_HOME': temporary, 'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'BABYLON60_SIGNING_SEED': '00' * 32}, clear=True), \
            patch.object(socket.socket, 'connect', forbidden), patch.object(socket.socket, 'connect_ex', forbidden), \
            patch.object(socket, 'getaddrinfo', forbidden), patch.object(os, 'kill', forbidden):
        sys.path.insert(0, str(ROOT / '01_KISH_ENGINE'))
        sys.modules['strike_rs'] = None
        import dotenv
        dotenv.load_dotenv = lambda *args, **kwargs: False
        dotenv.dotenv_values = lambda *args, **kwargs: {}
        os.chdir(temporary)
        print('SOURCE_HASHES_BEFORE ' + json.dumps(before), flush=True)
        try:
            import pytest
            args = [str(ROOT / p) for p in TESTS[:2]] + [str(ROOT / TESTS[2]) + '::' + name for name in ['test_v03_crl_rejects_bad_file', 'test_v03_crl_missing_file_and_controls', 'test_v03_cli_rejects_crl_without_traceback', 'test_v03_signed_revoked_certificate_remains_rejected']]
            if '--v04' in sys.argv:
                args = [str(ROOT / TESTS[2]) + '::' + name for name in ['test_v04_payload_hash_must_commit_content', 'test_v04_invalid_json_shape_rejected', 'test_v04_hash_only_scope_is_explicit']]
            args += ['-q', '-p', 'pytest_asyncio.plugin', '-p', 'no:cacheprovider', '-o', 'addopts=--tb=short', '--basetemp', str(Path(temporary) / 'cases')]
            print('PYTEST_ARGUMENTS ' + json.dumps(args), flush=True)
            result = pytest.main(args)
        finally:
            os.chdir(original_cwd)
    after = hashes()
    print('SOURCE_HASHES_AFTER ' + json.dumps(after), flush=True)
    assert before == after, 'Sources changed during regression run'
    return result


if __name__ == '__main__':
    raise SystemExit(main())
