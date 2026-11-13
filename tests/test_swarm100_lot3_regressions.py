"""Publication regressions; every Git/scanner/gate executable is fixture owned.

No ATTESTED fixture is generated and no hardware or remote effect is exercised.
"""

import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).absolute().parents[1]
SCRIPTS = ("c5_distill_public_mirror.sh", "c5_ship.sh")
COMMIT = "1" * 40
OTHER = "2" * 40
TREE = "3" * 40
BLOB = "4" * 40

FAKE_GIT = r"""
import base64, json, os, pathlib, sys
root = pathlib.Path(os.environ['FIXTURE_ROOT'])
a = sys.argv[1:]
if a[:1] == ['--no-replace-objects']: a = a[1:]
with (root/'calls.jsonl').open('a') as f:
    f.write(json.dumps({'tool':'git','args':a,'cwd':os.getcwd(), 'config':{
        k:v for k,v in os.environ.items() if k.startswith('GIT_CONFIG_')},
        'no_replace':os.environ.get('GIT_NO_REPLACE_OBJECTS')})+'\n')
if a and a[0].startswith('--git-dir='): a = a[1:]
if a[:1] == ['config']:
    if '--list' in a:
        sys.stdout.buffer.write(b'url.ssh://changed/.insteadof\nssh://fixed/\0http.extraheader\nfixture-auth\0')
    sys.exit(0)
if a[:2] == ['rev-parse','--abbrev-ref']: print('main')
elif a[:1] == ['rev-parse']:
    if '--git-path' in a: print(root/'pre-push' if a[-1] == 'hooks/pre-push' else root/'objects')
    elif '--show-object-format' in a: print('sha1')
    elif any('tree' in x for x in a): print('3'*40)
    else: print('1'*40)
elif a[:1] == ['rev-list']: print(0 if 'HEAD..origin/main' in a else 1)
elif a[:1] == ['status']: pass
elif a[:2] == ['remote','get-url']:
    print(os.environ.get('FIXTURE_URL', 'ssh://fixed/repo.git'))
elif a[:1] == ['ls-tree']:
    if os.environ.get('TREE_MODE') == 'gitlink':
        sys.stdout.buffer.write(b'160000 commit '+b'4'*40+b'\tsubmodule\0'); sys.exit(0)
    if os.environ.get('TREE_MODE') == 'unsafe':
        sys.stdout.buffer.write(b'100644 blob '+b'4'*40+b'\t../escape\0'); sys.exit(0)
    if '-rz' in a:
        sys.stdout.buffer.write(b'100644 blob '+b'4'*40+b'\t.gitleaks.toml\0'+
                                b'100644 blob '+b'5'*40+b'\texport-ignored.txt\0')
    else: print('.gitleaks.toml\nexport-ignored.txt')
elif a[:1] == ['cat-file']:
    data = b'[extend]\nuseDefault = true\n' if a[-1] == '4'*40 else b'FIXTURE_TREE_ONLY_SECRET\n'
    if a[-1] != '4'*40 and os.environ.get('TREE_MODE') == 'tar-padding': data = b'x'*(20971520-1000)
    if a[-1] != '4'*40 and os.environ.get('TREE_MODE') == 'lfs': data = b'version https://git-lfs.github.com/spec/v1\noid sha256:fixture\nsize 123\n'
    if a[-1] == '4'*40 and os.environ.get('TREE_MODE') == 'external-policy': data = b'[extend]\npath = \"/outside/policy\"\n'
    if os.environ.get('TREE_MODE') == 'big' and '-s' in a: print(20971520); sys.exit(0)
    if os.environ.get('TREE_MODE') == 'blob-error' and 'blob' in a: sys.exit(2)
    if '-s' in a: print(len(data))
    else: sys.stdout.buffer.write(data)
elif a[:1] == ['write-tree']: print(os.environ.get('FIXTURE_TREE_ID','3'*40))
elif a[:1] == ['commit-tree']: print(os.environ.get('FIXTURE_COMMIT','1'*40))
elif a[:1] == ['archive']: sys.stdout.buffer.write(b'tiny-fixture-tar')
elif a[:1] == ['branch']:
    if '-f' in a: (root/'branch').write_text(a[-1])
elif a[:1] == ['push']:
    ref = next((v for v in a if ':' in v and not v.startswith('ssh')), a[-1])
    selected = ref.split(':')[0]
    if selected in ('main', 'release/v5.0-clean'):
        selected = (root/'branch').read_text() if (root/'branch').exists() else '1'*40
    (root/'pushed').write_text(selected)
elif a[:1] == ['ls-remote']:
    print(('2'*40 if os.environ.get('REMOTE_MISMATCH') else (root/'pushed').read_text())+'\trefs/heads/main')
elif a[:1] == ['init']:
    dest = pathlib.Path(a[-1]); (dest/'objects/info').mkdir(parents=True)
elif a[:1] in (['diff-index'], ['read-tree'], ['rm'], ['fetch'], ['diff']): pass
else: sys.exit('UNSUPPORTED FIXTURE GIT '+repr(a))
"""
FAKE_SCAN = r"""
import json, os, pathlib, sys
root=pathlib.Path(os.environ['FIXTURE_ROOT'])
source = pathlib.Path(sys.argv[-1]) if sys.argv[1] == 'dir' else root
with (root/'calls.jsonl').open('a') as f:
    f.write(json.dumps({'tool':'gitleaks','args':sys.argv[1:], 'cwd':os.getcwd(),
      'files':{str(p.relative_to(source)):p.read_text() for p in source.rglob('*')
               if p.is_file() and p.suffix in ('.txt','.toml')}})+'\n')
sys.exit(int(os.environ.get('SCAN_EXIT','0')))
"""
FAKE_GATE = r"""
import hashlib, json, os, pathlib, subprocess, sys, time
root=pathlib.Path(os.environ['FIXTURE_ROOT'])
with (root/'calls.jsonl').open('a') as f:
    effects = []
    # Sibling runs delete their work directories concurrently, and Python 3.11's
    # rglob raises on a vanished directory: walk and skip what disappears.
    for dirpath, _dirs, names in os.walk(root/'tmp', onerror=lambda error: None):
        if 'effect.json' not in names: continue
        path=pathlib.Path(dirpath)/'effect.json'
        try:
            value=json.loads(path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            continue
        raw=json.dumps(value,sort_keys=True,separators=(',', ':'),ensure_ascii=False).encode()
        if hashlib.sha256(b'BABYLON60:GIT:PUBLISH:v1\0'+raw).hexdigest() == sys.argv[sys.argv.index('--causal-hash')+1]:
            effects.append(value)
    f.write(json.dumps({'tool':'gate','args':sys.argv[1:],
      'effects':effects})+'\n')
(root/'branch').write_text('2'*40)
mode=os.environ.get('GATE_MODE','empty')
if mode == 'race':
    child_env=dict(os.environ, FIXTURE_COMMIT='2'*40, FIXTURE_TREE_ID='6'*40)
    result=subprocess.run(['/bin/bash',str(root/'scripts/c5_git_utils/c5_distill_public_mirror.sh'),
                           '--dry-run'],env=child_env,capture_output=True)
    with (root/'calls.jsonl').open('a') as f:
        f.write(json.dumps({'tool':'concurrent-preview','code':result.returncode})+'\n')
if mode == 'timeout': time.sleep(4)
if mode == 'malformed': print('{broken')
if mode == 'oversized': print('x'*70000)
if mode == 'status': print(json.dumps({'status':'TEST_CONTROL_FLOW_ONLY'}))
sys.exit(1 if mode == 'failure' else 0)
"""


