"""The documentation gate preserves reviewed context and still rejects missing local code."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest
from scripts.c5_quality_gates.detect_ghost_nodes import (
    CONTEXT_FILE,
    EXCLUDE_DIRS,
    audit_ghost_nodes,
    build_symbol_table,
    classify_document_scope,
    main,
    partition_ghost_nodes,
)


def _registry(root: Path, **changes: object) -> None:
    entry: dict[str, object] = {
        "path": "guide.md",
        "symbol": "ForeignClient",
        "kind": "external",
        "reason": "Name attributed to an external SDK by this document.",
        "evidence": "guide.md describes this as an external client.",
    }
    document = root / "guide.md"
    context = "\n".join(line.strip() for line in document.read_text().splitlines() if "`ForeignClient`" in line)
    entry["context_sha256"] = hashlib.sha256(context.encode()).hexdigest()
    entry.update(changes)
    path = root / CONTEXT_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "references": [entry]}))


def test_known_and_missing_local_identifiers(tmp_path: Path) -> None:
    (tmp_path / "local.py").write_text("class LocalVerifier: pass\n")
    (tmp_path / "guide.md").write_text("`LocalVerifier` and `MissingVerifier`")
    assert audit_ghost_nodes(tmp_path, build_symbol_table(tmp_path)) == {
        (str(tmp_path / "guide.md"), "MissingVerifier")
    }


def test_context_is_scoped_to_exact_document_and_symbol(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text("External SDK: `ForeignClient`; local claim: `MissingVerifier`.")
    (tmp_path / "other.md").write_text("Local implementation: `ForeignClient`.")
    _registry(tmp_path)
    assert audit_ghost_nodes(tmp_path, set()) == {
        (str(tmp_path / "guide.md"), "MissingVerifier"),
        (str(tmp_path / "other.md"), "ForeignClient"),
    }


@pytest.mark.parametrize(
    "change",
    [
        {"path": "../outside.md"},
        {"kind": "ignore"},
        {"reason": ""},
        {"symbol": "NoLongerMentioned"},
    ],
)
def test_invalid_or_stale_context_is_rejected(tmp_path: Path, change: dict[str, object]) -> None:
    (tmp_path / "guide.md").write_text("`ForeignClient`")
    _registry(tmp_path, **change)
    with pytest.raises(ValueError):
        audit_ghost_nodes(tmp_path, set())


def test_warmup_and_repeated_scan_keeps_local_failure_visible(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text("`ForeignClient` and `MissingVerifier`.")
    _registry(tmp_path)
    expected = {(str(tmp_path / "guide.md"), "MissingVerifier")}
    for _ in range(16):
        assert audit_ghost_nodes(tmp_path, set()) == expected
    for _ in range(256):
        assert audit_ghost_nodes(tmp_path, set()) == expected


def test_context_change_requires_new_review(tmp_path: Path) -> None:
    document = tmp_path / "guide.md"
    document.write_text("External SDK: `ForeignClient`.")
    _registry(tmp_path)
    assert audit_ghost_nodes(tmp_path, set()) == set()
    document.write_text("The local runtime implements `ForeignClient`.")
    with pytest.raises(ValueError, match="context changed"):
        audit_ghost_nodes(tmp_path, set())


def test_build_and_generated_directories_are_excluded(tmp_path: Path) -> None:
    assert {"dist", "scratch", "target", "build"}.issubset(EXCLUDE_DIRS)
    for excluded in ("dist", "scratch", "target", "build"):
        doc = tmp_path / excluded / "generated.md"
        doc.parent.mkdir(parents=True, exist_ok=True)
        doc.write_text("`MissingGeneratedSymbol`")
    assert audit_ghost_nodes(tmp_path, set()) == set()


def test_scope_classification_separates_skill_library_from_core_and_docs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert classify_document_scope("README.md") == "core"
    assert classify_document_scope("docs/01_spec/spec.md") == "docs"
    assert classify_document_scope("tools/skill_library/global/example/SKILL.md") == "skill_library"

    core_doc = tmp_path / "README.md"
    docs_doc = tmp_path / "docs" / "guide.md"
    skill_doc = tmp_path / "tools" / "skill_library" / "global" / "demo" / "SKILL.md"
    docs_doc.parent.mkdir(parents=True)
    skill_doc.parent.mkdir(parents=True)
    core_doc.write_text("`MissingCoreSym`")
    docs_doc.write_text("`MissingDocsSym`")
    skill_doc.write_text("`MissingSkillSym`")

    all_ghosts = audit_ghost_nodes(tmp_path, set())
    buckets = partition_ghost_nodes(tmp_path, all_ghosts)
    assert buckets["core"] == {(str(core_doc), "MissingCoreSym")}
    assert buckets["docs"] == {(str(docs_doc), "MissingDocsSym")}
    assert buckets["skill_library"] == {(str(skill_doc), "MissingSkillSym")}

    assert audit_ghost_nodes(tmp_path, set(), scopes={"core"}) == {(str(core_doc), "MissingCoreSym")}
    assert audit_ghost_nodes(tmp_path, set(), scopes={"docs"}) == {(str(docs_doc), "MissingDocsSym")}
    assert audit_ghost_nodes(tmp_path, set(), scopes={"core", "docs"}) == {
        (str(core_doc), "MissingCoreSym"),
        (str(docs_doc), "MissingDocsSym"),
    }

    with pytest.raises(ValueError, match="Unknown document scope"):
        audit_ghost_nodes(tmp_path, set(), scopes={"unknown"})

    assert main(["--scope", "core", "--summary-only"], root=tmp_path) == 1
    out = capsys.readouterr().out
    assert "Scope breakdown: core=1, docs=1, tools/skill_library=1, total=3." in out
    assert "FAIL (core): 1 unresolved local code references." in out

    core_doc.write_text("Clean core doc.")
    assert main(["--scope", "core"], root=tmp_path) == 0
    out_pass = capsys.readouterr().out
    assert "PASS (core):" in out_pass
    assert main(["--scope", "docs", "--summary-only"], root=tmp_path) == 1
    assert main(["--scope", "skill-library", "--summary-only"], root=tmp_path) == 1


def test_codex_overrides_excluded_while_other_skill_library_and_same_dir_name_kept(tmp_path: Path) -> None:
    override_doc = tmp_path / "tools" / "skill_library" / "codex_overrides" / "vendor" / "SKILL.md"
    override_code = tmp_path / "tools" / "skill_library" / "codex_overrides" / "vendor" / "helper.py"
    global_doc = tmp_path / "tools" / "skill_library" / "global" / "demo" / "SKILL.md"
    local_override_doc = tmp_path / "docs" / "codex_overrides" / "note.md"
    for path in (override_doc, override_code, global_doc, local_override_doc):
        path.parent.mkdir(parents=True, exist_ok=True)

    override_code.write_text("class ThirdPartyOverrideOnly: pass\n")
    override_doc.write_text("`VendorEntrypoint` and `vendor_compat_date`")
    global_doc.write_text("`MissingGlobalSkillSym` and `ThirdPartyOverrideOnly`")
    local_override_doc.write_text("`MissingDocsOverrideSym`")

    symbols = build_symbol_table(tmp_path)
    assert "ThirdPartyOverrideOnly" not in symbols
    assert audit_ghost_nodes(tmp_path, symbols) == {
        (str(global_doc), "MissingGlobalSkillSym"),
        (str(global_doc), "ThirdPartyOverrideOnly"),
        (str(local_override_doc), "MissingDocsOverrideSym"),
    }


def test_hex_hashes_filtered_without_hiding_error_codes_or_words(tmp_path: Path) -> None:
    doc = tmp_path / "audit.md"
    short_sha = "a1b2c3d4"
    sha_40 = "a1b2c3d4" * 5
    sha_64 = "a1b2c3d4" * 8
    sig_128 = "a1b2c3d4" * 16
    doc.write_text(
        "\n".join(
            [
                f"Commits `{short_sha}`, `f1e2d3c4b5a6`, `{sha_40}`.",
                f"Digests `{sha_64}`, `DEADBEEF1234`, `{sig_128}`.",
                "Preserved tokens: `E9999`, `facade`, `DeadBeef01`, `MissingSyntheticSym`.",
            ]
        )
    )
    assert audit_ghost_nodes(tmp_path, set()) == {
        (str(doc), "E9999"),
        (str(doc), "facade"),
        (str(doc), "DeadBeef01"),
        (str(doc), "MissingSyntheticSym"),
    }


def test_gitignored_files_are_excluded_when_git_repo_present(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".gitignore").write_text("data/\n")
    ignored_doc = tmp_path / "data" / "local_only.md"
    ignored_doc.parent.mkdir(parents=True)
    ignored_doc.write_text("`GitIgnoredLocalSymbol`")
    tracked_doc = tmp_path / "guide.md"
    tracked_doc.write_text("`MissingTrackedSymbol`")
    assert audit_ghost_nodes(tmp_path, set()) == {(str(tracked_doc), "MissingTrackedSymbol")}
