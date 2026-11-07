#!/usr/bin/env bash
# Publish a bounded raw-blob projection after mandatory scanning and fresh authorization.
set -euo pipefail
export GIT_NO_REPLACE_OBJECTS=1

# PUBLICATION_TOOL_BEGIN
# Kept identical in both standalone entrypoints; regression checks enforce parity.
publication_tool() {
    B60_PUBLICATION_EFFECT="${FROZEN_EFFECT:-}" uv run --locked --no-sync python - "$@" <<'PY'
import base64
import hashlib
import json
import io
import math
import os
from pathlib import Path, PurePosixPath
import re
import pwd
import shlex
import secrets
import selectors
import signal
import subprocess
import sys
import time
import tarfile
import tomllib
from urllib.parse import urlsplit


def git(*args, env=None):
    selected_env = dict(os.environ if env is None else env)
    selected_env['GIT_NO_REPLACE_OBJECTS'] = '1'
    return subprocess.check_output(['git', *args], env=selected_env)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def effect_hash(effect):
    return sha(b'BABYLON60:GIT:PUBLISH:v1\0' + canonical(effect))


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate receipt key')
        result[key] = value
    return result


def validate_binding(receipt, effect, digest, started):
    for key, value in [('causal_hash', digest), ('action', effect['action']), ('scope', effect['scope'])]:
        if receipt.get(key) != value:
            raise ValueError('receipt effect mismatch')
    prefixes = ('Antigravity', 'Claude Code', 'Codex', 'Cursor', 'Windsurf', 'ChatGPT', 'Aider',
                'iTerm2', 'Ghostty', 'Warp', 'Terminal macOS', 'VS Code', 'Terminal / Shell')
    if receipt.get('agent') not in ('MOSKV-1', *(p+' · MOSKV-1' for p in prefixes)):
        raise ValueError('receipt agent mismatch')
    if not all(isinstance(receipt.get(k), str) and receipt[k].strip()
               for k in ('operator_user', 'operator_name')):
        raise ValueError('receipt session operator missing')
    if receipt['operator_user'] != pwd.getpwuid(os.getuid()).pw_name:
        raise ValueError('receipt operator differs from current session')
    timestamp = receipt.get('timestamp')
    if (isinstance(timestamp, bool) or not isinstance(timestamp, (int, float))
            or not math.isfinite(timestamp) or not started-5 <= timestamp <= time.time()+5):
        raise ValueError('receipt outside current gate interval')


def verify_signature(receipt, digest):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    key = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256R1(), base64.b64decode(receipt['public_key'], validate=True))
    signature = base64.b64decode(receipt['secure_enclave_signature'], validate=True)
    key.verify(signature, digest.encode('ascii'), ec.ECDSA(hashes.SHA256()))


def is_lfs_pointer(data):
    lines = data[:1024].lstrip().splitlines()
    if not lines:
        return False
    return lines[0].strip() in (
        b'version https://git-lfs.github.com/spec/v1',
        b'version https://hawser.github.com/spec/v1',
        b'version http://git-media.io/v/2',
    )


def retain_receipt(directory, receipt_bytes, effect):
    # This stores an already verified receipt; it never grants authorization.
    directory = Path(directory)
    directory.mkdir(mode=0o700, exist_ok=True)
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    temporary = 'receipt-'+effect['nonce']+'.tmp'
    created = False
    try:
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or info.st_mode & 0o022:
            raise ValueError('receipt directory must be session-owned and not publicly writable')
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        output = os.open(temporary, flags, 0o600, dir_fd=fd)
        created = True
        with os.fdopen(output, 'wb') as stream:
            record = json.loads(receipt_bytes, object_pairs_hook=unique)
            record['effect_descriptor'] = effect
            stream.write(canonical(record))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, 'last_ship_receipt.json', src_dir_fd=fd, dst_dir_fd=fd)
        created = False
        os.fsync(fd)
    finally:
        try:
            if created:
                try:
                    os.unlink(temporary, dir_fd=fd)
                except FileNotFoundError:
                    pass
        finally:
            os.close(fd)