class Fixture:
    def __init__(self, path):
        self.root = path
        self.bin = path / "bin"
        self.bin.mkdir()
        (path / "tmp").mkdir()
        (path / "objects").mkdir()
        self.env = {
            "PATH": str(self.bin),
            "HOME": str(path),
            "TMPDIR": str(path / "tmp"),
            "FIXTURE_ROOT": str(path),
            "LC_ALL": "C",
            "B60_GIT_GATE_TIMEOUT": "1",
        }
        for utility in ("dirname", "wc", "tr", "awk", "grep", "rm", "mktemp", "tee", "head", "sed", "paste", "mkdir"):
            target = shutil.which(utility)
            assert target
            (self.bin / utility).symlink_to(target)
        self.install("git", FAKE_GIT)
        self.install("gitleaks", FAKE_SCAN)
        self.install("c5_biometric_gate", FAKE_GATE)
        self.install(
            "uv",
            "import os, sys\na=sys.argv[1:]; i=a.index('python'); os.execv(sys.executable, [sys.executable]+a[i+1:])\n",
        )
        dest = path / "scripts/c5_git_utils"
        dest.mkdir(parents=True)
        for name in SCRIPTS:
            shutil.copyfile(ROOT / "scripts/c5_git_utils" / name, dest / name)
        (path / ".gitleaks.toml").write_text("[extend]\nuseDefault = true\n")

    def install(self, name, code):
        path = self.bin / name
        path.write_text("#!" + sys.executable + "\n" + code)
        path.chmod(0o700)

    def run(self, name, *args):
        return subprocess.run(
            ["/bin/bash", str(self.root / "scripts/c5_git_utils" / name), *args],
            cwd=self.root,
            env=self.env,
            capture_output=True,
            timeout=12,
        )

    def calls(self, tool):
        log = self.root / "calls.jsonl"
        return [c for c in map(json.loads, log.read_text().splitlines()) if c["tool"] == tool] if log.exists() else []

    def helper(self, *args):
        source = (self.root / "scripts/c5_git_utils" / SCRIPTS[0]).read_text()
        assert "# PUBLICATION_TOOL_BEGIN" in source
        helper = source.split("# PUBLICATION_TOOL_BEGIN", 1)[1].split("# PUBLICATION_TOOL_END", 1)[0]
        return subprocess.run(
            ["/bin/bash", "-c", helper + '\npublication_tool "$@"', "fixture", *args],
            cwd=self.root,
            env=self.env,
            capture_output=True,
            timeout=12,
        )


