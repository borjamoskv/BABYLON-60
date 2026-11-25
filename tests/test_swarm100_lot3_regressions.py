"""Publication regressions using simulated dispatch and temporary local Git histories.

Git remotes in these tests live under tmp_path; no ATTESTED fixture is generated.
"""

import base64
import hashlib
import json
import os
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
FORBIDDEN_PATH = "leads_10000_enterprise_babylon60.csv"

FAKE_GIT = r"""
import base64, json, os, pathlib, sys
root = pathlib.Path(os.environ['FIXTURE_ROOT'])
a = sys.argv[1:]
while a[:1] in (['--no-replace-objects'], ['--literal-pathspecs']): a = a[1:]
with (root/'calls.jsonl').open('a') as f:
    f.write(json.dumps({'tool':'git','args':a,'cwd':os.getcwd(), 'config':{
        k:v for k,v in os.environ.items() if k.startswith('GIT_CONFIG_')},
        'no_replace':os.environ.get('GIT_NO_REPLACE_OBJECTS')})+'\n')
if a and a[0].startswith('--git-dir='): a = a[1:]
if a[:1] == ['config']:
    if '--list' in a:
        sys.stdout.buffer.write(b'url.ssh://changed/.insteadof\nssh://fixed/\0http.extraheader\nfixture-auth\0')
    elif a[-1] == 'babylon60.topologyUpstreamHooksPath':
        if 'FIXTURE_UPSTREAM' not in os.environ: sys.exit(1)
        print(os.environ['FIXTURE_UPSTREAM'])
    sys.exit(0)
if a[:2] == ['rev-parse','--abbrev-ref']: print('main')
elif a[:1] == ['rev-parse']:
    if '--git-path' in a:
        print(os.environ.get('FIXTURE_PRE_PUSH', root/'pre-push') if a[-1] == 'hooks/pre-push' else root/'objects')
    elif '--is-shallow-repository' in a: print('false')
    elif '--show-object-format' in a: print('sha1')
    elif any('tree' in x for x in a): print('3'*40)
    else: print('1'*40)
elif a[:1] == ['rev-list']:
    history = os.environ.get('FIXTURE_HISTORY', 'clean')
    if '--count' in a: print(0 if 'HEAD..origin/main' in a else 1)
    elif history == 'error': sys.exit(128)
    elif '--' in a:
        if history == 'removed-path': print('6'*40)
    elif history == 'ancestor': print('ce25e51caf18a03d69fc512421cbf059ddf61e6f')
    else: print('1'*40)
elif a[:1] == ['status']: pass
elif a[:2] == ['remote','get-url']:
    print(os.environ.get('FIXTURE_URL', 'ssh://fixed/repo.git'))
elif a[:1] == ['ls-tree']:
    if os.environ.get('TREE_MODE') == 'gitlink':
        sys.stdout.buffer.write(b'160000 commit '+b'4'*40+b'\tsubmodule\0'); sys.exit(0)
    if os.environ.get('TREE_MODE') == 'unsafe':
        sys.stdout.buffer.write(b'100644 blob '+b'4'*40+b'\t../escape\0'); sys.exit(0)
    if '--name-only' in a and '--' in a:
        if os.environ.get('TREE_MODE') == 'forbidden-csv':
            sys.stdout.buffer.write(b'leads_10000_enterprise_babylon60.csv\0')
    elif '-rz' in a:
        sys.stdout.buffer.write(b'100644 blob '+b'4'*40+b'\t.gitleaks.toml\0'+
                                b'100644 blob '+b'5'*40+b'\texport-ignored.txt\0')
    else: print('.gitleaks.toml\nexport-ignored.txt')
elif a[:1] == ['cat-file']:
    if '--batch-check=%(objecttype)' in a: print('commit'); sys.exit(0)
    data = b'[extend]\nuseDefault = true\n' if a[-1] == '4'*40 else b'FIXTURE_TREE_ONLY_SECRET\n'
    if a[-1] != '4'*40 and os.environ.get('TREE_MODE') == 'tar-padding': data = b'x'*(33554432-1000)
    if a[-1] != '4'*40 and os.environ.get('TREE_MODE') == 'lfs': data = b'version https://git-lfs.github.com/spec/v1\noid sha256:fixture\nsize 123\n'
    if a[-1] == '4'*40 and os.environ.get('TREE_MODE') == 'external-policy': data = b'[extend]\npath = \"/outside/policy\"\n'
    if os.environ.get('TREE_MODE') == 'big' and '-s' in a: print(33554432); sys.exit(0)
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
    if (root/'pushed').exists():
        print(('2'*40 if os.environ.get('REMOTE_MISMATCH') else (root/'pushed').read_text())+'\trefs/heads/main')
    elif os.environ.get('FIXTURE_REMOTE_OID'):
        print(os.environ['FIXTURE_REMOTE_OID']+'\trefs/heads/main')
elif a[:1] == ['init']:
    dest = pathlib.Path(a[-1]); (dest/'objects/info').mkdir(parents=True)
elif a[:1] == ['hash-object']: print('7'*40)
elif a[:1] in (['diff-index'], ['read-tree'], ['rm'], ['fetch'], ['diff'], ['update-index']): pass
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
    for path in (root/'tmp').rglob('effect.json'):
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
if mode == 'timeout': time.sleep(15)
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
            "B60_GIT_GATE_TIMEOUT": "10",
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
        for name in (*SCRIPTS, "publication_policy.py"):
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
            timeout=30,
        )

    def calls(self, tool):
        log = self.root / "calls.jsonl"
        return [c for c in map(json.loads, log.read_text().splitlines()) if c["tool"] == tool] if log.exists() else []

    def helper(self, *args, cwd=None):
        source = (self.root / "scripts/c5_git_utils" / SCRIPTS[0]).read_text()
        assert "# PUBLICATION_TOOL_BEGIN" in source
        helper = source.split("# PUBLICATION_TOOL_BEGIN", 1)[1].split("# PUBLICATION_TOOL_END", 1)[0]
        return subprocess.run(
            ["/bin/bash", "-c", helper + '\npublication_tool "$@"', "fixture", *args],
            cwd=cwd or self.root,
            env={**self.env, "REPO_ROOT": str(self.root)},
            capture_output=True,
            timeout=30,
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
    if mode == "timeout":
        fixture.env["B60_GIT_GATE_TIMEOUT"] = "3"
    result = fixture.run(name)
    assert result.returncode != 0
    assert len(fixture.calls("gate")) == 1, result.stderr
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
    hooks_dir = next(
        Path(config[f"GIT_CONFIG_VALUE_{n}"])
        for n in range(int(config["GIT_CONFIG_COUNT"]))
        if config[f"GIT_CONFIG_KEY_{n}"] == "core.hooksPath"
    )
    assert hooks_dir.is_relative_to(fixture.root)
    assert os.access(hooks_dir / "pre-push", os.X_OK)


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


def test_changed_hook_is_rechecked_before_noop_dispatch(fixture):
    fixture.env["FROZEN_EFFECT"] = prepare(fixture)
    hook = fixture.root / "pre-push"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o700)
    result = fixture.helper("publish", str(fixture.root / "dispatch.git"))
    assert result.returncode != 0
    assert b"pre-push hook" in result.stderr
    assert not (fixture.root / "pushed").exists()


@pytest.fixture
def local_repository(tmp_path, monkeypatch):
    """Real Git, isolated from user config, hooks, remotes and the source checkout."""
    for key in list(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    repo = tmp_path / "local repository"
    repo.mkdir()
    monkeypatch.chdir(repo)

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()

    git("init", "--quiet", "--template=", "--initial-branch=main")
    git("config", "user.name", "Publication test")
    git("config", "user.email", "publication@example.invalid")
    return repo, git


@pytest.fixture
def topology_wrapper(fixture, local_repository):
    repo, git = local_repository
    upstream = repo / "operator's previous hooks"
    upstream.mkdir()
    previous = upstream / "pre-push"
    previous.write_text("#!/bin/sh\nexit 1\n")
    previous.chmod(0o700)
    git("config", "core.hooksPath", str(upstream))
    # The installer requires a successful worktree topology check. This repo
    # exercises its hook generator without needing a second BABYLON checkout.
    topology_check = repo / "scripts/guards/verify_active_topology.py"
    topology_check.parent.mkdir(parents=True)
    topology_check.write_text("raise SystemExit(0)\n")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/guards/install_topology_hook.py"), "--repo-root", str(repo)],
        check=True,
        capture_output=True,
    )
    wrapper = Path(git("rev-parse", "--path-format=absolute", "--git-path", "hooks/pre-push"))
    fixture.env["FIXTURE_PRE_PUSH"] = str(wrapper)
    fixture.env["FIXTURE_UPSTREAM"] = git("config", "--get", "babylon60.topologyUpstreamHooksPath")
    return wrapper, previous


@pytest.mark.parametrize("name", SCRIPTS)
@pytest.mark.parametrize("hook_state", ["inactive-upstream", "active-upstream", "modified-wrapper"])
def test_publishers_check_the_complete_installed_wrapper(fixture, topology_wrapper, name, hook_state):
    wrapper, previous = topology_wrapper
    if hook_state != "active-upstream":
        previous.unlink()
    if hook_state == "modified-wrapper":
        wrapper.write_text(wrapper.read_text() + "# outside the installed template\n")

    result = fixture.run(name)
    assert result.returncode != 0  # The fixture never issues an affirmative receipt.
    if hook_state == "inactive-upstream":
        assert len(fixture.calls("gate")) == 1, result.stderr
    else:
        assert b"pre-push hook" in result.stderr, result.stderr
        assert not fixture.calls("gate")
    assert not (fixture.root / "pushed").exists()


@pytest.mark.parametrize("name", SCRIPTS)
@pytest.mark.parametrize("policy_case", ["ancestor", "removed-path", "present-path", "error"])
def test_public_history_is_checked_before_authorization_even_without_hook(fixture, name, policy_case):
    # The mirror uses the public alias; ship uses origin with the public URL.
    if name == "c5_ship.sh":
        fixture.env["FIXTURE_URL"] = "git@github.com:borjamoskv/BABYLON-60.git"
    fixture.env["FIXTURE_REMOTE_OID"] = OTHER
    fixture.env["FIXTURE_HISTORY"] = policy_case
    if policy_case == "present-path":
        fixture.env["TREE_MODE"] = "forbidden-csv"
    result = fixture.run(name)
    assert result.returncode != 0
    assert not fixture.calls("gate")
    assert not (fixture.root / "pushed").exists()
    assert any("ls-remote" in c["args"] for c in fixture.calls("git")), result.stderr
    reason = {
        "ancestor": b"forbidden commit",
        "removed-path": b"forbidden path in outgoing",
        "present-path": b"forbidden path in public tree",
        "error": b"CalledProcessError",
    }
    assert reason[policy_case] in result.stderr, result.stderr


@pytest.mark.parametrize("name", SCRIPTS)
def test_private_destination_preserves_its_own_policy(fixture, name):
    fixture.env["FIXTURE_URL"] = "git@github.com:borjamoskv/BABYLON-60-VAULT.git"
    fixture.env["FIXTURE_HISTORY"] = "removed-path"
    args = ["vault"] if name == "c5_distill_public_mirror.sh" else []
    result = fixture.run(name, *args)
    assert result.returncode != 0
    assert len(fixture.calls("gate")) == 1, result.stderr
    assert not (fixture.root / "pushed").exists()


def test_public_policy_checks_actual_outgoing_history(local_repository):
    from scripts.c5_git_utils.publication_policy import check_public_history

    repo, git = local_repository
    git("commit", "--allow-empty", "-qm", "clean base")
    base = git("rev-parse", "HEAD")
    check_public_history(base, None)

    protected = repo / FORBIDDEN_PATH
    protected.write_text("synthetic fixture row\n")
    git("add", "--", FORBIDDEN_PATH)
    git("commit", "-qm", "add fixture row")
    with pytest.raises(ValueError):
        check_public_history(git("rev-parse", "HEAD"), base)

    git("rm", "--", FORBIDDEN_PATH)
    git("commit", "-qm", "remove fixture row")
    removed = git("rev-parse", "HEAD")
    with pytest.raises(ValueError):
        check_public_history(removed, base)
    with pytest.raises(ValueError):
        check_public_history(removed, None)
    with pytest.raises(ValueError):
        check_public_history(removed, "f" * len(removed))

    git("commit", "--allow-empty", "-qm", "clean incremental change")
    check_public_history(git("rev-parse", "HEAD"), removed)


def test_prepare_binds_the_remote_tip_and_checks_outgoing_objects_with_real_git(fixture, local_repository):
    repo, git = local_repository
    remote = repo.parent / "advertised.git"
    git("init", "--quiet", "--bare", "--template=", str(remote))
    git("commit", "--allow-empty", "-qm", "advertised base")
    base = git("rev-parse", "HEAD")
    git("push", "--quiet", str(remote), "HEAD:refs/heads/main")
    git("remote", "add", "public", "ssh://fixture.invalid/advertised.git")

    # Both the source checkout and the isolated preflight bare use real Git.
    # The SSH stub accepts a single upload-pack request for the temporary bare.
    real_git = shutil.which("git")
    assert real_git
    (fixture.bin / "git").unlink()
    (fixture.bin / "git").symlink_to(real_git)
    fixture.install(
        "ssh",
        "import os, shlex, sys\n"
        "if sys.argv[1:-1] != ['fixture.invalid'] or "
        "shlex.split(sys.argv[-1]) != ['git-upload-pack', '/advertised.git']:\n"
        "    raise SystemExit('unexpected SSH request')\n"
        f"os.execv({real_git!r}, ['git', 'upload-pack', {str(remote)!r}])\n",
    )
    fixture.env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_SSH="ssh",
        GIT_SSH_VARIANT="simple",
    )
    (repo / "candidate.txt").write_text("only in the source object database\n")
    git("add", "candidate.txt")
    git("commit", "-qm", "unpublished candidate")
    candidate = git("rev-parse", "HEAD")
    effect_file = fixture.root / "effect.json"

    def prepare_head():
        return fixture.helper(
            "prepare",
            git("rev-parse", "HEAD"),
            git("rev-parse", "HEAD^{tree}"),
            "public",
            "true",
            "Fixture",
            "Fixture",
            str(effect_file),
            cwd=repo,
        )

    result = prepare_head()
    assert result.returncode == 0, result.stderr
    effect = json.loads(effect_file.read_bytes())
    assert json.loads(base64.b64decode(result.stdout))["effect"] == effect
    assert (effect["commit"], effect["public_ref_base"]) == (candidate, base)
    effect_file.unlink()

    (repo / FORBIDDEN_PATH).write_text("fixture\n")
    git("add", "--", FORBIDDEN_PATH)
    git("commit", "-qm", "temporary protected path")
    git("rm", "--", FORBIDDEN_PATH)
    git("commit", "-qm", "remove protected path")
    result = prepare_head()
    assert result.returncode != 0
    assert b"forbidden path in outgoing" in result.stderr
    assert not effect_file.exists()


def test_dispatch_guard_checks_actual_advertisement_before_updating_local_bare_remote(local_repository):
    from scripts.c5_git_utils.publication_policy import install_dispatch_hook

    repo, git = local_repository
    remote = repo.parent / "remote.git"
    git("init", "--quiet", "--bare", "--template=", str(remote))
    ref = "refs/heads/main"
    git("commit", "--allow-empty", "-qm", "base")
    base = git("rev-parse", "HEAD")
    git("commit", "--allow-empty", "-qm", "intervening update")
    intervening = git("rev-parse", "HEAD")
    git("commit", "--allow-empty", "-qm", "candidate")
    candidate = git("rev-parse", "HEAD")
    first_hooks = repo / "first push hooks"
    install_dispatch_hook(first_hooks, base, ref, None)
    git("-c", f"core.hooksPath={first_hooks}", "push", "--quiet", str(remote), base + ":" + ref)
    # Simulate another writer after the first advertised destination was checked.
    git("push", "--quiet", str(remote), intervening + ":" + ref)
    stale_hooks = repo / "stale hooks"
    install_dispatch_hook(stale_hooks, candidate, ref, base)
    with pytest.raises(subprocess.CalledProcessError):
        git("-c", f"core.hooksPath={stale_hooks}", "push", "--quiet", str(remote), candidate + ":" + ref)
    assert git("--git-dir=" + str(remote), "rev-parse", ref) == intervening

    fresh_hooks = repo / "fresh hooks"
    install_dispatch_hook(fresh_hooks, candidate, ref, intervening)
    git("-c", f"core.hooksPath={fresh_hooks}", "push", "--quiet", str(remote), candidate + ":" + ref)
    assert git("--git-dir=" + str(remote), "rev-parse", ref) == candidate


@pytest.mark.parametrize("name", SCRIPTS)
def test_topology_pre_push_hook_contract_allows_clean_projection(fixture, name):
    fixture.env["FIXTURE_UPSTREAM"] = "/nonexistent/chained dir"
    hook = fixture.root / "pre-push"
    hook.write_text(
        "#!/bin/sh\n"
        "# Generated by BABYLON-60 install_topology_hook.py\n"
        "if [ -x '/nonexistent/chained dir/pre-push' ]; then\n"
        "    exec '/nonexistent/chained dir/pre-push' \"$@\"\n"
        "fi\n"
        "exit 0\n"
    )
    hook.chmod(0o700)
    result = fixture.run(name)
    assert b"pre-push hook" not in result.stderr
    assert len(fixture.calls("gate")) == 1, result.stderr.decode()


@pytest.mark.parametrize("name", SCRIPTS)
@pytest.mark.parametrize(
    "hook_body",
    [
        (
            "#!/bin/sh\n"
            "# Generated by BABYLON-60 install_topology_hook.py\n"
            "# C5-REAL Fail-Closed Gate: Block any push to public remote.\n"
            "exit 0\n"
        ),
        ("#!/bin/sh\n# Generated by BABYLON-60 install_topology_hook.py\necho 'denied' >&2\nexit 1\n"),
        ("#!/bin/sh\n# Generated by BABYLON-60 install_topology_hook.py\nexit 1\n"),
        (
            "#!/bin/sh\n"
            "# Generated by BABYLON-60 install_topology_hook.py\n"
            'if [ -x /nonexistent/chained ]; then\n    exec /nonexistent/chained "$@"\nfi\nexit 1\n'
        ),
        (
            "#!/bin/sh\n"
            "# Generated by BABYLON-60 install_topology_hook.py\n"
            'if [ -x /nonexistent/a ]; then\n    exec /nonexistent/b "$@"\nfi\nexit 0\n'
        ),
        (
            "#!/bin/sh\n"
            "# Generated by BABYLON-60 install_topology_hook.py\n"
            'if [ -x /nonexistent/chained ]; then\n    exec /nonexistent/chained "$@"\nfi\nexit 0\necho "extra"\n'
        ),
    ],
)
def test_topology_pre_push_hook_rejects_public_gate_and_header_bypass_fail_closed(fixture, name, hook_body):
    fixture.env["FIXTURE_UPSTREAM"] = "/nonexistent/chained dir"
    hook = fixture.root / "pre-push"
    hook.write_text(hook_body)
    hook.chmod(0o700)
    result = fixture.run(name)
    assert result.returncode != 0
    assert b"pre-push hook" in result.stderr
    assert not fixture.calls("gate")
    assert not (fixture.root / "pushed").exists()


@pytest.mark.parametrize("name", SCRIPTS)
def test_pre_push_hook_rejects_symlink_and_active_quoted_chains(fixture, name):
    fixture.env["FIXTURE_UPSTREAM"] = "/nonexistent/chained dir"
    target = fixture.root / "real_hook.sh"
    target.write_text("#!/bin/sh\nexit 0\n")
    target.chmod(0o700)
    hook = fixture.root / "pre-push"
    hook.symlink_to(target)
    res_symlink = fixture.run(name)
    assert res_symlink.returncode != 0
    assert b"pre-push hook" in res_symlink.stderr
    assert not fixture.calls("gate")
    assert not (fixture.root / "pushed").exists()

    hook.unlink()
    spaced_dir = fixture.root / "chained dir"
    spaced_dir.mkdir()
    fixture.env["FIXTURE_UPSTREAM"] = str(spaced_dir)
    chained = spaced_dir / "pre-push"
    chained.write_text("#!/bin/sh\nexit 1\n")
    chained.chmod(0o700)
    hook.write_text(
        "#!/bin/sh\n"
        "# Generated by BABYLON-60 install_topology_hook.py\n"
        f"if [ -x '{chained}' ]; then\n"
        f"    exec '{chained}' \"$@\"\n"
        "fi\n"
        "exit 0\n"
    )
    hook.chmod(0o700)
    res_chain = fixture.run(name)
    assert res_chain.returncode != 0
    assert b"pre-push hook" in res_chain.stderr
    assert not fixture.calls("gate")
    assert not (fixture.root / "pushed").exists()


@pytest.mark.parametrize("name", SCRIPTS)
@pytest.mark.parametrize("newline_seq", ["\r\n", "\r", "\u2028", "\x0b", "\x85"])
def test_pre_push_hook_rejects_non_lf_line_endings_before_gate(fixture, name, newline_seq):
    fixture.env["FIXTURE_UPSTREAM"] = "/nonexistent/chained dir"
    hook = fixture.root / "pre-push"
    lines = [
        "#!/bin/sh",
        "# Generated by BABYLON-60 install_topology_hook.py",
        "if [ -x '/nonexistent/chained dir/pre-push' ]; then",
        "    exec '/nonexistent/chained dir/pre-push' \"$@\"",
        "fi",
        "exit 0",
    ]
    hook.write_bytes((newline_seq.join(lines) + newline_seq).encode("utf-8"))
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
    assert b"32 MiB" in result.stderr
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


def test_public_projection_strips_private_tests_and_stages_manifest(fixture):
    result = fixture.run(SCRIPTS[0], "--dry-run")
    assert result.returncode == 0, result.stderr
    git_calls = fixture.calls("git")
    rm_calls = [c["args"] for c in git_calls if c["args"][:1] == ["rm"]]
    assert rm_calls
    removed = set(rm_calls[0])
    assert "tests/test_swarm100_lot2_regressions.py" in removed
    assert "tests/test_regulatory_native_validation.py" in removed
    update_calls = [c["args"] for c in git_calls if c["args"][:1] == ["update-index"]]
    assert any(".github/public_projection_manifest.json" in arg for args in update_calls for arg in args)
