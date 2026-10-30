"""Regression coverage for the public documentation checks and index generator."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import pytest


REPO_ROOT = Path(__file__).absolute().parents[1]
LINTER_PATH = REPO_ROOT / "scripts" / "docs_lint.py"
INDEXER_PATH = REPO_ROOT / "scripts" / "c5_quality_gates" / "sync_docs_index.py"


@pytest.fixture
def linter() -> ModuleType:
    spec = importlib.util.spec_from_file_location("docs_quality_linter", LINTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_doc(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def scan(linter: ModuleType, root: Path, page: Path) -> int:
    registry = linter.build_anchor_registry(list((root / "docs").rglob("*.md")))
    return linter.scan_file(page, root, registry)


def run_script(script: Path, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )


def test_badge_outer_link_is_checked(linter: ModuleType, tmp_path: Path) -> None:
    page = write_doc(
        tmp_path,
        "docs/page.md",
        "# Status\n[![badge](https://img.shields.io/badge/status-current)](missing.md)\n",
    )
    assert scan(linter, tmp_path, page) > 0


def test_existing_badge_target_is_accepted(linter: ModuleType, tmp_path: Path) -> None:
    write_doc(tmp_path, "docs/target.md", "# Target\n")
    page = write_doc(
        tmp_path,
        "docs/page.md",
        "# Status\n[![badge](https://img.shields.io/badge/status-current)](target.md)\n",
    )
    assert scan(linter, tmp_path, page) == 0


def test_machine_local_file_url_is_rejected(linter: ModuleType, tmp_path: Path) -> None:
    target = write_doc(tmp_path, "docs/target.md", "# Target\n")
    page = write_doc(tmp_path, "docs/page.md", f"# Status\n[local]({target.as_uri()})\n")
    assert scan(linter, tmp_path, page) > 0


def test_reference_destinations_and_angle_paths_are_checked(linter: ModuleType, tmp_path: Path) -> None:
    write_doc(tmp_path, "docs/Target Guide.md", "# Target\n")
    page = write_doc(
        tmp_path,
        "docs/page.md",
        "# Status\n[guide](<Target Guide.md>)\n[reference][manual]\n\n[manual]: <Target Guide.md>\n",
    )
    assert scan(linter, tmp_path, page) == 0
    page.write_text("# Status\n[reference][manual]\n\n[manual]: missing.md\n", encoding="utf-8")
    assert scan(linter, tmp_path, page) > 0


def test_gfm_anchor_slug_preserves_emoji_separator(linter: ModuleType) -> None:
    assert linter.slugify("📚 Hello, `World`!") == "-hello-world"


def test_duplicate_headings_and_fenced_headings_match_gfm(linter: ModuleType, tmp_path: Path) -> None:
    page = write_doc(
        tmp_path,
        "docs/target.md",
        "# Repeat\n# Repeat\n```md\n# Hidden\n```\n# 📚 Start\n",
    )
    registry = linter.build_anchor_registry([page])
    anchors = next(iter(registry.values()))
    assert {"repeat", "repeat-1", "-start"} <= anchors
    assert "hidden" not in anchors


def test_valid_duplicate_anchor_and_missing_fenced_anchor(linter: ModuleType, tmp_path: Path) -> None:
    write_doc(tmp_path, "docs/target.md", "# Repeat\n# Repeat\n```md\n# Hidden\n```\n")
    page = write_doc(tmp_path, "docs/page.md", "# Links\n[second](target.md#repeat-1)\n")
    assert scan(linter, tmp_path, page) == 0
    page.write_text("# Links\n[example](target.md#hidden)\n", encoding="utf-8")
    assert scan(linter, tmp_path, page) > 0


def test_link_examples_inside_code_are_not_live_links(linter: ModuleType, tmp_path: Path) -> None:
    page = write_doc(
        tmp_path,
        "docs/page.md",
        "# Examples\n`[inline](missing.md)`\n```md\n[block](also-missing.md)\n```\n",
    )
    assert scan(linter, tmp_path, page) == 0


def test_documented_linter_accepts_docs_directory(tmp_path: Path) -> None:
    write_doc(tmp_path, "docs/page.md", "# Page\n")
    write_doc(tmp_path, "docs/00_index.md", "# Index\n\n| [`page.md`](page.md) | Page |\n")
    result = run_script(LINTER_PATH, tmp_path, "docs/", "--repo-root", str(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr


def test_indexer_includes_security_and_operational_docs_and_detects_staleness(tmp_path: Path) -> None:
    write_doc(tmp_path, "docs/03_guides/kernel.md", "# Kernel setup\n")
    write_doc(tmp_path, "docs/security/authorization.md", "# Authorization profile\n")
    write_doc(tmp_path, "docs/README.md", "# Documentation\n")
    docs_dir = tmp_path / "docs"

    stale = run_script(INDEXER_PATH, tmp_path, "--docs-dir", str(docs_dir), "--check")
    assert stale.returncode != 0

    generated = run_script(INDEXER_PATH, tmp_path, "--docs-dir", str(docs_dir))
    assert generated.returncode == 0, generated.stdout + generated.stderr
    index = (docs_dir / "00_index.md").read_text(encoding="utf-8")
    assert "03_guides/kernel.md" in index
    assert "security/authorization.md" in index
    assert "100% Synchronized" not in index
    assert "STATUS.md" not in index

    checked = run_script(INDEXER_PATH, tmp_path, "--docs-dir", str(docs_dir), "--check")
    assert checked.returncode == 0, checked.stdout + checked.stderr

    graph = run_script(INDEXER_PATH, tmp_path, "--docs-dir", str(docs_dir), "--json")
    assert graph.returncode == 0, graph.stdout + graph.stderr
    assert json.loads(graph.stdout)["total_documents"] == 3

    write_doc(tmp_path, "docs/security/recovery.md", "# Recovery\n")
    stale_again = run_script(INDEXER_PATH, tmp_path, "--docs-dir", str(docs_dir), "--check")
    assert stale_again.returncode != 0