def main():
    mode, *args = sys.argv[1:]
    if mode == 'snapshot':
        tree, destination = args
        dest = Path(destination)
        dest.mkdir(mode=0o700)
        total = 0
        paths = []
        for entry in git('ls-tree', '-rz', '--full-tree', tree).split(b'\0'):
            if not entry:
                continue
            header, raw = entry.split(b'\t', 1)
            filemode, kind, oid = header.decode('ascii').split()
            name = raw.decode('utf-8', errors='strict')
            path = PurePosixPath(name)
            if (path.is_absolute() or any(p in ('.', '..', '.git') for p in name.split('/'))
                    or '\\' in name or any(ord(c) < 32 for c in name)):
                raise ValueError('unsafe snapshot path')
            if kind != 'blob' or filemode not in ('100644', '100755', '120000'):
                raise ValueError('unsupported snapshot object (including submodules)')
            if path.suffix.lower() in ('.csv', '.jsonl', '.db', '.vtt'):
                raise ValueError('forbidden public file type')
            size = int(git('cat-file', '-s', oid))
            total += size  # Early raw-data budget; the serialized tar is measured below.
            if total >= 20971520:
                raise ValueError('public snapshot exceeds 20 MiB budget')
            data = git('cat-file', 'blob', oid)
            if is_lfs_pointer(data):
                raise ValueError('LFS object publication is unsupported')
            if len(data) != size:
                raise ValueError('snapshot blob size mismatch')
            target = dest.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            # Git symlinks are scanned as their raw blob, never followed.
            with target.open('xb') as stream:
                stream.write(data)
            target.chmod(0o600)
            paths.append((name, filemode))
        if ('.gitleaks.toml', '100644') not in paths and ('.gitleaks.toml', '100755') not in paths:
            raise ValueError('tracked regular scanner policy required')
        policy = tomllib.loads((dest/'.gitleaks.toml').read_text())
        if 'path' in policy.get('extend', {}):
            raise ValueError('external scanner configuration is forbidden')
        class BudgetSink(io.BytesIO):
            size = 0

            def write(self, data):
                self.size += len(data)
                if self.size >= 20971520:
                    raise ValueError('serialized snapshot tar reaches 20 MiB')
                return len(data)

        def metadata(info):
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ''
            return info

        sink = BudgetSink()
        with tarfile.open(fileobj=sink, mode='w|', format=tarfile.PAX_FORMAT) as bundle:
            bundle.add(dest, arcname='.', recursive=True, filter=metadata)
        print(f'Snapshot: {len(paths)} raw blobs, {total} data bytes, {sink.size} serialized tar bytes')
        return
    if mode == 'prepare':
        commit, tree, remote, force, action, scope, output = args
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', commit + ''):
            raise ValueError('invalid immutable commit')
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', tree):
            raise ValueError('invalid immutable tree')
        hook = Path(git('rev-parse', '--path-format=absolute', '--git-path', 'hooks/pre-push').decode().strip())
        if hook.is_file() and os.access(hook, os.X_OK):
            raise ValueError('active pre-push hook requires a supported publication contract')
        # Reject LFS even when its hook is absent. Inspect only the pointer prefix,
        # without allocating large blobs from a private ship tree.
        for entry in git('ls-tree', '-rz', '--full-tree', tree).split(b'\0'):
            if not entry:
                continue
            header, _ = entry.split(b'\t', 1)
            _, kind, oid = header.decode('ascii').split()
            if kind != 'blob':
                raise ValueError('submodule publication is unsupported')
            with subprocess.Popen(['git', '--no-replace-objects', 'cat-file', 'blob', oid],
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as child:
                if child.stdout is None:
                    raise ValueError('object stream unavailable')
                prefix = child.stdout.read(1024)
                child.stdout.close()
                code = child.wait()
            if is_lfs_pointer(prefix):
                raise ValueError('LFS object publication is unsupported')
            # SIGPIPE is expected when stopping after a large non-pointer blob.
            if code not in (0, -signal.SIGPIPE, 128+signal.SIGPIPE, 141):
                raise ValueError('unable to inspect publication object')
        urls = git('remote', 'get-url', '--push', '--all', remote).decode().splitlines()
        if len(urls) != 1 or not urls[0] or any(c.isspace() for c in urls[0]):
            raise ValueError('exactly one unambiguous push destination required')
        url = urls[0]
        if not (url.startswith(('https://', 'ssh://')) or re.fullmatch(r'[\w.-]+@[\w.-]+:[^\s]+', url)):
            raise ValueError('only explicit SSH/HTTPS destinations are supported')
        if '://' in url and (urlsplit(url).password or not urlsplit(url).hostname):
            raise ValueError('embedded passwords or invalid hosts are forbidden')
        config = []
        for record in git('config', '--null', '--list', '--includes').split(b'\0'):
            if not record:
                continue
            key, _, value = record.decode().partition('\n')
            if key.startswith(('credential.', 'http.', 'https.')) or key in (
                    'core.sshcommand', 'core.gitproxy', 'core.askpass', 'ssh.variant'):
                config.append((key, value))
        for variable, key in [('GIT_SSH_COMMAND', 'core.sshcommand'), ('GIT_SSH', 'core.sshcommand'),
                              ('GIT_ASKPASS', 'core.askpass'), ('GIT_SSH_VARIANT', 'ssh.variant')]:
            if variable in os.environ and not (variable == 'GIT_SSH' and 'GIT_SSH_COMMAND' in os.environ):
                config.append((key, shlex.quote(os.environ[variable]) if variable == 'GIT_SSH' else os.environ[variable]))
        objects = git('rev-parse', '--path-format=absolute', '--git-path', 'objects').decode().strip()
        fmt = git('rev-parse', '--show-object-format').decode().strip()
        if not Path(objects).is_absolute() or '\n' in objects or fmt not in ('sha1', 'sha256'):
            raise ValueError('invalid source object store')
        effect = dict(schema='BABYLON60:GIT:PUBLISH:v1', commit=commit, tree=tree,
                      destination_sha256=sha(url.encode()), target_ref='refs/heads/main',
                      force=force == 'true', action=action, scope=scope, agent='MOSKV-1',
                      nonce=secrets.token_hex(32), transport_config_sha256=sha(canonical(config)))
        Path(output).write_bytes(canonical(effect))
        envelope = dict(effect=effect, url=url, config=config, objects=objects, format=fmt)
        print(base64.b64encode(canonical(envelope)).decode())
        return
    envelope = json.loads(base64.b64decode(os.environ['B60_PUBLICATION_EFFECT'], validate=True))
    effect = envelope['effect']
    digest = effect_hash(effect)
    if mode == 'gate':
        receipt_path, *command = args
        timeout = int(os.environ.get('B60_GIT_GATE_TIMEOUT', '45'))
        if not 1 <= timeout <= 60:
            raise ValueError('gate timeout outside 1..60 seconds')
        # The selected local gate is trusted. Receipt self-consistency alone does
        # not establish Secure Enclave key provenance independently of that gate.
        env = {k:v for k,v in os.environ.items() if k != 'B60_PUBLICATION_EFFECT'}
        started = time.time()
        with subprocess.Popen([*command, '--causal-hash', digest, '--action', effect['action'],
                               '--agent', effect['agent'], '--scope', effect['scope'], '--no-sound'],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env,
                              start_new_session=True) as process:
            deadline = time.monotonic()+timeout
            stdout = bytearray()
            try:
                if process.stdout is None:
                    raise ValueError('gate receipt stream unavailable')
                with selectors.DefaultSelector() as reader:
                    reader.register(process.stdout, selectors.EVENT_READ)
                    while True:
                        remaining = deadline-time.monotonic()
                        if remaining <= 0 or not reader.select(remaining):
                            raise ValueError('gate deadline exceeded; no retry')
                        chunk = os.read(process.stdout.fileno(), min(4096, 65537-len(stdout)))
                        if not chunk:
                            break
                        stdout.extend(chunk)
                        if len(stdout) > 65536:
                            raise ValueError('gate receipt exceeds 64 KiB')
                process.wait(timeout=max(0.001, deadline-time.monotonic()))
                if process.returncode or not stdout:
                    raise ValueError('gate failed, cancelled or returned no receipt')
            except (ValueError, subprocess.TimeoutExpired):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                raise ValueError('gate rejected, failed or exceeded deadline/receipt budget; no retry') from None
        receipt = json.loads(stdout, object_pairs_hook=unique)
        if receipt.get('status') != 'ATTESTED':
            raise ValueError('gate did not attest')
        validate_binding(receipt, effect, digest, started)
        verify_signature(receipt, digest)
        with Path(receipt_path).open('xb') as stream:
            stream.write(canonical(receipt))
        return
    if mode == 'retain':
        receipt_path, directory = args
        retain_receipt(directory, Path(receipt_path).read_bytes(), effect)
        return
    if mode == 'publish':
        dispatch, = args
        if (sha(envelope['url'].encode()) != effect['destination_sha256']
                or sha(canonical(envelope['config'])) != effect['transport_config_sha256']):
            raise ValueError('frozen destination/config mismatch')
        env = {k:v for k,v in os.environ.items()
               if not k.startswith('GIT_') and k != 'B60_PUBLICATION_EFFECT'}
        env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT='0')
        git('init', '--bare', '--template=', '--object-format='+envelope['format'], dispatch, env=env)
        alternates = Path(dispatch)/'objects/info/alternates'
        alternates.write_text(json.dumps(envelope['objects'], ensure_ascii=False)+'\n')
        config = [*envelope['config'], ('core.hooksPath', os.devnull),
                  ('protocol.ext.allow', 'never'), ('protocol.file.allow', 'never')]
        env['GIT_CONFIG_COUNT'] = str(len(config))
        for index, (key, value) in enumerate(config):
            env[f'GIT_CONFIG_KEY_{index}'] = key
            env[f'GIT_CONFIG_VALUE_{index}'] = value
        prefix = '--git-dir='+dispatch
        force_args = ['--force'] if effect['force'] else []
        refspec = effect['commit']+':'+effect['target_ref']
        subprocess.run(['git', prefix, 'push', *force_args, '--', envelope['url'], refspec], env=env, check=True)
        observed = git(prefix, 'ls-remote', '--exit-code', '--', envelope['url'], effect['target_ref'], env=env)
        if observed.decode().strip() != effect['commit']+'\t'+effect['target_ref']:
            raise ValueError('remote ref differs after push; no retry')
        print('Remote ref verified against immutable commit '+effect['commit'])
        return
    raise ValueError('unsupported publication operation')


