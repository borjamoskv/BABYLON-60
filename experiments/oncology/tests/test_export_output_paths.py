"""The real export CLI must reject colliding destinations without changing them."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).absolute().parents[1] / "scripts" / "export_ontology.py"


def run_export(directory: Path, json_out: Path, lean_out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", "-S", str(SCRIPT), "--json-out", str(json_out), "--lean-out", str(lean_out)],
        cwd=directory, capture_output=True, text=True, timeout=30,
    )


def directory_alias(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"Directory symlinks are unavailable: {error}")


@pytest.mark.parametrize("alias", ["identical", "normalized", "symlink-parent", "hardlink"])
def test_cli_rejects_existing_output_aliases_without_changes(tmp_path: Path, alias: str) -> None:
    real = tmp_path / "real"
    real.mkdir()
    first = real / "catalog.json"
    first.write_bytes(b'{"previous":"preserve"}\n')
    if alias == "identical":
        second = first
    elif alias == "normalized":
        nested = real / "nested"
        nested.mkdir()
        second = nested / ".." / first.name
    elif alias == "symlink-parent":
        link = tmp_path / "linked"
        directory_alias(link, real)
        second = link / first.name
    else:
        second = real / "second-name.lean"
        os.link(first, second)
    before = {
        path: (path.read_bytes(), path.stat().st_ino, path.stat().st_mtime_ns)
        for path in (first, second)
    }

    result = run_export(tmp_path, first, second)

    assert result.returncode == 2, result.stdout + result.stderr
    assert "must refer to different files" in result.stderr
    for path, expected in before.items():
        assert (path.read_bytes(), path.stat().st_ino, path.stat().st_mtime_ns) == expected


def test_cli_rejects_new_targets_under_symlinked_parent_before_creating_files(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    canary = real / "canary.txt"
    canary.write_bytes(b"unchanged")
    link = tmp_path / "linked"
    directory_alias(link, real)

    result = run_export(tmp_path, real / "new.json", link / "new.json")

    assert result.returncode == 2, result.stdout + result.stderr
    assert "must refer to different files" in result.stderr
    assert sorted(path.name for path in real.iterdir()) == ["canary.txt"]
    assert canary.read_bytes() == b"unchanged"


@pytest.mark.parametrize(
    ("json_name", "lean_name"),
    [
        pytest.param("catalog.JSON", "catalog.json", id="case-only"),
        pytest.param("\u00e9.json", "e\u0301.json", id="nfc-equivalent"),
    ],
)
def test_cli_rejects_portably_equivalent_new_targets_before_creating_files(
    tmp_path: Path, json_name: str, lean_name: str
) -> None:
    canary = tmp_path / "canary.txt"
    canary.write_bytes(b"unchanged")
    before = (canary.read_bytes(), canary.stat().st_ino, canary.stat().st_mtime_ns)

    result = run_export(tmp_path, tmp_path / json_name, tmp_path / lean_name)

    assert result.returncode == 2, result.stdout + result.stderr
    assert "must refer to different files" in result.stderr
    assert sorted(path.name for path in tmp_path.iterdir()) == ["canary.txt"]
    assert (canary.read_bytes(), canary.stat().st_ino, canary.stat().st_mtime_ns) == before


def test_cli_distinct_targets_still_export_both_formats(tmp_path: Path) -> None:
    json_out = tmp_path / "catalog.json"
    lean_out = tmp_path / "catalog.lean"

    result = run_export(tmp_path, json_out, lean_out)

    assert result.returncode == 0, result.stdout + result.stderr
    catalog = json.loads(json_out.read_text())
    assert catalog["total_primitives"] == len(catalog["primitives"]) == 300
    assert "theorem ontology_count_invariant" in lean_out.read_text()
