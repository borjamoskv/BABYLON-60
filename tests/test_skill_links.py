import json
from pathlib import Path
from urllib.error import HTTPError

import pytest

from scripts.c5_quality_gates import audit_skill_links
from scripts.c5_quality_gates.audit_skill_links import anchors, inspect, main


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


def test_allow_unverified_403_host_preserves_evidence_without_weakening_other_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "skills"
    root.mkdir()
    doc = root / "SKILL.md"
    doc.write_text("[Dash](https://dash.cloudflare.com/tokens)\n")
    out = tmp_path / "links.json"

    def fake_urlopen(req: object, timeout: int = 18) -> object:
        url = getattr(req, "full_url", str(req))
        code = 404 if "missing" in url else 403
        raise HTTPError(url, code, "denied", {}, None)  # type: ignore[arg-type]

    monkeypatch.setattr(audit_skill_links, "urlopen", fake_urlopen)

    assert main(["--root", str(root), "--output", str(out)]) == 1
    assert (
        main(
            [
                "--root",
                str(root),
                "--allow-unverified-403-host",
                "dash.cloudflare.com",
                "--output",
                str(out),
            ]
        )
        == 0
    )
    evidence = json.loads(out.read_text(encoding="utf-8"))
    assert evidence["findings"][0]["status"] == "unverified"
    assert evidence["findings"][0]["reason"] == "403"

    doc.write_text("[Dash](https://dash.cloudflare.com/tokens#sec)\n")
    assert (
        main(
            [
                "--root",
                str(root),
                "--allow-unverified-403-host",
                "dash.cloudflare.com",
                "--output",
                str(out),
            ]
        )
        == 1
    )

    doc.write_text("[Missing](https://dash.cloudflare.com/missing)\n")
    assert (
        main(
            [
                "--root",
                str(root),
                "--allow-unverified-403-host",
                "dash.cloudflare.com",
                "--output",
                str(out),
            ]
        )
        == 1
    )
