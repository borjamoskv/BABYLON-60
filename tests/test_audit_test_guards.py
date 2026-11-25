"""Negative controls for audit test prerequisites; no native runtime is launched."""

from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).absolute().parents[1]


def test_merkle_fixture_refreshes_existing_binary(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    namespace = runpy.run_path(str(ROOT / "tests/test_merkle_cross_bisimulation.py"))
    fixture = namespace["rust_bin"].__wrapped__
    binary = tmp_path / "target/debug/babylon-attest"
    binary.parent.mkdir(parents=True)
    binary.write_text("stale")
    monkeypatch.setitem(fixture.__globals__, "__file__", str(tmp_path / "tests/test_merkle.py"))
    calls = []

    def build(command: list[str], **kwargs: object) -> None:
        calls.append((command, kwargs))
        binary.write_text("fresh")

    monkeypatch.setattr(namespace["subprocess"], "run", build)
    assert fixture() == binary
    assert binary.read_text() == "fresh"
    assert calls[0][0] == [
        "cargo",
        "build",
        "--locked",
        "-p",
        "babylon-attest",
        "--target-dir",
        str(tmp_path / "target"),
    ]
    assert calls[0][1]["cwd"] == tmp_path
    assert calls[0][1]["check"] is True


@pytest.mark.parametrize("library_found", [False, True])
def test_native_gate_rejects_missing_or_unloadable_library(
    monkeypatch: pytest.MonkeyPatch,
    library_found: bool,
) -> None:
    namespace = runpy.run_path(str(ROOT / "tests/test_exergy_binary_ipc.py"))
    fixture = namespace["require_native_bridge_in_ci"].__wrapped__
    monkeypatch.setenv("BABYLON60_REQUIRE_NATIVE", "1")
    monkeypatch.setitem(
        fixture.__globals__, "find_babylon60_dylib", lambda: "/invalid/library" if library_found else None
    )

    class UnlinkedWriter:
        is_native = False

    monkeypatch.setitem(fixture.__globals__, "SharedManifestFFIWriter", UnlinkedWriter)
    with pytest.raises(AssertionError, match="Required native"):
        fixture()
