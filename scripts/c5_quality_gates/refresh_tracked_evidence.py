#!/usr/bin/env python3
"""Refresh tracked release evidence so it stays valid across squash and rebase merges.

The tracked evidence (GENERATED_EVIDENCE in verify_claims.py) is a receipt: "the claim suites
passed on source commit C, whose source tree digest is D". The repository only merges by squash
or rebase, so after a merge C is not in main's history and main's tree may differ from D.

``--check`` reports, without touching anything, whether the evidence tracked at a ref is valid
for that ref's own tree (FRESH), stale (STALE), names a commit whose tree does not have the
recorded digest (FALSE_LABEL), or is inconsistent across files (INCONSISTENT).

The default mode regenerates the evidence in a dedicated clean worktree at the tip B of the
remote branch and creates a local branch ``evidence-refresh/<B12>`` with exactly one commit that
contains only GENERATED_EVIDENCE and cites B. If that commit is merged (squash or rebase) before
any other source change lands, main ends up with a tree whose digest is the recorded one and with
B as its parent. Nothing remote is touched unless ``--push`` (and ``--open-pr``) is given.

Exit codes: 0 fresh or refreshed, 1 generation or validation failure, 2 precondition not met,
3 not fresh (``--check``), 4 refreshed but the remote branch moved to a tree with other source.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import stat
import subprocess
import sys
import time
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

# Each commit's digest uses that commit's own exclusion rules, read literally (never executed).
RULES_SOURCE = "scripts/c5_quality_gates/verify_claims.py"
SUPPORTED_RULE = "relative in GENERATED_EVIDENCE or relative.startswith(VAULT_ONLY_PREFIXES)"

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_PRECONDITION = 2
EXIT_NOT_FRESH = 3
EXIT_BASE_MOVED = 4

EVIDENCE_FILES = (
    "evidence.json",
    "claims.lock",
    "RELEASE_MANIFEST.json",
    "scripts/c5_quality_gates/claims_sitrep.json",
)
# Digest exclusions are not write authorization: projection policy is never refreshable.
REFRESHABLE_ARTIFACTS = frozenset(
    (
        *EVIDENCE_FILES,
        "RELEASE_MANIFEST.json.sig",
        "RELEASE_MANIFEST.json.ots",
        "evidence.json.ots",
        "sbom.cargo.cdx.json",
        "sbom.python.cdx.json",
    )
)
SUPPORTED_MODES = {"100644", "100755", "120000"}
OBJECT_ID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
# Location variables could point git at another repository, index or object store.
KEPT_GIT_VARIABLES = {
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_NOSYSTEM",
    "GIT_CONFIG_SYSTEM",
    "GIT_AUTHOR_NAME",
    "GIT_AUTHOR_EMAIL",
    "GIT_COMMITTER_NAME",
    "GIT_COMMITTER_EMAIL",
    "GIT_TERMINAL_PROMPT",
    "GIT_SSH_COMMAND",
    "GIT_ASKPASS",
}
DEFAULT_GENERATOR = (
    "uv sync --locked --extra dev --extra gemini",
    "cargo test --locked --no-run",
    "cargo test --locked --no-run --features cortex-persist,cortex-telemetry",
    "uv run --locked --no-sync python scripts/c5_quality_gates/verify_claims.py",
    "uv run --locked --no-sync python scripts/c5_quality_gates/compile_claims_manifest.py",
)
DEFAULT_VERIFY = "bash verify.sh"
LOCK_NAME = "evidence-refresh.lock"
LOG_NAME = "evidence-refresh.log"


class RefreshError(Exception):
    """A failure with an exit code and a message meant for the operator."""

    def __init__(self, message: str, code: int = EXIT_FAILURE) -> None:
        super().__init__(message)
        self.code = code


class RulesUnavailable(RefreshError):
    """A commit does not carry exclusion rules this tool can read without executing code."""


class UnsupportedTree(RefreshError):
    """A commit holds entries (gitlinks, non-UTF-8 paths) the source digest cannot represent."""


class ObjectsUnavailable(RefreshError):
    """Objects needed for a digest are absent from a partial clone."""


def git_environment() -> Dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_") or key in KEPT_GIT_VARIABLES}
    # Local grafts would fabricate history; replace refs are disabled per command.
    env["GIT_GRAFT_FILE"] = os.devnull
    # The variable, unlike the --no-lazy-fetch option (git >= 2.44), is ignored by older git.
    env["GIT_NO_LAZY_FETCH"] = "1"
    return env


def git(
    repo: Path, *args: str, stdin: Optional[bytes] = None, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    command = ["git", "--no-replace-objects", "-C", str(repo), *args]
    try:
        done = subprocess.run(command, input=stdin, capture_output=True, env=git_environment())
    except OSError as error:
        raise RefreshError(f"git is not available: {error}", EXIT_PRECONDITION) from error
    if check and done.returncode != 0:
        stderr = done.stderr.decode("utf-8", "replace").strip()
        raise RefreshError(f"git {' '.join(args[:3])} failed: {stderr or f'exit {done.returncode}'}")
    return done


def git_text(repo: Path, *args: str) -> str:
    return git(repo, *args).stdout.decode("utf-8", "replace").strip()


def resolve_commit(repo: Path, ref: str) -> str:
    """Resolve a revision once, before addressing objects by their complete IDs."""
    resolved = git_text(repo, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}")
    if not OBJECT_ID.fullmatch(resolved):
        raise RefreshError(f"revision did not resolve to a full object ID: {ref!r}")
    return resolved


def object_kind(repo: Path, object_id: str) -> Optional[str]:
    """Return the object type, or None when the object is absent from this repository."""
    done = git(repo, "cat-file", "--batch-check", stdin=object_id.encode("ascii") + b"\n")
    fields = done.stdout.decode("ascii", "replace").split()
    if len(fields) == 2 and fields[1] == "missing":
        return None
    if len(fields) != 3 or fields[0] != object_id:
        raise RefreshError(f"unexpected cat-file answer for {object_id}: {fields}")
    return fields[1]


class ObjectStore:
    """Reads objects with ``git cat-file --batch`` and re-hashes each one: git does not verify on read."""

    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self.algorithm = git_text(repo, "rev-parse", "--show-object-format")
        if self.algorithm not in {"sha1", "sha256"}:
            raise RefreshError(f"unsupported object format {self.algorithm!r}")
        self.id_bytes = 20 if self.algorithm == "sha1" else 32

    def read(self, object_ids: Sequence[str]) -> Dict[str, Tuple[str, bytes]]:
        unique = list(dict.fromkeys(object_ids))
        if not unique:
            return {}
        if any(not OBJECT_ID.fullmatch(oid) or len(oid) != self.id_bytes * 2 for oid in unique):
            raise RefreshError("object reader requires full canonical object IDs")
        stream = git(self.repo, "cat-file", "--batch", stdin=b"".join(oid.encode("ascii") + b"\n" for oid in unique))
        output = stream.stdout
        position = 0
        objects: Dict[str, Tuple[str, bytes]] = {}
        missing: List[str] = []
        for object_id in unique:
            header_end = output.index(b"\n", position)
            header = output[position:header_end].decode("ascii", "replace").split(" ")
            position = header_end + 1
            if header == [object_id, "missing"]:
                missing.append(object_id)
                continue
            if len(header) != 3 or header[0] != object_id:
                raise RefreshError(f"unexpected cat-file header {header} for {object_id}")
            kind, size = header[1], int(header[2])
            payload = output[position : position + size]
            if len(payload) != size:
                raise RefreshError(f"truncated object {object_id}")
            position += size + 1
            actual = hashlib.new(self.algorithm, f"{kind} {size}".encode("ascii") + b"\0" + payload).hexdigest()
            if actual != object_id:
                raise RefreshError(f"object store is corrupt or tampered: {object_id} hashes to {actual}")
            objects[object_id] = (kind, payload)
        if missing:
            listed = ", ".join(object_id[:12] for object_id in missing[:5])
            if self.partial_clone():
                raise ObjectsUnavailable(f"objects absent from this partial clone: {listed}")
            raise RefreshError(f"objects missing from a repository that is not a partial clone: {listed}")
        return objects

    def partial_clone(self) -> bool:
        pattern = r"^(extensions\.partialclone|remote\..*\.promisor)$"
        done = git(self.repo, "config", "--get-regexp", pattern, check=False)
        for line in done.stdout.decode("utf-8", "replace").splitlines():
            key, _, value = line.partition(" ")
            if key == "extensions.partialclone" and value.strip():
                return True
            if key.endswith(".promisor") and value.strip().lower() in {"true", "yes", "on", "1"}:
                return True
        return False

    def tree_entries(self, payload: bytes) -> List[Tuple[bytes, bytes, str]]:
        entries: List[Tuple[bytes, bytes, str]] = []
        position = 0
        while position < len(payload):
            space = payload.index(b" ", position)
            nul = payload.index(b"\0", space)
            raw_id = payload[nul + 1 : nul + 1 + self.id_bytes]
            if len(raw_id) != self.id_bytes:
                raise RefreshError("truncated tree entry")
            entries.append((payload[position:space], payload[space + 1 : nul], raw_id.hex()))
            position = nul + 1 + self.id_bytes
        return entries

    def tree_of(self, commit: str) -> str:
        kind, payload = self.read([commit])[commit]
        if kind != "commit":
            raise RefreshError(f"{commit[:12]} is a {kind}, not a commit")
        first_line = payload.split(b"\n", 1)[0]
        if not first_line.startswith(b"tree "):
            raise RefreshError(f"commit {commit[:12]} has no tree line")
        return first_line[5:].decode("ascii")

    def blob_at(self, commit: str, path: str) -> Optional[bytes]:
        """Regular file contents at ``path`` in ``commit``, read through verified objects only."""
        current = self.tree_of(commit)
        parts = path.split("/")
        for index, part in enumerate(parts):
            kind, payload = self.read([current])[current]
            if kind != "tree":
                raise RefreshError(f"{current[:12]} is a {kind}, not a tree")
            found = [entry for entry in self.tree_entries(payload) if entry[1] == part.encode("utf-8")]
            if not found:
                return None
            mode, _name, child = found[0]
            if index == len(parts) - 1:
                if mode not in {b"100644", b"100755"}:
                    return None
                kind, data = self.read([child])[child]
                return data if kind == "blob" else None
            if mode != b"40000":
                return None
            current = child
        return None


def normalize_symlink(payload: bytes, raw_path: bytes) -> bytes:
    """verify_claims hashes str(Path.readlink()), which drops "./", trailing and doubled slashes."""
    try:
        target = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise UnsupportedTree(f"symlink target is not UTF-8: {raw_path!r}") from error
    return str(PurePosixPath(target)).encode("utf-8")


@dataclass(frozen=True)
class ExclusionRules:
    generated: FrozenSet[str]
    prefixes: Tuple[str, ...]

    def excludes(self, relative: str) -> bool:
        return relative in self.generated or relative.startswith(self.prefixes)

    def excludes_directory(self, relative: str) -> bool:
        """Every path under the directory starts with an excluded prefix, so it need not be read."""
        return (relative + "/").startswith(self.prefixes)


def parse_exclusion_rules(source: bytes, origin: str) -> ExclusionRules:
    """Read GENERATED_EVIDENCE and VAULT_ONLY_PREFIXES from verify_claims.py source as literals."""
    try:
        module = ast.parse(source.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as error:
        raise RulesUnavailable(f"cannot parse {RULES_SOURCE} at {origin}: {error}") from error
    values: Dict[str, object] = {}
    rule_supported = False
    expected = ast.dump(ast.parse(SUPPORTED_RULE, mode="eval").body)
    for node in module.body:
        target: Optional[ast.expr] = None
        value: Optional[ast.expr] = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            target, value = node.target, node.value
        if isinstance(target, ast.Name) and target.id in {"GENERATED_EVIDENCE", "VAULT_ONLY_PREFIXES"} and value:
            try:
                values[target.id] = ast.literal_eval(value)
            except ValueError as error:
                raise RulesUnavailable(f"{target.id} at {origin} is not a literal") from error
        if isinstance(node, ast.FunctionDef) and node.name == "is_excluded_from_public_tree":
            body = [
                statement
                for statement in node.body
                if not (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant))
            ]
            rule_supported = (
                len(body) == 1
                and isinstance(body[0], ast.Return)
                and body[0].value is not None
                and ast.dump(body[0].value) == expected
            )
    generated = values.get("GENERATED_EVIDENCE")
    prefixes = values.get("VAULT_ONLY_PREFIXES")
    if not isinstance(generated, (set, frozenset)) or not all(isinstance(item, str) for item in generated):
        raise RulesUnavailable(f"GENERATED_EVIDENCE at {origin} is not a set of strings")
    if not isinstance(prefixes, tuple) or not all(isinstance(item, str) for item in prefixes):
        raise RulesUnavailable(f"VAULT_ONLY_PREFIXES at {origin} is not a tuple of strings")
    if not rule_supported:
        raise RulesUnavailable(f"is_excluded_from_public_tree at {origin} is not `{SUPPORTED_RULE}`")
    return ExclusionRules(frozenset(generated), prefixes)


def rules_at(repo: Path, commit: str, store: Optional[ObjectStore] = None) -> ExclusionRules:
    commit = resolve_commit(repo, commit)
    source = (store or ObjectStore(repo)).blob_at(commit, RULES_SOURCE)
    if source is None:
        raise RulesUnavailable(f"{RULES_SOURCE} is not tracked at {commit[:12]}; its exclusion rules are unknown")
    return parse_exclusion_rules(source, commit[:12])


def commit_tree_digest(
    repo: Path, commit: str, rules: Optional[ExclusionRules] = None, store: Optional[ObjectStore] = None
) -> str:
    """verify_claims.source_tree_digest of ``commit``, computed from re-hashed git objects instead of a checkout."""
    commit = resolve_commit(repo, commit)
    store = store or ObjectStore(repo)
    rules = rules if rules is not None else rules_at(repo, commit, store)
    level: List[Tuple[bytes, str]] = [(b"", store.tree_of(commit))]
    files: List[Tuple[bytes, str, bytes]] = []
    while level:
        trees = store.read([object_id for _, object_id in level])
        following: List[Tuple[bytes, str]] = []
        for prefix, object_id in level:
            kind, payload = trees[object_id]
            if kind != "tree":
                raise RefreshError(f"{object_id[:12]} is a {kind}, not a tree")
            for mode, name, child in store.tree_entries(payload):
                raw_path = prefix + name
                try:
                    relative = raw_path.decode("utf-8")
                except UnicodeDecodeError as error:
                    raise UnsupportedTree(f"tree path is not UTF-8 in {commit}: {raw_path!r}") from error
                if mode == b"40000":
                    if not rules.excludes_directory(relative):
                        following.append((raw_path + b"/", child))
                    continue
                if rules.excludes(relative):
                    continue
                if mode.decode("ascii", "replace") not in SUPPORTED_MODES:
                    raise UnsupportedTree(
                        f"unsupported tree entry for the source digest in {commit}: {relative} {mode.decode()}"
                    )
                files.append((raw_path, child, mode))
        level = following
    files.sort(key=lambda entry: entry[0])
    blobs = store.read([object_id for _, object_id, _ in files])
    digest = hashlib.sha256()
    for raw_path, object_id, mode in files:
        kind, payload = blobs[object_id]
        if kind != "blob":
            raise RefreshError(f"{raw_path!r} points at a {kind}, not a blob")
        if mode == b"120000":
            payload = normalize_symlink(payload, raw_path)
        digest.update(raw_path + b"\0")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


@dataclass
class EvidenceBinding:
    commit: str
    tree_digest: str


@dataclass
class Assessment:
    ref: str
    ref_commit: str
    ref_digest: str
    status: str
    binding: Optional[EvidenceBinding] = None
    label: str = "NOT_CHECKED"
    details: List[str] = field(default_factory=list)

    @property
    def fresh(self) -> bool:
        return self.status == "FRESH"


def _binding_from_documents(documents: Dict[str, dict[str, object]]) -> Tuple[Optional[EvidenceBinding], List[str]]:
    problems: List[str] = []
    commits = {
        "evidence.json": documents["evidence.json"].get("source_commit"),
        "claims.lock": documents["claims.lock"].get("commit"),
        "RELEASE_MANIFEST.json": documents["RELEASE_MANIFEST.json"].get("commit"),
        "scripts/c5_quality_gates/claims_sitrep.json": documents["scripts/c5_quality_gates/claims_sitrep.json"].get(
            "source_commit"
        ),
    }
    digests = {name: documents[name].get("source_tree_digest") for name in EVIDENCE_FILES}
    commit = commits["evidence.json"]
    tree_digest = digests["evidence.json"]
    if not isinstance(commit, str) or not isinstance(tree_digest, str):
        return None, ["source commit and source tree digest must be strings"]
    if any(not isinstance(value, str) or value != commit for value in commits.values()):
        problems.append(f"cited commits differ across files: {commits}")
    if any(not isinstance(value, str) or value != tree_digest for value in digests.values()):
        problems.append(f"source tree digests differ across files: {digests}")
    if not OBJECT_ID.fullmatch(commit):
        problems.append(f"cited commit is not a full lowercase object id: {commit!r}")
    if not re.fullmatch(r"[0-9a-f]{64}", tree_digest):
        problems.append(f"recorded source tree digest is malformed: {tree_digest!r}")
    if problems:
        return None, problems
    return EvidenceBinding(commit, tree_digest), problems


def read_binding_at(repo: Path, ref_commit: str) -> Tuple[Optional[EvidenceBinding], List[str]]:
    documents: Dict[str, dict[str, object]] = {}
    for name in EVIDENCE_FILES:
        shown = git(repo, "cat-file", "blob", f"{ref_commit}:{name}", check=False)
        if shown.returncode != 0:
            return None, [f"{name} is not tracked at {ref_commit[:12]}"]
        try:
            document = json.loads(shown.stdout.decode("utf-8"))
            if not isinstance(document, dict):
                return None, [f"{name} at {ref_commit[:12]} is not a JSON object"]
            documents[name] = document
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            return None, [f"{name} at {ref_commit[:12]} is not valid JSON: {error}"]
    return _binding_from_documents(documents)


def read_binding_from_files(root: Path) -> Tuple[Optional[EvidenceBinding], List[str]]:
    documents: Dict[str, dict[str, object]] = {}
    open_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    for name in EVIDENCE_FILES:
        path = root / name
        try:
            fd = os.open(path, open_flags)
        except OSError:
            return None, [f"{name} was not produced as a regular file"]
        try:
            with os.fdopen(fd, "r", encoding="utf-8") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    return None, [f"{name} was not produced as a regular file"]
                raw = stream.read()
            document = json.loads(raw)
            if not isinstance(document, dict):
                return None, [f"{name} is not a JSON object"]
            documents[name] = document
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            return None, [f"{name} is not valid JSON: {error}"]
    return _binding_from_documents(documents)


def assess(repo: Path, ref: str) -> Assessment:
    ref_commit = resolve_commit(repo, ref)
    store = ObjectStore(repo)
    ref_digest = commit_tree_digest(repo, ref_commit, store=store)
    binding, problems = read_binding_at(repo, ref_commit)
    if binding is None:
        status = "MISSING" if any("is not tracked" in problem for problem in problems) else "INCONSISTENT"
        return Assessment(ref, ref_commit, ref_digest, status, details=problems)
    assessment = Assessment(ref, ref_commit, ref_digest, "STALE", binding)
    kind = object_kind(repo, binding.commit)
    if kind is None:
        assessment.label = "NOT_CHECKED"
        assessment.details.append(f"cited commit {binding.commit[:12]} is not available here; label unverifiable")
    elif kind != "commit":
        assessment.label = "FAIL"
        assessment.status = "FALSE_LABEL"
        assessment.details.append(f"cited object {binding.commit[:12]} is a {kind}, not a commit")
        return assessment
    else:
        try:
            cited_rules = rules_at(repo, binding.commit, store)
            cited_digest: Optional[str] = commit_tree_digest(repo, binding.commit, cited_rules, store)
        except (RulesUnavailable, ObjectsUnavailable) as error:
            assessment.label = "NOT_CHECKED"
            assessment.details.append(f"label unverifiable: {error}")
            cited_digest = None
        except UnsupportedTree as error:
            assessment.label = "FAIL"
            assessment.status = "FALSE_LABEL"
            assessment.details.append(f"cited commit cannot carry a source digest: {error}")
            return assessment
        if cited_digest is not None and cited_digest != binding.tree_digest:
            assessment.label = "FAIL"
            assessment.status = "FALSE_LABEL"
            assessment.details.append(
                f"evidence names {binding.commit[:12]} but its tree digest is {cited_digest[:16]}…, "
                f"not the recorded {binding.tree_digest[:16]}…"
            )
            return assessment
        if cited_digest is not None:
            assessment.label = "PASS"
    if ref_digest == binding.tree_digest:
        assessment.status = "FRESH"
    else:
        assessment.details.append(
            f"tree of {ref_commit[:12]} has digest {ref_digest[:16]}…; evidence was produced for "
            f"{binding.tree_digest[:16]}… ({binding.commit[:12]})"
        )
    return assessment


def print_assessment(assessment: Assessment) -> None:
    print(f"[EVIDENCE] {assessment.ref} = {assessment.ref_commit[:12]}: {assessment.status}")
    if assessment.binding is not None:
        print(f"  cited commit : {assessment.binding.commit}")
        print(f"  recorded tree: {assessment.binding.tree_digest}")
    print(f"  ref tree     : {assessment.ref_digest}")
    print(f"  label        : {assessment.label}")
    for detail in assessment.details:
        print(f"  - {detail}")


def remote_tip(repo: Path, remote: str, branch: str, fetch: bool) -> str:
    if fetch:
        git(repo, "fetch", "--no-tags", remote, f"+refs/heads/{branch}:refs/remotes/{remote}/{branch}")
    resolved = git(repo, "rev-parse", "--verify", "--quiet", f"refs/remotes/{remote}/{branch}^{{commit}}", check=False)
    if resolved.returncode != 0:
        raise RefreshError(f"refs/remotes/{remote}/{branch} does not resolve; fetch it first", EXIT_PRECONDITION)
    return resolved.stdout.decode("ascii").strip()


def porcelain_paths(worktree: Path) -> List[str]:
    """Every changed, deleted or untracked path (not ignored ones) relative to the worktree root."""
    done = git(worktree, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames")
    paths: List[str] = []
    for record in done.stdout.split(b"\0"):
        if not record:
            continue
        paths.append(record[3:].decode("utf-8", "replace"))
    return sorted(set(paths))


def restore_generated(worktree: Path, generated: FrozenSet[str]) -> None:
    """Undo whatever the generator wrote to GENERATED_EVIDENCE; never touches other paths."""
    for relative in porcelain_paths(worktree):
        if relative not in generated:
            continue
        tracked = git(worktree, "ls-files", "--error-unmatch", "--", relative, check=False).returncode == 0
        if tracked:
            git(worktree, "checkout", "--", relative)
        else:
            (worktree / relative).unlink(missing_ok=True)


@dataclass
class WorktreeLock:
    path: Path

    def acquire(self) -> None:
        for _attempt in range(2):
            try:
                descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                if self._holder_is_dead():
                    self.path.unlink(missing_ok=True)
                    print(f"[WARN] removed stale lock {self.path}")
                    continue
                raise RefreshError(
                    f"another refresh holds {self.path}; if none is running, delete the file", EXIT_PRECONDITION
                )
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(f"{os.getpid()} {int(time.time())}\n")
            return
        raise RefreshError(f"could not acquire {self.path}", EXIT_PRECONDITION)

    def _holder_is_dead(self) -> bool:
        try:
            pid = int(self.path.read_text(encoding="utf-8").split()[0])
        except (OSError, ValueError, IndexError):
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        return False

    def release(self) -> None:
        self.path.unlink(missing_ok=True)


def prepare_worktree(repo: Path, worktree: Path, base: str) -> None:
    invoking_root = Path(git_text(repo, "rev-parse", "--show-toplevel")).resolve()
    common_dir = Path(git_text(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
    if worktree.resolve() == invoking_root:
        raise RefreshError("refusing to use the invoking checkout as the refresh worktree", EXIT_PRECONDITION)
    if not worktree.exists():
        git(repo, "worktree", "add", "--detach", str(worktree), base)
        return
    if not worktree.is_dir():
        raise RefreshError(f"{worktree} exists and is not a directory", EXIT_PRECONDITION)
    probe = git(worktree, "rev-parse", "--path-format=absolute", "--git-common-dir", check=False)
    if probe.returncode != 0 or Path(probe.stdout.decode("utf-8").strip()).resolve() != common_dir:
        raise RefreshError(f"{worktree} is not a worktree of this repository", EXIT_PRECONDITION)
    toplevel = Path(git_text(worktree, "rev-parse", "--show-toplevel")).resolve()
    if toplevel != worktree.resolve():
        raise RefreshError(f"{worktree} is inside another worktree ({toplevel})", EXIT_PRECONDITION)
    dirty = porcelain_paths(worktree)
    if dirty:
        listed = ", ".join(dirty[:10]) + (f" (+{len(dirty) - 10} more)" if len(dirty) > 10 else "")
        raise RefreshError(f"refresh worktree {worktree} is not clean: {listed}", EXIT_PRECONDITION)
    git(worktree, "checkout", "--quiet", "--detach", base)


def run_steps(steps: Sequence[str], cwd: Path, log_path: Path, label: str) -> None:
    env = git_environment()
    with log_path.open("a", encoding="utf-8") as log:
        for step in steps:
            argv = shlex.split(step)
            log.write(f"\n=== {label}: {step} ({time.strftime('%Y-%m-%dT%H:%M:%S')})\n")
            log.flush()
            try:
                done = subprocess.run(argv, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
            except OSError as error:
                raise RefreshError(f"{label} step could not start ({step}): {error}") from error
            if done.returncode != 0:
                raise RefreshError(f"{label} step failed with exit {done.returncode}: {step} (log: {log_path})")


def validate_outputs(worktree: Path, base: str, base_digest: str, generated: FrozenSet[str]) -> EvidenceBinding:
    changed = porcelain_paths(worktree)
    outside = [path for path in changed if path not in generated]
    if outside:
        listed = ", ".join(outside[:10]) + (f" (+{len(outside) - 10} more)" if len(outside) > 10 else "")
        raise RefreshError(f"the generator changed files outside GENERATED_EVIDENCE: {listed}")
    if not changed:
        raise RefreshError("the generator did not change any evidence file")
    binding, problems = read_binding_from_files(worktree)
    if binding is None:
        raise RefreshError("generated evidence is inconsistent: " + "; ".join(problems))
    if binding.commit != base:
        raise RefreshError(f"generated evidence cites {binding.commit}, not the base {base}")
    if binding.tree_digest != base_digest:
        raise RefreshError(
            f"generated evidence records tree {binding.tree_digest}, but the base tree digest is {base_digest}"
        )
    return binding


def commit_message(base: str, binding: EvidenceBinding, trailers: Sequence[str]) -> str:
    lines = [
        f"[AX-0] EVIDENCE: refrescar evidencia rastreada sobre {base[:12]}",
        "",
        f"Generada por scripts/c5_quality_gates/refresh_tracked_evidence.py en un worktree limpio en {base}.",
        "Este commit solo contiene archivos de GENERATED_EVIDENCE y cita la base"
        f" (source_tree_digest {binding.tree_digest[:16]}…).",
        "Fusionarlo antes que cualquier otro cambio de fuente; si la rama base avanza, volver a ejecutar.",
    ]
    if trailers:
        lines.append("")
        lines.extend(trailers)
    return "\n".join(lines) + "\n"


def refresh(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    common_dir = Path(git_text(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
    worktree = Path(args.worktree).resolve() if args.worktree else common_dir.parent / ".worktrees" / "evidence-refresh"
    base = remote_tip(repo, args.remote, args.branch, fetch=not args.no_fetch)
    before = assess(repo, base)
    print_assessment(before)
    if before.fresh and not args.force:
        print("[OK] tracked evidence is already fresh for the base; nothing to do")
        return EXIT_OK
    base_digest = before.ref_digest
    generated = rules_at(repo, base).generated & REFRESHABLE_ARTIFACTS
    prepare_worktree(repo, worktree, base)
    worktree_git_dir = Path(git_text(worktree, "rev-parse", "--path-format=absolute", "--git-dir"))
    lock = WorktreeLock(worktree_git_dir / LOCK_NAME)
    lock.acquire()
    try:
        log_path = worktree_git_dir / LOG_NAME
        print(f"[RUN] regenerating evidence in {worktree} at {base[:12]} (log: {log_path})")
        try:
            run_steps(args.generator or DEFAULT_GENERATOR, worktree, log_path, "generator")
            binding = validate_outputs(worktree, base, base_digest, generated)
            if not args.no_verify:
                run_steps([args.verify_cmd], worktree, log_path, "verify")
                binding = validate_outputs(worktree, base, base_digest, generated)
        except RefreshError:
            restore_generated(worktree, generated)
            raise
        branch = f"evidence-refresh/{base[:12]}"
        git(worktree, "switch", "--quiet", "-C", branch)
        changed = porcelain_paths(worktree)
        git(worktree, "add", "--all", "--", *changed)
        staged = git_text(worktree, "diff", "--cached", "--name-only", "--no-renames").splitlines()
        if not staged or any(path not in generated for path in staged):
            raise RefreshError(f"refusing to commit an unexpected staged set: {staged}")
        git(worktree, "commit", "--quiet", "-m", commit_message(base, binding, args.trailer))
        evidence_commit = git_text(worktree, "rev-parse", "HEAD")
    finally:
        lock.release()
    after = assess(repo, evidence_commit)
    if not after.fresh or after.label != "PASS":
        raise RefreshError(f"the evidence commit does not verify: {after.status} / label {after.label}")
    print(f"[OK] {branch} = {evidence_commit[:12]} cites {base[:12]} ({len(staged)} generated files)")
    code = EXIT_OK
    if not args.no_fetch:
        tip = remote_tip(repo, args.remote, args.branch, fetch=True)
        if tip != base and commit_tree_digest(repo, tip) != base_digest:
            print(
                f"[WARN] {args.remote}/{args.branch} moved to {tip[:12]} with other source changes during the "
                "refresh: this evidence is valid only if merged before them; run again otherwise"
            )
            code = EXIT_BASE_MOVED
    if args.push:
        if code != EXIT_OK:
            print("[FAIL] refusing to push stale evidence", file=sys.stderr)
            return code
        git(worktree, "push", "--set-upstream", args.remote, branch)
        print(f"[OK] pushed {branch} to {args.remote}")
        if args.open_pr:
            body = (
                f"Evidencia rastreada regenerada sobre `{base}` con "
                "`scripts/c5_quality_gates/refresh_tracked_evidence.py`. Solo cambia GENERATED_EVIDENCE.\n\n"
                "Fusionar antes que cualquier otro cambio de fuente para que siga siendo válida.\n"
            )
            created = subprocess.run(
                [
                    "gh",
                    "pr",
                    "create",
                    "--base",
                    args.branch,
                    "--head",
                    branch,
                    "--title",
                    f"[AX-0] EVIDENCE: refrescar evidencia rastreada sobre {base[:12]}",
                    "--body",
                    body,
                ],
                cwd=worktree,
                env=git_environment(),
            )
            if created.returncode != 0:
                raise RefreshError("gh pr create failed; the branch is pushed, open the PR by hand")
    else:
        print("Next steps (not run):")
        print(f"  git -C {shlex.quote(str(worktree))} push --set-upstream {args.remote} {branch}")
        print(f"  gh pr create --base {args.branch} --head {branch}")
    return code


def check(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    if args.ref is None:
        assessment = assess(repo, remote_tip(repo, args.remote, args.branch, fetch=args.fetch))
        assessment.ref = f"{args.remote}/{args.branch}"
    else:
        assessment = assess(repo, args.ref)
    print_assessment(assessment)
    return EXIT_OK if assessment.fresh else EXIT_NOT_FRESH


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--repo", default=".", help="repository to operate on (default: current directory)")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--check", action="store_true", help="only report whether evidence at REF is fresh")
    parser.add_argument("ref", nargs="?", help="with --check: ref to assess (default: <remote>/<branch>)")
    parser.add_argument("--fetch", action="store_true", help="with --check: fetch the remote branch first")
    parser.add_argument("--no-fetch", action="store_true", help="refresh from the current remote-tracking ref")
    parser.add_argument("--worktree", help="dedicated worktree (default: <repo>/.worktrees/evidence-refresh)")
    parser.add_argument(
        "--generator", action="append", help="generator step, repeatable (default: claims run + compile)"
    )
    parser.add_argument(
        "--verify-cmd", default=DEFAULT_VERIFY, help=f"verification command (default: {DEFAULT_VERIFY})"
    )
    parser.add_argument("--no-verify", action="store_true", help="skip the verification command")
    parser.add_argument("--force", action="store_true", help="refresh even if the evidence is already fresh")
    parser.add_argument("--trailer", action="append", default=[], help="extra commit message trailer line")
    parser.add_argument("--push", action="store_true", help="push the evidence branch (never force)")
    parser.add_argument("--open-pr", action="store_true", help="with --push: open a pull request with gh")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.open_pr and not args.push:
        print("[FAIL] --open-pr requires --push", file=sys.stderr)
        return EXIT_PRECONDITION
    if args.push and (args.no_fetch or args.no_verify or args.generator or args.verify_cmd != DEFAULT_VERIFY):
        print(
            "[FAIL] --push requires a fetched base and the default generation and verification commands", file=sys.stderr
        )
        return EXIT_PRECONDITION
    if args.ref is not None and not args.check:
        print("[FAIL] a ref argument is only valid with --check", file=sys.stderr)
        return EXIT_PRECONDITION
    try:
        return check(args) if args.check else refresh(args)
    except RefreshError as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return error.code


if __name__ == "__main__":
    raise SystemExit(main())
