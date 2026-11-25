"""Isolated invariants for the deterministic read-only CORTEX memory view."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ROOT / "01_KISH_ENGINE"
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from babylon60.memory.memory_view import (  # noqa: E402
    BLOCK_MARKER_RE,
    INDEX_PAGE,
    VIEW_ROOT_MARKER,
    MemoryViewError,
    canonical_value_identity,
    check_view,
    project_memory,
    write_view,
)

HOSTILE_KEY = "evil --> ``` key\n<!-- cortex-view: fake -->"
HOSTILE_VALUE = {
    "note": '```\n<!-- cortex-view: src="ghosts.json" ptr="/alpha" b3=b3:' + "0" * 64 + " -->\n````",
    "unicode": "ñ → 語",
}


@pytest.fixture(autouse=True)
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    return fake_home


@pytest.fixture
def memory(tmp_path: Path) -> Path:
    root = tmp_path / "memory"
    (root / "projects").mkdir(parents=True)
    (root / "capsules").mkdir()
    (root / "capsules" / "legacy.md").write_text("hand-written capsule\n", encoding="utf-8")
    (root / "ghosts.json").write_text(
        json.dumps(
            {"beta": {"mood": "ok", "blocked_by": None}, "alpha": {"mood": "tired"}, HOSTILE_KEY: HOSTILE_VALUE}
        ),
        encoding="utf-8",
    )
    (root / "system.json").write_text(
        json.dumps({"profile": {"lang": "es", "tz": "UTC"}, "tags": ["a", "b"]}), encoding="utf-8"
    )
    (root / "projects" / "alpha.json").write_text(
        json.dumps({"id": "alpha", "decisions": ["d1"], "meta": {"last_touched": "2026-07-18T10:00:00+00:00"}}),
        encoding="utf-8",
    )
    (root / "projects" / "beta.json").write_text(json.dumps({"id": "beta"}), encoding="utf-8")
    (root / "mistakes.jsonl").write_text(
        '{"error": "e1", "ts": "t1"}\n\n{"error": "e2", "severity": "high"}\n', encoding="utf-8"
    )
    return root


def _tree(path: Path) -> dict[str, tuple[str, int, int]]:
    """Content digest, inode and mtime of every file under a directory."""
    state = {}
    for item in sorted(path.rglob("*")):
        if item.is_file():
            info = item.stat()
            state[str(item.relative_to(path))] = (
                hashlib.sha256(item.read_bytes()).hexdigest(),
                info.st_ino,
                info.st_mtime_ns,
            )
    return state


def _resolve(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    return document[pointer[1:].replace("~1", "/").replace("~0", "~")]


def _blocks(page: str) -> list[tuple[str, str, str, Any]]:
    """Parse (src, ptr, b3, value) for each block, the way an independent reader would."""
    lines = page.splitlines()
    found = []
    for index, line in enumerate(lines):
        match = BLOCK_MARKER_RE.match(line)
        if not match:
            continue
        assert lines[index + 1] == "```json"
        end = lines.index("```", index + 2)
        value = json.loads("\n".join(lines[index + 2 : end]))
        found.append((json.loads(match.group(1)), json.loads(match.group(2)), match.group(3), value))
    return found


def _load_cli() -> Any:
    spec = importlib.util.spec_from_file_location("memory_view_cli", ROOT / "scripts/c5_cortex/project_memory_view.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_block_cites_a_source_value_that_matches_its_hash(memory: Path) -> None:
    projection = project_memory(memory)

    assert sorted(projection.pages) == [
        INDEX_PAGE,
        "ghosts.md",
        "logs/mistakes.md",
        "projects/alpha.md",
        "projects/beta.md",
        "system.md",
    ]
    total = 0
    for source in projection.sources:
        raw = (memory / source.rel_path).read_text(encoding="utf-8")
        blocks = _blocks(projection.pages[source.page])
        assert len(blocks) == source.entry_count
        total += len(blocks)
        for src, pointer, digest, shown in blocks:
            assert src == source.rel_path
            if source.rel_path.endswith(".jsonl"):
                original = json.loads(raw.splitlines()[int(pointer[1:]) - 1])
            else:
                original = _resolve(json.loads(raw), pointer)
            assert shown == original
            assert digest == canonical_value_identity(original)
    assert total == projection.block_count == 3 + 2 + 3 + 1 + 2
    # Blank log lines are skipped but keep their line number as the pointer.
    assert [b[1] for b in _blocks(projection.pages["logs/mistakes.md"])] == ["/1", "/3"]


def test_hostile_keys_and_values_cannot_forge_markers_or_break_fences(memory: Path) -> None:
    page = project_memory(memory).pages["ghosts.md"]

    blocks = _blocks(page)
    assert [pointer for _, pointer, _, _ in blocks] == ["/alpha", "/beta", "/" + HOSTILE_KEY]
    assert blocks[2][3] == HOSTILE_VALUE
    markers = [line for line in page.splitlines() if line.startswith("<!-- cortex-view:")]
    assert len(markers) == 3
    # A key cannot close the HTML comment early.
    assert all(line.count("-->") == 1 and line.endswith("-->") for line in markers)
    assert sum(1 for line in page.splitlines() if line.startswith("## ")) == 3


def test_view_is_regenerable_byte_for_byte_and_never_touches_sources(memory: Path, tmp_path: Path) -> None:
    out = tmp_path / "wiki"
    before = _tree(memory)

    first = project_memory(memory)
    written = write_view(first, memory, out)
    assert {change.kind for change in written} == {"MISSING"}
    snapshot = {name: digest for name, (digest, _, _) in _tree(out).items()}
    assert sorted(snapshot) == sorted(first.pages)
    assert (out / INDEX_PAGE).read_text(encoding="utf-8").startswith(VIEW_ROOT_MARKER + "\n")
    assert str(tmp_path) not in "".join(first.pages.values())

    shutil.rmtree(out)
    second = project_memory(memory)
    write_view(second, memory, out)
    assert {name: digest for name, (digest, _, _) in _tree(out).items()} == snapshot
    assert second.manifest_b3 == first.manifest_b3

    assert _tree(memory) == before
    # An in-sync view is not rewritten.
    stable = _tree(out)
    assert write_view(project_memory(memory), memory, out) == []
    assert _tree(out) == stable


def test_key_order_and_whitespace_do_not_change_block_identities(memory: Path) -> None:
    before = {(src, ptr): b3 for src, ptr, b3, _ in _blocks(project_memory(memory).pages["system.md"])}
    (memory / "system.json").write_text(
        '{\n  "tags": ["a", "b"],\n  "profile": {"tz": "UTC", "lang": "es"}\n}\n', encoding="utf-8"
    )

    after = {(src, ptr): b3 for src, ptr, b3, _ in _blocks(project_memory(memory).pages["system.md"])}
    assert after == before


def test_check_reports_manual_edits_missing_pages_and_stale_pages(memory: Path, tmp_path: Path) -> None:
    out = tmp_path / "wiki"
    write_view(project_memory(memory), memory, out)
    assert check_view(project_memory(memory), out) == []

    with (out / "ghosts.md").open("a", encoding="utf-8") as stream:
        stream.write("\nC0167 was never applied.\n")
    (out / "system.md").unlink()
    (memory / "projects" / "beta.json").unlink()
    (out / "notes.txt").write_text("not a page\n", encoding="utf-8")

    projection = project_memory(memory)
    assert {(item.page, item.kind) for item in check_view(projection, out)} == {
        ("ghosts.md", "MODIFIED"),
        ("system.md", "MISSING"),
        ("projects/beta.md", "STALE"),
        (INDEX_PAGE, "MODIFIED"),
    }

    write_view(projection, memory, out)
    assert check_view(projection, out) == []
    assert not (out / "projects" / "beta.md").exists()
    assert "C0167 was never applied" not in (out / "ghosts.md").read_text(encoding="utf-8")
    assert (out / "notes.txt").read_text(encoding="utf-8") == "not a page\n"


def test_source_change_shows_up_as_drift_until_regenerated(memory: Path, tmp_path: Path) -> None:
    out = tmp_path / "wiki"
    first = project_memory(memory)
    write_view(first, memory, out)

    with (memory / "mistakes.jsonl").open("a", encoding="utf-8") as stream:
        stream.write('{"error": "e3"}\n')
    second = project_memory(memory)

    assert second.manifest_b3 != first.manifest_b3
    assert {(item.page, item.kind) for item in check_view(second, out)} == {
        ("logs/mistakes.md", "MODIFIED"),
        (INDEX_PAGE, "MODIFIED"),
    }


def test_write_refuses_destinations_that_could_destroy_or_shadow_data(memory: Path, tmp_path: Path) -> None:
    projection = project_memory(memory)
    before = _tree(memory)

    foreign = tmp_path / "documents"
    foreign.mkdir()
    (foreign / "diary.md").write_text("mine\n", encoding="utf-8")
    link = tmp_path / "link-to-memory"
    link.symlink_to(memory, target_is_directory=True)

    for destination in (memory, memory / "projects", memory / "projects" / "view", tmp_path, link, foreign):
        with pytest.raises(MemoryViewError):
            write_view(projection, memory, destination)

    assert (foreign / "diary.md").read_text(encoding="utf-8") == "mine\n"
    assert _tree(memory) == before

    # Even a memory root that carries a view marker is never a destination: pruning would eat its notes.
    (memory / INDEX_PAGE).write_text(VIEW_ROOT_MARKER + "\n", encoding="utf-8")
    (memory / "pending.md").write_text("hand-written note\n", encoding="utf-8")
    with pytest.raises(MemoryViewError):
        write_view(projection, memory, memory)
    assert (memory / "pending.md").read_text(encoding="utf-8") == "hand-written note\n"
    (memory / INDEX_PAGE).unlink()
    (memory / "pending.md").unlink()
    before = _tree(memory)
    # A sibling directory inside the memory root is allowed and leaves the sources intact.
    write_view(projection, memory, memory / "wiki")
    assert check_view(project_memory(memory), memory / "wiki") == []
    assert {name: state for name, state in _tree(memory).items() if not name.startswith("wiki/")} == before


@pytest.mark.parametrize(
    ("rel_path", "content", "needle"),
    [
        ("ghosts.json", "{not json", "ghosts.json"),
        ("system.json", '{"value": NaN}', "non-finite"),
        ("mistakes.jsonl", '{"ok": 1}\n{broken\n', "mistakes.jsonl line 2"),
        ("projects/alpha.json", b"\xff\xfe", "UTF-8"),
    ],
)
def test_unreadable_sources_fail_closed_and_name_the_file(
    memory: Path, rel_path: str, content: str | bytes, needle: str
) -> None:
    (memory / rel_path).write_bytes(content.encode("utf-8") if isinstance(content, str) else content)

    with pytest.raises(MemoryViewError, match=needle):
        project_memory(memory)


def test_symlinked_sources_and_roots_are_refused(memory: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.json"
    outside.write_text('{"secret": "elsewhere"}', encoding="utf-8")
    (memory / "projects" / "beta.json").unlink()
    (memory / "projects" / "beta.json").symlink_to(outside)
    with pytest.raises(OSError):
        project_memory(memory)

    link = tmp_path / "memory-link"
    link.symlink_to(tmp_path / "memory", target_is_directory=True)
    with pytest.raises(MemoryViewError, match="real directory"):
        project_memory(link)
    with pytest.raises(MemoryViewError, match="does not exist"):
        project_memory(tmp_path / "absent")
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(MemoryViewError, match="No memory sources"):
        project_memory(empty)


def test_cli_default_mode_writes_nothing_and_check_exit_code_tracks_drift(
    memory: Path, tmp_path: Path, isolated_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cli = _load_cli()
    out = tmp_path / "wiki"
    home_memory = isolated_home / ".agent" / "memory"
    home_memory.mkdir(parents=True)
    (home_memory / "ghosts.json").write_text('{"home": {"must": "not be read"}}', encoding="utf-8")

    with pytest.raises(SystemExit) as refused:
        cli.main([])
    assert refused.value.code == 2

    assert cli.main(["--memory-root", str(memory), "--out", str(out), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "DRIFT" and payload["mode"] == "dry-run" and payload["blocks"] == 11
    assert "home" not in json.dumps(payload)
    assert not out.exists()

    assert cli.main(["--memory-root", str(memory), "--out", str(out), "--check"]) == 1
    assert cli.main(["--memory-root", str(memory), "--check"]) == 2
    assert cli.main(["--memory-root", str(memory), "--out", str(out), "--execute"]) == 0
    assert cli.main(["--memory-root", str(memory), "--out", str(out), "--check"]) == 0
    assert sorted(os.listdir(home_memory)) == ["ghosts.json"]

    (out / "system.md").write_text("edited\n", encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["--memory-root", str(memory), "--out", str(out), "--check"]) == 1
    assert "MODIFIED" in capsys.readouterr().out