@pytest.fixture
def fixture(tmp_path):
    return Fixture(tmp_path)


def test_c0413_missing_scanner_never_dispatches(fixture):
    (fixture.bin / "gitleaks").unlink()
    result = fixture.run(SCRIPTS[0])
    assert result.returncode != 0, result.stdout
    assert not (fixture.root / "pushed").exists()


def test_c0418_missing_gate_never_dispatches(fixture):
    (fixture.bin / "c5_biometric_gate").unlink()
    result = fixture.run(SCRIPTS[1])
    assert result.returncode != 0, result.stdout
    assert not (fixture.root / "pushed").exists()


def test_mutable_branch_never_selects_second_commit(fixture):
    result = fixture.run(SCRIPTS[0])
    assert fixture.calls("gate"), result.stderr
    assert not (fixture.root / "pushed").exists() or (fixture.root / "pushed").read_text() == COMMIT


@pytest.mark.parametrize("name", SCRIPTS)
@pytest.mark.parametrize("mode", ["empty", "failure", "malformed", "status", "timeout", "oversized"])
def test_gate_rejection_has_no_dispatch_or_retry(fixture, name, mode):
    fixture.env["GATE_MODE"] = mode
    result = fixture.run(name)
    assert result.returncode != 0
    assert len(fixture.calls("gate")) == 1
    assert not (fixture.root / "pushed").exists()
    assert b"Recibo validado" not in result.stdout


@pytest.mark.parametrize("status", ["1", "2", "126"])
def test_scanner_error_never_calls_gate_or_push(fixture, status):
    fixture.env["SCAN_EXIT"] = status
    assert fixture.run(SCRIPTS[0]).returncode != 0
    assert not fixture.calls("gate")
    assert not (fixture.root / "pushed").exists()