try:
    main()
except Exception as error:
    # Do not echo URLs/configuration/credential helper output into diagnostics.
    detail = str(error) if type(error) is ValueError else type(error).__name__
    print('Publication refused: '+detail, file=sys.stderr)
    sys.exit(1)
PY
}
# PUBLICATION_TOOL_END

select_gate() {
    if command -v c5_biometric_gate >/dev/null 2>&1; then
        GATE=("$(command -v c5_biometric_gate)")
    elif command -v swift >/dev/null 2>&1 && [ -f "$REPO_ROOT/01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift" ]; then
        GATE=("$(command -v swift)" "$REPO_ROOT/01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift")
    else
        echo 'FATAL: c5_biometric_gate unavailable; publication refused.' >&2
        exit 1
    fi
    command -v uv >/dev/null 2>&1 || { echo 'FATAL: provisioned uv required.' >&2; exit 1; }
    uv run --locked --no-sync python -c 'import cryptography' >/dev/null
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"
TARGET_REMOTE=public
DRY_RUN=0
REMOTE_SET=0
for argument in "$@"; do
    case "$argument" in
        --dry-run) DRY_RUN=1 ;;
        -*) echo 'Unknown option' >&2; exit 1 ;;
        *)
            [ "$REMOTE_SET" -eq 0 ] || { echo 'Only one remote is supported' >&2; exit 1; }
            TARGET_REMOTE="$argument"; REMOTE_SET=1 ;;
    esac
