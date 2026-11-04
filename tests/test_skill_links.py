from pathlib import Path

import pytest

from scripts.c5_quality_gates.audit_skill_links import anchors, inspect


def test_heading_ids_and_duplicates() -> None:
    assert anchors("# Hola, mundo!\n## Código `Rust`\n# Hola, mundo!\n```md\n# Ignorado\n```") == {
        "hola-mundo",
        "código-rust",
        "hola-mundo-1",
    }


def test_local_missing_anchor_is_not_hidden(tmp_path: Path) -> None:
    page = tmp_path / "page.md"
    page.write_text("# Real\n[good](#real)\n[bad](#missing)\n[file](absent.md)")
    result = inspect([tmp_path], remote=False)
    assert len(result["findings"]) == 2
    assert {f["reason"] for f in result["findings"]} == {"missing local anchor", "missing file"}


def test_remote_not_checked_is_unverified(tmp_path: Path) -> None:
    (tmp_path / "page.md").write_text("[remote](https://example.com/doc#section)")
    result = inspect([tmp_path], remote=False)
    assert result["findings"][0]["status"] == "unverified"


def test_missing_root_is_not_a_successful_empty_audit(tmp_path: Path) -> None:
    with pytest.raises(OSError, match="Missing Markdown root"):
        inspect([tmp_path / "missing"], remote=False)


def test_file_uris_are_checked_including_fragments(tmp_path: Path) -> None:
    dest = tmp_path / "target space.md"
    dest.write_text("# Present\n")
    (tmp_path / "page.md").write_text(
        f"[good]({dest.as_uri()}#present)\n[bad]({dest.as_uri()}#absent)\n"
        f"[missing]({(tmp_path / 'missing.md').as_uri()})\n[remote](file://other-host/file.md)"
    )
    result = inspect([tmp_path], remote=False)
    assert {f["reason"] for f in result["findings"]} == {"missing local anchor", "missing file", "remote file host"}
