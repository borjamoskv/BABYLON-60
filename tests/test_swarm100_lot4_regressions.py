"""Bundle checks confined to copies, synthetic roots and software-only keys.

No ATTESTED object, real operator key, native/hardware effect or remote is used.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

ROOT = Path(__file__).absolute().parents[1]
PATHS = ('proof/bundles/attestation_bundle_v1/verify',
         'scripts/generate_attestation_bundle.py', 'scripts/generate_attestation_bundle_v2.py')
ARTIFACTS = ['Cargo.toml', 'src/lib.rs', 'src/ontology.rs', 'src/secure_fs.rs',
             'src/executor.rs', 'src/admission.rs', 'src/capability.rs',
             'src/bin/fl005_toctou_stress.rs', 'src/bin/fl006_crash_consistency.rs',
             'src/bin/fl007_admission_stress.rs', 'src/bin/fl008_confused_deputy.rs',
             'CLAIMS.toml', 'SECURITY.md']
BOOTSTRAP = """import os, runpy, sys
os.uname = lambda: os.uname_result(('FixtureOS', 'fixture', '0', 'fixture', 'fixture-arch'))
script = sys.argv.pop(1)
runpy.run_path(script, run_name='__main__')
"""


class Fixture:
    def __init__(self, path):
        self.root = path
        for relative in PATHS:
            p = path/relative
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/relative, p)
        for relative in ARTIFACTS:
            p = path/relative
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('software fixture: '+relative+'\n')
        tools = path/'bin'
        tools.mkdir()
        git = tools/'git'
        git.write_text('#!'+sys.executable+'\nprint("'+'1'*40+'")\n')
        git.chmod(0o700)
        self.env = {'PATH':str(tools), 'HOME':str(path), 'TMPDIR':str(path), 'LC_ALL':'C'}

    def generate(self, version, *extra):
        script = self.root/('scripts/generate_attestation_bundle'+('_v2' if version==2 else '')+'.py')
        out = self.output(version)
        result = subprocess.run([sys.executable, '-c', BOOTSTRAP, str(script),
                                 '--root',str(self.root),'--output',str(out),*extra],
                                env=self.env,cwd=self.root,capture_output=True,timeout=20)
        return result, out

    def output(self, version):
        return self.root/('proof/bundles/attestation_bundle_v2' if version==2 else 'attestation_bundle_v1')

    def verify(self, bundle, *extra, version=1):
        script = bundle/'verify' if version==2 else self.root/PATHS[0]
        return subprocess.run([sys.executable,str(script),str(bundle),'--artifact-root',str(self.root),*extra],
                              env=self.env,cwd=self.root,capture_output=True,timeout=15)

    def legacy(self):
        bundle = self.root/'legacy'
        bundle.mkdir()
        digest = 'a'*64
        key = ec.generate_private_key(ec.SECP256R1())
        values = {'manifest.json':json.dumps(dict(binary_sha3='b'*64,causal_hash=digest)),
                  'binary.sha3':'b'*64,'commit.txt':'1'*40,'environment.json':'{}',
                  'claims.snapshot':'fixture','test-results.json':'{"gates":{}}',
                  'causal_hash':digest,'timestamp':'1790000000'}
        for name,value in values.items():
            (bundle/name).write_text(value)
        (bundle/'signature.der').write_bytes(key.sign(digest.encode(),ec.ECDSA(hashes.SHA256())))
        (bundle/'public_key.der').write_bytes(key.public_key().public_bytes(
            serialization.Encoding.X962,serialization.PublicFormat.UncompressedPoint))
        return bundle


@pytest.fixture
def fixture(tmp_path):
    return Fixture(tmp_path)


@pytest.mark.parametrize('version',[1,2])
def test_generators_never_emit_unexecuted_pass(fixture, version):
    result,out = fixture.generate(version)
    assert result.returncode==0,result.stderr
    p=out/('test_results.json' if (out/'test_results.json').exists() else 'test-results.json')
    value=json.loads(p.read_text())
    assert value.get('status')=='NOT_EXECUTED',value
    assert not (fixture.root/'keys').exists()


@pytest.mark.parametrize('component',['claims.snapshot','environment.json','test-results.json','commit.txt','timestamp','manifest.json'])
def test_c0061_legacy_unbound_metadata_is_rejected(fixture, component):
    bundle=fixture.legacy()
    p=bundle/component
    if component.endswith('.json'):
        value=json.loads(p.read_text())
        value['forged']='fixture'
        p.write_text(json.dumps(value))
    else:
        p.write_text('fixture changed metadata')
    result=fixture.verify(bundle)
    assert result.returncode!=0,result.stdout


def test_c0060_bad_signature_does_not_exit_success(fixture):
    bundle=fixture.legacy()
    (bundle/'signature.der').write_bytes(b'invalid DER fixture')
    assert fixture.verify(bundle).returncode!=0


def test_c0087_verifier_recomputes_external_artifact(fixture):
    result,bundle=fixture.generate(2)
    assert result.returncode==0,result.stderr
    initial=fixture.verify(bundle,'--integrity-only',version=2)
    assert initial.returncode==0,initial.stderr
    (fixture.root/'src/lib.rs').write_text('fixture tampered after bundle')
    result=fixture.verify(bundle,'--integrity-only',version=2)
    assert result.returncode!=0,result.stdout


def test_c0088_environment_never_claims_hardware_certification(fixture):
    result,bundle=fixture.generate(2)
    assert result.returncode==0,result.stderr
    environment=json.loads((bundle/'environment.json').read_text())
    assert environment.get('hw_provenance')=='UNVERIFIED',environment
    assert environment.get('os')=='FixtureOS'
    assert 'M3 Pro' not in json.dumps(environment)


@pytest.mark.parametrize('version',[1,2])
def test_importing_generator_has_no_effects(fixture, version):
    name='generate_attestation_bundle'+('_v2' if version==2 else '')+'.py'
    code='import runpy,sys;runpy.run_path(sys.argv[1])'
    result=subprocess.run([sys.executable,'-c',code,str(fixture.root/'scripts'/name)],
                          env=fixture.env,cwd=fixture.root,capture_output=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert not fixture.output(version).exists()
    assert not (fixture.root/'keys').exists()


def core():
    import runpy
    return runpy.run_path(str(ROOT/PATHS[0]))


def rehash(bundle, mutation=None):
    api=core()
    manifest=json.loads((bundle/'manifest.json').read_text())
    if mutation:
        mutation(manifest)
    raw=api['canonical'](manifest)+b'\n'
    (bundle/'manifest.json').write_bytes(raw)
    (bundle/'manifest.blake3').write_text(api['digest'](raw)+'\n')
    return manifest


def replace_component(bundle, name, value):
    api=core()
    data=api['canonical'](value)
    (bundle/name).write_bytes(data)
    return rehash(bundle,lambda m:m['components'].update({name:api['file_record'](name,data)}))


def sign_fixture(bundle, root, key=None, message=None):
    """Software signature only, outside any attestation/authorization protocol."""
    key=key or ec.generate_private_key(ec.SECP256R1())
    manifest=json.loads((bundle/'manifest.json').read_text())
    data=core()['signature_message'](manifest) if message is None else message
    (bundle/'signature.der').write_bytes(key.sign(data,ec.ECDSA(hashes.SHA256())))
    anchor=root/'external-software-trust.pem'
    anchor.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,
                                                   serialization.PublicFormat.SubjectPublicKeyInfo))
    return anchor,key


@pytest.mark.parametrize('version',[1,2])
def test_unsigned_snapshot_requires_explicit_integrity_mode(fixture, version):
    result,bundle=fixture.generate(version)
    assert result.returncode==0,result.stderr
    default=fixture.verify(bundle,version=version)
    assert default.returncode==2
    assert json.loads(default.stdout)['result']=='NOT_AUTHENTICATED'
    explicit=fixture.verify(bundle,'--integrity-only',version=version)
    assert explicit.returncode==0,explicit.stderr
    status=json.loads(explicit.stdout)
    assert status['result']=='UNAUTHENTICATED_INTEGRITY_ONLY'
    assert status['tests']=='NOT_EXECUTED'
    assert status['certification']=='NONE'
    assert status['hw_provenance']=='UNVERIFIED'


@pytest.mark.parametrize('version',[1,2])
def test_software_signed_integrity_requires_external_key_and_never_certifies_tests(fixture, version):
    result,bundle=fixture.generate(version)
    assert result.returncode==0,result.stderr
    anchor,_=sign_fixture(bundle,fixture.root)
    assert fixture.verify(bundle,'--integrity-only',version=version).returncode!=0
    result=fixture.verify(bundle,'--trusted-public-key',str(anchor),version=version)
    assert result.returncode==0,result.stderr
    value=json.loads(result.stdout)
    assert value['signature']=='VERIFIED_AGAINST_EXTERNAL_KEY'
    assert value['tests']=='NOT_EXECUTED'
    assert value['hw_provenance']=='UNVERIFIED'
    assert value['certification']=='NONE'


@pytest.mark.parametrize('field',['commit','created_at','producer','environment','claims','tests'])
def test_metadata_mutation_with_recomputed_digests_still_breaks_signature(fixture, field):
    _,bundle=fixture.generate(2)
    anchor,_=sign_fixture(bundle,fixture.root)
    if field=='environment':
        value=json.loads((bundle/'environment.json').read_text())
        value['arch']='changed fixture arch'
        replace_component(bundle,'environment.json',value)
    elif field in ('claims','tests'):
        name='claims.snapshot' if field=='claims' else 'test-results.json'
        if field=='tests':
            replace_component(bundle,name,dict(status='PASS',executed_at=1))
        else:
            (bundle/name).write_text('changed claims')
            rehash(bundle,lambda m:m['components'].update({name:core()['file_record'](name,(bundle/name).read_bytes())}))
    else:
        values=dict(commit='2'*40,created_at=json.loads((bundle/'manifest.json').read_text())['created_at']-1,
                    producer='v1-wrapper')
        rehash(bundle,lambda m:m.update({field:values[field]}))
    assert fixture.verify(bundle,'--trusted-public-key',str(anchor),version=2).returncode!=0


@pytest.mark.parametrize('message',[b'wrong domain',b'a'*64,bytes.fromhex('a'*64)])
def test_signature_contract_rejects_other_message_representations(fixture, message):
    _,bundle=fixture.generate(1)
    anchor,_=sign_fixture(bundle,fixture.root,message=message)
    assert fixture.verify(bundle,'--trusted-public-key',str(anchor)).returncode!=0


def test_bad_external_key_cannot_be_replaced_by_bundle_key(fixture):
    _,bundle=fixture.generate(2)
    _,key=sign_fixture(bundle,fixture.root)
    other=ec.generate_private_key(ec.SECP256R1())
    anchor=fixture.root/'wrong-anchor.pem'
    anchor.write_bytes(other.public_key().public_bytes(serialization.Encoding.PEM,
                                                     serialization.PublicFormat.SubjectPublicKeyInfo))
    assert fixture.verify(bundle,'--trusted-public-key',str(anchor),version=2).returncode!=0
    (bundle/'public_key.der').write_bytes(key.public_key().public_bytes(
        serialization.Encoding.X962,serialization.PublicFormat.UncompressedPoint))
    assert fixture.verify(bundle,'--trusted-public-key',str(anchor),version=2).returncode!=0


@pytest.mark.parametrize('field,value',[('schema','unknown'),('digest_algorithm','SHA3'),
    ('certification','CERTIFIED'),('hw_provenance','INVENTED_HARDWARE_CERTIFICATION'),
    ('artifact_scope','ENTIRE_REPOSITORY'),('signature_contract','unknown'),('producer','unknown'),
    ('test_execution','PASS'),('commit',True),('created_at',True)])
def test_unknown_or_overclaimed_contracts_are_rejected(fixture, field, value):
    _,bundle=fixture.generate(2)
    rehash(bundle,lambda m:m.update({field:value}))
    assert fixture.verify(bundle,'--integrity-only',version=2).returncode!=0


@pytest.mark.parametrize('seconds',[-86401,60])
def test_expired_or_future_snapshot_rejected_even_with_software_signature(fixture, seconds):
    import time
    _,bundle=fixture.generate(2)
    rehash(bundle,lambda m:m.update(created_at=int(time.time())+seconds))
    anchor,_=sign_fixture(bundle,fixture.root)
    assert fixture.verify(bundle,'--trusted-public-key',str(anchor),version=2).returncode!=0


@pytest.mark.parametrize('payload',[b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}',b'{"x":1e999}',b'[]',b'null'])
def test_invalid_json_metadata_rejected(fixture, payload):
    _,bundle=fixture.generate(2)
    (bundle/'manifest.json').write_bytes(payload)
    (bundle/'manifest.blake3').write_text(core()['digest'](payload)+'\n')
    assert fixture.verify(bundle,'--integrity-only',version=2).returncode!=0


@pytest.mark.parametrize('name',['../escape','/absolute','src/../escape','src\\escape','.git/config','src//lib.rs'])
def test_unsafe_artifact_paths_are_rejected(fixture, name):
    _,bundle=fixture.generate(2)
    def mutate(manifest):
        manifest['artifacts'][-1]['path']=name
        manifest['artifacts'].sort(key=lambda r:r['path'])
    rehash(bundle,mutate)
    assert fixture.verify(bundle,'--integrity-only',version=2).returncode!=0


def test_duplicate_artifact_paths_are_rejected(fixture):
    _,bundle=fixture.generate(2)
    rehash(bundle,lambda m:m['artifacts'].append(m['artifacts'][0]))
    assert fixture.verify(bundle,'--integrity-only',version=2).returncode!=0


@pytest.mark.parametrize('kind',['file','parent','fifo','missing'])
def test_uninspectable_external_artifact_is_rejected(fixture, kind):
    import os
    _,bundle=fixture.generate(2)
    p=fixture.root/'src/lib.rs'
    if kind=='parent':
        (fixture.root/'src').rename(fixture.root/'real-src')
        (fixture.root/'src').symlink_to(fixture.root/'real-src',target_is_directory=True)
    else:
        data=p.read_bytes()
        p.unlink()
        if kind=='file':
            target=fixture.root/'canary'
            target.write_bytes(data)
            p.symlink_to(target)
        elif kind=='fifo':
            os.mkfifo(p)
    assert fixture.verify(bundle,'--integrity-only',version=2).returncode!=0


@pytest.mark.parametrize('component',['claims.snapshot','test-results.json','environment.json','verify'])
def test_missing_or_tampered_component_never_succeeds(fixture, component):
    _,bundle=fixture.generate(2)
    (bundle/component).unlink()
    assert fixture.verify(bundle,'--integrity-only',version=1).returncode!=0


@pytest.mark.parametrize('version',[1,2])
def test_output_existing_bundle_is_never_overwritten(fixture, version):
    result,bundle=fixture.generate(version)
    assert result.returncode==0,result.stderr
    before={p.name:p.read_bytes() for p in bundle.iterdir()}
    second,_=fixture.generate(version)
    assert second.returncode!=0
    assert {p.name:p.read_bytes() for p in bundle.iterdir()}==before


@pytest.mark.parametrize('version',[1,2])
def test_missing_selected_artifact_rejects_before_output(fixture, version):
    (fixture.root/'src/lib.rs').unlink()
    result,bundle=fixture.generate(version)
    assert result.returncode!=0
    assert not bundle.exists()


def test_integrity_result_is_limited_to_selected_files(fixture):
    _,bundle=fixture.generate(2)
    (fixture.root/'unselected.txt').write_text('not part of this declared selection')
    result=fixture.verify(bundle,'--integrity-only',version=2)
    assert result.returncode==0,result.stderr
    manifest=json.loads((bundle/'manifest.json').read_text())
    assert manifest['artifact_scope']=='SELECTED_FILES'
    assert 'unselected.txt' not in [r['path'] for r in manifest['artifacts']]


def test_portable_verifier_does_not_need_repository_code_at_runtime(fixture):
    _,bundle=fixture.generate(2)
    (fixture.root/PATHS[0]).unlink()
    (fixture.root/PATHS[1]).unlink()
    (fixture.root/PATHS[2]).unlink()
    assert fixture.verify(bundle,'--integrity-only',version=2).returncode==0


@pytest.mark.parametrize('version',[1,2])
def test_claims_budget_matches_verifier_before_output_creation(fixture, version):
    (fixture.root/'CLAIMS.toml').write_bytes(b'x'*(4*1024*1024+1))
    result,bundle=fixture.generate(version)
    assert result.returncode!=0
    assert not bundle.exists()


@pytest.mark.parametrize('version',[1,2])
def test_output_symlink_is_never_followed(fixture, version):
    target=fixture.root/'preserved-output'
    target.mkdir()
    (target/'canary').write_text('preserve fixture')
    fixture.output(version).symlink_to(target,target_is_directory=True)
    result,_=fixture.generate(version)
    assert result.returncode!=0
    assert (target/'canary').read_text()=='preserve fixture'
    assert list(p.name for p in target.iterdir())==['canary']


@pytest.mark.parametrize('name',['claims.snapshot','environment.json','test-results.json'])
def test_component_symlink_is_rejected(fixture, name):
    _,bundle=fixture.generate(2)
    content=(bundle/name).read_bytes()
    (bundle/name).unlink()
    target=fixture.root/'outside-component'
    target.write_bytes(content)
    (bundle/name).symlink_to(target)
    assert fixture.verify(bundle,'--integrity-only',version=2).returncode!=0
    assert target.read_bytes()==content


@pytest.mark.parametrize('value',[dict(status='PASS',executed_at=1),dict(status='NOT_EXECUTED',suites=['passed']),
                                 dict(status='SUPPORTED_WITHIN_DOMAIN',timestamp=0)])
def test_even_signed_test_claims_need_a_supported_execution_contract(fixture, value):
    _,bundle=fixture.generate(2)
    replace_component(bundle,'test-results.json',value)
    anchor,_=sign_fixture(bundle,fixture.root)
    assert fixture.verify(bundle,'--trusted-public-key',str(anchor),version=2).returncode!=0


@pytest.mark.parametrize('kind',['extra-file','subdirectory','missing-signature','invalid-signature','wrong-curve'])
def test_unexpected_or_invalid_signature_inputs_never_succeed(fixture, kind):
    _,bundle=fixture.generate(2)
    anchor,_=sign_fixture(bundle,fixture.root)
    if kind=='extra-file':
        (bundle/'unexpected').write_text('fixture')
    elif kind=='subdirectory':
        (bundle/'unexpected-directory').mkdir()
    elif kind=='missing-signature':
        (bundle/'signature.der').unlink()
    elif kind=='invalid-signature':
        (bundle/'signature.der').write_bytes(b'invalid fixture DER')
    elif kind=='wrong-curve':
        key=ec.generate_private_key(ec.SECP384R1())
        anchor.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,
                                                       serialization.PublicFormat.SubjectPublicKeyInfo))
    assert fixture.verify(bundle,'--trusted-public-key',str(anchor),version=2).returncode!=0


@pytest.mark.parametrize('payload',[b'{"hw_provenance":"UNVERIFIED","provenance":"OBSERVED_PLATFORM_ONLY","x":1e999}',
    b'{"hw_provenance":"UNVERIFIED","hw_provenance":"UNVERIFIED"}'])
def test_environment_nonfinite_and_duplicate_values_rejected_after_rehash(fixture, payload):
    _,bundle=fixture.generate(2)
    (bundle/'environment.json').write_bytes(payload)
    rehash(bundle,lambda m:m['components'].update({'environment.json':core()['file_record']('environment.json',payload)}))
    assert fixture.verify(bundle,'--integrity-only',version=2).returncode!=0


@pytest.mark.parametrize('version',[1,2])
def test_cli_requires_explicit_new_output_and_help_has_no_effects(fixture, version):
    script=fixture.root/('scripts/generate_attestation_bundle'+('_v2' if version==2 else '')+'.py')
    missing=subprocess.run([sys.executable,str(script)],env=fixture.env,cwd=fixture.root,
                           capture_output=True,timeout=10)
    help_result=subprocess.run([sys.executable,str(script),'--help'],env=fixture.env,cwd=fixture.root,
                               capture_output=True,timeout=10)
    assert missing.returncode!=0
    assert help_result.returncode==0
    assert not fixture.output(version).exists()
    assert not (fixture.root/'keys').exists()


def test_repeated_parallel_integrity_checks_and_rejections_are_stable(fixture):
    from concurrent.futures import ThreadPoolExecutor
    _,bundle=fixture.generate(2)
    api=core()
    assert api['verify_bundle'](bundle,fixture.root,integrity_only=True)[1]==0  # Warmup.
    with ThreadPoolExecutor(max_workers=4) as pool:
        statuses=list(pool.map(lambda _:api['verify_bundle'](bundle,fixture.root,integrity_only=True)[1],range(32)))
    assert statuses==[0]*32
    (fixture.root/'src/lib.rs').write_text('tampered after warmup')
    def rejected(_):
        try:
            api['verify_bundle'](bundle,fixture.root,integrity_only=True)
        except ValueError:
            return True
        return False
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert all(pool.map(rejected,range(32)))



def test_missing_platform_observations_are_explicit_unknown_and_verifiable(fixture):
    from types import SimpleNamespace
    api=core()
    namespace=api['build_snapshot'].__globals__
    namespace['platform']=SimpleNamespace(system=lambda:'',machine=lambda:'',release=lambda:'',python_version=lambda:'')
    namespace['subprocess']=SimpleNamespace(check_output=lambda *a,**k:b'1'*40, DEVNULL=-3, SubprocessError=RuntimeError)
    output=fixture.root/'unknown-platform-snapshot'
    api['build_snapshot'](fixture.root,output,ARTIFACTS,'v2-wrapper')
    environment=json.loads((output/'environment.json').read_text())
    assert all(environment[k]=='UNKNOWN' for k in ('os','arch','release','python'))
    assert environment['hw_provenance']=='UNVERIFIED'
    assert api['verify_bundle'](output,fixture.root,integrity_only=True)[1]==0



def test_manifest_budget_is_checked_before_creating_output(fixture):
    from types import SimpleNamespace
    api=core()
    namespace=api['build_snapshot'].__globals__
    namespace['platform']=SimpleNamespace(system=lambda:'fixture',machine=lambda:'fixture',
                                          release=lambda:'fixture',python_version=lambda:'fixture')
    namespace['subprocess']=SimpleNamespace(check_output=lambda *a,**k:b'1'*40,
                                            DEVNULL=-3,SubprocessError=RuntimeError)
    tiny_verifier=fixture.root/'small-template'
    tiny_verifier.write_text('fixture template used only for budget rejection')
    namespace['__file__']=str(tiny_verifier)
    namespace['MAX_METADATA']=1024
    output=fixture.root/'oversized-manifest-output'
    with pytest.raises(ValueError,match='manifest budget'):
        api['build_snapshot'](fixture.root,output,ARTIFACTS,'v2-wrapper')
    assert not output.exists()