done
command -v git >/dev/null 2>&1
command -v uv >/dev/null 2>&1
command -v gitleaks >/dev/null 2>&1 || { echo 'FATAL: mandatory Gitleaks unavailable.' >&2; exit 1; }
GATE=()
if [ "$DRY_RUN" -eq 0 ]; then select_gate; fi
if [ "$DRY_RUN" -eq 0 ] && ! git diff-index --quiet HEAD --; then
    echo 'FATAL: tracked changes must be committed before projection.' >&2
    exit 1
fi
umask 077
WORK="$(mktemp -d "${TMPDIR:-/tmp}/b60-publication.XXXXXXXX")"
trap 'rm -rf -- "$WORK"' EXIT
BASE_COMMIT="$(git rev-parse --verify HEAD)"
GIT_INDEX_FILE="$WORK/index" git read-tree "$BASE_COMMIT"
GIT_INDEX_FILE="$WORK/index" git rm --cached -r -q --ignore-unmatch \
    .agents/rules \
    .agents/mcp_config.json \
    .playwright-mcp \
    docs/security/evidence \
    tools/skill_library \
    assets/brand/github-art-brut.svg \
    assets/AppIcon.icns \
    assets/babylon60_brutalist_logo_1024.png
CLEAN_TREE="$(GIT_INDEX_FILE="$WORK/index" git write-tree)"
readonly CLEAN_TREE
# Raw blobs include export-ignored files. No worktree, attributes or symlinks can
# substitute the scanner input after the immutable tree has been selected.
publication_tool snapshot "$CLEAN_TREE" "$WORK/snapshot"
(
    cd "$WORK/snapshot"
    gitleaks dir --config "$WORK/snapshot/.gitleaks.toml" \
        --gitleaks-ignore-path "$WORK/snapshot" --redact --no-banner \
        --exit-code 1 --timeout 60 "$WORK/snapshot"
)
CLEAN_COMMIT="$(git commit-tree "$CLEAN_TREE" -m 'feat(release): bounded public projection')"
readonly CLEAN_COMMIT
# Convenience ref only; it is never used as the dispatch source.
git branch -f release/v5.0-clean "$CLEAN_COMMIT"
if [ "$DRY_RUN" -eq 1 ]; then
    echo "Preview scanned tree $CLEAN_TREE; local commit $CLEAN_COMMIT. Authorization/push NOT_CHECKED."
    exit 0
fi
FROZEN_EFFECT="$(publication_tool prepare "$CLEAN_COMMIT" "$CLEAN_TREE" "$TARGET_REMOTE" true \
    'Proyección Pública' BABYLON-60-PUBLIC "$WORK/effect.json")"
readonly FROZEN_EFFECT
publication_tool gate "$WORK/receipt.json" "${GATE[@]}"
publication_tool publish "$WORK/dispatch.git"
echo "Public projection dispatched and remote ref checked: $CLEAN_COMMIT"
