"""C0565 regression: the container compiler must satisfy the manifests' rust-version."""

import json
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "deploy" / "Dockerfile"


def _version(text: str) -> tuple[int, ...]:
    """Versión normalizada a tres componentes: "1.89" y "1.89.0" son iguales."""
    parts = [int(part) for part in text.split(".")]
    return tuple(parts + [0] * (3 - len(parts)))


def _required_rust_version() -> tuple[int, ...]:
    manifest = tomllib.loads((ROOT / "Cargo.toml").read_text(encoding="utf-8"))
    return _version(manifest["package"]["rust-version"])


def test_builder_image_satisfies_workspace_rust_version():
    images = re.findall(r"^FROM\s+rust:(\d+(?:\.\d+)+)", DOCKERFILE.read_text(encoding="utf-8"), re.M)
    assert images, "deploy/Dockerfile no declara una imagen rust:<versión> fijada"
    required = _required_rust_version()
    for image in images:
        assert _version(image) >= required, f"rust:{image} no satisface rust-version {required}"


def test_container_build_uses_locked_dependencies():
    builds = [line for line in DOCKERFILE.read_text(encoding="utf-8").splitlines() if "cargo build" in line]
    assert builds, "deploy/Dockerfile no ejecuta cargo build"
    assert all("--locked" in line for line in builds), "cargo build sin --locked en el contenedor"


def _dependency_msrv(package: str) -> tuple[tuple[int, ...], str]:
    """Highest rust-version declared across the locked normal/build dependency closure."""
    result = subprocess.run(
        ["cargo", "metadata", "--locked", "--offline", "--format-version", "1"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        pytest.skip(f"cargo metadata offline no disponible: {result.stderr.strip()[:200]}")
    meta = json.loads(result.stdout)
    packages = {p["id"]: p for p in meta["packages"]}
    nodes = {n["id"]: n for n in meta["resolve"]["nodes"]}
    root = next(p["id"] for p in meta["packages"] if p["name"] == package)
    seen, stack = set(), [root]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        for dep in nodes[current]["deps"]:
            if any(kind["kind"] in (None, "build") for kind in dep["dep_kinds"]):
                stack.append(dep["pkg"])
    declared = [
        (_version(packages[i]["rust_version"]), f"{packages[i]['name']} {packages[i]['version']}")
        for i in seen
        if packages[i].get("rust_version")
    ]
    return max(declared) if declared else ((0,), "ninguna")


def test_builder_image_satisfies_locked_dependency_msrv():
    if shutil.which("cargo") is None:
        pytest.skip("cargo no disponible")
    images = re.findall(r"^FROM\s+rust:(\d+(?:\.\d+)+)", DOCKERFILE.read_text(encoding="utf-8"), re.M)
    required, culprit = _dependency_msrv("babylon-attest")
    for image in images:
        assert _version(image) >= required, f"rust:{image} < MSRV {required} exigida por {culprit}"


def test_version_comparison_ignores_missing_patch_component():
    assert _version("1.89") == _version("1.89.0")
    assert _version("1.89") >= _version("1.89.0")
    assert _version("1.90") > _version("1.89.9")