def test_scanner_gets_raw_tree_not_worktree_or_export_filtered_archive(fixture):
    result = fixture.run(SCRIPTS[0], "--dry-run")
    assert result.returncode == 0, result.stderr
    (scan,) = fixture.calls("gitleaks")
    assert scan["files"]["export-ignored.txt"] == "FIXTURE_TREE_ONLY_SECRET\n"
    assert "export-ignored.txt" not in [p.name for p in fixture.root.iterdir()]
    assert scan["cwd"].endswith("/snapshot")
    args = scan["args"]
    assert args[args.index("--gitleaks-ignore-path") + 1] == scan["cwd"]
    assert args[args.index("--config") + 1] == scan["cwd"] + "/.gitleaks.toml"
    assert not fixture.calls("gate")
    assert not (fixture.root / "pushed").exists()
    assert b"NOT_CHECKED" in result.stdout


@pytest.mark.parametrize("mode", ["gitlink", "unsafe", "external-policy", "big", "blob-error"])
def test_uninspectable_snapshot_never_scanned_or_dispatched(fixture, mode):
    fixture.env["TREE_MODE"] = mode
    assert fixture.run(SCRIPTS[0], "--dry-run").returncode != 0
    assert not fixture.calls("gitleaks")
    assert not fixture.calls("gate")
    assert not (fixture.root / "escape").exists()


@pytest.mark.parametrize(
    "url",
    [
        "ssh://fixed/one\nssh://fixed/two",
        "",
        "file:///tmp/fixture",
        "ext::forbidden",
        "https://name:password@host/repo",
    ],
)
def test_ambiguous_or_unsafe_push_target_rejected_before_gate(fixture, url):
    fixture.env["FIXTURE_URL"] = url
    assert fixture.run(SCRIPTS[0]).returncode != 0
    assert not fixture.calls("gate")
    assert not (fixture.root / "pushed").exists()


