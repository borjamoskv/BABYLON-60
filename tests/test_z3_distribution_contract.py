"""Check the installed Z3 artifact, independently of a successful native import."""

from email.parser import Parser
from importlib.metadata import distribution
from pathlib import Path
import tomllib
from urllib.parse import unquote, urlsplit

from packaging.tags import Tag, parse_tag, sys_tags
from packaging.utils import parse_wheel_filename
from packaging.version import Version
import pytest
import z3


def _compatible_tags(wheel_metadata: str, supported: set[Tag]) -> set[Tag]:
    headers = Parser().parsestr(wheel_metadata)
    declared = set().union(*(parse_tag(value) for value in headers.get_all("Tag", [])))
    assert declared, "Z3 WHEEL metadata has no compatibility tags"
    assert declared & supported, f"Z3 WHEEL tags are incompatible with this interpreter: {declared}"
    return declared


def test_installed_z3_wheel_tags_match_interpreter_and_locked_filename() -> None:
    installed = distribution("z3-solver")
    metadata = installed.read_text("WHEEL")
    assert metadata is not None, "Installed Z3 distribution has no WHEEL metadata"
    supported = set(sys_tags())
    declared = _compatible_tags(metadata, supported)

    # An older environment must still exercise its own metadata, not the lock's release.
    lock = tomllib.loads((Path(__file__).absolute().parents[1] / "uv.lock").read_text())
    candidates = []
    for package in lock["package"]:
        if package["name"] != "z3-solver" or Version(package["version"]) != Version(installed.version):
            continue
        for wheel in package.get("wheels", []):
            filename = Path(unquote(urlsplit(wheel["url"]).path)).name
            _, _, _, filename_tags = parse_wheel_filename(filename)
            if filename_tags & supported:
                candidates.append(filename_tags)
    if candidates:
        assert declared in candidates, "Installed Z3 WHEEL tags differ from compatible locked wheel filenames"


@pytest.fixture
def broken_macos_wheel_metadata() -> str:
    return "Wheel-Version: 1.0\nTag: py3-none-macosx_13_3_arm64\n\n"


def test_rejects_incompatible_internal_wheel_tag(broken_macos_wheel_metadata: str) -> None:
    supported = {Tag("py3", "none", "macosx_13_0_arm64")}
    valid_metadata = broken_macos_wheel_metadata.replace("macosx_13_3", "macosx_13_0")
    assert _compatible_tags(valid_metadata, supported) == supported
    with pytest.raises(AssertionError, match="incompatible with this interpreter"):
        _compatible_tags(broken_macos_wheel_metadata, supported)


def test_installed_z3_native_solver_distinguishes_sat_and_unsat() -> None:
    value = z3.Int("distribution_contract_value")
    solver = z3.Solver()
    solver.set(timeout=2000)
    solver.add(value > 0)
    assert solver.check() == z3.sat
    solver.add(value < 0)
    assert solver.check() == z3.unsat
