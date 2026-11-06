"""Synthetic credentials under keys/ must reach all secret scanning layers."""

import base64
import json
from pathlib import Path
import shutil
import subprocess
import struct
import zlib

import pytest

from scripts.c5_cli.opsec_sentinel_c5 import OpsecSentinelC5
from scripts.c5_quality_gates.secret_swarm_auditor import get_target_files, scan_file


@pytest.fixture
def credential_tree(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "workspace"
    key_dir = root / "keys" / "nested"
    key_dir.mkdir(parents=True)
    candidate = key_dir / "credentials.txt"
    # Synthetic and deliberately not the globally allowlisted AWS example.
    candidate.write_text('aws_access_key_id = "' + "AKIA" + "BCDEFGHIJKLMNOPQ" + '"\n')
    return root, candidate


def test_swarm_scans_nested_keys(credential_tree: tuple[Path, Path]) -> None:
    root, candidate = credential_tree
    targets = get_target_files(str(root))
    assert str(candidate) in targets
    assert "AWS_ACCESS_KEY" in {finding["type"] for finding in scan_file(str(candidate))}


def test_sentinel_scans_and_persists_nested_keys(credential_tree: tuple[Path, Path], tmp_path: Path) -> None:
    root, candidate = credential_tree
    sentinel = OpsecSentinelC5(str(root), str(tmp_path / "audit.sqlite"))
    report = sentinel.run_full_scan()
    assert report["violations_found"] == 1
    assert report["details"][0]["file_path"] == str(candidate.relative_to(root))
    assert report["details"][0]["violation_type"] == "AWS_ACCESS_KEY"


@pytest.mark.skipif(not shutil.which("gitleaks"), reason="gitleaks executable unavailable")
def test_gitleaks_scans_nested_keys(credential_tree: tuple[Path, Path], tmp_path: Path) -> None:
    root, candidate = credential_tree
    config = Path(__file__).parents[1] / ".gitleaks.toml"
    report_path = tmp_path / "report.json"
    result = subprocess.run(
        [
            "gitleaks",
            "detect",
            "--no-git",
            "--source",
            str(root),
            "--config",
            str(config),
            "--redact",
            "--no-banner",
            "--report-format",
            "json",
            "--report-path",
            str(report_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 1, result.stderr
    findings = json.loads(report_path.read_text())
    assert any(Path(finding["File"]).name == candidate.name for finding in findings)


def png_fixture() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    pixels = b"".join(b"\0" + bytes((row + column) % 256 for column in range(48)) for row in range(16))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 16, 16, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(pixels))
        + chunk(b"IEND", b"")
    )


def test_png_data_url_is_exempt_only_from_entropy(tmp_path: Path) -> None:
    path = tmp_path / "image.svg"
    encoded = base64.b64encode(png_fixture()).decode()
    path.write_text(f'<svg><image href="data:image/png;base64,{encoded}"/></svg>')
    assert scan_file(str(path)) == []
    path.write_text(
        f'<svg><image href="data:image/png;base64,{encoded}"/>aws_access_key_id="'
        + "AKIA"
        + "BCDEFGHIJKLMNOPQ"
        + '"</svg>'
    )
    assert "AWS_ACCESS_KEY" in {finding["type"] for finding in scan_file(str(path))}


def test_malformed_png_data_url_is_not_exempt(tmp_path: Path) -> None:
    png = bytearray(png_fixture())
    png[-1] ^= 1  # A plausible signature cannot excuse invalid PNG chunk integrity.
    encoded = base64.b64encode(png).decode()
    path = tmp_path / "malformed.svg"
    path.write_text(f'<svg><image href="data:image/png;base64,{encoded}"/></svg>')
    assert "HIGH_ENTROPY_STRING" in {finding["type"] for finding in scan_file(str(path))}


def test_png_exemption_preserves_other_svg_attribute_entropy(tmp_path: Path) -> None:
    encoded = base64.b64encode(png_fixture()).decode()
    outside = base64.b64encode(bytes(range(256))).decode()
    path = tmp_path / "image.svg"
    path.write_text(f'<svg data-external="{outside}"><image href="data:image/png;base64,{encoded}"/></svg>')
    assert "HIGH_ENTROPY_STRING" in {finding["type"] for finding in scan_file(str(path))}
