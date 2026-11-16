"""Independent Lot4 checks: temporary files and software cryptography only.

Never invokes Git, a generator on repository data, hardware, or authorization.
All executable code loaded here is the reviewed import-safe snapshot core.
"""
import hashlib
import json
import os
from pathlib import Path
import runpy
import tempfile
import types

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'proof/bundles/attestation_bundle_v1/verify'
EVIDENCE = Path(__file__).parent
RESULTS = []


def rejected(call):
    try:
        call()
    except Exception as error:
        return type(error).__name__
    raise AssertionError('Expected rejection')


def check(name, function):
    try:
        detail = function()
        RESULTS.append(dict(name=name, status='PASS', detail=detail))
    except Exception as error:
        RESULTS.append(dict(name=name, status='FAIL', error=repr(error)))


def main():
    initial_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    old_cwd, old_home = Path.cwd(), os.environ.get('HOME')
    with tempfile.TemporaryDirectory(prefix='lot4-independent-') as temporary:
        workspace = Path(temporary)
        os.environ['HOME'] = temporary
        os.chdir(temporary)
        try:
            api = runpy.run_path(str(SOURCE))
            namespace = api['build_snapshot'].__globals__
            namespace['subprocess'] = types.SimpleNamespace(
                check_output=lambda *a, **k: b'1' * 40,
                SubprocessError=RuntimeError, DEVNULL=-3)
            namespace['platform'] = types.SimpleNamespace(
                system=lambda: 'FixtureOS', machine=lambda: 'FixtureArch',
                release=lambda: 'FixtureRelease', python_version=lambda: 'FixturePython')
            namespace['time'] = types.SimpleNamespace(time=lambda: 1_790_000_000)

            def build(name):
                folder = workspace / name
                folder.mkdir()
                (folder / 'CLAIMS.toml').write_bytes(b'claims fixture\n')
                (folder / 'artifact').write_bytes(b'artifact fixture\n')
                bundle = folder / 'bundle'
                manifest = api['build_snapshot'](
                    folder, bundle, ['CLAIMS.toml', 'artifact'], 'v1-wrapper')
                return folder, bundle, manifest

            def baseline():
                folder, bundle, _ = build('baseline')
                result, status = api['verify_bundle'](bundle, folder)
                assert status == 2 and result['result'] == 'NOT_AUTHENTICATED'
                result, status = api['verify_bundle'](bundle, folder, integrity_only=True)
                assert status == 0 and result['tests'] == 'NOT_EXECUTED'
                assert result['hw_provenance'] == 'UNVERIFIED'
                return 'Default refuses authentication; explicit integrity stays limited.'

            def signature_binding():
                folder, bundle, manifest = build('signature')
                key = ec.generate_private_key(ec.SECP256R1())
                anchor = folder / 'external-fixture-anchor.pem'
                anchor.write_bytes(key.public_key().public_bytes(
                    serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
                signature = key.sign(api['signature_message'](manifest), ec.ECDSA(hashes.SHA256()))
                (bundle / 'signature.der').write_bytes(signature)
                value, status = api['verify_bundle'](bundle, folder, trusted_key=anchor)
                assert status == 0 and value['tests'] == 'NOT_EXECUTED'
                assert value['certification'] == 'NONE'
                manifest['commit'] = '2' * 40
                raw = api['canonical'](manifest) + b'\n'
                (bundle / 'manifest.json').write_bytes(raw)
                (bundle / 'manifest.blake3').write_text(api['digest'](raw) + '\n')
                assert rejected(lambda: api['verify_bundle'](bundle, folder, trusted_key=anchor)) == 'InvalidSignature'
                return 'Temporary P-256 math validates unchanged body and rejects rehashed commit mutation.'

            def claims_budget():
                folder = workspace / 'claims-budget'
                folder.mkdir()
                (folder / 'CLAIMS.toml').write_bytes(b'x' * (api['MAX_METADATA'] + 1))
                output = folder / 'bundle'
                rejected(lambda: api['build_snapshot'](folder, output, ['CLAIMS.toml'], 'v1-wrapper'))
                assert not output.exists()
                return 'Oversize claims rejected before output creation.'

            def parser():
                for data in (b'{"n":1e999}', b'{"n":NaN}', b'{"n":Infinity}',
                             b'{"x":1,"x":2}', b'{"bad":"\\ud800"}'):
                    rejected(lambda data=data: api['parse_json'](data))
                return 'Overflow, nonfinite literals, duplicate keys and invalid surrogate rejected.'

            def unknown_platform():
                old_platform = namespace['platform']
                namespace['platform'] = types.SimpleNamespace(
                    system=lambda: 'FixtureOS', machine=lambda: '',
                    release=lambda: 'FixtureRelease', python_version=lambda: 'FixturePython')
                try:
                    try:
                        folder, bundle, _ = build('unknown-platform')
                    except ValueError:
                        assert not (workspace / 'unknown-platform' / 'bundle').exists()
                        return 'Unavailable platform observation rejected before writing.'
                    result, status = api['verify_bundle'](bundle, folder, integrity_only=True)
                    assert status == 0 and result['hw_provenance'] == 'UNVERIFIED'
                    return 'Unavailable platform observation explicitly represented without hardware certification.'
                finally:
                    namespace['platform'] = old_platform

            def manifest_budget():
                folder = workspace / 'manifest-budget'
                folder.mkdir()
                (folder / 'CLAIMS.toml').write_bytes(b'claims fixture')
                parts = ['d' * 200] * 84
                fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    for part in parts:
                        os.mkdir(part, dir_fd=fd)
                        child = os.open(part, os.O_RDONLY | os.O_DIRECTORY, dir_fd=fd)
                        os.close(fd)
                        fd = child
                    names = ['CLAIMS.toml']
                    for i in range(255):
                        name = f'f{i:03d}'
                        leaf = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=fd)
                        try:
                            os.write(leaf, b'x')
                        finally:
                            os.close(leaf)
                        names.append('/'.join(parts + [name]))
                finally:
                    os.close(fd)
                bundle = folder / 'bundle'
                rejected(lambda: api['build_snapshot'](folder, bundle, names, 'v1-wrapper'))
                assert not bundle.exists()
                return 'Actual manifest larger than 4 MiB from valid long paths rejected before output.'

            def output_collision():
                for kind in ('file', 'directory', 'symlink'):
                    parent = workspace / ('collision-' + kind)
                    parent.mkdir()
                    target = parent / 'existing'
                    sentinel = parent / 'sentinel'
                    sentinel.write_bytes(b'preserve')
                    if kind == 'file':
                        target.write_bytes(b'preserve existing')
                    elif kind == 'directory':
                        target.mkdir()
                        (target / 'prior').write_bytes(b'preserve prior')
                    else:
                        target.symlink_to(sentinel)
                    rejected(lambda: api['write_new_bundle'](target, {'fixture': b'new'}))
                    assert sentinel.read_bytes() == b'preserve'
                    if kind == 'file':
                        assert target.read_bytes() == b'preserve existing'
                    elif kind == 'directory':
                        assert (target / 'prior').read_bytes() == b'preserve prior'
                    else:
                        assert target.is_symlink()
                return 'Existing file, directory and symlink preserved.'

            def rollback():
                target = workspace / 'failed-write'
                real_os = namespace['os']
                class FailingSync:
                    def __getattr__(self, name):
                        return getattr(real_os, name)
                    def fsync(self, fd):
                        raise OSError('injected fixture sync failure')
                namespace['os'] = FailingSync()
                try:
                    rejected(lambda: api['write_new_bundle'](target, {'fixture': b'new'}))
                finally:
                    namespace['os'] = real_os
                assert not target.exists()
                return 'Failure during first fsync removes only the newly created output.'

            def observed_mutation():
                folder, _, _ = build('read-mutation')
                real_os = namespace['os']
                class MutatingStat:
                    calls = 0
                    def __getattr__(self, name):
                        return getattr(real_os, name)
                    def fstat(self, fd):
                        self.calls += 1
                        if self.calls == 2:
                            (folder / 'artifact').write_bytes(b'changed concurrently\n')
                        return real_os.fstat(fd)
                namespace['os'] = MutatingStat()
                root_fd = api['open_root'](folder)
                try:
                    rejected(lambda: api['read_relative'](root_fd, 'artifact'))
                finally:
                    real_os.close(root_fd)
                    namespace['os'] = real_os
                return 'Observed size/identity change while reading is rejected.'

            def unexpected_entries():
                folder, bundle, _ = build('extra-entry')
                (bundle / 'unbound-field').mkdir()
                rejected(lambda: api['verify_bundle'](bundle, folder, integrity_only=True))
                return 'Extra bundle entries rejected rather than silently left unbound.'

            def budget_equality():
                folder, _, _ = build('budget-equality')
                root_fd = api['open_root'](folder)
                try:
                    data = (folder / 'artifact').read_bytes()
                    assert api['read_relative'](root_fd, 'artifact', len(data)) == data
                    rejected(lambda: api['read_relative'](root_fd, 'artifact', len(data) - 1))
                finally:
                    os.close(root_fd)
                return 'Read budget accepts exact bound and rejects one byte over.'

            for name, test in (
                ('unsigned_baseline', baseline), ('signed_body_binding', signature_binding),
                ('claims_budget', claims_budget), ('strict_json', parser),
                ('unknown_platform_consistency', unknown_platform),
                ('manifest_budget', manifest_budget),
                ('output_collisions', output_collision), ('write_rollback', rollback),
                ('observed_read_mutation', observed_mutation),
                ('unexpected_bundle_entry', unexpected_entries), ('exact_read_budget', budget_equality)):
                check(name, test)
        finally:
            os.chdir(old_cwd)
            if old_home is None:
                os.environ.pop('HOME', None)
            else:
                os.environ['HOME'] = old_home
    final_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    report = dict(source_sha256=initial_hash, final_source_sha256=final_hash,
                  source_stable=initial_hash == final_hash, checks=RESULTS,
                  passed=sum(r['status'] == 'PASS' for r in RESULTS),
                  failed=sum(r['status'] == 'FAIL' for r in RESULTS),
                  scope='Temporary roots/HOME, observed-platform and Git stubs, temporary software keys; no ATTESTED, hardware, real Git, network or operator data.')
    (EVIDENCE / 'independent-adversarial.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if not report['failed'] and report['source_stable'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
