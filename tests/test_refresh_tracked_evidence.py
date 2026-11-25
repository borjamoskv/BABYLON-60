"""refresh_tracked_evidence: squash-safe freshness checks and the evidence refresh flow.

Every test builds throwaway git repositories (a bare remote plus a clone) and injects a tiny real
generator that writes the four evidence files with the real object-based tree digest. Nothing runs
the 10-minute claim suites and nothing is mocked.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import textwrap

import pytest

from scripts.c5_quality_gates import refresh_tracked_evidence as tool
from scripts.c5_quality_gates.verify_claims import GENERATED_EVIDENCE, source_tree_digest

REPO_ROOT = Path(__file__).resolve().parents[1]

GENERATOR = textwrap.dedent(
    """
    import json, pathlib, subprocess, sys, time
    sys.path.insert(0, {root!r})
    from scripts.c5_quality_gates.refresh_tracked_evidence import commit_tree_digest

    mode = sys.argv[1] if len(sys.argv) > 1 else "ok"
    cwd = pathlib.Path.cwd()
    if mode == "move-remote":
        mover = pathlib.Path(sys.argv[2])
        (mover / "src" / "moved.py").write_text("MOVED = True\\n")
        subprocess.run(["git", "-C", str(mover), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(mover), "commit", "-q", "-m", "move"], check=True)
        subprocess.run(["git", "-C", str(mover), "push", "-q", "origin", "HEAD:main"], check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd, text=True).strip()
    digest = commit_tree_digest(cwd, head)
    documents = {{
        "evidence.json": {{"source_commit": head, "source_tree_digest": digest, "run": time.time()}},
        "claims.lock": {{"commit": head, "source_tree_digest": digest}},
        "RELEASE_MANIFEST.json": {{"commit": head, "source_tree_digest": digest}},
        "scripts/c5_quality_gates/claims_sitrep.json": {{"source_commit": head, "source_tree_digest": digest}},
    }}
    for name, document in documents.items():
        path = cwd / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document, indent=2) + "\\n")
    if mode == "touch-source":
        (cwd / "src" / "app.py").write_text("TOUCHED = True\\n")
    if mode == "fail":
        (cwd / "RELEASE_MANIFEST.json.sig").write_text("partial\\n")
        sys.exit(1)
    """
).format(root=str(REPO_ROOT))


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def isolated_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    config = tmp_path / "gitconfig"
    hooks = tmp_path / "no-hooks"
    hooks.mkdir()
    config.write_text(
        "[user]\n\tname = Test\n\temail = test@example.invalid\n"
        "[init]\n\tdefaultBranch = main\n[commit]\n\tgpgsign = false\n"
        f"[core]\n\thooksPath = {hooks}\n"
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    return tmp_path


@pytest.fixture
def project(isolated_git: Path) -> dict[str, Path]:
    """A bare remote and a clone whose main holds sources, a symlink, an executable and a vault-only file."""
    remote = isolated_git / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    work = isolated_git / "work"
    subprocess.run(["git", "clone", "-q", str(remote), str(work)], check=True, capture_output=True)
    (work / "src").mkdir()
    (work / "src" / "app.py").write_text("VALUE = 1\n")
    (work / "README.md").write_text("readme\n")
    os.symlink("README.md", work / "LINK.md")
    (work / "bin").mkdir()
    (work / "bin" / "run.sh").write_text("#!/bin/sh\necho run\n")
    (work / "bin" / "run.sh").chmod(0o755)
    (work / "docs" / "security" / "evidence").mkdir(parents=True)
    (work / "docs" / "security" / "evidence" / "vault-only.txt").write_text("vault\n")
    # The digest of each commit follows the exclusion rules that commit carries.
    (work / tool.RULES_SOURCE).parent.mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / tool.RULES_SOURCE, work / tool.RULES_SOURCE)
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "S0")
    git(work, "push", "-q", "origin", "HEAD:main")
    generator = isolated_git / "gen.py"
    generator.write_text(GENERATOR)
    return {"root": isolated_git, "remote": remote, "work": work, "generator": generator}


def generator_step(project: dict[str, Path], *mode: str) -> str:
    return " ".join(shlex.quote(part) for part in (sys.executable, str(project["generator"]), *mode))


def commit_evidence_on_main(project: dict[str, Path]) -> str:
    """Produce evidence for the current HEAD of the clone with the generator and push it to main."""
    work = project["work"]
    subprocess.run(shlex.split(generator_step(project)), cwd=work, check=True)
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "evidence")
    git(work, "push", "-q", "origin", "HEAD:main")
    return git(work, "rev-parse", "HEAD")


def add_source_commit(project: dict[str, Path], content: str = "VALUE = 2\n") -> str:
    work = project["work"]
    (work / "src" / "app.py").write_text(content)
    git(work, "commit", "-q", "-am", "source change")
    git(work, "push", "-q", "origin", "HEAD:main")
    return git(work, "rev-parse", "HEAD")


def refresh_args(project: dict[str, Path], *extra: str) -> list[str]:
    return [
        "--repo",
        str(project["work"]),
        "--worktree",
        str(project["root"] / "wt"),
        "--no-verify",
        *extra,
    ]


def test_commit_tree_digest_matches_checkout_digest(project: dict[str, Path]) -> None:
    work = project["work"]
    assert tool.commit_tree_digest(work, git(work, "rev-parse", "HEAD")) == source_tree_digest(work)


def test_commit_tree_digest_rejects_gitlinks(project: dict[str, Path]) -> None:
    work = project["work"]
    head = git(work, "rev-parse", "HEAD")
    git(work, "update-index", "--add", "--cacheinfo", f"160000,{head},vendored")
    git(work, "commit", "-q", "-m", "gitlink")
    with pytest.raises(tool.RefreshError, match="unsupported tree entry"):
        tool.commit_tree_digest(work, git(work, "rev-parse", "HEAD"))


def test_check_reports_fresh_then_stale(project: dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
    commit_evidence_on_main(project)
    assert tool.main(["--check", "--fetch", "--repo", str(project["work"])]) == tool.EXIT_OK
    add_source_commit(project)
    assert tool.main(["--check", "--fetch", "--repo", str(project["work"])]) == tool.EXIT_NOT_FRESH
    assert "STALE" in capsys.readouterr().out


def test_false_label_detected_even_with_replace_refs(project: dict[str, Path]) -> None:
    work = project["work"]
    parent = git(work, "rev-parse", "HEAD")
    child = add_source_commit(project)
    digest = tool.commit_tree_digest(work, child)
    for name in tool.EVIDENCE_FILES:
        key = "source_commit" if name in {"evidence.json", "scripts/c5_quality_gates/claims_sitrep.json"} else "commit"
        path = work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({key: parent, "source_tree_digest": digest}) + "\n")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "mislabelled evidence")
    mislabelled = git(work, "rev-parse", "HEAD")
    assert tool.assess(work, mislabelled).status == "FALSE_LABEL"
    git(work, "replace", parent, child)
    assessment = tool.assess(work, mislabelled)
    assert assessment.status == "FALSE_LABEL" and assessment.label == "FAIL"


def test_squash_without_cited_object_is_fresh_with_unverifiable_label(project: dict[str, Path]) -> None:
    evidence_commit = commit_evidence_on_main(project)
    work = project["work"]
    squashed = git(work, "commit-tree", f"{evidence_commit}^{{tree}}", "-m", "squash")
    git(work, "branch", "squashed", squashed)
    other = project["root"] / "other"
    subprocess.run(
        ["git", "clone", "-q", "--no-local", "--single-branch", "--branch", "squashed", str(work), str(other)],
        check=True,
        capture_output=True,
    )
    assessment = tool.assess(other, "HEAD")
    assert assessment.status == "FRESH"
    assert assessment.label == "NOT_CHECKED"


def test_refresh_creates_single_generated_only_commit_citing_base(project: dict[str, Path]) -> None:
    commit_evidence_on_main(project)
    base = add_source_commit(project)
    code = tool.main(refresh_args(project, "--generator", generator_step(project), "--trailer", "Test-Trailer: yes"))
    assert code == tool.EXIT_OK
    work = project["work"]
    branch = f"evidence-refresh/{base[:12]}"
    assert git(work, "rev-list", "--count", f"{base}..{branch}") == "1"
    changed = set(git(work, "diff", "--name-only", base, branch).splitlines())
    assert changed and changed <= GENERATED_EVIDENCE
    assessment = tool.assess(work, branch)
    assert (assessment.status, assessment.label) == ("FRESH", "PASS")
    assert assessment.binding is not None and assessment.binding.commit == base
    assert "Test-Trailer: yes" in git(work, "log", "-1", "--format=%B", branch)
    squashed_onto_base = git(work, "commit-tree", f"{branch}^{{tree}}", "-p", base, "-m", "squash")
    assert tool.assess(work, squashed_onto_base).fresh
    assert git(project["remote"], "for-each-ref", "--format=%(refname)") == "refs/heads/main"


def test_refresh_is_a_noop_when_evidence_is_fresh(project: dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
    commit_evidence_on_main(project)
    assert tool.main(refresh_args(project, "--generator", generator_step(project))) == tool.EXIT_OK
    assert "already fresh" in capsys.readouterr().out
    assert not (project["root"] / "wt").exists()


def test_refresh_rejects_generator_touching_sources(
    project: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    base = add_source_commit(project)
    code = tool.main(refresh_args(project, "--generator", generator_step(project, "touch-source")))
    assert code == tool.EXIT_FAILURE
    assert "outside GENERATED_EVIDENCE: src/app.py" in capsys.readouterr().err
    worktree = project["root"] / "wt"
    assert tool.porcelain_paths(worktree) == ["src/app.py"]
    assert git(project["work"], "branch", "--list", f"evidence-refresh/{base[:12]}") == ""


def test_refresh_restores_evidence_when_generator_fails(project: dict[str, Path]) -> None:
    add_source_commit(project)
    code = tool.main(refresh_args(project, "--generator", generator_step(project, "fail")))
    assert code == tool.EXIT_FAILURE
    assert git(project["root"] / "wt", "status", "--porcelain", "--untracked-files=all") == ""


def test_refresh_restores_evidence_when_verification_fails(project: dict[str, Path]) -> None:
    add_source_commit(project)
    failing = f"{shlex.quote(sys.executable)} -c 'import sys; sys.exit(7)'"
    args = ["--repo", str(project["work"]), "--worktree", str(project["root"] / "wt")]
    code = tool.main([*args, "--generator", generator_step(project), "--verify-cmd", failing])
    assert code == tool.EXIT_FAILURE
    assert git(project["root"] / "wt", "status", "--porcelain", "--untracked-files=all") == ""


def test_refresh_refuses_dirty_worktree(project: dict[str, Path]) -> None:
    base = add_source_commit(project)
    worktree = project["root"] / "wt"
    git(project["work"], "worktree", "add", "-q", "--detach", str(worktree), base)
    (worktree / "stray.txt").write_text("stray\n")
    assert tool.main(refresh_args(project, "--generator", generator_step(project))) == tool.EXIT_PRECONDITION


def test_refresh_refuses_the_invoking_checkout(project: dict[str, Path]) -> None:
    add_source_commit(project)
    args = ["--repo", str(project["work"]), "--worktree", str(project["work"]), "--no-verify"]
    assert tool.main([*args, "--generator", generator_step(project)]) == tool.EXIT_PRECONDITION


def test_refresh_reports_base_moved_during_generation(project: dict[str, Path]) -> None:
    add_source_commit(project)
    mover = project["root"] / "mover"
    subprocess.run(["git", "clone", "-q", str(project["remote"]), str(mover)], check=True, capture_output=True)
    code = tool.main(refresh_args(project, "--generator", generator_step(project, "move-remote", str(mover))))
    assert code == tool.EXIT_BASE_MOVED


def test_lock_blocks_live_holder_and_clears_dead_one(project: dict[str, Path]) -> None:
    base = add_source_commit(project)
    worktree = project["root"] / "wt"
    git(project["work"], "worktree", "add", "-q", "--detach", str(worktree), base)
    lock = Path(git(worktree, "rev-parse", "--path-format=absolute", "--git-dir")) / tool.LOCK_NAME
    lock.write_text(f"{os.getpid()} 0\n")
    assert tool.main(refresh_args(project, "--generator", generator_step(project))) == tool.EXIT_PRECONDITION
    finished = subprocess.run([sys.executable, "-c", "import os; print(os.getpid())"], capture_output=True, text=True)
    lock.write_text(f"{finished.stdout.strip()} 0\n")
    assert tool.main(refresh_args(project, "--generator", generator_step(project))) == tool.EXIT_OK
    assert not lock.exists()


def test_open_pr_requires_push() -> None:
    assert tool.main(["--open-pr"]) == tool.EXIT_PRECONDITION


def test_evidence_before_an_exclusion_change_is_stale_not_mislabelled(project: dict[str, Path]) -> None:
    """A later commit that widens VAULT_ONLY_PREFIXES must not turn a truthful label into a false one."""
    evidence_commit = commit_evidence_on_main(project)
    work = project["work"]
    rules_path = work / tool.RULES_SOURCE
    source = rules_path.read_text(encoding="utf-8")
    widened = source.replace('    "tools/skill_library/",\n', '    "tools/skill_library/",\n    "README.md",\n', 1)
    assert widened != source
    rules_path.write_text(widened, encoding="utf-8")
    git(work, "commit", "-q", "-am", "widen exclusions")
    git(work, "push", "-q", "origin", "HEAD:main")
    assessment = tool.assess(work, "HEAD")
    assert (assessment.status, assessment.label) == ("STALE", "PASS")
    cited = assessment.binding.commit if assessment.binding else ""
    with_current_rules = tool.commit_tree_digest(work, cited, tool.rules_at(work, "HEAD"))
    original_binding, _ = tool.read_binding_at(work, evidence_commit)
    assert original_binding is not None
    assert with_current_rules != original_binding.tree_digest


def test_rules_parser_reads_literals_and_rejects_other_forms() -> None:
    rules = tool.parse_exclusion_rules((REPO_ROOT / tool.RULES_SOURCE).read_bytes(), "HEAD")
    assert "evidence.json" in rules.generated and rules.excludes("docs/security/evidence/x")
    other_rule = b"GENERATED_EVIDENCE = {'a'}\nVAULT_ONLY_PREFIXES = ('b/',)\n"
    other_rule += b"def is_excluded_from_public_tree(relative):\n    return relative.startswith('x')\n"
    with pytest.raises(tool.RulesUnavailable, match="is not"):
        tool.parse_exclusion_rules(other_rule, "fixture")
    computed = b"GENERATED_EVIDENCE = set(['a'])\nVAULT_ONLY_PREFIXES = ('b/',)\n"
    with pytest.raises(tool.RulesUnavailable, match="not a literal"):
        tool.parse_exclusion_rules(computed, "fixture")


def test_label_pointing_at_a_commit_without_rules_is_unverifiable(project: dict[str, Path]) -> None:
    work = project["work"]
    parent = git(work, "rev-parse", "HEAD")
    digest = tool.commit_tree_digest(work, parent)
    empty_tree = (
        subprocess.run(
            ["git", "-C", str(work), "hash-object", "-t", "tree", "--stdin"], input=b"", capture_output=True, check=True
        )
        .stdout.decode()
        .strip()
    )
    ruleless = git(work, "commit-tree", empty_tree, "-m", "no rules here")
    for name in tool.EVIDENCE_FILES:
        key = "source_commit" if name in {"evidence.json", "scripts/c5_quality_gates/claims_sitrep.json"} else "commit"
        (work / name).write_text(json.dumps({key: ruleless, "source_tree_digest": digest}) + "\n")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "evidence labelled with a rule-less commit")
    assessment = tool.assess(work, "HEAD")
    assert (assessment.status, assessment.label) == ("FRESH", "NOT_CHECKED")
    assert any("label unverifiable" in detail for detail in assessment.details)


def test_ref_resolution_keeps_object_reader_strict(project: dict[str, Path]) -> None:
    work = project["work"]
    head = git(work, "rev-parse", "HEAD")
    assert tool.rules_at(work, "HEAD") == tool.rules_at(work, head)
    assert tool.commit_tree_digest(work, "HEAD") == tool.commit_tree_digest(work, head)
    with pytest.raises(tool.RefreshError, match="full canonical object IDs"):
        tool.ObjectStore(work).read(["HEAD"])


@pytest.mark.parametrize("payload", [[], "not an object", 42, None])
def test_binding_reader_rejects_non_object_json(project: dict[str, Path], payload: object) -> None:
    commit_evidence_on_main(project)
    work = project["work"]
    (work / "evidence.json").write_text(json.dumps(payload))
    binding, problems = tool.read_binding_from_files(work)
    assert binding is None
    assert any("not a JSON object" in problem for problem in problems)
    git(work, "commit", "-q", "-am", "malformed fixture")
    binding, problems = tool.read_binding_at(work, git(work, "rev-parse", "HEAD"))
    assert binding is None
    assert any("not a JSON object" in problem for problem in problems)


@pytest.mark.parametrize(
    "flags",
    [["--no-fetch"], ["--no-verify"], ["--generator", "true"], ["--verify-cmd", "true"]],
)
def test_push_refuses_noncanonical_generation(flags: list[str]) -> None:
    assert tool.main(["--push", *flags]) == tool.EXIT_PRECONDITION


def test_projection_manifest_never_refreshable() -> None:
    assert ".github/public_projection_manifest.json" not in tool.REFRESHABLE_ARTIFACTS
