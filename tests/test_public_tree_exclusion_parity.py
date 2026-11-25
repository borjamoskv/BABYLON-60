"""The public source_tree_digest must be computable from both VAULT and its public projection.

`c5_distill_public_mirror.sh` strips paths with `git rm --cached`; `VAULT_ONLY_PREFIXES`
(copied in verify_claims.py, package_release.sh and verify_release.sh) removes the same
paths from the digest. If the two lists drift, VAULT evidence binds bytes the public
checkout does not have and verify_release.sh rejects it with
"Public source_tree_digest mismatch". Files the distill adds to the projection index
(`git update-index --add`) do not exist in VAULT, so they must stay out of the digest too.
"""

from __future__ import annotations

import ast
import os
import re
import shlex
import subprocess
from pathlib import Path

import pytest

from scripts.c5_quality_gates.verify_claims import (
    GENERATED_EVIDENCE,
    VAULT_ONLY_PREFIXES,
    is_excluded_from_public_tree,
    source_commit,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DISTILL_REL = "scripts/c5_git_utils/c5_distill_public_mirror.sh"
PREFIX_COPIES = (
    "scripts/c5_quality_gates/verify_claims.py",
    "scripts/package_release.sh",
    "scripts/verify_release.sh",
)
SHELL_OPERATORS = frozenset({";", "&&", "||", "|", "&", "(", ")"})
# The copies match with str.startswith, so they can only mirror literal pathspecs.
PATHSPEC_MAGIC = re.compile(r"[*?\[]|^:")
MUTATORS = r"(?:add|update|discard|remove|pop|clear|append|extend|insert)"


def _shell_commands(script_text: str, *keywords: str) -> list[tuple[str, list[str]]]:
    """Tokenize each logical shell line (continuations joined) whose tokens contain all keywords."""
    commands: list[tuple[str, list[str]]] = []
    for logical_line in script_text.replace("\\\n", " ").splitlines():
        if not all(keyword in logical_line for keyword in keywords):
            continue
        lexer = shlex.shlex(logical_line, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = "#"
        tokens = list(lexer)
        if all(keyword in tokens for keyword in keywords):
            commands.append((logical_line.strip(), tokens))
    return commands


def _git_invocations(tokens: list[str], subcommand: str) -> list[list[str]]:
    """Arguments of each plain `git <subcommand>` in a token list, up to the next shell operator."""
    invocations: list[list[str]] = []
    for start in (i for i in range(len(tokens) - 1) if tokens[i : i + 2] == ["git", subcommand]):
        args: list[str] = []
        for token in tokens[start + 2 :]:
            if token in SHELL_OPERATORS:
                break
            args.append(token)
        invocations.append(args)
    return invocations


def _distill_text() -> str:
    return (REPO_ROOT / DISTILL_REL).read_text(encoding="utf-8")


def _projection_added_paths(script_text: str) -> tuple[str, ...]:
    """Return every path a `git update-index` invocation adds to the projection index.

    Fails closed on what it cannot read: entries fed through stdin, non-literal paths,
    removals that bypass `git rm --cached` and unrecognised `update-index` forms.
    """
    paths: list[str] = []
    for line, tokens in _shell_commands(script_text, "update-index"):
        invocations = _git_invocations(tokens, "update-index")
        assert invocations, f"unrecognised `update-index` form, extend the parser: {line!r}"
        for args in invocations:
            assert not {"--index-info", "--stdin"} & set(args), f"index entries not on the command line: {args}"
            assert not {"--remove", "--force-remove"} & set(args), f"strip with `git rm --cached`: {args}"
            remaining = iter(args)
            for arg in remaining:
                if arg == "--cacheinfo":
                    value = next(remaining)
                    if value.count(",") == 2:
                        path = value.split(",", 2)[2]
                    else:  # --cacheinfo <mode> <object> <path>
                        next(remaining)
                        path = next(remaining)
                elif arg.startswith("-"):
                    continue
                else:
                    path = arg
                assert "$" not in path, f"projection path must be literal: {path!r}"
                paths.append(path.removeprefix("./"))
    return tuple(paths)


def _git_rm_cached_paths(script_text: str) -> tuple[str, ...]:
    """Return every pathspec passed to any `git rm --cached` invocation in a shell script.

    Fails closed on forms it cannot mirror: a `--cached` removal that is not a plain
    `git rm` (`git -C dir rm`, `"$GIT" rm`, `xargs`), `--pathspec-from-file` and globs.
    """
    paths: list[str] = []
    for line, tokens in _shell_commands(script_text, "rm", "--cached"):
        consumed = False
        for args in _git_invocations(tokens, "rm"):
            if "--cached" not in args:
                continue
            consumed = True
            assert any(not arg.startswith("-") for arg in args), f"pathspecs not on the command line: {args}"
            for arg in args:
                assert not arg.startswith("--pathspec-from-file"), f"unsupported pathspec source: {arg!r}"
                if arg.startswith("-"):
                    continue
                path = arg.removeprefix("./")
                assert not PATHSPEC_MAGIC.search(path), f"glob or pathspec magic cannot be mirrored: {path!r}"
                paths.append(path)
        assert consumed, f"unrecognised `rm --cached` form, extend the parser: {line!r}"
    return tuple(paths)


def _distill_stripped_paths() -> tuple[str, ...]:
    paths = _git_rm_cached_paths(_distill_text())
    assert paths, f"{DISTILL_REL}: no `git rm --cached` pathspecs found"
    return paths


def _literal_assignment(rel: str, name: str, closing: str) -> object:
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    bindings = re.findall(rf"^[ \t]*{name}[ \t]*(?::[^=\n]*)?[-+|&]?=(?!=)", text, re.MULTILINE)
    assert len(bindings) == 1, f"{rel}: expected exactly one binding of {name}, found {bindings}"
    mutations = re.findall(rf"\b{name}\.{MUTATORS}\(", text)
    assert mutations == [], f"{rel}: {name} is mutated after its literal: {mutations}"
    match = re.search(rf"^{name} = (.*?^{re.escape(closing)})", text, re.MULTILINE | re.DOTALL)
    assert match, f"{rel}: {name} literal not found at module level"
    return ast.literal_eval(match.group(1))


def _function_source(rel: str, name: str) -> str:
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    definitions = re.findall(rf"^[ \t]*def {name}\b", text, re.MULTILINE)
    rebindings = re.findall(rf"^[ \t]*{name}[ \t]*(?::[^=\n]*)?=(?!=)", text, re.MULTILINE)
    assert len(definitions) == 1 and rebindings == [], f"{rel}: {name} must be defined exactly once"
    match = re.search(rf"^def {name}\(.*?(?=^\S|\Z)", text, re.MULTILINE | re.DOTALL)
    assert match, f"{rel}: def {name} not found at module level"
    return match.group(0).strip()


def _removed_by_distill(relative: str, stripped: tuple[str, ...]) -> bool:
    return any(relative == path or relative.startswith(path.rstrip("/") + "/") for path in stripped)


def test_git_rm_cached_parser_follows_shell_syntax() -> None:
    script = (
        "trap 'rm -rf -- \"$WORK\"' EXIT\n"
        'GIT_INDEX_FILE="$WORK/index" git rm --cached -r -q --ignore-unmatch \\\n'
        "    first/dir \\\n"
        '    "quoted path" ./dotted second \\\n'
        "    last  # trailing comment\n"
        "git rm -r --cached -- later && echo done\n"
        "git rm unrelated\n"
        "echo 'git rm --cached inside a string'  # git rm --cached in a comment\n"
    )
    assert _git_rm_cached_paths(script) == ("first/dir", "quoted path", "dotted", "second", "last", "later")


@pytest.mark.parametrize(
    "line",
    [
        'git -C "$REPO" rm --cached private\n',
        '"$GIT" rm --cached private\n',
        "printf 'x' | xargs git rm --cached\n",
        "git rm --cached --pathspec-from-file=list.txt\n",
        "git rm --cached -r 'tests/test_private_*.py'\n",
        "git rm --cached ':(glob)tests/**'\n",
    ],
)
def test_git_rm_cached_parser_fails_closed_on_unmirrorable_forms(line: str) -> None:
    with pytest.raises(AssertionError):
        _git_rm_cached_paths(line)


def test_update_index_parser_reads_added_paths() -> None:
    script = (
        'MANIFEST_BLOB="$(printf x | git hash-object -w --stdin)"\n'
        'GIT_INDEX_FILE="$WORK/index" git update-index --add --cacheinfo \\\n'
        '    "100644,${MANIFEST_BLOB},.github/public_projection_manifest.json"\n'
        'git update-index --add --cacheinfo 100644 "$BLOB" ./NOTICE && echo done\n'
        "git update-index --refresh\n"
    )
    assert _projection_added_paths(script) == (".github/public_projection_manifest.json", "NOTICE")


@pytest.mark.parametrize(
    "line",
    [
        "printf 'x' | git update-index --add --index-info\n",
        "git update-index --add --stdin < list.txt\n",
        "git update-index --force-remove tests/test_private.py\n",
        'git update-index --add --cacheinfo "100644,$BLOB,$TARGET"\n',
        'git -C "$REPO" update-index --add --cacheinfo 100644,abc,NOTICE\n',
    ],
)
def test_update_index_parser_fails_closed(line: str) -> None:
    with pytest.raises(AssertionError):
        _projection_added_paths(line)


def test_files_added_to_the_projection_stay_out_of_the_digest() -> None:
    added = _projection_added_paths(_distill_text())
    bound = [path for path in added if not is_excluded_from_public_tree(path)]
    assert bound == [], (
        f"the projection adds {bound}, which VAULT does not have; exclude them from the digest "
        "(GENERATED_EVIDENCE in verify_claims.py, package_release.sh and verify_release.sh)"
    )


def test_exclusion_copies_are_identical() -> None:
    for rel in PREFIX_COPIES:
        assert _literal_assignment(rel, "VAULT_ONLY_PREFIXES", ")") == VAULT_ONLY_PREFIXES, rel
        assert _literal_assignment(rel, "GENERATED_EVIDENCE", "}") == GENERATED_EVIDENCE, rel
        assert _function_source(rel, "is_excluded_from_public_tree") == _function_source(
            PREFIX_COPIES[0], "is_excluded_from_public_tree"
        ), rel


def test_vault_only_prefixes_match_distill_strip_list() -> None:
    parsed = _distill_stripped_paths()
    stripped = {path.rstrip("/") for path in parsed}
    declared = {prefix.rstrip("/") for prefix in VAULT_ONLY_PREFIXES}
    assert declared - stripped == set(), f"excluded from the digest but published; distill strips {sorted(stripped)}"
    assert stripped - declared == set(), f"stripped by the projection but bound by the VAULT digest; parsed {parsed}"


def test_directory_prefixes_cannot_match_sibling_paths() -> None:
    for prefix in VAULT_ONLY_PREFIXES:
        if not prefix.endswith("/"):
            assert not (REPO_ROOT / prefix).is_dir(), f"directory prefix {prefix!r} needs a trailing '/'"


def test_tracked_files_hash_identically_in_vault_and_projection() -> None:
    try:
        result = subprocess.run(["git", "ls-files", "-z"], cwd=REPO_ROOT, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        pytest.skip(f"NOT_CHECKED: git ls-files unavailable: {exc}")
    stripped = _distill_stripped_paths()
    drift = sorted(
        relative
        for relative in (raw.decode("utf-8") for raw in result.stdout.split(b"\0") if raw)
        if relative not in GENERATED_EVIDENCE
        and _removed_by_distill(relative, stripped) != is_excluded_from_public_tree(relative)
    )
    assert drift == [], f"files whose digest membership differs between VAULT and projection: {drift}"


def test_editing_a_vault_only_test_still_marks_the_source_dirty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # An inherited GIT_DIR or GIT_INDEX_FILE (e.g. pytest run from a git hook) would point
    # these commands, and source_commit(), at another repository.
    for key in [key for key in os.environ if key.startswith("GIT_")]:
        monkeypatch.delenv(key)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    vault_test = next(prefix for prefix in VAULT_ONLY_PREFIXES if prefix.startswith("tests/"))
    files = {vault_test: "def test_x():\n    pass\n", "tools/skill_library/catalog.json": "{}\n"}
    for rel, content in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(content, encoding="utf-8")
    git = ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid"]
    git += ["-c", "commit.gpgsign=false", "-c", f"core.hooksPath={os.devnull}"]
    try:
        subprocess.run([*git, "init", "-q"], cwd=tmp_path, check=True)
    except OSError as exc:
        pytest.skip(f"NOT_CHECKED: git unavailable: {exc}")
    subprocess.run([*git, "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run([*git, "commit", "-q", "-m", "fixture"], cwd=tmp_path, check=True)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True).stdout.strip()

    (tmp_path / "tools/skill_library/catalog.json").write_text('{"edited": true}\n', encoding="utf-8")
    assert source_commit(tmp_path) == head, "edits to Vault-only library data stay exempt, as before"

    (tmp_path / vault_test).write_text("raise SystemExit('import-time side effect')\n", encoding="utf-8")
    assert source_commit(tmp_path).startswith(head + "+dirty:"), "VAULT claims import tests/, so edits taint evidence"