def test_effect_binding_is_sha256_and_attempt_specific(fixture):
    for _ in range(2):
        assert fixture.run(SCRIPTS[0]).returncode != 0
    first, second = fixture.calls("gate")
    descriptors = []
    for call in (first, second):
        (descriptor,) = call["effects"]
        digest = call["args"][call["args"].index("--causal-hash") + 1]
        raw = json.dumps(descriptor, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        assert digest == hashlib.sha256(b"BABYLON60:GIT:PUBLISH:v1\0" + raw).hexdigest()
        assert descriptor["commit"] == COMMIT
        assert descriptor["tree"] == TREE
        assert descriptor["target_ref"] == "refs/heads/main"
        assert descriptor["force"] is True
        assert descriptor["destination_sha256"] == hashlib.sha256(b"ssh://fixed/repo.git").hexdigest()
        assert "--message" not in call["args"]
        assert "--no-sound" in call["args"]
        descriptors.append(descriptor)
    assert descriptors[0]["nonce"] != descriptors[1]["nonce"]


def prepare(fixture, *, force="true"):
    result = fixture.helper(
        "prepare", COMMIT, TREE, "public", force, "Fixture", "Fixture", str(fixture.root / "effect.json")
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.decode().strip()


@pytest.mark.parametrize("force", ["true", "false"])
def test_dispatch_uses_frozen_commit_and_isolated_config_in_noop_fixture(fixture, force):
    # Direct invocation of the actual private helper only against fake Git.
    # This proves dispatch selection, not authorization or hardware integration.
    envelope = prepare(fixture, force=force)
    fixture.env["B60_PUBLICATION_EFFECT"] = envelope
    fixture.env["FROZEN_EFFECT"] = envelope
    fixture.env["GIT_CONFIG_COUNT"] = "1"
    fixture.env["GIT_CONFIG_KEY_0"] = "url.ssh://evil/.insteadOf"
    fixture.env["GIT_CONFIG_VALUE_0"] = "ssh://fixed/"
    (fixture.root / "branch").write_text(OTHER)
    result = fixture.helper("publish", str(fixture.root / "dispatch.git"))
    assert result.returncode == 0, result.stderr
    assert (fixture.root / "pushed").read_text() == COMMIT
    (push,) = [c for c in fixture.calls("git") if "push" in c["args"]]
    assert push["args"][-2:] == ["ssh://fixed/repo.git", COMMIT + ":refs/heads/main"]
    assert ("--force" in push["args"]) == (force == "true")
    assert push["args"][0].startswith("--git-dir=" + str(fixture.root))
    config = push["config"]
    assert config["GIT_CONFIG_NOSYSTEM"] == "1"
    assert config["GIT_CONFIG_GLOBAL"] == "/dev/null"
    assert all("instead" not in value.lower() for value in config.values())
    assert "fixture-auth" in config.values()


def test_independent_remote_observation_failure_is_reported(fixture):
    fixture.env["FROZEN_EFFECT"] = prepare(fixture)
    fixture.env["REMOTE_MISMATCH"] = "1"
    result = fixture.helper("publish", str(fixture.root / "dispatch.git"))
    assert result.returncode != 0
    assert (fixture.root / "pushed").read_text() == COMMIT
    assert len([c for c in fixture.calls("git") if "push" in c["args"]]) == 1


def test_corrupt_frozen_destination_denied_before_noop_push(fixture):
    envelope = json.loads(base64.b64decode(prepare(fixture)))
    envelope["url"] = "ssh://changed/repo.git"
    fixture.env["FROZEN_EFFECT"] = base64.b64encode(json.dumps(envelope).encode()).decode()
    assert fixture.helper("publish", str(fixture.root / "dispatch.git")).returncode != 0
    assert not (fixture.root / "pushed").exists()


def test_status_remains_read_only_without_gate(fixture):
    (fixture.bin / "c5_biometric_gate").unlink()
    assert fixture.run(SCRIPTS[1], "--status").returncode == 0
    assert not any(c["args"][0] in ("config", "fetch", "push", "commit", "merge") for c in fixture.calls("git"))


def test_missing_gate_precedes_all_ship_mutations(fixture):
    (fixture.bin / "c5_biometric_gate").unlink()
    assert fixture.run(SCRIPTS[1]).returncode != 0
    assert not any(c["args"][0] in ("config", "fetch", "push", "commit", "merge", "add") for c in fixture.calls("git"))


def test_native_failure_does_not_fall_back_to_swift(fixture):
    fixture.env["GATE_MODE"] = "failure"
    fixture.install("swift", "raise SystemExit('Swift must not be invoked')\n")
    source = fixture.root / "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift"
    source.parent.mkdir(parents=True)
    source.write_text("// fixture only")
    assert fixture.run(SCRIPTS[1]).returncode != 0
    assert len(fixture.calls("gate")) == 1
    assert not (fixture.root / "pushed").exists()


def test_helper_parity_and_production_call_order():
    sources = [(ROOT / "scripts/c5_git_utils" / p).read_text() for p in SCRIPTS]
    helpers = [s.split("# PUBLICATION_TOOL_BEGIN", 1)[1].split("# PUBLICATION_TOOL_END", 1)[0] for s in sources]
    assert helpers[0] == helpers[1]
    for source in sources:
        assert source.index('publication_tool gate "$WORK/receipt.json"') < source.index(
            'publication_tool publish "$WORK/dispatch.git"'
        )


@pytest.mark.parametrize("name", SCRIPTS)
def test_active_pre_push_hook_requires_explicit_supported_contract(fixture, name):
    hook = fixture.root / "pre-push"
    hook.write_text("fixture hook must never execute")
    hook.chmod(0o700)
    result = fixture.run(name)
    assert result.returncode != 0
    assert b"pre-push hook" in result.stderr
    assert not fixture.calls("gate")
    assert not (fixture.root / "pushed").exists()


@pytest.mark.parametrize("name", SCRIPTS)
def test_lfs_pointer_never_published_as_complete_payload(fixture, name):
    fixture.env["TREE_MODE"] = "lfs"
    result = fixture.run(name)
    assert result.returncode != 0
    assert b"LFS" in result.stderr
    assert not fixture.calls("gate")
    assert not (fixture.root / "pushed").exists()


def test_object_reads_disable_replace_refs(fixture):
    assert fixture.run(SCRIPTS[0], "--dry-run").returncode == 0
    assert all(
        c["no_replace"] == "1"
        for c in fixture.calls("git")
        if c["args"][0] in ("ls-tree", "cat-file", "rev-parse", "read-tree", "commit-tree")
    )


def software_contract():
    """Load pure binding/crypto functions, never the gate or dispatcher entrypoint."""
    import ast

    source = (ROOT / "scripts/c5_git_utils" / SCRIPTS[0]).read_text().split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
    tree = ast.parse(source)
    definitions: list[ast.stmt] = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))]
    namespace: dict[str, object] = {}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), "<publication-contract>", "exec"), namespace)
    from types import SimpleNamespace

    namespace["pwd"] = SimpleNamespace(getpwuid=lambda _: SimpleNamespace(pw_name="fixture-user"))
    namespace["os"] = SimpleNamespace(getuid=lambda: 1234)
    return namespace


