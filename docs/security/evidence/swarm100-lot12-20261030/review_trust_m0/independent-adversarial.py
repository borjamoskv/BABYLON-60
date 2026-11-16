"""Independent software-only trust and M0 coverage checks in a disposable HOME."""
import base64
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from blake3 import blake3
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).absolute().parents[5]
SOURCES = [
    '01_KISH_ENGINE/babylon60/attestation/conformal_tree.py',
    '01_KISH_ENGINE/babylon60/attestation/merkle_anchor.py',
    'tools/tamkarum_license_provisioner.py',
    '01_KISH_ENGINE/babylon60/verifier/standalone_verify.py',
]
TESTS = ['tests/test_swarm100_lot12_s2_trust_regressions.py', 'tests/test_swarm100_lot12_m0_regressions.py']
COMPILER = '01_KISH_ENGINE/babylon60/compliance_exporter/m0_evidence_pack.py'
CONTENT = ('manifest.json', 'claims.json', 'scope.json', 'environment.json', 'evidence/ledger_l0.sqlite', 'evidence/execution-trace.jsonl', 'evidence/nemesis-results.json', 'evidence/formal-proofs.json', 'compliance/regulatory-matrix.json', 'compliance/auditor-report.pdf', 'README.md')
sys.dont_write_bytecode = True


def hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCES + TESTS + [COMPILER]}


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def public(key):
    return key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def sign_manifest(key, value):
    value = copy.deepcopy(value)
    value['sovereign_identity'].pop('ed25519_signature_b64', None)
    value['sovereign_identity']['ed25519_signature_b64'] = base64.b64encode(key.sign(canonical(value))).decode()
    return value