@pytest.mark.parametrize(
    "field,value",
    [
        ("causal_hash", "b" * 64),
        ("action", "Other action"),
        ("scope", "Other scope"),
        ("agent", "prefix MOSKV-1 suffix"),
        ("agent", "Codex · Other"),
        ("operator_user", ""),
        ("operator_user", "not-this-session"),
        ("operator_name", ""),
        ("timestamp", 0),
        ("timestamp", float("nan")),
        ("timestamp", float("inf")),
        ("timestamp", True),
    ],
)
def test_binding_rejects_mismatch_expiry_or_wrong_operator_without_attestation(field, value):
    import time

    contract = software_contract()
    now = time.time()
    receipt = dict(
        causal_hash="a" * 64,
        action="Fixture",
        scope="Fixture",
        agent="Codex · MOSKV-1",
        operator_user="fixture-user",
        operator_name="Software fixture",
        timestamp=now,
    )
    receipt[field] = value
    # There is deliberately no ATTESTED status, key or signature in this unit input.
    with pytest.raises(ValueError):
        contract["validate_binding"](receipt, dict(action="Fixture", scope="Fixture"), "a" * 64, now)


def test_prior_attempt_binding_is_rejected_without_replay_attestation():
    import time

    contract = software_contract()
    first = dict(action="Fixture", scope="Fixture", nonce="first")
    second = dict(first, nonce="second")
    receipt = dict(
        causal_hash=contract["effect_hash"](first),
        action="Fixture",
        scope="Fixture",
        agent="MOSKV-1",
        operator_user="fixture-user",
        operator_name="Software fixture",
        timestamp=time.time(),
    )
    with pytest.raises(ValueError, match="mismatch"):
        contract["validate_binding"](receipt, second, contract["effect_hash"](second), time.time())


def test_signature_math_uses_ascii_sha256_contract_without_hardware_claim():
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    contract = software_contract()
    key = ec.generate_private_key(ec.SECP256R1())
    digest = "a" * 64
    signature = key.sign(digest.encode("ascii"), ec.ECDSA(hashes.SHA256()))
    # Bare software signature fields only: no attestation, session or effect dispatch.
    fields = dict(
        public_key=base64.b64encode(
            key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        ).decode(),
        secure_enclave_signature=base64.b64encode(signature).decode(),
    )
    contract["verify_signature"](fields, digest)
    with pytest.raises(InvalidSignature):
        contract["verify_signature"](fields, "b" * 64)
    fields["secure_enclave_signature"] = base64.b64encode(
        key.sign(bytes.fromhex(digest), ec.ECDSA(hashes.SHA256()))
    ).decode()
    with pytest.raises(InvalidSignature):
        contract["verify_signature"](fields, digest)


@pytest.mark.parametrize(
    "header", ["https://git-lfs.github.com/spec/v1", "https://hawser.github.com/spec/v1", "http://git-media.io/v/2"]
)
@pytest.mark.parametrize("prefix,suffix", [(b"", b"\n"), (b" \n", b"\r\n")])
def test_lfs_rejection_covers_legacy_pointer_headers(header, prefix, suffix):
    assert software_contract()["is_lfs_pointer"](
        prefix + b"version " + header.encode() + suffix + b"oid sha256:fixture"
    )


def test_fixture_programs_are_valid_python():
    for source in (FAKE_GIT, FAKE_SCAN, FAKE_GATE):
        compile(source, "<isolated-program>", "exec")


def test_scheduled_second_invocation_cannot_change_first_dispatch(fixture):
    fixture.env["GATE_MODE"] = "race"
    fixture.env["B60_GIT_GATE_TIMEOUT"] = "10"
    result = fixture.run(SCRIPTS[0])
    assert result.returncode != 0  # The fixture never issues ATTESTED.
    (child,) = fixture.calls("concurrent-preview")
    assert child["code"] == 0
    assert (fixture.root / "branch").read_text() == OTHER
    assert not (fixture.root / "pushed").exists()
    (first,) = fixture.calls("gate")
    assert first["effects"][0]["commit"] == COMMIT
    assert first["effects"][0]["tree"] == TREE


def test_parallel_rejected_attempts_keep_distinct_effects_and_no_push(fixture):
    from concurrent.futures import ThreadPoolExecutor

    # Warmup, then four overlapping fixture invocations. No hardware/performance claim.
    assert fixture.run(SCRIPTS[0]).returncode != 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: fixture.run(SCRIPTS[0]), range(4)))
    assert all(result.returncode != 0 for result in results)
    effects = [call["effects"] for call in fixture.calls("gate")]
    assert len(effects) == 5
    # Gate sees all concurrently created manifests; each has a unique nonce.
    descriptors = {item["nonce"]: item for group in effects for item in group}
    assert len(descriptors) == 5
    assert all(item["commit"] == COMMIT and item["tree"] == TREE for item in descriptors.values())
    assert not (fixture.root / "pushed").exists()


def test_serialized_tar_padding_is_counted_against_budget(fixture):
    fixture.env["TREE_MODE"] = "tar-padding"
    result = fixture.run(SCRIPTS[0], "--dry-run")
    assert result.returncode != 0
    assert b"20 MiB" in result.stderr
    assert not fixture.calls("gitleaks")
    assert not (fixture.root / "pushed").exists()


def test_receipt_storage_is_atomic_private_and_preserves_symlink_targets(tmp_path):
    import os

    contract = software_contract()
    contract["os"] = os  # Real file descriptors, exclusively in this owned tmp_path.
    directory = tmp_path / "receipts"
    outside = tmp_path / "untouched"
    outside.write_text("do not overwrite")
    directory.mkdir(mode=0o700)
    (directory / "last_ship_receipt.json").symlink_to(outside)
    effect = dict(nonce="software-fixture-nonce")
    # Storage-only input has no ATTESTED status, signature, key or approval.
    contract["retain_receipt"](directory, b'{"fixture":"storage-only"}', effect)
    saved = directory / "last_ship_receipt.json"
    assert outside.read_text() == "do not overwrite"
    assert not saved.is_symlink()
    assert saved.stat().st_mode & 0o777 == 0o600
    assert json.loads(saved.read_text()) == dict(fixture="storage-only", effect_descriptor=effect)
    assert not list(directory.glob("*.tmp"))
    alias = tmp_path / "directory-link"
    alias.symlink_to(directory, target_is_directory=True)
    with pytest.raises(OSError):
        contract["retain_receipt"](alias, b"{}", effect)


def test_receipt_retention_is_after_authorization_before_dispatch():
    source = (ROOT / "scripts/c5_git_utils" / SCRIPTS[1]).read_text()
    assert (
        source.index('publication_tool gate "$WORK/receipt.json"')
        < source.index('publication_tool retain "$WORK/receipt.json"')
        < source.index('publication_tool publish "$WORK/dispatch.git"')
    )


@pytest.mark.parametrize("mode", ["collision", "unsafe-directory"])
def test_receipt_storage_never_deletes_a_preexisting_temporary(tmp_path, mode):
    import os

    contract = software_contract()
    contract["os"] = os
    directory = tmp_path / "receipts"
    directory.mkdir(mode=0o700)
    temporary = directory / "receipt-fixture-nonce.tmp"
    temporary.write_text("foreign temporary: preserve")
    previous = directory / "last_ship_receipt.json"
    previous.write_text("previous receipt: preserve")
    if mode == "unsafe-directory":
        directory.chmod(0o770)
    with pytest.raises((FileExistsError, ValueError)):
        contract["retain_receipt"](directory, b'{"fixture":"storage-only"}', dict(nonce="fixture-nonce"))
    assert temporary.read_text() == "foreign temporary: preserve"
    assert previous.read_text() == "previous receipt: preserve"