def main():
    before = hashes()
    checks = []
    forbidden_calls = []
    original_cwd = Path.cwd()

    def forbidden(*args, **kwargs):
        forbidden_calls.append('kill/network/subprocess')
        raise AssertionError('Protected operation forbidden in fixture')

    with tempfile.TemporaryDirectory(prefix='lot12-independent-trust-') as temporary, \
            patch.dict(os.environ, {'HOME': temporary, 'BABYLON_HOME': temporary, 'PATH': '/usr/bin:/bin'}, clear=True), \
            patch.object(os, 'kill', forbidden), patch.object(subprocess, 'Popen', forbidden), \
            patch.object(socket.socket, 'connect', forbidden), patch.object(socket.socket, 'connect_ex', forbidden), \
            patch.object(socket, 'getaddrinfo', forbidden):
        boundary = Path(temporary).resolve()
        os.chdir(boundary)
        try:
            for name in ('babylon60', 'babylon60.attestation', 'babylon60.verifier', 'babylon60.compliance_exporter'):
                package = ModuleType(name)
                package.__path__ = []
                sys.modules[name] = package
            anchor = load('babylon60.attestation.merkle_anchor', SOURCES[1])
            hardware_calls = []

            def synthetic_identity(self):
                hardware_calls.append('synthetic_identifier')
                return {'uuid': 'SYNTHETIC-UUID', 'machine': 'SyntheticCPU', 'os': 'Fixture', 'enclave_type': 'UNVERIFIED_SOFTWARE'}

            anchor.MerkleCausalAnchor.get_hardware_identity = synthetic_identity
            conformal = load('babylon60.attestation.conformal_tree', SOURCES[0])
            license_module = load('fixture_license_provisioner', SOURCES[2])
            verifier = load('babylon60.verifier.standalone_verify', SOURCES[3])
            compiler = load('babylon60.compliance_exporter.m0_evidence_pack', COMPILER)
            compiler.platform = SimpleNamespace(system=lambda: 'FixtureOS', release=lambda: 'fixture', machine=lambda: 'FixtureCPU', python_version=lambda: 'fixture', platform=lambda: 'FixturePlatform')
            key = Ed25519PrivateKey.generate()
            foreign = Ed25519PrivateKey.generate()
            pin = base64.b64encode(public(key)).decode()
            body = {'schema': 'babylon60.aeon-manifest.v2', 'aeon_id': 'INDEPENDENT-FIXTURE', 'status': 'FROZEN_C5_REAL', 'merkle_root': 'ab' * 32, 'total_claims_sealed': 1, 'sovereign_identity': {'l0_public_key_b64': pin, 'signed_payload': 'manifest-canonical-json-v2', 'fixture_metadata': {'label': 'software'}}, 'hardware_attestation': {'hardware_uuid': 'SYNTHETIC-UUID', 'attestation_status': 'SOFTWARE_ONLY_UNATTESTED'}, 'extensions': {'nested': [1, 'Ω', None]}}
            valid = sign_manifest(key, body)
            manifest_path = boundary / 'manifest.json'

            def verify_manifest(value, **kwargs):
                manifest_path.write_text(json.dumps(value))
                return conformal.AeonVerifier.verify_manifest(manifest_path, **kwargs)

            assert verify_manifest(valid)['overall_valid'] is False
            assert verify_manifest(valid, expected_public_key_b64=base64.b64encode(public(foreign)).decode())['overall_valid'] is False
            result = verify_manifest(valid, expected_public_key_b64=pin)
            assert result['overall_valid'] and result['identity_trusted'] and result['verification_scope'] == 'AUTHENTICATED_MANIFEST_ONLY'
            os.environ['BABYLON_AEON_TRUSTED_PUBLIC_KEY_B64'] = pin
            assert verify_manifest(valid)['overall_valid']
            assert verify_manifest(valid, expected_public_key_b64='')['overall_valid'] is False
            os.environ.pop('BABYLON_AEON_TRUSTED_PUBLIC_KEY_B64')
            checks.append({'name': 'external_pin_required_and_explicit_empty_does_not_fall_back', 'cases': 5, 'passed': True})

            mutations = []
            for field, value in [('aeon_id', 'ALTERED'), ('status', 'ALTERED'), ('merkle_root', 'cd' * 32), ('total_claims_sealed', 2), ('schema', 'legacy'), ('extensions', {'nested': [2, 'Ω', None]}), ('hardware_attestation', {'hardware_uuid': 'ALTERED'}), ('new_unsigned_field', {'value': True})]:
                changed = copy.deepcopy(valid)
                changed[field] = value
                mutations.append(changed)
            for field, value in [('fixture_metadata', {'label': 'ALTERED'}), ('signed_payload', 'root-only'), ('l0_public_key_b64', base64.b64encode(public(foreign)).decode())]:
                changed = copy.deepcopy(valid)
                changed['sovereign_identity'][field] = value
                mutations.append(changed)
            for changed in mutations:
                result = verify_manifest(changed, expected_public_key_b64=pin)
                assert result['overall_valid'] is False and result['ed25519_signature_valid'] is False
            checks.append({'name': 'all_signed_manifest_fields_including_unknown_nested_identity_fields', 'cases': len(mutations), 'passed': True})

            legacy = copy.deepcopy(body)
            legacy.pop('schema')
            legacy['sovereign_identity'].pop('signed_payload')
            legacy['sovereign_identity']['ed25519_signature_b64'] = base64.b64encode(key.sign(bytes.fromhex(body['merkle_root']))).decode()
            assert verify_manifest(legacy, expected_public_key_b64=pin)['overall_valid'] is False
            malformed = []
            for field, value in [('merkle_root', 'gg' * 32), ('total_claims_sealed', True), ('total_claims_sealed', 0)]:
                changed = copy.deepcopy(body)
                changed[field] = value
                malformed.append(sign_manifest(key, changed))
            for changed in malformed:
                assert verify_manifest(changed, expected_public_key_b64=pin)['overall_valid'] is False
            manifest_path.write_text('{"aeon_id":"one","aeon_id":"two"}')
            try:
                conformal.AeonVerifier.verify_manifest(manifest_path, expected_public_key_b64=pin)
            except ValueError:
                pass
            else:
                raise AssertionError('Duplicate keys accepted')
            checks.append({'name': 'legacy_root_signature_schema_and_duplicate_fields_rejected', 'cases': 5, 'passed': True})

            db = boundary / 'claims.sqlite'
            claims = [(f'claim-{i}', f'advisory-{i}', 'fixture.test', i, f'payload-{i}', str(i), 'software', f'anchor-{i}') for i in range(3)]
            with sqlite3.connect(db) as conn:
                conn.execute('CREATE TABLE bounty_claims (claim_id, advisory_id, domain, risk_score, payload_hash, timestamp_utc, hardware_anchor, attestation_merkle_root)')
                conn.executemany('INSERT INTO bounty_claims VALUES (?,?,?,?,?,?,?,?)', claims)
            leaves = [blake3(':'.join(str(row[i]) for i in (0, 1, 2, 4, 7)).encode()).hexdigest() for row in claims]
            layer = list(leaves)
            while len(layer) > 1:
                layer = [blake3((layer[i] + ':' + layer[min(i + 1, len(layer) - 1)]).encode()).hexdigest() for i in range(0, len(layer), 2)]
            db_body = copy.deepcopy(body)
            db_body.update(merkle_root=layer[0], total_claims_sealed=3)
            signed_db = sign_manifest(key, db_body)
            assert verify_manifest(signed_db, expected_public_key_b64=pin, db_path=db)['verification_scope'] == 'AUTHENTICATED_MANIFEST_AND_LEDGER'
            with sqlite3.connect(db) as conn:
                conn.execute("UPDATE bounty_claims SET payload_hash='altered' WHERE claim_id='claim-1'")
            assert verify_manifest(signed_db, expected_public_key_b64=pin, db_path=db)['overall_valid'] is False
            checks.append({'name': 'owned_sqlite_root_and_cardinality_match_then_mutation_rejected', 'cases': 2, 'passed': True})

            quote = anchor.MerkleCausalAnchor().generate_hardware_pcr_quote('ab' * 32)
            assert quote['hardware_attestation_verified'] is False and quote['tpm_quote_signature'] == ''
            assert quote['attestation_status'] == 'SOFTWARE_ONLY_UNATTESTED'
            previous_calls = len(hardware_calls)
            try:
                anchor.MerkleCausalAnchor().generate_hardware_pcr_quote('ab' * 32, require_hardware=True)
            except RuntimeError:
                pass
            else:
                raise AssertionError('Hardware requirement passed')
            assert len(hardware_calls) == previous_calls
            forged_hw = copy.deepcopy(body)
            forged_hw['hardware_attestation']['attestation_status'] = 'TEST_FORGED_HARDWARE_CLAIM'
            forged_hw['hardware_attestation']['tpm_quote_signature'] = '00' * 64
            report = verify_manifest(sign_manifest(key, forged_hw), expected_public_key_b64=pin, require_hardware=True)
            assert report['ed25519_signature_valid'] and report['hardware_attestation_verified'] is False and report['overall_valid'] is False
            checks.append({'name': 'software_quote_negative_boolean_and_hardware_requirement_never_approved', 'cases': 3, 'passed': True})

            for seed in (None, '', 'ab', 'gg' * 32, '00' * 32, ' ' + 'ab' * 32, 'ab' * 33):
                if seed is None:
                    os.environ.pop('BABYLON_LICENSE_ED25519_SEED', None)
                else:
                    os.environ['BABYLON_LICENSE_ED25519_SEED'] = seed
                try:
                    license_module.generate_license_certificate('Synthetic Client', 'SYNTHETIC', 'pilot')
                except ValueError:
                    pass
                else:
                    raise AssertionError('Missing/malformed authority accepted')
            raw_seed = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
            os.environ['BABYLON_LICENSE_ED25519_SEED'] = raw_seed.hex()
            certificate, digest = license_module.generate_license_certificate('Synthetic Client', 'SYNTHETIC', 'pilot')
            seal = certificate.pop('cryptographic_seal')
            encoded = json.dumps(certificate, sort_keys=True, ensure_ascii=False).encode()
            key.public_key().verify(bytes.fromhex(seal['signature_hex']), encoded)
            assert seal['digest'] == digest == hashlib.sha256(encoded).hexdigest()
            assert seal['status'] == 'SIGNED_WITH_CONFIGURED_AUTHORITY'
            certificate['entitlements']['max_cluster_nodes'] = 999
            try:
                key.public_key().verify(bytes.fromhex(seal['signature_hex']), json.dumps(certificate, sort_keys=True, ensure_ascii=False).encode())
            except InvalidSignature:
                pass
            else:
                raise AssertionError('License entitlement tamper verified')
            os.environ.pop('BABYLON_LICENSE_ED25519_SEED')
            checks.append({'name': 'license_requires_explicit_software_authority_and_signs_entitlements', 'cases': 9, 'passed': True})

            fixture_repo = boundary / 'm0-input'
            fixture_repo.mkdir()
            claims_file = fixture_repo / 'CLAIMS.toml'
            claims_file.write_text('[claim.synthetic]\nstatus="untested"\n')
            base_pack = boundary / 'base-pack'
            compiler.M0EvidencePackCompiler(repo_root=fixture_repo, claims_toml_path=claims_file, signing_seed_hex=raw_seed.hex()).compile_pack(base_pack)
            assert verifier.verify_m0_evidence_pack(base_pack)['valid'] is True
            checks.append({'name': 'real_m0_producer_complete_pack_accepted_with_fixture_key_and_repo', 'cases': 1, 'passed': True})
            counter = 0

            def pack_copy():
                nonlocal counter
                counter += 1
                target = boundary / f'pack-{counter}'
                shutil.copytree(base_pack, target)
                return target

            def sign_pack(target, digests, checksum_bytes=None, signing_key=key):
                metadata_path = target / 'verification/verifier-metadata.json'
                metadata = json.loads(metadata_path.read_text())
                envelope = metadata['signing_envelope']
                envelope['file_digests'] = digests
                if checksum_bytes is None:
                    checksum_bytes = ''.join(f'{value}  {name}\n' for name, value in sorted(digests.items())).encode() if isinstance(digests, dict) else b''
                (target / 'verification/checksums.sha256').write_bytes(checksum_bytes)
                envelope['checksums_sha256_digest'] = hashlib.sha256(checksum_bytes).hexdigest()
                data = canonical(envelope)
                metadata['signed_envelope_sha256'] = hashlib.sha256(data).hexdigest()
                metadata['public_key'] = public(signing_key).hex()
                metadata_path.write_text(json.dumps(metadata))
                (target / 'verification/signature.sig').write_text(signing_key.sign(data).hex())

            original_digests = json.loads((base_pack / 'verification/verifier-metadata.json').read_text())['signing_envelope']['file_digests']
            assert set(original_digests) == set(CONTENT)
            for omitted in CONTENT:
                target = pack_copy()
                digests = dict(original_digests)
                del digests[omitted]
                sign_pack(target, digests)
                result = verifier.verify_m0_evidence_pack(target)
                assert result['valid'] is False and result['checksums_valid'] is False and result['epistemic_status'] == 'INCOMPLETE_DIGEST_COVERAGE'
            checks.append({'name': 'each_of_eleven_required_m0_content_digests_cannot_be_omitted_even_when_resigned', 'cases': 11, 'passed': True})

            for content in CONTENT:
                target = pack_copy()
                with (target / content).open('ab') as stream:
                    stream.write(b' ')
                result = verifier.verify_m0_evidence_pack(target)
                assert result['valid'] is False and result['checksums_valid'] is False
            checks.append({'name': 'every_required_content_byte_stream_is_checked', 'cases': 11, 'passed': True})

            layouts = [None, [], False, {}, {**original_digests, '../outside': '0' * 64}, {**original_digests, '/outside': '0' * 64}, {**original_digests, 'evidence/../claims.json': '0' * 64}]
            for layout in layouts:
                target = pack_copy()
                sign_pack(target, layout)
                with patch.object(verifier, '_sha256_file_standalone', forbidden):
                    result = verifier.verify_m0_evidence_pack(target)
                assert result['valid'] is False
            checks.append({'name': 'invalid_digest_maps_and_noncanonical_paths_rejected_before_content_hash_reads', 'cases': len(layouts), 'passed': True})

            checksum_original = (base_pack / 'verification/checksums.sha256').read_bytes()
            for raw in (b'\xff\xfe', checksum_original + checksum_original.splitlines(keepends=True)[0], b'', checksum_original.replace(b'claims.json', b'./claims.json')):
                target = pack_copy()
                sign_pack(target, dict(original_digests), checksum_bytes=raw)
                assert verifier.verify_m0_evidence_pack(target)['valid'] is False
            for invalid_digest in (True, None, 'g' * 64, '0' * 63):
                target = pack_copy()
                values = dict(original_digests)
                values['environment.json'] = invalid_digest
                sign_pack(target, values)
                assert verifier.verify_m0_evidence_pack(target)['valid'] is False
            checks.append({'name': 'signed_checksum_format_duplicates_coverage_and_digest_values_rejected', 'cases': 8, 'passed': True})

            rekeyed = pack_copy()
            sign_pack(rekeyed, dict(original_digests), signing_key=foreign)
            assert verifier.verify_m0_evidence_pack(rekeyed)['valid'] is True
            checks.append({'name': 'm0_external_identity_anchor_not_inferred_from_content_integrity', 'cases': 1, 'passed': True, 'observation': 'Re-signing an otherwise complete fixture pack with another software key remains accepted: this API does not authenticate an externally pinned identity, outside C0175.'})

            parallel_good = boundary / 'parallel-good.json'
            parallel_bad = boundary / 'parallel-bad.json'
            parallel_good.write_text(json.dumps(valid))
            bad = copy.deepcopy(valid)
            bad['extensions']['nested'][0] = 99
            parallel_bad.write_text(json.dumps(bad))

            def pair(_):
                good_result = conformal.AeonVerifier.verify_manifest(parallel_good, expected_public_key_b64=pin)
                bad_result = conformal.AeonVerifier.verify_manifest(parallel_bad, expected_public_key_b64=pin)
                assert good_result['overall_valid'] is True and bad_result['overall_valid'] is False

            for i in range(3):
                pair(i)
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(pair, range(16)))
            checks.append({'name': 'bounded_software_warmup_and_concurrent_valid_tampered_pairs', 'warmup_pairs': 3, 'parallel_pairs': 16, 'threads': 4, 'passed': True})
            assert forbidden_calls == []
        finally:
            os.chdir(original_cwd)
    after = hashes()
    assert after == before, 'Reviewed sources/tests changed during execution'
    print(json.dumps({'status': 'PASS', 'control_count': len(checks), 'checks': checks, 'source_sha256_before': before, 'source_sha256_after': after, 'forbidden_calls': forbidden_calls, 'scope': 'Owned temporary HOME/repo/SQLite and ephemeral software keys only; package side effects bypassed with inert package containers; actual target modules and compiler loaded. Network, kill, subprocess blocked before imports; hardware identifiers replaced by synthetic provider. No hardware/physical-stress/power-cut/real-license/authority deployment claim.'}, indent=2))


if __name__ == '__main__':
    main()
